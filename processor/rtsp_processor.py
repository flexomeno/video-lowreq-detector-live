# processor/rtsp_processor.py
import cv2
import os
import time
from ultralytics import YOLO # Importa la librería para el modelo YOLO

# --- CONFIGURACIÓN ---
# Las variables de entorno serán inyectadas por Kubernetes Secret
RTSP_URL = os.getenv('RTSP_URL', 'rtsp://user:pass@simulated-camera-ip/stream')
OUTPUT_DIR = '/app/videos' # Debe coincidir con el volumeMountPath en el Deployment
MODEL_PATH = 'yolov8n.pt' # Modelo Nano optimizado para CPU
FRAME_SKIP = 5 # Procesar 1 de cada 5 cuadros (aprox. 5-6 FPS)
VIDEO_DURATION_SECONDS = 10
# ---------------------

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Directorio de salida creado: {OUTPUT_DIR}")

    # 1. Cargar el modelo YOLO
    # Se recomienda usar la versión 'n' (nano) para CPU
    try:
        model = YOLO(MODEL_PATH)
        print("Modelo YOLOv8 Nano cargado exitosamente.")
    except Exception as e:
        print(f"Error al cargar el modelo: {e}")
        return

    # 2. Conectar al stream RTSP
    cap = cv2.VideoCapture(RTSP_URL)
    if not cap.isOpened():
        print(f"ERROR: No se pudo conectar al stream RTSP en {RTSP_URL}. Reintentando en 10s...")
        time.sleep(10)
        return main() # Intenta de nuevo

    print(f"Conectado exitosamente al stream RTSP.")

    frame_count = 0
    recording = False
    video_writer = None
    frames_buffer = [] # Para almacenar los frames previos a la detección (buffer de 5s)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Stream finalizado o error de lectura. Reiniciando conexión...")
            cap.release()
            return main()

        frame_count += 1
        
        # Almacena el frame actual en el buffer
        frames_buffer.append(frame)
        if len(frames_buffer) > 30 * 5: # Mantener un buffer de 5 segundos (asumiendo 30 FPS teóricos)
            frames_buffer.pop(0)

        # 3. Detección (solo en cuadros seleccionados para ahorrar CPU)
        if frame_count % FRAME_SKIP == 0:
            
            # --- Ejecutar Detección ---
            # Detección de objetos: 0 es persona, 2 es carro en COCO
            results = model.predict(frame, classes=[0, 2], conf=0.5, verbose=False) 
            
            detection_found = False
            for r in results:
                if len(r.boxes) > 0:
                    detection_found = True
                    break
            
            # 4. Lógica de Grabación
            if detection_found and not recording:
                print("¡Detección de Persona/Carro! Iniciando grabación...")
                recording = True
                
                # Configura el grabador de video
                filename = os.path.join(OUTPUT_DIR, f"detection_{int(time.time())}.mp4")
                fps = cap.get(cv2.CAP_PROP_FPS) or 25.0 # Usar 25 FPS por defecto si la cámara no lo indica
                width, height = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
                video_writer = cv2.VideoWriter(filename, fourcc, fps, (width, height))

                # Escribe el buffer (los frames previos) al inicio del video
                for buffered_frame in frames_buffer:
                    video_writer.write(buffered_frame)
                
                start_time = time.time()

            if recording:
                # 5. Continúa grabando hasta alcanzar la duración
                video_writer.write(frame)
                
                if time.time() - start_time >= VIDEO_DURATION_SECONDS:
                    print(f"Grabación de {VIDEO_DURATION_SECONDS}s completa. Archivo: {filename}")
                    video_writer.release()
                    recording = False
                    frames_buffer = [] # Limpiar el buffer después de grabar

        # Pequeña pausa para evitar el uso excesivo de CPU en el bucle
        time.sleep(0.01)

if __name__ == "__main__":
    main()
