import xbmcgui
import time
import os
import urllib.request
import json
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
