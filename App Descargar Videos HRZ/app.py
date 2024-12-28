# Autor: Andrés Hincapie Ruiz (A.HRZ)
# Fecha de creación: 16 de diciembre de 2024
# Aplicación principal para el descargador de YouTube V2

# Importo las bibliotecas necesarias para mi aplicación
from flask import Flask, request, jsonify, send_file  # Necesito Flask para crear mi servidor web
import yt_dlp  # Esta es mi herramienta principal para descargar videos
import os  # La uso para manejar directorios y archivos
import logging  # Para registrar eventos y debuggear mi aplicación
from pathlib import Path  # Me ayuda a manejar rutas de archivos de manera más eficiente

# Configuro el sistema de logging para hacer seguimiento a los eventos de mi aplicación
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Inicializo mi aplicación Flask con la configuración de archivos estáticos
app = Flask(__name__, static_folder='static', static_url_path='/static')

# Defino mi ruta principal que servirá la página de inicio
@app.route('/')
def home():
    try:
        return app.send_static_file('index.html')  # Envío mi archivo HTML principal
    except Exception as e:
        logger.error(f"Error al servir index.html: {str(e)}")  # Registro cualquier error que ocurra
        return jsonify({'error': 'Error interno del servidor'}), 500

# Mi ruta principal para manejar las descargas
@app.route('/descargar')
def descargar():
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
        base_dir = os.path.dirname(__file__)
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

        # Opciones de descarga para MP3
        if format == 'mp3':
            ydl_opts = {
                'format': 'bestaudio/best',  # Selecciono la mejor calidad de audio disponible
                'outtmpl': os.path.join(descargas_dir, '%(title)s.%(ext)s'),  # Defino la plantilla para el nombre del archivo
                'postprocessors': [{  # Configuro el procesamiento posterior del archivo
                    'key': 'FFmpegExtractAudio',  # Uso FFmpeg para extraer el audio
                    'preferredcodec': 'mp3',  # Establezco MP3 como formato preferido
                    'preferredquality': '192',  # Defino la calidad del audio en 192kbps
                }],
                'prefer_ffmpeg': True,  # Priorizo el uso de FFmpeg
                'ffmpeg_location': ffmpeg_location,  # Especifico la ubicación de FFmpeg
                'keepvideo': False  # No conservo el video original
            }
        # Configuro las opciones para descarga de MP4
        else:
            # Establezco la calidad del video según la selección del usuario
            format_string = {
                'highest': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',  # Máxima calidad disponible
                '720p': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',  # Calidad 720p
                '480p': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best',  # Calidad 480p
                '360p': 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best'   # Calidad 360p
            }.get(quality, 'best')

            ydl_opts = {
                'format': format_string,  # Aplico el formato de video seleccionado
                'outtmpl': os.path.join(descargas_dir, '%(title)s.%(ext)s'),  # Defino la plantilla para el nombre
                'prefer_ffmpeg': True,  # Priorizo el uso de FFmpeg
                'ffmpeg_location': ffmpeg_location  # Especifico la ubicación de FFmpeg
            }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # Inicio el proceso de descarga
                # Extraigo la información del video
                info = ydl.extract_info(url, download=True)
                title = info['title']  # Obtengo el título del video
                
                # Construyo el nombre del archivo según el formato
                if format == 'mp3':
                    filename = os.path.join(descargas_dir, f"{title}.mp3")
                else:
                    filename = os.path.join(descargas_dir, f"{title}.mp4")

                # Verifico si el archivo se descargó correctamente
                if os.path.exists(filename):
                    return jsonify({
                        'success': True,
                        'message': f'{"Audio" if format == "mp3" else "Video"} descargado exitosamente',
                        'file': os.path.basename(filename)
                    })
                else:
                    # Busco el archivo en el directorio por si el nombre es diferente
                    files = os.listdir(descargas_dir)
                    for file in files:
                        if title in file:
                            actual_file = os.path.join(descargas_dir, file)
                            if format == 'mp3':
                                # Renombro el archivo a .mp3 si es necesario
                                new_file = os.path.join(descargas_dir, f"{title}.mp3")
                                os.rename(actual_file, new_file)
                                filename = new_file
                            else:
                                filename = actual_file
                            break

                    return jsonify({
                        'success': True,
                        'message': f'{"Audio" if format == "mp3" else "Video"} descargado exitosamente',
                        'file': os.path.basename(filename)
                    })

        except Exception as e:
            logger.error(f"Error en la descarga: {str(e)}")  # Registro cualquier error durante la descarga
            return jsonify({
                'success': False,
                'error': f'Error en la descarga: {str(e)}'
            })

    except Exception as e:
        logger.error(f"Error general: {str(e)}")  # Registro errores generales de la aplicación
        return jsonify({'success': False, 'error': f'Error general: {str(e)}'})

# Inicio mi aplicación en modo debug en el puerto 5000
if __name__ == '__main__':
    app.run(debug=True, port=5000)
