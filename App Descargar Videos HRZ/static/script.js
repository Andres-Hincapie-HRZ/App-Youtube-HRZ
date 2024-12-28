// Autor: Andrés Hincapie Ruiz (A.HRZ)
// Fecha de creación: 16 de diciembre de 2024
// Script principal para la funcionalidad del descargador de YouTube

// Añado un evento para mostrar/ocultar el selector de calidad según el formato
document.getElementById('format').addEventListener('change', function() {
    const qualityContainer = document.getElementById('quality-container');
    qualityContainer.style.display = this.value === 'mp4' ? 'flex' : 'none';
});

// Función para obtener información del video
async function obtenerInfoVideo(url) {
    const status = document.getElementById('status');
    const loader = document.getElementById('loader');
    const previewContainer = document.getElementById('preview-container');
    
    try {
        loader.style.display = 'block';
        status.innerHTML = 'Obteniendo información del video...';
        
        const response = await fetch(`/obtener-info?url=${encodeURIComponent(url)}`);
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('thumbnail').src = data.thumbnail;
            document.getElementById('video-title').textContent = data.title;
            document.getElementById('video-duration').textContent = data.duration;
            previewContainer.style.display = 'flex';
            status.innerHTML = '';
        } else {
            status.innerHTML = 'Error: ' + data.error;
            previewContainer.style.display = 'none';
        }
    } catch (error) {
        status.innerHTML = 'Error al obtener información del video: ' + error.message;
        previewContainer.style.display = 'none';
    } finally {
        loader.style.display = 'none';
    }
}

// Función para actualizar el progreso de descarga
function actualizarProgreso(progress, format, isConverting) {
    const status = document.getElementById('status');
    if (status) {
        let mensaje = '';
        if (format === 'mp3') {
            if (isConverting) {
                mensaje = 'Convirtiendo a MP3...';
            } else if (progress < 50) {
                mensaje = 'Descargando audio...';
            }
        }
        
        status.innerHTML = `
            <div class="progress-container">
                <div class="progress-bar" style="width: ${progress}%"></div>
                <span class="progress-text">${progress}%${mensaje ? ' - ' + mensaje : ''}</span>
            </div>`;
    }
}

// Función para resetear el estado de la descarga
function resetearEstado() {
    if (window.progressInterval) {
        clearInterval(window.progressInterval);
        window.progressInterval = null;
    }
    
    const status = document.getElementById('status');
    const loader = document.getElementById('loader');
    
    if (status) status.innerHTML = '';
    if (loader) loader.style.display = 'none';
    
    fetch('/reset-progress');
}

// Función para limpiar completamente la interfaz
function limpiarTodo() {
    resetearEstado();
    
    const previewContainer = document.getElementById('preview-container');
    const urlInput = document.getElementById('url');
    
    if (previewContainer) previewContainer.style.display = 'none';
    if (urlInput) urlInput.value = '';
}

// Función principal de descarga
async function descargar() {
    try {
        const url = document.getElementById('url').value;
        const format = document.getElementById('format').value;
        const quality = document.getElementById('quality').value;
        const status = document.getElementById('status');
        const loader = document.getElementById('loader');

        if (!url) {
            status.innerHTML = '<div class="error-message"><i class="fas fa-exclamation-circle"></i> Por favor, ingresa una URL de YouTube</div>';
            return;
        }

        resetearEstado();
        status.innerHTML = '<div class="info-message"><i class="fas fa-info-circle"></i> Iniciando descarga...</div>';
        loader.style.display = 'block';

        // Configurar el intervalo de progreso
        window.progressInterval = setInterval(async () => {
            try {
                const response = await fetch('/progreso');
                if (!response.ok) throw new Error('Error al obtener progreso');
                const data = await response.json();
                if (data.progress !== undefined) {
                    const progress = Math.min(100, Math.max(0, data.progress)).toFixed(1);
                    actualizarProgreso(progress, format, data.converting);
                }
            } catch (error) {
                console.error('Error al obtener progreso:', error);
            }
        }, 1000);

        const response = await fetch(`/descargar?url=${encodeURIComponent(url)}&format=${format}&quality=${quality}`);
        if (!response.ok) throw new Error('Error en la respuesta del servidor');
        
        const data = await response.json();
        resetearEstado();

        if (data.success) {
            const filePath = format === 'mp3' 
                ? `descargas/audio/${data.file}`
                : `descargas/video/${data.file}`;
            
            const sanitizedPath = format === 'mp3'
                ? `descargas/audio/${data.sanitized_file}`
                : `descargas/video/${data.sanitized_file}`;

            status.innerHTML = `
                <div class="success-message">
                    <i class="fas fa-check-circle"></i> ${data.message}
                    <div class="download-actions">
                        <button class="action-button" onclick="openFile('${filePath}', '${data.sanitized_file}')">
                            <i class="fas fa-play"></i> Reproducir
                        </button>
                        <button class="action-button" onclick="openFolder('${filePath}')">
                            <i class="fas fa-folder-open"></i> Abrir carpeta
                        </button>
                    </div>
                </div>`;
        } else {
            throw new Error(data.error || 'Error desconocido en la descarga');
        }
    } catch (error) {
        console.error('Error en la descarga:', error);
        const status = document.getElementById('status');
        status.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i> Error en la descarga: ${error.message}
            </div>`;
    } finally {
        const loader = document.getElementById('loader');
        if (loader) loader.style.display = 'none';
    }
}

function sanitizeFileName(name) {
    return name
        .replace(/:/g, '')
        .replace(/"/g, '')
        .replace(/\\/g, '/')
        .replace(/\/+/g, '/')
        .trim();
}

function openFile(filePath, sanitizedPath) {
    // Obtener solo el nombre del archivo del path sanitizado
    const sanitizedFileName = sanitizedPath;  // Ya viene sanitizado desde el backend
    const format = document.getElementById('format').value;
    
    console.log('Intentando abrir archivo:', sanitizedFileName, 'formato:', format);
    
    fetch(`/abrir-archivo?sanitized_path=${encodeURIComponent(sanitizedFileName)}&format=${format}`)
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                console.error('Error al abrir archivo:', data.error);
                alert('No se pudo abrir el archivo: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error al abrir el archivo:', error);
            alert('Error al intentar abrir el archivo');
        });
}

function openFolder(filePath) {
    // Sanitizar la ruta de la carpeta
    filePath = sanitizeFileName(filePath);
    
    // Asegurarnos de que la ruta comience correctamente
    if (!filePath.startsWith('/')) {
        filePath = '/' + filePath;
    }
    
    console.log('Intentando abrir carpeta:', filePath); // Para depuración
    
    fetch(`/abrir-carpeta?path=${encodeURIComponent(filePath)}`)
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                console.error('Error al abrir carpeta:', data.error);
                alert('No se pudo abrir la carpeta: ' + data.error);
            } else {
                console.log('Carpeta abierta exitosamente');
            }
        })
        .catch(error => {
            console.error('Error al abrir la carpeta:', error);
            alert('Error al intentar abrir la carpeta');
        });
}

// Event Listeners
document.getElementById('url').addEventListener('paste', function(e) {
    limpiarTodo();
    setTimeout(() => obtenerInfoVideo(this.value), 100);
});
