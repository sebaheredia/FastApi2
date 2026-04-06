# Imagen base oficial de Python liviana
FROM python:3.13-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar e instalar dependencias primero (aprovecha cache de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Puerto que expone el contenedor
EXPOSE 8000

# Comando para levantar la API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
