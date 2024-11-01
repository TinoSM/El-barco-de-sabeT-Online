import urllib.request
import base64
import time
import xbmcgui
import xbmcplugin
import xbmc
from cache_utils import guardar_cache  # Importa guardar_cache desde cache_utils
# URL en Base64
asdf = "aHR0cHM6Ly9naXN0LmdpdGh1YnVzZXJjb250ZW50LmNvbS9FbEJhcmNvRGVTYWJlVC9jMDYyZGJjODAyYWU3NmMwNTBlOWU3YmM0MjhiN2U2ZC9yYXcv"

# Función para obtener el contenido de la web sin proxy
def obtener_contenido_web_sin_proxy():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    try:
        # Decodificar URL y obtener el contenido
        qwert = base64.b64decode(asdf).decode('utf-8')
        req = urllib.request.Request(qwert, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            contenido_base64 = response.read().decode('utf-8')
            # Decodificar el contenido desde Base64
            contenido = base64.b64decode(contenido_base64).decode('utf-8')
            return contenido
    except Exception as e:
        xbmcgui.Dialog().notification("Error", f"No se pudo obtener el contenido: {str(e)}")
        return None

# Función para extraer enlaces del contenido obtenido
def extraer_enlaces(contenido):
    enlaces = []
    titulos = []

    # Saltar la primera línea
    lineas = contenido.strip().split('\n')[1:]

    # Procesar cada línea
    for linea in lineas:
        if ':' in linea:
            partes = linea.split(':')
            titulo_base = partes[0]
            enlace_id = partes[1].strip()

            # Crear el enlace en el formato adecuado
            enlace = f"plugin://script.module.horus?action=play&id={enlace_id}"

            # Modificar el título para incluir el enlace y los últimos cuatro dígitos del ID
            titulo = f"{titulo_base} - {enlace[-4:]}"  # Agrega los últimos 4 dígitos del ID al título

            enlaces.append(enlace)
            titulos.append(titulo)

    return enlaces, titulos


# Función para actualizar y descargar la lista de enlaces
def actualizar_lista(cache_file, handle):
    # Intentar cerrar cualquier diálogo de "Busy" que pueda estar abierto
    xbmc.executebuiltin('Dialog.Close(busydialog)')
    time.sleep(0.2)

    contenido = obtener_contenido_web_sin_proxy()

    if contenido:
        enlaces, titulos = extraer_enlaces(contenido)

        # Guardar en caché y mostrar confirmación de descarga
        origen = "Archivo Remoto"
        guardar_cache(cache_file, enlaces, titulos, origen, time.strftime('%d-%m-%Y %H:%M'))
        xbmcgui.Dialog().ok("Éxito", "Descarga correcta. Reinicia el addon para ver los cambios.")

        # Finalizar el directorio con el handle proporcionado
        xbmcplugin.endOfDirectory(handle, updateListing=True)

        return enlaces, titulos, origen, time.strftime('%d-%m-%Y %H:%M')
    else:
        return [], [], "Error en Contenido", None
