
import os
import time
import requests

from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

from config import (
    USUARIO_AIO,
    AIO_KEY,
    INFLUXDB_URL,
    INFLUXDB_ORG,
    INFLUXDB_BUCKET
)


# =====================================================
# CONFIGURACIÓN
# =====================================================

URL_ADAFRUIT = f"https://io.adafruit.com/api/v2/{USUARIO_AIO}"

TOKEN_INFLUXDB = os.getenv("INFLUXDB_TOKEN")

INTERVALO = 15

AULA = "Aula 101"
ORIGEN = "real"

FEEDS = [
    "temperatura",
    "humedad",
    "luminosidad"
]


# =====================================================
# CONEXIÓN CON ADAFRUIT IO
# =====================================================

def obtener_ultima_medicion(feed):
    url = f"{URL_ADAFRUIT}/feeds/{feed}/data/last"

    respuesta = requests.get(
        url,
        auth=(USUARIO_AIO, AIO_KEY),
        timeout=15
    )

    respuesta.raise_for_status()

    return respuesta.json()


# =====================================================
# TRANSFERENCIA A INFLUXDB
# =====================================================

def guardar_en_influx(write_api, feed, medicion):

    valor = float(medicion["value"])

    fecha = datetime.fromisoformat(
        medicion["created_at"].replace("Z", "+00:00")
    )

    punto = (
        Point("monitoreo_aula")
        .tag("aula_id", AULA)
        .tag("origen", ORIGEN)
        .tag("variable", feed)
        .field("valor", valor)
        .time(fecha, WritePrecision.S)
    )

    write_api.write(
        bucket=INFLUXDB_BUCKET,
        org=INFLUXDB_ORG,
        record=punto
    )

    print(
        f"{feed}: {valor} | "
        f"Fecha: {fecha.isoformat()} | Guardado en InfluxDB"
    )


# =====================================================
# PROGRAMA PRINCIPAL
# =====================================================

def iniciar_transferencia():

    if not TOKEN_INFLUXDB:
        raise RuntimeError(
            "No se encontró la variable INFLUXDB_TOKEN."
        )

    print("Iniciando transferencia Adafruit IO -> InfluxDB")
    print(f"Aula: {AULA}")
    print(f"Intervalo: {INTERVALO} segundos")
    print("Presiona Ctrl + C para detener.\n")

    ultima_fecha = {}

    with InfluxDBClient(
        url=INFLUXDB_URL,
        token=TOKEN_INFLUXDB,
        org=INFLUXDB_ORG
    ) as cliente:

        write_api = cliente.write_api(
            write_options=SYNCHRONOUS
        )

        while True:
            for feed in FEEDS:

                try:
                    medicion = obtener_ultima_medicion(feed)

                    fecha = medicion["created_at"]

                    # Evita guardar varias veces la misma lectura
                    if ultima_fecha.get(feed) == fecha:
                        continue

                    guardar_en_influx(
                        write_api,
                        feed,
                        medicion
                    )

                    ultima_fecha[feed] = fecha

                except requests.RequestException as error:
                    print(f"Error consultando {feed}: {error}")

                except Exception as error:
                    print(f"Error procesando {feed}: {error}")

            print("\nEsperando nuevas mediciones...\n")
            time.sleep(INTERVALO)


# =====================================================
# EJECUCIÓN
# =====================================================

if __name__ == "__main__":

    try:
        iniciar_transferencia()

    except KeyboardInterrupt:
        print("\nTransferencia detenida por el usuario.")
