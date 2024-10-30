import base64
import urllib.request
import xbmcplugin
import xbmcgui
import xbmc
import datetime
import gc
import importlib
importlib.reload(datetime)



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

def analizar_fecha_manual(fecha_hora_str):
    """Analiza manualmente una fecha y hora en el formato dd/mm/yyyy hh:mm."""   
    try:
        # Dividir la fecha y hora
        fecha_partes = fecha_hora_str.split(" ")
        fecha = fecha_partes[0]
        hora = fecha_partes[1]

        # Extraer día, mes y año
        dia, mes, anio = map(int, fecha.split("/"))
        
        # Extraer horas y minutos
        hora, minuto = map(int, hora.split(":"))
        
        # Crear un objeto datetime con los componentes extraídos
        import datetime
        fecha_hora_evento = datetime.datetime(anio, mes, dia, hora, minuto)
        
        xbmc.log(f"Directos: Fecha y hora analizada manualmente -> {fecha_hora_evento}", level=xbmc.LOGINFO)
        return fecha_hora_evento
    except Exception as e:
        xbmc.log(f"Directos: Error en el análisis manual de fecha y hora -> {fecha_hora_str} | Error: {e}", level=xbmc.LOGERROR)
        return None


def mostrar_directos(handle):
    import base64
    import urllib.request
    import datetime

    xbmc.log("Directos: Iniciando mostrar_directos", level=xbmc.LOGINFO)
    contenido = obtener_contenido_directos()

    if contenido:
        try:
            contenido_decodificado = base64.b64decode(contenido).decode('utf-8')

            lineas = contenido_decodificado.strip().split('\n')
            for linea in lineas:
                xbmc.log(f"Directos: Procesando línea -> {linea}", level=xbmc.LOGINFO)
                
                # Extraer y analizar la fecha y hora con el método manual
                fecha_hora_str = linea.split(' CET')[0]
                fecha_hora_evento = analizar_fecha_manual(fecha_hora_str)

                if fecha_hora_evento is None:
                    continue  # Si falla el análisis de fecha, omitir esta línea

                # Calcular la diferencia de tiempo con la hora actual
                diferencia = datetime.datetime.now() - fecha_hora_evento
                xbmc.log(f"Directos: Diferencia calculada -> {diferencia}", level=xbmc.LOGINFO)

                if diferencia.total_seconds() > 6 * 3600:
                    xbmc.log(f"Directos: Evento omitido por ser mayor a 6 horas -> {linea}", level=xbmc.LOGINFO)
                    continue

                # Procesamiento de título y enlace
                partes = linea.rsplit(':', 1)
                if len(partes) == 2:
                    titulo_fecha = partes[0].strip()
                    enlace_id = partes[1].strip()
                    enlace = f"plugin://script.module.horus?action=play&id={enlace_id}"
                    titulo = f"{titulo_fecha} - {enlace_id[-4:]}"

                    list_item = xbmcgui.ListItem(label=titulo)
                    list_item.setInfo('video', {'title': titulo})
                    list_item.setProperty('IsPlayable', 'true')

                    try:
                        xbmcplugin.addDirectoryItem(handle, enlace, list_item, isFolder=False)
                    except Exception as e:
                        xbmc.log(f"Directos: Error al añadir item al directorio -> {str(e)}", level=xbmc.LOGERROR)
                else:
                    xbmc.log(f"Directos: Formato incorrecto en línea -> {linea}", level=xbmc.LOGWARNING)

            xbmcplugin.endOfDirectory(handle)

        except Exception as e:
            xbmc.log(f"Directos: Error al decodificar contenido -> {str(e)}", level=xbmc.LOGERROR)
            xbmcgui.Dialog().notification("Error", f"No se pudo decodificar el contenido: {str(e)}")
    else:
        xbmc.log("Directos: No se encontró contenido para mostrar", level=xbmc.LOGWARNING)
        xbmcgui.Dialog().notification("Error", "No se encontraron directos disponibles.")
        
    # Liberar variables al final de la función
    contenido = None
    contenido_decodificado = None
    lineas = None
    diferencia = None
    xbmc.log("Directos: Variables limpiadas al finalizar la ejecución", level=xbmc.LOGINFO)
    # Después de limpiar variables
    gc.collect()
    xbmc.log("Directos: Recolector de basura ejecutado para liberar memoria", level=xbmc.LOGINFO)
