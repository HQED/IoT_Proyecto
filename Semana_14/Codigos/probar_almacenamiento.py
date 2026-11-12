
import sqlite3
from datetime import datetime

# Ruta de nuestra base de datos
RUTA_DB = r"D:\Bases_Datos_SQLite_Browser\monitoreo_aula\monitoreo_aula.db"

# Conectar con SQLite
conexion = sqlite3.connect(RUTA_DB)
cursor = conexion.cursor()

# Datos de prueba
mediciones = [
    ("temperatura", 28.5),
    ("humedad", 62.0),
    ("luminosidad", 1201)
]

# Guardar cada medición
for variable, valor in mediciones:
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO mediciones (variable, valor, fecha_hora)
        VALUES (?, ?, ?)
    """, (variable, valor, fecha))

# Confirmar los cambios
conexion.commit()
conexion.close()

print("Mediciones guardadas correctamente.")
