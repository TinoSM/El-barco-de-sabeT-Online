import os
import json
import time

def cargar_cache(cache_file):
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def guardar_cache(cache_file, enlaces, titulos, origen, fecha):
    # Crear los datos del caché en un diccionario
    cache_data = {
        'enlaces': enlaces,
        'titulos': titulos,
        'origen': origen,
        'fecha': fecha
    }
    # Guardar el caché en el archivo especificado
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f)
