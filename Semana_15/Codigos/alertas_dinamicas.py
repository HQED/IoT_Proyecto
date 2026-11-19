
import os
import time
import logging
from statistics import mean, stdev

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from config import INFLUXDB_URL, INFLUXDB_ORG, INFLUXDB_BUCKET


# =====================================================
# CONFIGURACIÓN DEL MONITOREO
# =====================================================

AULA = "Aula 101"
ORIGEN = "real"
VARIABLE = "temperatura"

INTERVALO = 15
PERIODO_HISTORICO = "-7d"

TOKEN = os.getenv("INFLUXDB_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "No se encontró INFLUXDB_TOKEN en las variables de entorno."
    )


# =====================================================
# CONFIGURACIÓN DEL REGISTRO DE ALERTAS
# =====================================================

logging.basicConfig(
    filename="alertas.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8"
)


# =====================================================
# CONSULTAR EL HISTÓRICO DE TEMPERATURA
# =====================================================

def consultar_historico(query_api):

    consulta = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: {PERIODO_HISTORICO})
        |> filter(fn: (r) => r["_measurement"] == "monitoreo_aula")
        |> filter(fn: (r) => r["_field"] == "valor")
        |> filter(fn: (r) => r["variable"] == "{VARIABLE}")
        |> filter(fn: (r) => r["aula_id"] == "{AULA}")
        |> filter(fn: (r) => r["origen"] == "{ORIGEN}")
    '''

    tablas = query_api.query(consulta, org=INFLUXDB_ORG)

    temperaturas = []

    for tabla in tablas:
        for registro in tabla.records:
            temperaturas.append(float(registro.get_value()))

    return temperaturas


# =====================================================
# CONSULTAR LA TEMPERATURA MÁS RECIENTE
# =====================================================

def consultar_temperatura_actual(query_api):

    consulta = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: -1h)
        |> filter(fn: (r) => r["_measurement"] == "monitoreo_aula")
        |> filter(fn: (r) => r["_field"] == "valor")
        |> filter(fn: (r) => r["variable"] == "{VARIABLE}")
        |> filter(fn: (r) => r["aula_id"] == "{AULA}")
        |> filter(fn: (r) => r["origen"] == "{ORIGEN}")
        |> last()
    '''

    tablas = query_api.query(consulta, org=INFLUXDB_ORG)

    for tabla in tablas:
        for registro in tabla.records:
            return (
                float(registro.get_value()),
                registro.get_time()
            )

    return None, None


# =====================================================
# CALCULAR EL UMBRAL DINÁMICO
# =====================================================

def calcular_umbral(temperaturas):

    if len(temperaturas) < 2:
        return None, None, None

    promedio = mean(temperaturas)
    desviacion = stdev(temperaturas)

    # Fórmula solicitada por el profesor:
    # Umbral = media + 2 * desviación estándar
    umbral = promedio + (2 * desviacion)

    return promedio, desviacion, umbral


# =====================================================
# GUARDAR RESULTADOS DEL MONITOREO EN INFLUXDB
# =====================================================

def guardar_estado(
    write_api,
    temperatura,
    promedio,
    desviacion,
    umbral,
    fecha
):

    # Calcular el límite intermedio de precaución
    limite_precaucion = promedio + desviacion

    # Clasificar el estado de temperatura
    if temperatura > umbral:
        estado = 2
        nombre_estado = "ALERTA"

    elif temperatura >= limite_precaucion:
        estado = 1
        nombre_estado = "PRECAUCION"

    else:
        estado = 0
        nombre_estado = "NORMAL"

    # Crear un registro independiente para las alertas.
    # Esto evita conflictos con los datos de monitoreo_aula.
    punto = (
        Point("alertas_dinamicas")
        .tag("aula_id", AULA)
        .tag("origen", ORIGEN)
        .field("temperatura_actual", float(temperatura))
        .field("promedio_historico", float(promedio))
        .field("desviacion_estandar", float(desviacion))
        .field("umbral_dinamico", float(umbral))
        .field("limite_precaucion", float(limite_precaucion))
        .field("estado", int(estado))
        .time(fecha)
    )

    # Guardar el registro en InfluxDB
    write_api.write(
        bucket=INFLUXDB_BUCKET,
        org=INFLUXDB_ORG,
        record=punto
    )

    print(f"Estado dinámico: {nombre_estado}")
    print(f"Código de estado: {estado}")
    print(f"Límite de precaución: {limite_precaucion:.2f} °C")
    print(f"Umbral guardado: {umbral:.2f} °C")

    return estado


# =====================================================
# PROCESO PRINCIPAL DE MONITOREO
# =====================================================

def iniciar_monitoreo():

    print("Iniciando sistema de alertas dinámicas...")
    print(f"Aula monitoreada: {AULA}")
    print(f"Periodo histórico: {PERIODO_HISTORICO}")
    print("Presiona Ctrl + C para detener el programa.\n")

    ultima_fecha = None

    with InfluxDBClient(
        url=INFLUXDB_URL,
        token=TOKEN,
        org=INFLUXDB_ORG
    ) as cliente:

        query_api = cliente.query_api()

        write_api = cliente.write_api(
            write_options=SYNCHRONOUS
        )

        try:

            while True:

                try:

                    # Consultar las temperaturas históricas
                    temperaturas = consultar_historico(query_api)

                    if len(temperaturas) < 2:
                        print(
                            "Se necesitan al menos dos mediciones "
                            "históricas para calcular el umbral."
                        )
                        time.sleep(INTERVALO)
                        continue

                    # Calcular las estadísticas históricas
                    promedio, desviacion, umbral = calcular_umbral(
                        temperaturas
                    )

                    # Consultar la última temperatura
                    temperatura, fecha = consultar_temperatura_actual(
                        query_api
                    )

                    if temperatura is None:
                        print("No hay una temperatura reciente disponible.")
                        time.sleep(INTERVALO)
                        continue

                    # Evitar procesar la misma lectura
                    if fecha == ultima_fecha:
                        time.sleep(INTERVALO)
                        continue

                    ultima_fecha = fecha

                    print("--------------------------------------")
                    print(f"Temperatura actual: {temperatura:.2f} °C")
                    print(f"Promedio histórico: {promedio:.2f} °C")
                    print(f"Desviación estándar: {desviacion:.2f}")
                    print(f"Umbral dinámico: {umbral:.2f} °C")

                    # Guardar los cálculos y el estado en InfluxDB
                    estado = guardar_estado(
                        write_api,
                        temperatura,
                        promedio,
                        desviacion,
                        umbral,
                        fecha
                    )

                    # Registrar las alertas
                    if estado == 2:

                        mensaje = (
                            f"ALERTA: Temperatura de {temperatura:.2f} °C. "
                            f"Supera el umbral de {umbral:.2f} °C."
                        )

                        print(mensaje)
                        logging.warning(mensaje)

                    elif estado == 1:

                        mensaje = (
                            f"PRECAUCIÓN: Temperatura de "
                            f"{temperatura:.2f} °C. "
                            f"Se aproxima al umbral dinámico."
                        )

                        print(mensaje)
                        logging.warning(mensaje)

                    else:

                        print("Estado normal. No se detectan anomalías.")

                except Exception as error:

                    print(f"Error durante el monitoreo: {error}")

                    logging.error(
                        "Error durante el monitoreo: %s",
                        error
                    )

                time.sleep(INTERVALO)

        finally:
            write_api.close()


# =====================================================
# EJECUCIÓN DEL PROGRAMA
# =====================================================

if __name__ == "__main__":

    try:
        iniciar_monitoreo()

    except KeyboardInterrupt:
        print("\nMonitoreo detenido por el usuario.")
