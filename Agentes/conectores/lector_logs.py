import glob
import os

def consultar_logs_tiempo_real(lineas: int = 50, palabra_clave: str = "") -> str:
    ruta_logs = r"C:\_PROJECTS\b4571\Server\B4571\bin\Debug\Log"
    patron = os.path.join(ruta_logs, "Server*.log")
    
    archivos = glob.glob(patron)
    if not archivos:
        return f"No se han encontrado archivos de log en {ruta_logs}"
        
    archivo_mas_reciente = max(archivos, key=os.path.getmtime)
    
    try:
        with open(archivo_mas_reciente, 'r', encoding='utf-8', errors='replace') as f:
            lineas_totales = f.readlines()
            
        if palabra_clave:
            lineas_filtradas = [l for l in lineas_totales if palabra_clave.lower() in l.lower()]
            resultado = lineas_filtradas[-lineas:] if lineas_filtradas else []
        else:
            resultado = lineas_totales[-lineas:]
            
        if not resultado:
            return f"No se encontró la palabra '{palabra_clave}' en el log actual."
            
        texto = "".join(resultado)
        nombre_archivo = os.path.basename(archivo_mas_reciente)
        return f"--- LEYENDO LOG ACTUAL: {nombre_archivo} ---\n{texto}"
        
    except Exception as e:
        return f"Error leyendo el log en tiempo real: {e}"