# processor/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema para OpenCV
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    # Dependencia genérica de OpenGL que incluye GLX
    libgl1 \
    # Dependencias de X11/GUI necesarias para OpenCV
    libsm6 \
    libxext6 \
    libxrender1 \
    libfontconfig1 \
    # Herramienta para manejo de video
    ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código y el modelo (asegúrate de que yolov8n.pt esté en el directorio)
COPY rtsp_processor.py .
COPY yolov8n.pt . 

CMD ["python", "rtsp_processor.py"]
