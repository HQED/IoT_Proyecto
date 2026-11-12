
import sqlite3

# Ruta de nuestra base de datos
RUTA_DB = r"D:\Bases_Datos_SQLite_Browser\monitoreo_aula\monitoreo_aula.db"

# Conectar con SQLite
conexion = sqlite3.connect(RUTA_DB)
cursor = conexion.cursor()

# Crear tabla para almacenar las mediciones
cursor.execute("""
CREATE TABLE IF NOT EXISTS mediciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variable TEXT NOT NULL,
    valor REAL NOT NULL,
    fecha_hora TEXT NOT NULL
)
""")

# Guardar los cambios
conexion.commit()

# Cerrar la conexión
conexion.close()

print("Base de datos y tabla creadas correctamente.")
