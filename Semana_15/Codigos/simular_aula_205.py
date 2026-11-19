import os
import time
import random

from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

from config import INFLUXDB_URL, INFLUXDB_ORG, INFLUXDB_BUCKET

# Token de InfluxDB guardado en la variable de entorno
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")

# Comprobar que existe el token
if not INFLUXDB_TOKEN:
    raise ValueError("No se encontró el token de InfluxDB.")

# Conectar con InfluxDB
cliente = InfluxDBClient(
    url=INFLUXDB_URL,
    token=INFLUXDB_TOKEN,
    org=INFLUXDB_ORG
)

write_api = cliente.write_api(write_options=SYNCHRONOUS)

# Valores iniciales de la simulación
temperatura = 27.0
humedad = 60.0
luminosidad = 1500.0

print("Simulación iniciada para el Aula 205.")
print("Los datos se guardarán en InfluxDB cada 15 segundos.")
print("Presiona Ctrl + C para detenerla.")

try:
    while True:

        # Generar pequeñas variaciones en las mediciones
        temperatura += random.uniform(-0.4, 0.4)
        humedad += random.uniform(-1.5, 1.5)
        luminosidad += random.uniform(-80, 80)

        # Mantener los valores dentro de rangos razonables
        temperatura = max(22, min(temperatura, 35))
        humedad = max(40, min(humedad, 80))
        luminosidad = max(100, min(luminosidad, 4000))

        mediciones = {
            "temperatura": round(temperatura, 2),
            "humedad": round(humedad, 2),
            "luminosidad": round(luminosidad, 2)
        }

        # Guardar cada variable en InfluxDB
        for variable, valor in mediciones.items():

            punto = (
                Point("monitoreo_aula")
                .tag("aula_id", "Aula 205")
                .tag("origen", "simulado")
                .tag("variable", variable)
                .field("valor", valor)
                .time(datetime.now(timezone.utc), WritePrecision.S)
            )

            write_api.write(
                bucket=INFLUXDB_BUCKET,
                org=INFLUXDB_ORG,
                record=punto
            )

            print(f"{variable}: {valor} guardado correctamente")

        print("Esperando 15 segundos...\n")
        time.sleep(15)

except KeyboardInterrupt:
    print("\nSimulación detenida.")

finally:
    write_api.close()
    cliente.close()