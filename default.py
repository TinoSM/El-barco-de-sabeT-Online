import sys
import os
import xbmc
import xbmcgui
import xbmcaddon
import urllib.request
import json
import re
import time

# Añadir la carpeta 'lib' a la ruta de búsqueda de Python
addon_dir = xbmcaddon.Addon().getAddonInfo('path')
lib_path = os.path.join(addon_dir, 'lib')
sys.path.append(lib_path)

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
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')  # Obtener fecha y hora actual
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
def exportar_m3u(enlaces, titulos):
    ruta_m3u = seleccionar_ruta_m3u()

    if ruta_m3u:
        try:
            with open(ruta_m3u, 'w', encoding='utf-8') as f:
                # Escribir la cabecera M3U y el origen del EPG
                f.write("#EXTM3U url-tvg=\"https://raw.githubusercontent.com/davidmuma/EPG_dobleM/master/guiatv.xml, https://raw.githubusercontent.com/Icastresana/lista1/main/epg.xml\"\n")

                for titulo, enlace in zip(titulos, enlaces):
                    # Eliminar los últimos 4 dígitos del título y normalizar
                    nombre_canal = " ".join(titulo.split()[:-1]).strip().lower()  # Obtener solo el nombre sin los últimos 4 dígitos y en minúsculas
                    canal = next((c for c in canales if c.nombre.lower() == nombre_canal), None)  # Comparar en minúsculas
                    if canal:
                        f.write(f'#EXTINF:-1 tvg-id="{canal.tvg_id}" tvg-logo="{canal.logo}",{titulo}\n{enlace}\n')
                    else:
                        f.write(f"#EXTINF:-1,{titulo}\n{enlace}\n")
            xbmcgui.Dialog().notification("Éxito", f"Lista M3U exportada a {ruta_m3u}")
        except Exception as e:
            xbmcgui.Dialog().notification("Error", f"No se pudo exportar el archivo M3U: {str(e)}")
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
        return None, None, None

    url_seleccionada = "https://elcano.top" if seleccion_actualizar == 0 else "https://viendoelfutbolporlaface.pages.dev/"
    origen_seleccionado = "Principal" if seleccion_actualizar == 0 else "Espejo"

    proxies_url = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=json"
    proxies = obtener_proxies(proxies_url)

    if not proxies:
        xbmcgui.Dialog().notification("Error", "No se encontraron proxies.")
        return None, None, None

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
        return None, None, None

    enlaces, titulos = extraer_enlaces(contenido_html)
    guardar_cache(enlaces, titulos, origen_seleccionado)

    return enlaces, titulos, origen_seleccionado

# Función principal
def main():
    # Cargar el caché al inicio
    cache = cargar_cache()
    enlaces_cache = cache.get('enlaces', [])
    titulos_cache = cache.get('titulos', [])
    origen_cache = cache.get('origen', 'Desconocido')
    fecha_cache = cache.get('fecha', 'Desconocida')

    # Verificar si hay caché disponible
    if enlaces_cache and titulos_cache:
        # Mostrar las opciones desde el caché incluyendo el origen y la fecha
        opciones = [f"Actualizar lista (Última: {origen_cache}, {fecha_cache})", "Exportar M3U"] + titulos_cache
    else:
        # Si no hay caché, directamente actualizar la lista sin mostrar primero los servidores
        enlaces, titulos, _ = actualizar_lista()
        if not enlaces or not titulos:
            return
        else:
            # Mostrar la lista de títulos obtenida después de actualizar
            seleccion = xbmcgui.Dialog().select("Selecciona un enlace", titulos)
            if seleccion != -1:
                reproducir_enlace(enlaces[seleccion])
            return

    # Mostrar el diálogo con las opciones cuando hay caché
    seleccion = xbmcgui.Dialog().select("Selecciona una opción", opciones)

    if seleccion == -1:  # Si el usuario cancela, salir
        return

    # Si se selecciona "Actualizar lista"
    if seleccion == 0:
        enlaces, titulos, origen = actualizar_lista()
        if not enlaces or not titulos:
            return
        else:
            # Guardar los nuevos enlaces y títulos en el caché tras actualizar la lista
            guardar_cache(enlaces, titulos, origen)
            # Mostrar la lista de títulos obtenida después de actualizar
            seleccion = xbmcgui.Dialog().select("Selecciona un enlace", titulos)
            if seleccion != -1:
                reproducir_enlace(enlaces[seleccion])
            return

    # Si selecciona "Exportar M3U"
    elif seleccion == 1:
        exportar_m3u(enlaces_cache, titulos_cache)
        return
    else:
        # Reproducir el enlace seleccionado desde el caché
        reproducir_enlace(enlaces_cache[seleccion - 2])

if __name__ == '__main__':
    main()