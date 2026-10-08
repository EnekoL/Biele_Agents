import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from asyncua import Client

URL_OPCUA = "opc.tcp://127.0.0.1:4840"

AGENTES_DIR = Path(__file__).resolve().parents[1]
DOCUMENTOS_DIR = AGENTES_DIR / "documentos"


def cargar_catalogo():
    ruta_1 = Path.cwd() / 'catalogo_plc_ai.json'
    ruta_2 = DOCUMENTOS_DIR / 'catalogo_plc_ai.json'
    ruta_3 = AGENTES_DIR / 'conectores' / 'documentos' / 'catalogo_plc_ai.json'

    rutas_a_probar = [ruta_1, ruta_2, ruta_3]

    for ruta in rutas_a_probar:
        if ruta.exists():
            with open(ruta, 'r', encoding='utf-8') as f:
                catalogo = json.load(f)
                if catalogo:
                    print(f"    [INFO] Catálogo cargado desde: {ruta} ({len(catalogo)} máquinas)")
                    return catalogo

    print(f"    [ERROR] No se pudo encontrar un catálogo válido en ninguna de las rutas: {[str(r) for r in rutas_a_probar]}")
    return {}

async def _leer_nodo_async(node_id: str) -> str:
    async with Client(url=URL_OPCUA) as client:
        nodo = client.get_node(node_id)
        valor = await nodo.get_value()
        return str(valor)


def _leer_nodo(node_id: str) -> str:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(_leer_nodo_async(node_id))

    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(asyncio.run, _leer_nodo_async(node_id)).result()


def buscar_en_catalogo(palabra_clave: str) -> str:
    print(f"\n[🔍 AGENTE BUSCANDO] -> Explorando catálogo para la palabra: '{palabra_clave}'")
    CATALOGO_PLC = cargar_catalogo()
    palabra_clave = palabra_clave.lower()
    coincidencias = []
    
    for maquina, info_maquina in CATALOGO_PLC.items():
        # BAJAMOS AL NIVEL CORRECTO DEL JSON
        diccionario_variables = info_maquina.get("variables", {})
        
        for clave, datos in diccionario_variables.items():
            descripcion = datos.get("descripcion_ia", "").lower()
            if palabra_clave in maquina.lower() or palabra_clave in clave.lower() or palabra_clave in descripcion:
                coincidencias.append(
                    f"- Máquina: '{maquina}' | Variable: '{clave}' | Desc: '{datos.get('descripcion_ia', clave)}'"
                )
    
    if not coincidencias:
        return f"No se han encontrado variables relacionadas con '{palabra_clave}'."
    
    if len(coincidencias) > 15:
        resultado = "\n".join(coincidencias[:15]) + f"\n...y {len(coincidencias) - 15} más."
    else:
        resultado = "\n".join(coincidencias)
        
    print(f"[✅ BÚSQUEDA EXITOSA] -> Encontradas {len(coincidencias)} variables relevantes.")
    return "Variables encontradas en el catálogo:\n" + resultado

def leer_variable_plc(nombre_maquina: str, nombre_variable: str) -> str:
    print(f"\n[🤖 AGENTE MÁQUINA SOLICITA] -> Máquina: {nombre_maquina} | Variable: {nombre_variable}")
    CATALOGO_PLC = cargar_catalogo()

    maquinas_keys = {k.lower(): k for k in CATALOGO_PLC.keys()}
    nombre_maquina_baja = nombre_maquina.lower()
    
    if nombre_maquina_baja not in maquinas_keys:
        return f"ERROR SEMÁNTICO: La máquina '{nombre_maquina}' no existe en el catálogo."
    
    maquina_real = maquinas_keys[nombre_maquina_baja]
    
    # BAJAMOS AL NIVEL CORRECTO PARA LEER LA VARIABLE
    diccionario_variables = CATALOGO_PLC[maquina_real].get("variables", {})
    variables_keys = {k.lower(): k for k in diccionario_variables.keys()}
    
    nombre_variable_baja = nombre_variable.lower()
    
    if nombre_variable_baja not in variables_keys:
        return f"ERROR SEMÁNTICO: La variable '{nombre_variable}' no está mapeada para '{maquina_real}'."

    variable_real = variables_keys[nombre_variable_baja]
    datos_variable = diccionario_variables[variable_real]
    node_id_real = datos_variable["node_id"]
    descripcion_humana = datos_variable.get("descripcion_ia", variable_real)

    try:
        valor_actual = _leer_nodo(node_id_real)
        
        if "traduccion" in datos_variable:
            mapa_traduccion = datos_variable["traduccion"]
            if str(valor_actual) in mapa_traduccion:
                valor_traducido = f"{valor_actual} ({mapa_traduccion[str(valor_actual)]})"
            else:
                valor_traducido = str(valor_actual)
        else:
            valor_traducido = str(valor_actual)
            
        resultado = f"Lectura exitosa. [{descripcion_humana}] = {valor_traducido}"
        print(f"[✅ OPC-UA RESPONSE] -> {resultado}")
        return resultado
    except Exception as e:
        error_msg = f"ERROR OPC-UA: No se pudo leer el nodo {node_id_real}. Detalle: {e}"
        print(f"[❌ OPC-UA ERROR] -> {error_msg}")
        return error_msg