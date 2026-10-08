import pandas as pd
import xml.etree.ElementTree as ET
import json
import re
import autogen

# =======================================================================
# 1. CONFIGURACIÓN DEL MODELO IA (Azure)
# =======================================================================
llm_config = {
    "config_list": [{
        "model": "gpt-4.1-mini", 
        "api_key": "7stAl77n9CcLxUALopzGkpYVLftUT5racLrapg145NtDa181fRToJQQJ99CIACR0EKYXJ3w3AAAAACOGzzY9", 
        "base_url": "https://tfm-biele-operation-adv-resource.services.ai.azure.com/openai/v1"
    }],
    "temperature": 0.0 # Temperatura 0 para que sea analítico y no invente
}

# Inicializamos el cliente de AutoGen para llamadas directas
cliente_ia = autogen.OpenAIWrapper(**llm_config)

# =======================================================================
# 2. DICCIONARIOS SEMÁNTICOS (C#)
# =======================================================================
# b4571/Server/B4571.Common/Enums/... 
DICCIONARIOS_CSHARP = {
    # ZoneStatus.cs
    "ZoneStatus": {0: "Manual", 1: "Stopped", 2: "Running", 3: "SafetyNoOk", 4: "FaultStopped", 5: "FaultStopping", 6: "RunningCtrldStop", 7: "StoppedWaittingAirPreesure", 8: "LineMayorFaultOrRecovering"},
    # OrderStatus.cs
    "OrderStatus": {0: "Pending", 1: "Running", 2: "Paused", 3: "Canceled"},
    # StackStatus.cs
    "StackStatus": {0: "Pending", 1: "Started", 2: "Finished", 3: "Canceled"},
    # LabelPrintStatus.cs
    "LabelPrintStatus": {0: "Pending", 1: "Printed", 2: "Failed"}
}

def inferir_diccionario(nombre_campo: str) -> str:
    nom = nombre_campo.lower()
    if "status" in nom or "state" in nom:
        if any(zona in nom for zona in ["zone", "roller", "bogie", "pusher", "conveyor", "saw", "stacker", "feeder", "tracks"]): return "ZoneStatus"
        elif "workorder" in nom or "wo_" in nom: return "OrderStatus"
        elif "stack" in nom: return "StackStatus"
        elif "print" in nom or "barcode" in nom: return "LabelPrintStatus"
        elif re.search(r'z\d+_status', nom): return "ZoneStatus"
    return None

# =======================================================================
# 3. EXTRACCIÓN BRUTA DEL EXCEL
# =======================================================================
def extraer_textos_excel(ruta_excel):
    print(f"[📊] Extrayendo descripciones del Excel: {ruta_excel}...")
    textos = set()
    try:
        xls = pd.ExcelFile(ruta_excel)
        tipos_validos = ['INT', 'REAL', 'BOOL', 'DINT', 'WORD', 'DWORD', 'STRING', 'BYTE', 'LINT']
        
        for hoja in xls.sheet_names:
            if hoja.lower() in ['hoja1', 'hoja2', 'work order communication chart']: continue
            df = pd.read_excel(xls, sheet_name=hoja)
            for _, row in df.iterrows():
                valores = [str(val).strip() for val in row.values if pd.notna(val) and str(val).strip() != '']
                if any(v.upper() in tipos_validos for v in valores):
                    # Cogemos la celda de texto más larga asumiendo que es la descripción
                    candidatos = [v for v in valores if v.upper() not in tipos_validos and not v.upper().startswith('DB')]
                    if candidatos:
                        textos.add(max(candidatos, key=len).replace('\n', ' ').strip())
        return list(textos)
    except Exception as e:
        print(f"[❌] Error en Excel: {e}")
        return []

# =======================================================================
# 4. MAPEADOR INTELIGENTE (LLM)
# =======================================================================
def emparejar_con_ia(variables_xml: list, descripciones_excel: list) -> dict:
    """Envía un lote de variables al LLM para que las empareje semánticamente con el Excel."""
    
    # Para ahorrar tokens y evitar colapsos, le pasamos solo las descripciones humanas como contexto
    contexto_excel = "\n".join([f"- {desc}" for desc in descripciones_excel])
    lote_xml = "\n".join([f"- {var}" for var in variables_xml])
    
    prompt = f"""Eres un ingeniero de automatización experto en sistemas Siemens TIA Portal de la empresa Biele.
    Tu tarea es mapear nombres técnicos de variables OPC-UA con su descripción humana más lógica.
    Ten en cuenta que hay términos en inglés y español (ej: Feeder = Alimentador, Saw = Sierra, Stacker = Apilador).
    
    LISTA DE DESCRIPCIONES HUMANAS DISPONIBLES (Extraídas del Excel):
    {contexto_excel}
    
    VARIABLES TÉCNICAS A MAPEAR (Del XML):
    {lote_xml}
    
    Devuelve ÚNICAMENTE un objeto JSON válido donde la clave sea la "Variable Técnica" y el valor sea una frase que combine el nombre técnico y la descripción humana encontrada. Si no encuentras relación clara, devuelve solo el nombre técnico.
    Ejemplo de salida:
    {{
        "FormatSaw.PLC13.Status.MaterialFeederZone": "FormatSaw.PLC13.Status.MaterialFeederZone (Estado de la zona del alimentador de la sierra)",
        "LineInput.WorkOrderA.Request.ReportNumber": "LineInput.WorkOrderA.Request.ReportNumber"
    }}
    """
    
    print(f"[🧠] Consultando al modelo de Azure para {len(variables_xml)} variables...")
    try:
        respuesta = cliente_ia.create(
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"} # Forzamos salida JSON pura
        )
        contenido = respuesta.choices[0].message.content
        return json.loads(contenido)
    except Exception as e:
        print(f"[⚠️️] Fallo en la llamada a la IA: {e}")
        # En caso de fallo de red, devolvemos el nombre original como fallback
        return {var: var for var in variables_xml}

# =======================================================================
# 5. ORQUESTACIÓN PRINCIPAL
# =======================================================================
def generar_catalogo_ia(ruta_xml, ruta_excel, ruta_json):
    textos_excel = extraer_textos_excel(ruta_excel)
    
    print(f"\n[⚙️] Analizando topología física del XML: {ruta_xml}...")
    try:
        tree = ET.parse(ruta_xml)
        root = tree.getroot()
    except Exception as e:
        print(f"[❌] Error leyendo XML: {e}")
        return

    catalogo = {}
    procesos_plc = root.findall(".//process[@ip]")

    for process in procesos_plc:
        nombre_plc = process.get("name")
        ip_plc = process.get("ip")
        
        if not nombre_plc or "Simulator" in nombre_plc or "PlcAlarms" in nombre_plc:
            continue

        maquina_dict = {"ip_conexion": ip_plc, "variables": {}}
        nombres_variables_plc = []
        datos_en_bruto = {}
        
        # 1. Recopilar todas las variables reales del PLC
        for group in process.findall("group"):
            db_numero = group.get("dbnumber")
            if not db_numero: continue
                
            for field in group.findall(".//field"):
                nombre_campo = field.get("name")
                tipo_dato = field.get("type", "BOOL").upper()
                
                if not nombre_campo or "Spare" in nombre_campo: continue

                node_id = f'ns=3;s="DB{db_numero}"."{nombre_campo}"'
                nombres_variables_plc.append(nombre_campo)
                
                datos_en_bruto[nombre_campo] = {
                    "db": db_numero,
                    "tipo_dato": tipo_dato,
                    "node_id": node_id
                }

        if not nombres_variables_plc:
            continue
            
        print(f"\nProcesando PLC: {nombre_plc} ({len(nombres_variables_plc)} variables)")
        
        # 2. Emparejamiento Semántico por Lotes (Para no saturar la ventana de contexto del LLM)
        tamano_lote = 40
        descripciones_enriquecidas = {}
        
        for i in range(0, len(nombres_variables_plc), tamano_lote):
            lote = nombres_variables_plc[i:i+tamano_lote]
            mapa_lote = emparejar_con_ia(lote, textos_excel)
            descripciones_enriquecidas.update(mapa_lote)
            
        # 3. Construir el diccionario final con los estados de C# y el texto de la IA
        for nombre_campo, info_cruda in datos_en_bruto.items():
            clave_json = str(nombre_campo).replace('.', '_').strip()
            enum_asociado = inferir_diccionario(nombre_campo)
            
            # Cogemos el texto que la IA decidió, o el original si la IA falló
            desc_final = descripciones_enriquecidas.get(nombre_campo, nombre_campo)
            
            variable_obj = {
                "descripcion_ia": desc_final,
                "db": info_cruda["db"],
                "tipo_dato": info_cruda["tipo_dato"],
                "node_id": info_cruda["node_id"]
            }
            
            if enum_asociado and info_cruda["tipo_dato"] in ["INT", "DINT", "WORD", "BYTE"]:
                variable_obj["tipo_semantico"] = enum_asociado
                variable_obj["traduccion"] = DICCIONARIOS_CSHARP[enum_asociado]
            
            maquina_dict["variables"][clave_json] = variable_obj
            
        catalogo[nombre_plc] = maquina_dict

    with open(ruta_json, 'w', encoding='utf-8') as f:
        json.dump(catalogo, f, indent=4, ensure_ascii=False)
        
    print(f"\n[✅] ¡Catálogo IA completado! Guardado en: {ruta_json}")

if __name__ == "__main__":
    from pathlib import Path

    base_dir = Path(__file__).resolve().parent.parent
    documentos_dir = base_dir / 'documentos'
    XML_ORIGEN = documentos_dir / 'ServerManager.dev.xml'
    EXCEL_ORIGEN = documentos_dir / 'Gyllensvans  Comm Biele OA.xlsx'
    JSON_DESTINO = documentos_dir / 'catalogo_plc_ai.json'
    generar_catalogo_ia(str(XML_ORIGEN), str(EXCEL_ORIGEN), str(JSON_DESTINO))