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

def mostrar_menu_principal(handle, plugin_url, cache_file):
    # Cargar caché o actualizar lista si es la primera ejecución
    cache = cargar_cache(cache_file)

    if not cache:
        xbmc.log("Menú Principal: Caché no encontrada, actualizando lista", level=xbmc.LOGINFO)
        # Forzar una actualización de la lista
        enlaces, titulos, origen, fecha = actualizar_lista(cache_file, handle)
        if not enlaces:
            xbmcgui.Dialog().notification("Error", "No se pudo obtener canales, verifica la conexión.")
            return
        else:
            # Guardar en caché la lista obtenida
            guardar_cache(cache_file, enlaces, titulos, origen, fecha)
            xbmc.log("Menú Principal: Lista actualizada y guardada en caché", level=xbmc.LOGINFO)

            # Recargar el menú con la lista actualizada
            cache = {'enlaces': enlaces, 'titulos': titulos, 'origen': origen, 'fecha': fecha}

    # Mostrar el contenido del caché
    enlaces, titulos, origen, fecha = cache['enlaces'], cache['titulos'], cache['origen'], cache['fecha']
    xbmcplugin.setPluginCategory(handle, f" [El Barco de sabeT] Última actualización: {fecha}")
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
    if enlaces and titulos:
        for titulo, enlace in zip(titulos, enlaces):
            list_item = xbmcgui.ListItem(label=titulo)
            list_item.setInfo('video', {'title': titulo})
            list_item.setProperty('IsPlayable', 'true')
            xbmcplugin.addDirectoryItem(handle, enlace, list_item, isFolder=False)
    else:
        xbmc.log("Menú Principal: No hay enlaces ni títulos en caché para mostrar.", level=xbmc.LOGWARNING)

    # Finalizar el directorio
    xbmcplugin.endOfDirectory(handle)



# Manejo de las distintas acciones
# Agregar plugin_url como parámetro de la función
def handle_action(action, handle, cache_file, params, plugin_url):
    if action == 'actualizar':
        enlaces, titulos, origen, fecha = actualizar_lista(cache_file, handle)
        guardar_cache(cache_file, enlaces, titulos, origen, fecha)
        mostrar_menu_principal(handle, plugin_url, cache_file)
    elif action == 'exportar':
        cache = cargar_cache(cache_file)
        exportar_m3u(cache['enlaces'], cache['titulos'], cache['fecha'])
    elif action == 'directos':
        mostrar_directos(handle)
    else:
        xbmcgui.Dialog().notification("Acción no reconocida", f"La acción '{action}' no está implementada.")
