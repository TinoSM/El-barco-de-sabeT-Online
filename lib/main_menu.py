import time
import xbmcplugin
import xbmcgui
import xbmc
import urllib.parse
import time
from cache_utils import cargar_cache, guardar_cache
from actualizar_lista import actualizar_lista
from export_m3u import exportar_m3u
from mostrar_directos import mostrar_directos

from mostrar_directos import mostrar_directos  # Importar la función para directos

def mostrar_menu_principal(handle, plugin_url, cache_file):
    # Cargar caché o actualizar lista como siempre
    cache = cargar_cache(cache_file)

    if not cache:
        enlaces, titulos, origen, fecha = actualizar_lista(cache_file, handle)
        if not enlaces:
            xbmcgui.Dialog().notification("Error", "No se pudo obtener canales, verifica la conexión.")
            return
    else:
        enlaces, titulos, origen, fecha = cache['enlaces'], cache['titulos'], cache['origen'], cache['fecha']

    # Opción de actualizar lista
    actualizar_item = xbmcgui.ListItem(label="Actualizar lista")
    xbmcplugin.addDirectoryItem(handle, f"{plugin_url}?action=actualizar", actualizar_item, isFolder=False)

    # Opción para exportar lista M3U
    exportar_item = xbmcgui.ListItem(label="Exportar M3U")
    xbmcplugin.addDirectoryItem(handle, f"{plugin_url}?action=exportar", exportar_item, isFolder=False)

    # Opción para Directos
    directos_item = xbmcgui.ListItem(label="Directos - Funcion Beta")
    xbmcplugin.addDirectoryItem(handle, f"{plugin_url}?action=directos", directos_item, isFolder=True)

    # Añadir los canales del caché al menú
    for titulo, enlace in zip(titulos, enlaces):
        list_item = xbmcgui.ListItem(label=titulo)
        list_item.setInfo('video', {'title': titulo})
        list_item.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(handle, enlace, list_item, isFolder=False)

    # Finalizar el directorio
    xbmcplugin.endOfDirectory(handle)


# Manejo de las distintas acciones
def handle_action(action, handle, cache_file, params):
    if action == 'actualizar':
        enlaces, titulos, origen, fecha = actualizar_lista(cache_file, handle)  # Pasar handle aquí también
        guardar_cache(cache_file, enlaces, titulos, origen, fecha)
    elif action == 'exportar':
        cache = cargar_cache(cache_file)
        exportar_m3u(cache['enlaces'], cache['titulos'], cache['origen'])
    elif action == 'directos':
        mostrar_directos(handle)  # Llamada a la función Directos
    else:
        xbmcgui.Dialog().notification("Acción no reconocida", f"La acción '{action}' no está implementada.")
