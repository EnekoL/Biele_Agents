import pandas as pd
import json
import re

def limpiar_clave(texto):
    """Convierte un texto sucio en una clave (key) válida y limpia para JSON."""
    texto = str(texto).strip().lower()
    # Reemplaza cualquier cosa que no sea letra o número por un guion bajo
    texto = re.sub(r'[^a-z0-9]', '_', texto)
    # Elimina guiones bajos duplicados
    return re.sub(r'_+', '_', texto).strip('_')

def parsear_excel_a_json(ruta_excel, ruta_json):
    print(f"Leyendo archivo Excel: {ruta_excel}...")
    xls = pd.ExcelFile(ruta_excel)
    catalogo = {}
    
    # Tipos de datos estándar en Siemens TIA Portal
    tipos_validos = ['INT', 'REAL', 'BOOL', 'DINT', 'WORD', 'DWORD', 'STRING', 'BYTE']
    
    for hoja in xls.sheet_names:
        # Ignorar hojas que sabemos que son solo instrucciones o índices
        if hoja.lower() in ['hoja1', 'hoja2', 'work order communication chart']:
            continue
            
        df = pd.read_excel(xls, sheet_name=hoja)
        variables_hoja = {}
        
        for index, row in df.iterrows():
            # Extraer solo los valores de la celda que no sean nulos/NaN
            valores = [str(val).strip() for val in row.values if pd.notna(val) and str(val).strip() != '']
            
            # 1. Buscar si la fila contiene un tipo de dato válido
            tipo_encontrado = next((val for val in valores if val.upper() in tipos_validos), None)
            
            # 2. Buscar si la fila menciona un Data Block (Ej: DB9000, DB9049)
            db_encontrado = next((val for val in valores if val.upper().startswith('DB')), 'DB_Generico')
            
            # Si hay un tipo de dato, es altísimamente probable que sea una fila de variable válida
            if tipo_encontrado:
                # 3. La descripción/nombre será el texto más largo que no sea ni el Tipo ni el DB
                candidatos_desc = [val for val in valores if val != tipo_encontrado and val != db_encontrado and len(val) > 2]
                
                if candidatos_desc:
                    descripcion = max(candidatos_desc, key=len)
                    # Limpiamos saltos de línea (\n) que han metido los ingenieros en las celdas
                    descripcion_limpia = descripcion.replace('\n', ' ').strip()
                    
                    clave_json = limpiar_clave(descripcion_limpia)
                    
                    # 4. Formatear el Node-ID para la librería OPC-UA (Estructura TIA Portal)
                    node_id = f'ns=3;s="{db_encontrado}"."{descripcion_limpia}"'
                    
                    variables_hoja[clave_json] = {
                        "descripcion": descripcion_limpia,
                        "tipo_dato": tipo_encontrado.upper(),
                        "node_id": node_id
                    }
        
        # Si hemos encontrado variables en esta hoja, la añadimos al catálogo
        if variables_hoja:
            nombre_maquina = limpiar_clave(hoja)
            catalogo[nombre_maquina] = variables_hoja
            print(f"  -> Extraídas {len(variables_hoja)} variables de la máquina: {hoja}")
            
    # Guardar el diccionario completo como un archivo JSON
    with open(ruta_json, 'w', encoding='utf-8') as f:
        json.dump(catalogo, f, indent=4, ensure_ascii=False)
        
    print(f"\n¡Éxito! Catálogo semántico generado en: {ruta_json}")

if __name__ == "__main__":
    # Asegúrate de que el nombre del archivo Excel coincide exactamente
    ARCHIVO_EXCEL = 'pruebas\Gyllensvans  Comm Biele OA.xlsx' 
    ARCHIVO_JSON = 'catalogo_plc.json'
    
    parsear_excel_a_json(ARCHIVO_EXCEL, ARCHIVO_JSON)