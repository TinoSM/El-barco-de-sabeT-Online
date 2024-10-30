import base64
import urllib.request
import xbmcplugin
import xbmcgui
import xbmc
import datetime



def obtener_contenido_directos():
    # URL en Base64 para la lista de directos
    prt = "aHR0cHM6Ly9naXN0LmdpdGh1YnVzZXJjb250ZW50LmNvbS9FbEJhcmNvRGVTYWJlVC80ZDRmYzY5OWFjZWY1NDBmMmI1MDhlYzQ3NTRhODk4Yy9yYXcvYWRmNDYzZGY3ZWM3ZjE4ZWZmMGJjMjQ2N2JkNDQ4NjhlNDliNzY2Zi9iYXJjbzIudHh0"

    # Decodificar URL
    bms = base64.b64decode(prt).decode('utf-8')
    xbmc.log(f"Directos: URL decodificada -> {bms}", level=xbmc.LOGINFO)

    # Leer contenido de la URL
    try:
        with urllib.request.urlopen(bms) as response:
            contenido = response.read().decode('utf-8')
        xbmc.log("Directos: Contenido obtenido correctamente", level=xbmc.LOGINFO)
        return contenido
    except Exception as e:
        xbmcgui.Dialog().notification("Error", f"No se pudo obtener los directos: {str(e)}")
        xbmc.log(f"Directos: Error al obtener contenido -> {str(e)}", level=xbmc.LOGERROR)
        return None


def mostrar_directos(handle):
    xbmc.log("Directos: Iniciando mostrar_directos", level=xbmc.LOGINFO)
    contenido = obtener_contenido_directos()

    if contenido:
        try:
            # Decodificar el contenido en Base64
            contenido_decodificado = base64.b64decode(contenido).decode('utf-8')
            xbmc.log("Directos: Contenido decodificado correctamente", level=xbmc.LOGINFO)

            # Procesar cada línea del contenido decodificado
            lineas = contenido_decodificado.strip().split('\n')
            for linea in lineas:
                xbmc.log(f"Directos: Procesando línea -> {linea}", level=xbmc.LOGINFO)

                # Extraer fecha y hora del inicio de la línea
                try:
                    # Extraer la parte de la fecha y hora
                    fecha_hora_str = linea.split(' CET')[0]
                    fecha_hora_evento = datetime.datetime.strptime(fecha_hora_str, "%d/%m/%Y %H:%M")

                    # Calcular la diferencia de tiempo con la hora actual
                    diferencia = datetime.datetime.now() - fecha_hora_evento
                    if diferencia.total_seconds() > 6 * 3600:  # Si es mayor a 6 horas, omitir el evento
                        xbmc.log(f"Directos: Evento omitido por ser mayor a 6 horas -> {linea}", level=xbmc.LOGINFO)
                        continue
                except ValueError as e:
                    xbmc.log(f"Directos: Error al analizar la fecha y hora -> {linea} | Error: {e}", level=xbmc.LOGWARNING)
                    continue

                # Dividir la línea en título y ID usando rsplit para obtener solo la última parte después de ":"
                partes = linea.rsplit(':', 1)
                if len(partes) == 2:
                    titulo_fecha = partes[0].strip()  # Todo el título con la fecha y la hora
                    enlace_id = partes[1].strip()     # Solo el ID

                    # Crear el enlace en el formato adecuado
                    enlace = f"plugin://script.module.horus?action=play&id={enlace_id}"

                    # Agregar los últimos 4 dígitos del ID al título
                    titulo = f"{titulo_fecha} - {enlace_id[-4:]}"

                    # Crear el ListItem para el evento directo
                    list_item = xbmcgui.ListItem(label=titulo)
                    list_item.setInfo('video', {'title': titulo})
                    list_item.setProperty('IsPlayable', 'true')

                    # Añadir el elemento al menú
                    xbmcplugin.addDirectoryItem(handle, enlace, list_item, isFolder=False)
                    xbmc.log(f"Directos: Enlace añadido -> {enlace} con título -> {titulo}", level=xbmc.LOGINFO)
                else:
                    xbmc.log(f"Directos: Formato incorrecto en línea -> {linea}", level=xbmc.LOGWARNING)

            # Finalizar el directorio
            xbmcplugin.endOfDirectory(handle)

        except Exception as e:
            xbmc.log(f"Directos: Error al decodificar contenido -> {str(e)}", level=xbmc.LOGERROR)
            xbmcgui.Dialog().notification("Error", f"No se pudo decodificar el contenido: {str(e)}")
    else:
        xbmc.log("Directos: No se encontró contenido para mostrar", level=xbmc.LOGWARNING)
        xbmcgui.Dialog().notification("Error", "No se encontraron directos disponibles.")
