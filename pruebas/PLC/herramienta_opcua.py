import json
import asyncio
from asyncua import Client
from diccionario_estados import traducir_estado
# ==========================================
# 1. CARGA DEL CATÁLOGO (LA CHULETA DE LA IA)
# ==========================================
try:
    with open('catalogo_plc.json', 'r', encoding='utf-8') as f:
        CATALOGO_PLC = json.load(f)
except FileNotFoundError:
    print("⚠️ ADVERTENCIA: No se ha encontrado el archivo catalogo_plc.json")
    CATALOGO_PLC = {}

# URL del servidor OPC-UA del PLC de Siemens (TIA Portal)
# En producción, esto podría ser dinámico según la máquina.
URL_OPCUA = "opc.tcp://127.0.0.1:4840"

# ==========================================
# 2. CONEXIÓN FÍSICA AL PLC (MOTOR ASÍNCRONO)
# ==========================================
async def _leer_nodo_async(node_id: str) -> str:
    """Se conecta al PLC, lee el nodo exacto y cierra la conexión al instante."""
    # El bloque 'async with' garantiza que la conexión se cierre pase lo que pase
    async with Client(url=URL_OPCUA) as client:
        nodo = client.get_node(node_id)
        valor = await nodo.get_value()
        return str(valor)
def buscar_en_catalogo(palabra_clave: str) -> str:
    """
    Busca variables en el catálogo semántico usando una palabra clave (ej. 'apilador', 'robot').
    Devuelve las máquinas y claves exactas que coinciden con la búsqueda.
    """
    print(f"\n[🔍 AGENTE BUSCANDO] -> Explorando catálogo para la palabra: '{palabra_clave}'")
    
    palabra_clave = palabra_clave.lower()
    coincidencias = []
    
    # CATALOGO_PLC es el JSON que ya tienes cargado al principio de tu archivo
    for maquina, variables in CATALOGO_PLC.items():
        for clave, datos in variables.items():
            descripcion = datos["descripcion"].lower()
            # Buscamos en el nombre de la máquina, en la clave de la variable o en su descripción
            if palabra_clave in maquina.lower() or palabra_clave in clave or palabra_clave in descripcion:
                coincidencias.append(
                    f"- Máquina: '{maquina}' | Variable: '{clave}' | Desc: '{datos['descripcion']}'"
                )
    
    if not coincidencias:
        return f"No se han encontrado variables relacionadas con '{palabra_clave}'."
    
    # Si hay muchas coincidencias, limitamos la salida para no saturar al modelo (ahorro de tokens)
    if len(coincidencias) > 15:
        resultado = "\n".join(coincidencias[:15]) + f"\n...y {len(coincidencias) - 15} más."
    else:
        resultado = "\n".join(coincidencias)
        
    print(f"[✅ BÚSQUEDA EXITOSA] -> Encontradas {len(coincidencias)} variables relevantes.")
    return "Variables encontradas en el catálogo:\n" + resultado
# ==========================================
# 3. HERRAMIENTA BLINDADA PARA EL AGENTE (TOOL)
# ==========================================
def leer_variable_plc(nombre_maquina: str, nombre_variable: str) -> str:
    """
    Lee una variable en tiempo real del PLC. 
    Usa el nombre_maquina y nombre_variable exactos según tu catálogo.
    """
    print(f"\n[🤖 AGENTE MÁQUINA SOLICITA] -> Máquina: {nombre_maquina} | Variable: {nombre_variable}")

    # GUARDARRAÍL 1: ¿Existe la máquina en el catálogo?
    nombre_maquina = nombre_maquina.lower()
    if nombre_maquina not in CATALOGO_PLC:
        return f"ERROR SEMÁNTICO: La máquina '{nombre_maquina}' no existe en el catálogo de planta."
    
    # GUARDARRAÍL 2: ¿Existe la variable en esa máquina?
    nombre_variable = nombre_variable.lower()
    if nombre_variable not in CATALOGO_PLC[nombre_maquina]:
        return f"ERROR SEMÁNTICO: La variable '{nombre_variable}' no está mapeada para la máquina '{nombre_maquina}'."

    # 3. Extraer el Node-ID (La dirección absoluta para Siemens)
    datos_variable = CATALOGO_PLC[nombre_maquina][nombre_variable]
    node_id_real = datos_variable["node_id"]
    descripcion_humana = datos_variable["descripcion"]
    
    print(f"[🛡️ TRADUCCIÓN SEMÁNTICA] -> El Node-ID real es: {node_id_real}")

    # 4. Ejecución de Lectura (Impacto Cero)
    try:
        # Ejecutamos la función asíncrona dentro de la sincronía de la Tool
        valor_actual = asyncio.run(_leer_nodo_async(node_id_real))
        
        # 3. INTERCEPTAMOS EL VALOR ANTES DE ENVIARLO A LA IA
        if datos_variable["tipo_dato"] in ["INT", "DINT"]:
            valor_traducido = traducir_estado(nombre_variable, int(valor_actual))
        else:
            valor_traducido = str(valor_actual)
            
        resultado = f"Lectura exitosa. [{descripcion_humana}] = {valor_traducido}"
        print(f"[✅ OPC-UA RESPONSE] -> {resultado}")
        return resultado
    except Exception as e:
        error_msg = f"ERROR DE CONECTIVIDAD OPC-UA: No se pudo leer el nodo {node_id_real}. Detalle: {repr(e)}"
        print(f"[❌ OPC-UA ERROR] -> {error_msg}")
        return error_msg