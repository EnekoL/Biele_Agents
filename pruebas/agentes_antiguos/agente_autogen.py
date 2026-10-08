import autogen
import time
import chromadb
from chromadb.utils import embedding_functions
from Agentes.conectores.conector_sql import ConectorSQLImpactoCero
from Agentes.conectores.conector_opcua import ConectorOPCUAImpactoCero

# ==========================================
# 1. CONFIGURACIÓN DEL LLM LOCAL (Ollama)
# ==========================================
llm_config = {
    "config_list": [{
        "model": "llama3.2",
        "api_key": "ollama", 
        "base_url": "http://localhost:11434/v1",
        "price": [0, 0] 
    }],
    "temperature": 0.1
}

# ==========================================
# 2. INICIALIZACIÓN DE CONECTORES (Impacto Cero)
# ==========================================
# A. Conector SQL
CADENA_CONEXION = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost\\SQLEXPRESS;"
    "DATABASE=B4571;"
    "UID=sa;"
    "PWD=Biele1234!;"
)
conector_db = ConectorSQLImpactoCero(CADENA_CONEXION, intervalo_polling=5.0)
conector_db.iniciar()

# B. Conector OPC-UA (PLC Simulado)
URL_PLC = "opc.tcp://localhost:4840/freeopcua/server/"
NODOS_PRUEBA = {
    'orden_fabricacion': 'ns=2;i=2', 
    'estado_seguridad': 'ns=2;i=3'   
}
conector_plc = ConectorOPCUAImpactoCero(URL_PLC, NODOS_PRUEBA, intervalo_polling=1.0)
conector_plc.iniciar()

# ==========================================
# 3. MOTOR VECTORIAL (RAG)
# ==========================================
ollama_ef = embedding_functions.OllamaEmbeddingFunction(
    url="http://localhost:11434/api/embeddings", model_name="nomic-embed-text",
)
cliente_chroma = chromadb.PersistentClient(path="./memoria_vectorial")
coleccion_manuales = cliente_chroma.get_collection(name="manuales_biele", embedding_function=ollama_ef)

time.sleep(3) # Damos tiempo a que ambos hilos lean sus datos iniciales

# ==========================================
# 4. DEFINICIÓN DE HERRAMIENTAS (Tools)
# ==========================================
def consultar_eventos_historicos() -> str:
    """Lee la última alarma, error o evento registrado en la base de datos histórica de la máquina."""
    print("\n[SISTEMA INTERNO] -> Orquestador consulta SQL (Histórico)...")
    return conector_db.obtener_dato_ia()

def consultar_estado_tiempo_real() -> str:
    """Lee el estado en tiempo real del PLC (Orden de fabricación activa y zonas de seguridad)."""
    print("\n[SISTEMA INTERNO] -> Orquestador consulta OPC-UA (Tiempo Real)...")
    return conector_plc.obtener_dato_ia()

def consultar_manual_mantenimiento(sintoma: str) -> str:
    """Busca en los manuales técnicos de Biele cómo resolver un problema, alarma o síntoma. 
    Debe recibir como parámetro un texto describiendo el problema."""
    
    print(f"\n[SISTEMA INTERNO] -> Orquestador busca en el Manual RAG: '{sintoma}'...")
    
    # 1. Intentamos Búsqueda Híbrida: Forzamos a ChromaDB a que el texto contenga EXACTAMENTE el síntoma
    resultados = coleccion_manuales.query(
        query_texts=[sintoma],
        n_results=5,
        where_document={"$contains": sintoma} # El filtro léxico estricto
    )
    
    # 2. Fallback: Si no encuentra la palabra exacta (ej. porque está mal escrita o es un concepto),
    # hacemos la búsqueda semántica tradicional
    if not resultados["documents"][0]:
        print("[SISTEMA INTERNO] -> Búsqueda exacta fallida. Activando búsqueda semántica...")
        resultados = coleccion_manuales.query(
            query_texts=[sintoma],
            n_results=10
        )
    
    contexto = "\n\n".join(resultados["documents"][0])
    return f"Extractos del manual técnico:\n{contexto}"
# ==========================================
# 5. CREACIÓN DE AGENTES
# ==========================================
orquestador = autogen.AssistantAgent(
    name="Orquestador_Biele",
    system_message="""Eres el Orquestador IA de una línea industrial de Biele Digital. 
    - Para alarmas pasadas: usa 'consultar_eventos_historicos'.
    - Para el estado actual: usa 'consultar_estado_tiempo_real'.
    - Si te piden ayuda con un fallo, usa 'consultar_manual_mantenimiento' enviando SOLO el código de error (ej: 'F30001').
    - Analiza los extractos del manual devueltos. Si contienen comprobaciones ("Verifique..."), transfórmalas en una guía de pasos enumerados para el operario. Si la información útil no aparece en el extracto, indícalo claramente sin inventar pasos.""",
    llm_config=llm_config,
)

operario = autogen.UserProxyAgent(
    name="Operario", human_input_mode="NEVER", max_consecutive_auto_reply=1, code_execution_config=False,
)

# ==========================================
# 6. REGISTRO DE HERRAMIENTAS
# ==========================================
autogen.agentchat.register_function(
    consultar_eventos_historicos, caller=orquestador, executor=operario,
    name="consultar_eventos_historicos", description="Consulta alarmas y logs del pasado en SQL."
)

autogen.agentchat.register_function(
    consultar_estado_tiempo_real, caller=orquestador, executor=operario,
    name="consultar_estado_tiempo_real", description="Consulta la orden actual y estado de seguridad en el PLC."
)

autogen.agentchat.register_function(
    consultar_manual_mantenimiento, caller=orquestador, executor=operario,
    name="consultar_manual_mantenimiento", description="Busca en los manuales técnicos cómo resolver un problema o alarma."
)
# ==========================================
# 7. EJECUCIÓN (Prueba de estrés para el Orquestador)
# ==========================================
try:
    # Hacemos una pregunta compuesta para forzar al LLM a planificar
    pregunta = "El convertidor SINAMICS me ha tirado un fallo F30001. Búscame directamente en el manual cuáles son las posibles causas y cómo solucionarlo paso a paso."    
    print(f"\n[Operario]: {pregunta}\n")
    
    operario.initiate_chat(
        orquestador,
        message=pregunta
    )
    
finally:
    conector_db.detener()
    conector_plc.detener()