
import sqlite3
import requests
import time

from config import USUARIO_AIO, AIO_KEY, FEEDS, RUTA_DB

# Dirección de la API de Adafruit IO
URL_BASE = f"https://io.adafruit.com/api/v2/{USUARIO_AIO}/feeds"

# Encabezado de autenticación
ENCABEZADOS = {
    "X-AIO-Key": AIO_KEY
}

# Intervalo de consulta: 15 segundos
INTERVALO = 15


def conectar_bd():
    """Conecta con la base de datos SQLite."""
    return sqlite3.connect(RUTA_DB)


def obtener_ultima_lectura(feed):
    """Consulta la última lectura de un feed."""
    url = f"{URL_BASE}/{feed}/data/last"

    respuesta = requests.get(
        url,
        headers=ENCABEZADOS,
        timeout=15
    )

    respuesta.raise_for_status()
    return respuesta.json()


def guardar_medicion(feed, dato):
    """Guarda una lectura nueva en SQLite."""
    conexion = conectar_bd()
    cursor = conexion.cursor()

    valor = float(dato["value"])
    fecha = dato["created_at"]

    # Evitar guardar dos veces la misma lectura
    cursor.execute("""
        SELECT id FROM mediciones
        WHERE variable = ? AND fecha_hora = ?
    """, (feed, fecha))

    existe = cursor.fetchone()

    if existe is None:
        cursor.execute("""
            INSERT INTO mediciones
            (variable, valor, fecha_hora)
            VALUES (?, ?, ?)
        """, (feed, valor, fecha))

        conexion.commit()

        print(f"[GUARDADO] {feed}: {valor} | {fecha}")
    else:
        print(f"[SIN CAMBIOS] {feed}: lectura ya almacenada")

    conexion.close()


def iniciar_ingesta():
    """Consulta los feeds y almacena sus lecturas."""
    print("Iniciando almacenamiento de Adafruit IO...")
    print("Presiona CTRL + C para detener el programa.")

    while True:
        for feed in FEEDS:
            try:
                dato = obtener_ultima_lectura(feed)
                guardar_medicion(feed, dato)

            except requests.exceptions.RequestException as error:
                print(f"[ERROR DE CONEXION] {feed}: {error}")

            except (KeyError, ValueError, TypeError) as error:
                print(f"[ERROR DE DATOS] {feed}: {error}")

        print("Ciclo terminado. Esperando 15 segundos...\n")
        time.sleep(INTERVALO)


if __name__ == "__main__":
    try:
        iniciar_ingesta()
    except KeyboardInterrupt:
        print("\nPrograma detenido por el usuario.")
