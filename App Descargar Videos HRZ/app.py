# Autor: Andrés Hincapie Ruiz (A.HRZ)
# Fecha de creación: 16 de diciembre de 2024
# Aplicación principal para el descargador de YouTube

# Importo las bibliotecas necesarias para mi aplicación
from flask import Flask, request, jsonify, send_file  # Necesito Flask para crear mi servidor web
import yt_dlp  # Esta es mi herramienta principal para descargar videos
import os  # La uso para manejar directorios y archivos
import logging  # Para registrar eventos y debuggear mi aplicación
from pathlib import Path  # Me ayuda a manejar rutas de archivos de manera más eficiente
import subprocess
import platform

# Configuro el sistema de logging para hacer seguimiento a los eventos de mi aplicación
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Inicializo mi aplicación Flask con la configuración de archivos estáticos
app = Flask(__name__, static_folder='static', static_url_path='/static')

# Variable global para almacenar el progreso
download_progress = 0
is_converting = False
conversion_started = False

# Defino mi ruta principal que servirá la página de inicio- 
@app.route('/')
def home():
    try:
        return app.send_static_file('index.html')  # Envío mi archivo HTML principal
    except Exception as e:
        logger.error(f"Error al servir index.html: {str(e)}")  # Registro cualquier error que ocurra
        return jsonify({'error': 'Error interno del servidor'}), 500

def sanitize_filename(filename):
    # Reemplazar caracteres especiales y espacios -
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'ñ': 'n', 'Ñ': 'N',
        ' ': '_', '-': '_',
        '(': '', ')': '',
        '[': '', ']': '',
        "'": '', '"': ''
    }
    
    # Aplicar reemplazos
    for old, new in replacements.items():
        filename = filename.replace(old, new)
    
    # Eliminar otros caracteres especiales
    filename = ''.join(c for c in filename if c.isalnum() or c in '._')
    return filename

# Mi ruta principal para manejar las descargas
@app.route('/descargar')
def descargar():
    global download_progress
    download_progress = 0
    
    try:
        # Obtengo los parámetros de la solicitud
        url = request.args.get('url')  # URL del video a descargar
        format = request.args.get('format')  # Formato deseado (mp3 o mp4)
        quality = request.args.get('quality', 'highest')  # Calidad del video
        
        # Registro el inicio de la descarga para seguimiento
        logger.info(f"Iniciando descarga - URL: {url}, Formato: {format}, Calidad: {quality}")
        
        # Verifico que se haya proporcionado una URL
        if not url:
            return jsonify({'success': False, 'error': 'URL no proporcionada'})

        # Configuro las rutas de mis directorios de descarga
        base_dir = os.path.abspath(os.path.dirname(__file__))
        audio_dir = os.path.join(base_dir, 'descargas', 'audio')
        video_dir = os.path.join(base_dir, 'descargas', 'video')

        # Me aseguro de que existan mis directorios de descarga
        os.makedirs(audio_dir, exist_ok=True)
        os.makedirs(video_dir, exist_ok=True)

        # Selecciono el directorio apropiado según el formato
        descargas_dir = audio_dir if format == 'mp3' else video_dir

        # Configuro la ruta a mi ejecutable de ffmpeg
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ffmpeg_location = os.path.join(current_dir, 'ffmpeg.exe')

        # Establezco la calidad del video según la selección del usuario
        format_string = {
            'highest': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',  # Máxima calidad disponible
            '720p': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',  # Calidad 720p
            '480p': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best',  # Calidad 480p
            '360p': 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best'   # Calidad 360p
        }.get(quality, 'best')

        # Configuro las opciones para descarga de MP3
        if format == 'mp3':
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': '%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'prefer_ffmpeg': True,
                'ffmpeg_location': ffmpeg_location,
                'keepvideo': False,
                'progress_hooks': [my_hook],
                'paths': {'home': descargas_dir},
                'restrictfilenames': True,  # Usar nombres de archivo más seguros
                'windowsfilenames': True    # Asegurar compatibilidad con Windows
            }
        # Configuro las opciones para descarga de MP4
        else:
            ydl_opts = {
                'format': format_string,
                'outtmpl': '%(title)s.%(ext)s',
                'prefer_ffmpeg': True,
                'ffmpeg_location': ffmpeg_location,
                'progress_hooks': [my_hook],
                'paths': {'home': descargas_dir},
                'restrictfilenames': True,  # Usar nombres de archivo más seguros
                'windowsfilenames': True    # Asegurar compatibilidad con Windows
            }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info['title']
                
                # Guardar tanto el nombre original como el nombre sanitizado
                sanitized_title = sanitize_filename(title)
                
                if format == 'mp3':
                    filename = f"{sanitized_title}.mp3"
                    display_filename = f"{title}.mp3"
                else:
                    filename = f"{sanitized_title}.mp4"
                    display_filename = f"{title}.mp4"
                
                full_path = os.path.join(descargas_dir, filename)

                return jsonify({
                    'success': True,
                    'message': f'{"Audio" if format == "mp3" else "Video"} descargado exitosamente',
                    'file': display_filename,
                    'sanitized_file': filename,
                    'full_path': full_path
                })

        except Exception as e:
            logger.error(f"Error en la descarga: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'error': f'Error en la descarga: {str(e)}'})

    except Exception as e:
        logger.error(f"Error general: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': f'Error general: {str(e)}'})

@app.route('/obtener-info')
def obtener_info():
    try:
        url = request.args.get('url')
        if not url:
            return jsonify({'success': False, 'error': 'URL no proporcionada'})

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Formatear la duración
            duration_seconds = info.get('duration', 0)
            minutes = duration_seconds // 60
            seconds = duration_seconds % 60
            duration = f"{minutes}:{seconds:02d}"

            return jsonify({
                'success': True,
                'title': info.get('title', ''),
                'thumbnail': info.get('thumbnail', ''),
                'duration': duration
            })

    except Exception as e:
        logger.error(f"Error al obtener información del video: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/abrir-archivo')
def abrir_archivo():
    try:
        sanitized_path = request.args.get('sanitized_path')
        format_type = request.args.get('format')  # Añadir el parámetro de formato
        
        if not sanitized_path or not format_type:
            return jsonify({"success": False, "error": "Ruta o formato no proporcionado"})
            
        base_dir = os.path.abspath(os.path.dirname(__file__))
        
        # Construir la ruta completa del archivo basada en el formato
        archivo = os.path.join(
            base_dir, 
            'descargas',
            'audio' if format_type == 'mp3' else 'video',
            sanitized_path
        )
        
        logger.info(f"Intentando abrir archivo: {archivo}")
        
        if not os.path.exists(archivo):
            logger.error(f"Archivo no encontrado en {archivo}")
            return jsonify({"success": False, "error": "Archivo no encontrado"})
            
        # Verificar que la ruta está dentro del directorio permitido
        if not os.path.abspath(archivo).startswith(base_dir):
            return jsonify({"success": False, "error": "Ruta no permitida"})

        sistema = platform.system()
        try:
            if sistema == "Windows":
                os.startfile(archivo)
            elif sistema == "Darwin":  # macOS
                subprocess.run(["open", archivo], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", archivo], check=True)
            
            logger.info(f"Archivo abierto exitosamente: {archivo}")
            return jsonify({"success": True})
        except Exception as e:
            logger.error(f"Error al abrir archivo: {str(e)}")
            return jsonify({"success": False, "error": f"Error al abrir archivo: {str(e)}"})

    except Exception as e:
        logger.error(f"Error general al abrir archivo: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/abrir-carpeta')
def abrir_carpeta():
    try:
        path = request.args.get('path')
        if path.startswith('/'):
            path = path[1:]
            
        # Construir la ruta absoluta desde la raíz del proyecto
        base_dir = os.path.abspath(os.path.dirname(__file__))
        carpeta = os.path.join(base_dir, os.path.dirname(path))
        
        # Verificar que la carpeta existe
        if not os.path.exists(carpeta):
            logger.error(f"Carpeta no encontrada: {carpeta}")
            return jsonify({"success": False, "error": "Carpeta no encontrada"})
        
        # Verificar que la ruta está dentro del directorio del proyecto
        if not os.path.abspath(carpeta).startswith(base_dir):
            logger.error(f"Ruta no permitida: {carpeta}")
            return jsonify({"success": False, "error": "Ruta no permitida"})

        logger.info(f"Intentando abrir carpeta: {carpeta}")
        
        sistema = platform.system()
        try:
            if sistema == "Windows":
                os.startfile(carpeta)
            elif sistema == "Darwin":  # macOS
                subprocess.run(["open", carpeta], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", carpeta], check=True)
            
            logger.info(f"Carpeta abierta exitosamente: {carpeta}")
            return jsonify({"success": True})
        except Exception as e:
            logger.error(f"Error al abrir carpeta: {str(e)}")
            return jsonify({"success": False, "error": f"Error al abrir carpeta: {str(e)}"})

    except Exception as e:
        logger.error(f"Error general al abrir carpeta: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

# Modificar la función my_hook para un mejor manejo del progreso de MP3
def my_hook(d):
    global download_progress, is_converting, conversion_started
    try:
        if d['status'] == 'downloading':
            # Durante la descarga del archivo
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            if total_bytes > 0:
                downloaded = d.get('downloaded_bytes', 0)
                # Para MP3, la descarga es solo el 50% del proceso
                if d.get('filename', '').endswith('.webm'):
                    download_progress = (downloaded / total_bytes) * 50
                else:
                    download_progress = (downloaded / total_bytes) * 100
        elif d['status'] == 'finished':
            # Cuando termina la descarga y comienza la conversión
            if d.get('filename', '').endswith('.webm'):
                is_converting = True
                conversion_started = True
                download_progress = 50  # Mantener el progreso en 50% durante la conversión
            elif conversion_started:
                # Cuando termina la conversión
                download_progress = 100
                is_converting = False
                conversion_started = False
        elif d['status'] == 'error':
            download_progress = 0
            is_converting = False
            conversion_started = False
            logger.error(f"Error en la descarga: {d.get('error')}")
    except Exception as e:
        logger.error(f"Error al calcular progreso: {str(e)}")
        download_progress = 0
        is_converting = False
        conversion_started = False

@app.route('/progreso')
def obtener_progreso():
    global download_progress, is_converting
    return jsonify({
        "progress": download_progress,
        "converting": is_converting
    })

@app.route('/reset-progress')
def reset_progress():
    global download_progress, is_converting, conversion_started
    download_progress = 0
    is_converting = False
    conversion_started = False
    return jsonify({"success": True})

# Inicio mi aplicación en modo debug en el puerto 5000
if __name__ == '__main__':
    app.run(debug=True, port=5000)
