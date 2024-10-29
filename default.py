import sys
import os
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import urllib.request
import base64
import time
import json

# Añadir la carpeta 'lib' a la ruta de búsqueda de Python
addon_dir = xbmcaddon.Addon().getAddonInfo('path')
lib_path = os.path.join(addon_dir, 'lib')
sys.path.append(lib_path)

# Obtener el ID del plugin actual para el modo de video
plugin_url = sys.argv[0]
handle = int(sys.argv[1])

CACHE_FILE = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'cache.json')

# URL en Base64
url_origen_base64 = "aHR0cHM6Ly9naXN0LmdpdGh1YnVzZXJjb250ZW50LmNvbS9FbEJhcmNvRGVTYWJlVC9jMDYyZGJjODAyYWU3NmMwNTBlOWU3YmM0MjhiN2U2ZC9yYXcvMGZhNDZiZjc2M2ZhZmQ0NjNlODhjYWU1OTkxNGFmMWUzZDI3YWEzMy9iYXJjby50eHQ="

# Función para obtener el contenido de la web sin proxy
def obtener_contenido_web_sin_proxy():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    try:
        # Decodificar URL y obtener el contenido
        url_decodificada = base64.b64decode(url_origen_base64).decode('utf-8')
        req = urllib.request.Request(url_decodificada, headers=headers)
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
            titulo = partes[0]
            enlace_id = partes[1].strip()
            
            # Crear el enlace en el formato adecuado
            enlace = f"plugin://script.module.horus?action=play&id={enlace_id}"
            enlaces.append(enlace)
            titulos.append(titulo)
    
    return enlaces, titulos

# Función para cargar el caché
def cargar_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Función para guardar el caché con origen y fecha
def guardar_cache(enlaces, titulos, origen):
    timestamp = time.strftime('%d-%m-%Y %H:%M')  # Obtener fecha y hora actual
    cache_data = {
        'enlaces': enlaces,
        'titulos': titulos,
        'origen': origen,
        'fecha': timestamp
    }
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f)

# Función para exportar a un archivo M3U
def seleccionar_ruta_m3u():
    dialog = xbmcgui.Dialog()
    ruta_seleccionada = dialog.browse(3, 'Selecciona la carpeta donde guardar', 'files')

    if ruta_seleccionada:
        nombre_archivo = dialog.input('Nombre del archivo M3U', 'ElBarcoDeSabet.m3u', type=xbmcgui.INPUT_ALPHANUM)

        if nombre_archivo:
            if not nombre_archivo.endswith('.m3u'):
                nombre_archivo += '.m3u'

            return os.path.join(ruta_seleccionada, nombre_archivo)

    return None

def exportar_m3u(enlaces, titulos, origen):
    ruta_m3u = seleccionar_ruta_m3u()

    if ruta_m3u:
        try:
            with open(ruta_m3u, 'w', encoding='utf-8') as f:
                # Escribir la cabecera M3U y el origen del EPG
                f.write("#EXTM3U url-tvg=\"https://raw.githubusercontent.com/davidmuma/EPG_dobleM/master/guiatv.xml, https://raw.githubusercontent.com/Icastresana/lista1/main/epg.xml\"\n")

                # Obtener la fecha actual en el formato dd-mm-YY HH:MM
                fecha_actual = time.strftime('%d-%m-%Y %H:%M')

                # Agregar un canal ficticio que muestre el origen dinámico y la fecha, con el enlace correcto
                canal_ficticio = (
                    f'#EXTINF:-1,Origen: {origen} (Fecha: {fecha_actual})\n'
                    'plugin://script.module.horus?action=play&id=8819c851e10adc18ad914805ec4a13ddfb67063c\n'
                )
                f.write(canal_ficticio)

                # Escribir los canales reales
                for titulo, enlace in zip(titulos, enlaces):
                    f.write(f"#EXTINF:-1,{titulo}\n{enlace}\n")

            xbmcgui.Dialog().ok("Éxito", f"Lista M3U exportada a {ruta_m3u}")
        except Exception as e:
            xbmcgui.Dialog().ok("Error", f"No se pudo exportar el archivo M3U: {str(e)}")
    else:
        xbmcgui.Dialog().notification("Cancelado", "Exportación M3U cancelada.")

# Función para actualizar y descargar la lista de enlaces
def actualizar_lista():
    contenido = obtener_contenido_web_sin_proxy()
    
    if contenido:
        enlaces, titulos = extraer_enlaces(contenido)
        
        # Guardar en caché y mostrar confirmación de descarga
        origen = "Archivo Remoto"
        guardar_cache(enlaces, titulos, origen)
        xbmcgui.Dialog().ok("Éxito", "Descarga correcta. Reinicia el addon para ver los cambios.")
        xbmcplugin.endOfDirectory(handle, updateListing=True)
        
        return enlaces, titulos, origen, time.strftime('%d-%m-%Y %H:%M')
    else:
        return [], [], "Error en Contenido", None

# Función para mostrar el menú principal con los enlaces obtenidos
def mostrar_menu_principal():
    cache = cargar_cache()

    if not cache:
        enlaces, titulos, origen, fecha = actualizar_lista()
        if not enlaces:  # Si no se puede actualizar o se cancela, mostrar mensaje y salir
            xbmcgui.Dialog().notification("Información", "No se pudo obtener canales, por favor verifica la conexión.")
            return
        fecha = time.strftime('%d-%m-%Y %H:%M')
        origen = "Desconocido"
    else:
        enlaces, titulos, origen, fecha = cache['enlaces'], cache['titulos'], cache['origen'], cache['fecha']

    # Mostrar origen y fecha de la última actualización en el título del directorio
    xbmcplugin.setPluginCategory(handle, f"Lista de Canales - Origen: {origen} (Actualizado: {fecha})")

    # Opción para actualizar la lista (primero en la lista)
    actualizar_item = xbmcgui.ListItem(label="Actualizar lista")
    xbmcplugin.addDirectoryItem(handle, plugin_url + '?action=actualizar', actualizar_item, isFolder=False)

    # Opción para exportar la lista M3U (segundo en la lista)
    exportar_item = xbmcgui.ListItem(label="Exportar M3U")
    xbmcplugin.addDirectoryItem(handle, plugin_url + '?action=exportar', exportar_item, isFolder=False)

    # Añadir los enlaces a la lista del directorio
    for titulo, enlace in zip(titulos, enlaces):
        list_item = xbmcgui.ListItem(label=titulo)
        list_item.setInfo('video', {'title': titulo})
        list_item.setProperty('IsPlayable', 'true')

        xbmcplugin.addDirectoryItem(handle, enlace, list_item, isFolder=False)

    # Finalizar el directorio para que se muestre el menú en modo video
    xbmcplugin.endOfDirectory(handle)

# Comprobamos la acción seleccionada por el usuario
params = urllib.parse.parse_qs(sys.argv[2][1:])
action = params.get('action', [None])[0]

# Determinar la acción a realizar
if action == 'actualizar':
    actualizar_lista()
elif action == 'exportar':
    cache = cargar_cache()
    exportar_m3u(cache['enlaces'], cache['titulos'], cache['origen'])
else:
    mostrar_menu_principal()
