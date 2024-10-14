import sys
import os
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import urllib.request
import json
import re
import time

# Añadir la carpeta 'lib' a la ruta de búsqueda de Python
addon_dir = xbmcaddon.Addon().getAddonInfo('path')
lib_path = os.path.join(addon_dir, 'lib')
sys.path.append(lib_path)

# Obtener el ID del plugin actual para el modo de video
plugin_url = sys.argv[0]
handle = int(sys.argv[1])

CACHE_FILE = os.path.join(addon_dir, 'cache.json')

# Definición de la clase Canal
class Canal:
    def __init__(self, nombre, tvg_id, logo):
        self.nombre = nombre
        self.tvg_id = tvg_id
        self.logo = logo

# URL del archivo JSON con la lista de canales
URL_CANAL_JSON = "https://raw.githubusercontent.com/ElBarcoDeSabeT/El-barco-de-sabeT-Online/refs/heads/main/canales.json"

# Función para obtener la lista de canales desde una URL
def obtener_canales_desde_url(url):
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read().decode('utf-8')
            canales = json.loads(data)
            return [Canal(canal['nombre'], canal['tvg_id'], canal['logo']) for canal in canales]
    except Exception as e:
        xbmcgui.Dialog().notification("Error", f"No se pudo cargar la lista de canales: {str(e)}")
        return []

# Cargar canales desde el archivo JSON remoto
canales = obtener_canales_desde_url(URL_CANAL_JSON)

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

# Función para mostrar un diálogo y seleccionar dónde guardar el archivo M3U
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

# Función para exportar a un archivo M3U
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
                    # Eliminar los últimos 4 dígitos del título y normalizar
                    nombre_canal = " ".join(titulo.split()[:-1]).strip().lower()  # Obtener solo el nombre sin los últimos 4 dígitos y en minúsculas
                    canal = next((c for c in canales if c.nombre.lower() == nombre_canal), None)  # Comparar en minúsculas
                    if canal:
                        f.write(f'#EXTINF:-1 tvg-id="{canal.tvg_id}" tvg-logo="{canal.logo}",{titulo}\n{enlace}\n')
                    else:
                        f.write(f"#EXTINF:-1,{titulo}\n{enlace}\n")

            xbmcgui.Dialog().ok("Éxito", f"Lista M3U exportada a {ruta_m3u}")
        except Exception as e:
            xbmcgui.Dialog().ok("Error", f"No se pudo exportar el archivo M3U: {str(e)}")
    else:
        xbmcgui.Dialog().notification("Cancelado", "Exportación M3U cancelada.")

# Función para obtener la lista de proxies desde la URL
def obtener_proxies(url):
    try:
        with urllib.request.urlopen(url) as response:
            proxies_json = json.loads(response.read().decode('utf-8'))
            return proxies_json['proxies']  # Devolver la lista de proxies
    except Exception as e:
        xbmcgui.Dialog().notification("Error", f"No se pudo cargar la lista de proxies: {str(e)}")
        return []

# Filtrar proxies asiáticos
def filtrar_proxies_asia(proxies):
    proxies_asia = []
    for proxy in proxies:
        ip_data = proxy.get('ip_data')  # Obtener 'ip_data' de forma segura
        if ip_data and ip_data.get('continentCode') == 'AS':
            proxies_asia.append(proxy['proxy'])
    return proxies_asia

# Función para probar un proxy y obtener el contenido de la web
def obtener_contenido_web_con_proxy(url, proxy):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    proxy_handler = urllib.request.ProxyHandler({'http': proxy, 'https': proxy})
    opener = urllib.request.build_opener(proxy_handler)
    urllib.request.install_opener(opener)

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        return None  # Devolvemos None en caso de error

# Función para obtener el contenido de la web sin proxy
def obtener_contenido_web_sin_proxy(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        return None  # Devolvemos None en caso de error

# Función para extraer enlaces de la página web
def extraer_enlaces(html):
    enlaces = []
    titulos = []

    patrones = re.findall(r'<a href="(acestream://[^"]+)"[^>]*>(.*?)</a>', html)

    for enlace, titulo in patrones:
        nuevo_enlace = enlace.replace("acestream://", "plugin://script.module.horus?action=play&id=")
        enlaces.append(nuevo_enlace)

        id_acestream = enlace.split("://")[1]  # Obtener solo el ID
        ultimos_digitos = id_acestream[-4:]  # Obtener los últimos 4 dígitos

        titulos.append(f"{titulo.strip()} {ultimos_digitos}")

    return enlaces, titulos

# Función para reproducir el enlace
def reproducir_enlace(enlace):
    xbmc.Player().play(enlace)

# Función para actualizar y descargar la lista de enlaces
def actualizar_lista():
    # Permitir elegir entre el servidor principal y espejo para actualizar la lista
    opciones_actualizar = ["Servidor Principal", "Servidor Espejo"]
    seleccion_actualizar = xbmcgui.Dialog().select("Selecciona el servidor para actualizar", opciones_actualizar)

    if seleccion_actualizar == -1:  # Si el usuario cancela, salir
        return [], [], "Cancelado", None  # Cambiado a una lista vacía en lugar de None

    # Definir el origen basado en la selección
    origen_seleccionado = "Principal" if seleccion_actualizar == 0 else "Espejo"
    url_seleccionada = "https://elcano.top" if seleccion_actualizar == 0 else "https://viendoelfutbolporlaface.pages.dev/"

    proxies_url = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=json"
    proxies = obtener_proxies(proxies_url)

    if not proxies:
        xbmcgui.Dialog().notification("Error", "No se encontraron proxies.")
        return [], [], "Sin Proxies", None  # Cambiado a listas vacías en lugar de None

    # Filtrar proxies solo de Asia
    proxies_asia = filtrar_proxies_asia(proxies)

    # Intentar obtener el contenido de la web sin proxy
    xbmcgui.Dialog().notification("Conexión", "Intentando conectar a servidor sin proxy")
    contenido_html = obtener_contenido_web_sin_proxy(url_seleccionada)

    if contenido_html is None:  # Si no se obtuvo contenido, intentamos con los proxies asiáticos
        limite_intentos = 50  # Límite de intentos por vez
        total_proxies = len(proxies_asia)

        for i in range(0, total_proxies, limite_intentos):
            proxies_a_probar = proxies_asia[i:i + limite_intentos]  # Seleccionar un bloque de proxies

            for index, proxy in enumerate(proxies_a_probar):  # Enumerar los proxies
                xbmcgui.Dialog().notification("Proxy", f"Usando proxy {i + index + 1} de {total_proxies}")
                contenido_html = obtener_contenido_web_con_proxy(url_seleccionada, proxy)

                if contenido_html:  # Salir si se obtiene contenido
                    break
            else:  # Si no se obtuvo contenido con el bloque actual
                continue
            break  # Salir si se obtuvo contenido

    if contenido_html is None:
        xbmcgui.Dialog().notification("Error", "No se pudo obtener contenido.")
        return [], [], "Error en Contenido", None  # Cambiado a listas vacías en lugar de None

    enlaces, titulos = extraer_enlaces(contenido_html)

    # Establecer la fecha de la última actualización
    fecha = time.strftime('%d-%m-%Y %H:%M')  # Obtener la fecha y hora actual

    guardar_cache(enlaces, titulos, origen_seleccionado)
    xbmcgui.Dialog().ok("Atención", "Descarga correcta.\nSal y entra del addon para ver los cambios reflejados")
    # Forzar el refresco de la interfaz
    xbmcplugin.endOfDirectory(handle, updateListing=True)
    return enlaces, titulos, origen_seleccionado, fecha  # Retornar siempre cuatro elementos

# Menú principal en modo video
def mostrar_menu_principal():
    cache = cargar_cache()

    if not cache:
        enlaces, titulos, origen, fecha = actualizar_lista()
        if not enlaces:  # Si no se puede actualizar o se cancela, mostrar mensaje y salir
            xbmcgui.Dialog().notification("Información", "No se pudo obtener canales, por favor verifica la conexión.")
            return
        fecha = time.strftime('%d-%m-%Y %H:%M')  # Asignar la fecha al valor actual
        origen = "Desconocido"  # O valor predeterminado
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

    # Añadir los canales a la lista del directorio
    for i, titulo in enumerate(titulos):
        enlace = enlaces[i]
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
