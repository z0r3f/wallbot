# syntax=docker/dockerfile:1

FROM python:3.12-slim-bookworm

# Variables de entorno para Python y localización
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LANG=es_ES.UTF-8 \
    LC_ALL=es_ES.UTF-8 \
    TZ=Europe/Madrid

# Instalar locales, generar es_ES.UTF-8 y limpiar temporales de apt
RUN apt-get update && \
    apt-get install -y --no-install-recommends locales tzdata && \
    sed -i -e 's/# es_ES.UTF-8 UTF-8/es_ES.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Crear directorios de persistencia
RUN mkdir -p /data /logs

# Aprovechar la caché de Docker para las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente y archivos de versión
COPY VERSION .
COPY src/ ./src/

CMD ["python", "-m", "src.wallbot"]
