# Imagen base oficial de Python en su versión liviana (slim)
# "slim" significa que no tiene herramientas innecesarias del SO
# reduce el tamaño de la imagen final
FROM python:3.13-slim

# Define /app como el directorio de trabajo dentro del contenedor
# todos los comandos siguientes se ejecutan desde acá
# equivale a hacer: mkdir /app && cd /app
WORKDIR /app

# Copia SOLO el archivo de dependencias primero
# Se hace antes de copiar el código para aprovechar el cache de Docker:
# si requirements.txt no cambió, Docker reutiliza esta capa
# y no reinstala todo desde cero en el próximo build
COPY requirements.txt .

# Instala todas las dependencias Python listadas en requirements.txt
# --no-cache-dir: no guarda el cache de pip dentro de la imagen
# reduce el tamaño final de la imagen
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el código fuente al contenedor
# Se hace DESPUÉS de instalar dependencias para aprovechar el cache:
# si solo cambió el código pero no requirements.txt,
# Docker reutiliza la capa de pip install (más rápido)
COPY . .

# Documenta que el contenedor escucha en el puerto 8000
# Es solo informativo — no abre el puerto por sí solo
# Render usa $PORT en el CMD para saber dónde conectarse
EXPOSE 8000

# Comando que se ejecuta cuando el contenedor arranca
# Se usa "sh -c" para poder encadenar dos comandos con &&
CMD ["sh", "-c", 

  # Comando 1: crear las tablas en la base de datos
  # Se ejecuta ANTES de arrancar el servidor
  # Importa el engine (conexión a la DB) y los models (definición de tablas)
  # create_all() crea las tablas si no existen, no las toca si ya existen
  # Si DATABASE_URL apunta a PostgreSQL → crea las tablas ahí
  # Si DATABASE_URL apunta a SQLite → crea el archivo database.db
  "python -c 'from database import engine; import models; models.Base.metadata.create_all(bind=engine)'"

  # && significa: ejecutar el siguiente comando SOLO si el anterior fue exitoso
  # Si create_all falla (ej: no puede conectarse a la DB) → uvicorn no arranca
  " && "

  # Comando 2: arrancar el servidor web
  # uvicorn: el servidor ASGI que corre FastAPI
  # main:app: busca el objeto "app" dentro de "main.py"
  # --host 0.0.0.0: acepta conexiones de cualquier IP (necesario en Docker)
  # --port $PORT: usa el puerto que Render define en la variable $PORT
  #               Render asigna el puerto dinámicamente — siempre usar $PORT
  #               nunca hardcodear un número fijo acá
  "uvicorn main:app --host 0.0.0.0 --port $PORT"
]
