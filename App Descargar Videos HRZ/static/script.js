// Autor: Andrés Hincapie Ruiz (A.HRZ)
// Fecha de creación: 16 de diciembre de 2024
// Script principal para la funcionalidad del descargador de YouTube

// Añado un evento para mostrar/ocultar el selector de calidad según el formato
document.getElementById('format').addEventListener('change', function() {
    const qualitySelect = document.getElementById('quality');
    qualitySelect.style.display = this.value === 'mp4' ? 'inline' : 'none';
});

// Mi función principal para manejar las descargas
function descargar() {
    // Obtengo los valores de los campos del formulario
    const url = document.getElementById('url').value;
    const format = document.getElementById('format').value;
    const quality = document.getElementById('quality').value;
    const status = document.getElementById('status');

    // Verifico que se haya ingresado una URL
    if (!url) {
        status.innerHTML = 'Por favor, ingresa una URL de YouTube';
        return;
    }

    // Actualizo el estado para mostrar que la descarga está en proceso
    status.innerHTML = 'Descargando...';

    // Realizo la petición al servidor para iniciar la descarga
    fetch(`/descargar?url=${encodeURIComponent(url)}&format=${format}&quality=${quality}`)
        .then(response => response.json())
        .then(data => {
            // Manejo la respuesta exitosa
            if (data.success) {
                status.innerHTML = `${data.message}<br>Archivo: ${data.file}`;
            } else {
                // Manejo los errores reportados por el servidor
                status.innerHTML = 'Error: ' + data.error;
                console.error('Error:', data.error);
            }
        })
        .catch(error => {
            // Manejo los errores de red o del cliente
            status.innerHTML = 'Error en la descarga: ' + error.message;
            console.error('Error:', error);
        });
}
