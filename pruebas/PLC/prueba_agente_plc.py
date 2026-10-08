import autogen
from herramienta_opcua import leer_variable_plc, buscar_en_catalogo

llm_config_azure = {
            "config_list": [{
                "model": "gpt-4.1-mini", 
                "api_key": "7stAl77n9CcLxUALopzGkpYVLftUT5racLrapg145NtDa181fRToJQQJ99CIACR0EKYXJ3w3AAAAACOGzzY9", # Tu clave directa
                "base_url": "https://tfm-biele-operation-adv-resource.services.ai.azure.com/openai/v1"
            }],
            "temperature": 0.0
        }

# 1. El System Message ahora incluye la instrucción lógica del doble paso
agente_plc = autogen.AssistantAgent(
    name="Agente_Maquina_Biele",
    system_message="""Eres el Agente especialista en automatización industrial.
    Tienes dos herramientas a tu disposición:
    1. Si el usuario te hace una pregunta genérica (ej: "¿Cómo está el apilador 2?"), usa PRIMERO `buscar_en_catalogo` con una palabra clave (ej: "apilador 2") para descubrir qué máquinas y variables exactas existen.
    2. Una vez tengas las claves exactas, usa `leer_variable_plc` pasándole el 'nombre_maquina' y 'nombre_variable' para obtener el valor físico real del autómata.
    Nunca te inventes claves de variables. Busca siempre primero si no estás seguro.
    Termina tu respuesta con la palabra TERMINATE.""",
    llm_config=llm_config_azure,
)

admin = autogen.UserProxyAgent(
    name="Admin",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=4, # Aumentamos a 4 para permitir el ciclo Buscar -> Leer -> Responder
    is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config=False,
)

# 2. Registramos AMBAS herramientas
autogen.agentchat.register_function(
    buscar_en_catalogo,
    caller=agente_plc,
    executor=admin,
    name="buscar_en_catalogo",
    description="Busca en el diccionario de variables del PLC. Devuelve los nombres exactos de máquina y variable necesarios para leer los datos."
)

autogen.agentchat.register_function(
    leer_variable_plc,
    caller=agente_plc,
    executor=admin,
    name="leer_variable_plc",
    description="Lee un valor físico en tiempo real. Requiere el nombre de la máquina y la variable exactos."
)

if __name__ == "__main__":
    print("--- INICIANDO PRUEBA DE ARQUITECTURA DE DOS PASOS ---")
    
    # Petición genérica y ambigua de un operario
    mensaje = "Hola, ¿me puedes decir si la zona del robot y el alimentador infeed están activos?"
    
    admin.initiate_chat(
        agente_plc,
        message=mensaje
    )