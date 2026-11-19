import os

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime, timezone

from config import INFLUXDB_URL, INFLUXDB_ORG, INFLUXDB_BUCKET

# Leer el token desde la variable de entorno
TOKEN = os.getenv("INFLUXDB_TOKEN")

if not TOKEN:
    raise ValueError("No se encontró el token de InfluxDB.")

# Conectar con InfluxDB
cliente = InfluxDBClient(
    url=INFLUXDB_URL,
    token=TOKEN,
    org=INFLUXDB_ORG
)

write_api = cliente.write_api(write_options=SYNCHRONOUS)

try:
    # Crear una lectura artificial de temperatura
    punto = (
        Point("monitoreo_aula")
        .tag("aula_id", "Aula 101")
        .tag("origen", "real")
        .tag("variable", "temperatura")
        .field("valor", 40.0)
        .time(datetime.now(timezone.utc), WritePrecision.NS)
    )

    write_api.write(
        bucket=INFLUXDB_BUCKET,
        org=INFLUXDB_ORG,
        record=punto
    )

    print("Temperatura de prueba: 40 °C")
    print("Lectura guardada correctamente en InfluxDB.")

finally:
    write_api.close()
    cliente.close()