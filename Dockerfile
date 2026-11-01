FROM python:3.11-slim

WORKDIR /app

# PYTHONPATH necesario para que uvicorn encuentre src.main:app
ENV PYTHONPATH=/app/src

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero para cachear capa de dependencias
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente manteniendo estructura backend/src/ -> /app/src/
COPY backend/src/ /app/src/

# Crear directorio de uploads con permisos de escritura
RUN mkdir -p /app/src/uploads /app/data && chmod 777 /app/src/uploads /app/data

# Crear archivo de BD vacío si no existe
RUN touch /app/src/analizer.db && chmod 666 /app/src/analizer.db

# Exponer puerto
EXPOSE 8000

# Comando de inicio (respeta $PORT en plataformas como Render)
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
