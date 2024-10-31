import sys
import os
import xbmcaddon
import urllib.parse

# Añadir la carpeta 'lib' a la ruta de búsqueda de Python antes de importar módulos personalizados
addon_dir = xbmcaddon.Addon().getAddonInfo('path')
lib_path = os.path.join(addon_dir, 'lib')
sys.path.append(lib_path)

from main_menu import mostrar_menu_principal, handle_action  # Importar módulos personalizados después de añadir 'lib' a sys.path

plugin_url = sys.argv[0]
handle = int(sys.argv[1])
cache_file = os.path.join(addon_dir, 'cache.json')

# Comprobamos la acción seleccionada por el usuario y otros parámetros
params = urllib.parse.parse_qs(sys.argv[2][1:])
action = params.get('action', [None])[0]

# Ejecutar la acción o mostrar el menú principal
if action:
    handle_action(action, handle, cache_file, params, plugin_url)
else:
    mostrar_menu_principal(handle, plugin_url, cache_file)
