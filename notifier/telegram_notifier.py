# notifier/telegram_notifier.py
import os
import time
import telegram
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- CONFIGURACIÓN ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
MONITOR_DIR = '/app/videos/inbox' # Debe coincidir con el volumeMountPath
# ---------------------

class VideoHandler(FileSystemEventHandler):
    """Maneja los eventos de creación de archivos."""
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.mp4'):
            print(f"Nuevo video detectado: {event.src_path}")
            # Se usa una espera corta para asegurar que el archivo terminó de escribirse
            time.sleep(1) 
            send_video_to_telegram(event.src_path)

def send_video_to_telegram(video_path):
    """Envía el video a través del bot de Telegram."""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("ERROR: Token de Telegram o Chat ID no configurado.")
        return

    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        
        # Enviar el video
        with open(video_path, 'rb') as video_file:
            # Puedes añadir un caption con la hora y fecha de la detección
            caption = f"🚨 Detección de Vehículo/Persona el {time.strftime('%Y-%m-%d %H:%M:%S')}."
            bot.send_video(chat_id=CHAT_ID, video=video_file, caption=caption)
        
        print(f"Video enviado a Telegram exitosamente.")
        
        # Limpieza: Eliminar el archivo después de enviarlo
        os.remove(video_path)
        print(f"Archivo eliminado: {video_path}")
        
    except Exception as e:
        print(f"ERROR al enviar video a Telegram: {e}")

def main():
    if not os.path.exists(MONITOR_DIR):
        os.makedirs(MONITOR_DIR)
        print(f"Directorio a monitorear creado: {MONITOR_DIR}")

    event_handler = VideoHandler()
    observer = Observer()
    observer.schedule(event_handler, MONITOR_DIR, recursive=False)
    observer.start()
    
    print(f"Monitoreando directorio: {MONITOR_DIR}. Esperando videos...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
