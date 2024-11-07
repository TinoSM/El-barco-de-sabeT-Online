import urllib.request
import base64
import time
import xbmcgui
import xbmcplugin
import xbmc
import re
from cache_utils import guardar_cache  # Importa guardar_cache desde cache_utils

# Just add the code to scrap (HTML source code of a website typically) from zeronet links
HTML_CODE_BACKUP = """


"""


# Función para obtener el contenido de la web sin proxy
def obtener_contenido_web_sin_proxy(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode("utf-8")
    except Exception as e:
        return None  # Devolvemos None en caso de error


# Función para extraer enlaces de la página web
def extraer_enlaces(html, regex):
    enlaces_y_titulos = []
    
    
    patrones = re.findall(regex, html)

    for titulo, enlace in patrones:
        if "://" in titulo:
            titulo_tmp = titulo
            titulo = enlace
            enlace = titulo_tmp

        nuevo_enlace = enlace.replace(
            "acestream://", "plugin://script.module.horus?action=play&id="
        )

        id_acestream = enlace.split("://")[1]  # Obtener solo el ID
        ultimos_digitos = id_acestream[-4:]  # Obtener los últimos 4 dígitos
        


        enlaces_y_titulos.append((nuevo_enlace, f"{titulo.strip()} {ultimos_digitos}", 
                                  titulo.strip()))
        
        
        
    def custom_sort_uhd(strings):
        # Separate words that contain "2-9" and those that do not
        regexp = r'UHD'
        without_digits_2_to_9 = [s for s in strings if not re.search(regexp, s[2])]
        with_digits_2_to_9 = [s for s in strings if re.search(regexp, s[2])]
        
        # Concatenate lists with non-digit or '1' words first, then '2-9' words
        return without_digits_2_to_9 + with_digits_2_to_9
        
    def custom_sort_deportes_fav(strings):
        # Separate words that contain "2-9" and those that do not
        regexp = r'Liga|Campeones|DAZN'
        without_digits_2_to_9 = [s for s in strings if re.search(regexp, s[2])]
        with_digits_2_to_9 = [s for s in strings if not re.search(regexp, s[2])]
        
        # Concatenate lists with non-digit or '1' words first, then '2-9' words
        return custom_sort_uhd(without_digits_2_to_9) + with_digits_2_to_9
        
    def custom_sort(strings):
        # Separate words that contain "2-9" and those that do not
        regexp = r'[2-9]\b|1[0-9]\b'
        without_digits_2_to_9 = [s for s in strings if not re.search(regexp, s[2])]
        with_digits_2_to_9 = [s for s in strings if re.search(regexp, s[2])]
        
        # Concatenate lists with non-digit or '1' words first, then '2-9' words
        return custom_sort_deportes_fav(without_digits_2_to_9) + with_digits_2_to_9
    
    enlaces_y_titulos = custom_sort(enlaces_y_titulos)
    
    return [x[0] for x in enlaces_y_titulos], [x[1] for x in enlaces_y_titulos]


# Función para actualizar y descargar la lista de enlaces
def actualizar_lista(cache_file, handle):
    # Intentar cerrar cualquier diálogo de "Busy" que pueda estar abierto
    xbmc.executebuiltin('Dialog.Close(busydialog)')
    time.sleep(0.2)

    contenido = obtener_contenido_web_sin_proxy("XXX_put_a_url_here")
    if not contenido and HTML_CODE_BACKUP.strip():
        contenido = HTML_CODE_BACKUP.strip()

    if contenido:
        enlaces, titulos = extraer_enlaces(contenido, r'name":.*"(.*)".*"url":.*"(acestream://[^"]+)')
        if not enlaces:
            contenido = HTML_CODE_BACKUP.strip()
            enlaces, titulos = extraer_enlaces(contenido, r'name":.*"(.*)".*"url":.*"(acestream://[^"]+)')
            

        # Guardar en caché y mostrar confirmación de descarga
        origen = "Archivo Remoto"
        guardar_cache(cache_file, enlaces, titulos, origen, time.strftime('%d-%m-%Y %H:%M'))
        xbmcgui.Dialog().ok("Éxito", "Descarga correcta. Reinicia el addon para ver los cambios.")

        # Finalizar el directorio con el handle proporcionado
        xbmcplugin.endOfDirectory(handle, updateListing=True)

        return enlaces, titulos, origen, time.strftime('%d-%m-%Y %H:%M')
    else:
        return [], [], "Error en Contenido", None
