import autogen
import psycopg2 # <-- Librería para PostgreSQL
import os

# ==========================================
# 1. CONFIGURACIÓN DE AZURE
# ==========================================
llm_config_azure = {
    "config_list": [{
        "model": "gpt-4.1-mini", 
        # Pon aquí tu clave COMPLETA, la misma que usas en sistema_core.py:
        "api_key": "7stAl77n9CcLxUALopzGkpYVLftUT5racLrapg145NtDa181fRToJQQJ99CIACR0EKYXJ3w3AAAAACOGzzY9", 
        "base_url": "https://tfm-biele-operation-adv-resource.services.ai.azure.com/openai/v1"
    }],
    "temperature": 0.2 
}

# ==========================================
# 2. HERRAMIENTA DE EJECUCIÓN SQL (POSTGRESQL)
# ==========================================
def ejecutar_consulta_libre(query: str) -> str:
    """Ejecuta una consulta SQL libre generada por la IA en PostgreSQL y devuelve los resultados."""
    print(f"\n[🤖 EL AGENTE EJECUTA SQL] -> {query}")
    
    query_limpia = query.strip().lower()
    
    # Filtro 1: Prohibir modificaciones
    if not query_limpia.startswith("select"):
        return "ERROR: Operación no permitida. Solo puedes usar sentencias SELECT."
    
    # Filtro 2: Adaptado a PostgreSQL (Uso de LIMIT en lugar de TOP)
    if "limit " not in query_limpia:
        # Quitamos el punto y coma final si la IA lo ha puesto, añadimos LIMIT y cerramos
        query = query.strip().rstrip(";") + " LIMIT 50;"
        print(f"[🛡️ GUARDARRAÍL ACTIVADO] Query ajustada a: {query}")

    try:
        # Conexión inyectando los datos de tu docker-compose
        conexion = psycopg2.connect(
            host="localhost",
            port="5432",
            database="postgres", # Base de datos por defecto en la imagen de Postgres
            user="postgres",
            password="Biele943",
            connect_timeout=5
        )
        cursor = conexion.cursor()
        cursor.execute(query)
        
        # Obtener nombres de columnas
        columnas = [desc[0] for desc in cursor.description]
        filas = cursor.fetchall()
        
        cursor.close()
        conexion.close()
        
        if not filas:
            return "La consulta se ejecutó correctamente pero no devolvió ningún resultado."
        
        # Formatear el resultado como una tabla de texto simple
        resultado_str = " | ".join(columnas) + "\n"
        resultado_str += "-" * 50 + "\n"
        for fila in filas:
            resultado_str += " | ".join(str(valor) for valor in fila) + "\n"
            
        return resultado_str

    except Exception as e:
        return f"ERROR DE SINTAXIS O EJECUCIÓN (POSTGRESQL): {str(e)}"

# ==========================================
# 3. PREPARAR EL CONTEXTO (LEER ESQUEMA)
# ==========================================
def leer_esquema():
    ruta_archivo = "estructura_ligna.sql"
    if os.path.exists(ruta_archivo):
        with open(ruta_archivo, "r", encoding="utf-8") as archivo:
            return archivo.read()
    return "Error: No se encontró el archivo estructura_ligna.sql"

esquema_bd = leer_esquema()

# ==========================================
# 4. DEFINICIÓN DE AGENTES
# ==========================================
explorador = autogen.AssistantAgent(
    name="Analista_Datos_Biele",
    system_message=f"""Eres un Analista de Datos Senior industrial. 
    Tu objetivo es explorar libremente la base de datos PostgreSQL de producción y encontrar información relevante, anomalías o un resumen del estado de las órdenes.
    
    ESQUEMA DE LA BASE DE DATOS:
    {esquema_bd}
    
    INSTRUCCIONES DE OPERACIÓN:
    1. Usa la herramienta 'ejecutar_consulta_libre' para lanzar queries. Usa sintaxis PostgreSQL.
    2. Si recibes un error SQL, corrígelo y vuelve a intentarlo.
    3. REGLA CRÍTICA DE TIEMPO: No intentes analizar todas las tablas. Realiza un MÁXIMO de 5 o 6 consultas estratégicas (por ejemplo: estados de línea, alarmas más frecuentes o tiempos de ciclo).
    4. En cuanto ejecutes esas 5 o 6 consultas y tengas una idea general, DETÉN la exploración de inmediato.
    5. Redacta un informe ejecutivo detallado para la dirección resumiendo tus hallazgos.
    6. Tu último mensaje DEBE contener el informe y terminar obligatoriamente con la palabra "TERMINATE".
    """,
    llm_config=llm_config_azure,
)

usuario_proxy = autogen.UserProxyAgent(
    name="Admin",
    human_input_mode="NEVER", 
    max_consecutive_auto_reply=30, 
    is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config=False,
)

# Enlazar la herramienta
autogen.agentchat.register_function(
    ejecutar_consulta_libre, 
    caller=explorador, 
    executor=usuario_proxy, 
    name="ejecutar_consulta_libre", 
    description="Ejecuta consultas SELECT en la base de datos PostgreSQL."
)

# ==========================================
# 5. INICIAR EL EXPERIMENTO
# ==========================================
if __name__ == "__main__":
    print("\n--- INICIANDO EXPLORACIÓN AUTÓNOMA EN POSTGRESQL ---")
    usuario_proxy.initiate_chat(
        explorador,
        message="Por favor, audita la base de datos. Analiza el estado general de las órdenes de fabricación y los materiales, busca patrones interesantes y devuélveme un informe ejecutivo de la planta."
    )