import autogen
import time
import pyodbc
import os
from pathlib import Path
from conocimiento.motor_rag import MotorRAG
from conectores.herramienta_opcua import buscar_en_catalogo, leer_variable_plc
from conectores.lector_logs import consultar_logs_tiempo_real

# IMPORTAMOS EL NUEVO MÓDULO SEPARADO
from conocimiento.mapeador_bd import generar_mapa_bd, cargar_contexto_sql 
from conocimiento.generador_catalogo_definitivo import generar_catalogo_ia
from conocimiento.mapeador_bd import generar_mapa_bd, cargar_contexto_sql


class AsistenteOperacionalBieleHibrido:
    def __init__(self):
        self.llm_config_azure = {
            "config_list": [{
                "model": "gpt-4.1-mini", 
                "api_key": "7stAl77n9CcLxUALopzGkpYVLftUT5racLrapg145NtDa181fRToJQQJ99CIACR0EKYXJ3w3AAAAACOGzzY9", 
                "base_url": "https://tfm-biele-operation-adv-resource.services.ai.azure.com/openai/v1"
            }],
            "temperature": 0.0
        }
        
        self.cadena_sql = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=B4571;UID=sa;PWD=Biele1234!;"
        self.rag = MotorRAG()
        
        self._configurar_agentes()

    def _configurar_agentes(self):
        # Usamos la función importada para cargar el contexto
        contexto_sql = cargar_contexto_sql()

        self.orquestador = autogen.AssistantAgent(
            name="Orquestador_Biele_Cloud",
            system_message="""Eres el Orquestador IA principal de Biele Digital. Tienes 3 especialistas a tu cargo.
            
            JERARQUÍA ESTRICTA DE ANÁLISIS:
            1. ESTADO FÍSICO (OPC-UA): Si preguntan por el estado actual de la máquina ahora mismo, delega SIEMPRE en 'Agente_Maquina_Biele'.
            2. TRAZABILIDAD TEMPORAL (SQL): Si preguntan qué pasó de una hora a otra, o el historial de eventos/alarmas con fechas, delega en 'Agente_SQL'.
            3. MANUALES Y FALLOS DE SOFTWARE (RAG): Si piden consultar manuales técnicos, o investigar cuelgues, excepciones informáticas y errores internos en los logs de la aplicación OS, delega en 'Agente_Documentacion'.
            
            Coordina las respuestas y sintetiza la información final para el operario. Termina con TERMINATE.""",
            llm_config=self.llm_config_azure,
        )

        self.agente_plc = autogen.AssistantAgent(
            name="Agente_Maquina_Biele",
            system_message="""Eres el especialista OT de Biele.
            REGLA DE ORO: TIENES PROHIBIDO ADIVINAR NOMBRES DE MÁQUINAS O VARIABLES.
            
            Tu proceso de trabajo OBLIGATORIO:
            PASO 1: Usa SIEMPRE 'buscar_en_catalogo' pasándole una palabra clave (ej. 'saw', 'alimentador', 'roller').
            PASO 2: Analiza la respuesta de la búsqueda y extrae de ahí el nombre de la máquina y de la variable EXACTOS.
            PASO 3: Solo entonces, usa 'leer_variable_plc' con esos nombres exactos.""",
            llm_config=self.llm_config_azure,
        )

        self.agente_sql = autogen.AssistantAgent(
            name="Agente_SQL",
            system_message=f"""Eres el Analista de Datos SQL.
            
            {contexto_sql}
            
            REGLAS CRÍTICAS DE ENRUTAMIENTO MULTI-DB:
            1. Tienes acceso a 3 bases de datos distintas ('local', 'ClientTraceability', 'ClientMonitor'). 
            2. Selecciona la tabla correcta basándote en el contexto y pasa OBLIGATORIAMENTE el 'db_id' correcto a tu herramienta.
            3. Si consultas 'EventHistory' en la BD 'local', recuerda cruzar con 'DefEvent'.
            4. Usa 'SELECT TOP 5 ... ORDER BY [ColumnaFecha] DESC' para estados recientes en SQL Server. (En SQL Anywhere usa 'TOP 5').""",
            llm_config=self.llm_config_azure,
        )

        self.agente_doc = autogen.AssistantAgent(
            name="Agente_Documentacion",
            system_message="""Eres el especialista en conocimiento y registros del sistema.
            - Si el usuario pide consultar manuales técnicos o instrucciones de mantenimiento, usa 'consultar_manual_mantenimiento' (que usa RAG).
            - Si el usuario pide revisar errores informáticos, caídas de software o qué está pasando en los logs de la aplicación, usa 'consultar_logs_tiempo_real'.""",
            llm_config=self.llm_config_azure,
        )

        terminacion_func = lambda x: x.get("content", "") and "TERMINATE" in x.get("content", "")

        self.operario = autogen.UserProxyAgent(
            name="Operario",
            human_input_mode="NEVER",
            code_execution_config=False,
            is_termination_msg=terminacion_func
        )

        def ejecutar_consulta_libre_sql(query: str, db_id: str) -> str:
            print(f"\n[🤖 AGENTE SQL EJECUTA en {db_id}] -> {query}")
            
            # Importar las conexiones directamente del mapeador para mantener un único punto de verdad
            from conocimiento.mapeador_bd import CONEXIONES_BD
            
            if db_id not in CONEXIONES_BD:
                return f"ERROR: La base de datos '{db_id}' no existe. Usa 'local', 'ClientTraceability' o 'ClientMonitor'."
            
            if not query.strip().lower().startswith("select"):
                return "ERROR: Solo se permiten sentencias SELECT."
            
            def handle_datetimeoffset(dto_value):
                return str(dto_value)
            
            try:
                with pyodbc.connect(CONEXIONES_BD[db_id], timeout=5) as conexion:
                    if "SQL Server" in CONEXIONES_BD[db_id]:
                        conexion.add_output_converter(-155, handle_datetimeoffset)
                    
                    cursor = conexion.cursor()
                    cursor.execute(query)
                    columnas = [desc[0] for desc in cursor.description]
                    filas = cursor.fetchall()
                    if not filas: return "0 resultados encontrados."
                    
                    res = " | ".join(columnas) + "\n" + "-"*40 + "\n"
                    for fila in filas:
                        res += " | ".join(str(v) for v in fila) + "\n"
                    return res
            except Exception as e:
                return f"ERROR SQL en {db_id}: {str(e)}"
               
        def consultar_rag(sintoma: str) -> str:
            return self.rag.consultar_manual(sintoma)
        def consultar_logs(consulta: str) -> str:
            return self.rag.consultar_logs_os(consulta)
        
        autogen.agentchat.register_function(buscar_en_catalogo, caller=self.agente_plc, executor=self.operario, name="buscar_en_catalogo", description="Busca variables.")
        autogen.agentchat.register_function(leer_variable_plc, caller=self.agente_plc, executor=self.operario, name="leer_variable_plc", description="Lee valor OPC-UA.")
        autogen.agentchat.register_function(ejecutar_consulta_libre_sql, caller=self.agente_sql, executor=self.operario, name="ejecutar_consulta_libre_sql", description="Ejecuta SELECT en SQL Server.")
        autogen.agentchat.register_function(consultar_rag, caller=self.agente_doc, executor=self.operario, name="consultar_manual_mantenimiento", description="Busca en RAG.")
        autogen.agentchat.register_function(
            consultar_logs_tiempo_real, 
            caller=self.agente_doc, 
            executor=self.operario, 
            name="consultar_logs_tiempo_real", 
            description="Lee las últimas líneas del archivo de log más reciente en vivo de la aplicación OA. Útil para buscar errores o ver qué hace el software informático. Puedes pasar una palabra_clave (ej. 'Exception') y el número de líneas."
        )
        """ autogen.agentchat.register_function(
            consultar_logs, 
            caller=self.agente_doc, 
            executor=self.operario, 
            name="consultar_logs_os", 
            description="Busca errores, advertencias o eventos recientes en los Logs del Sistema Operativo (OS)."
        ) """

        self.groupchat = autogen.GroupChat(
            agents=[self.operario, self.orquestador, self.agente_plc, self.agente_sql, self.agente_doc],
            messages=[], max_round=20, speaker_selection_method="auto"
        )
        self.manager = autogen.GroupChatManager(groupchat=self.groupchat, llm_config=self.llm_config_azure)

    def iniciar_servicios(self):
        # 1. Mapa SQL (Es muy rápido, se puede hacer en cada arranque)
        generar_mapa_bd()

        # 2. Catálogo PLC Semántico (Lento, usa la IA)
        agenes_dir = Path(__file__).resolve().parent
        documentos_dir = agenes_dir / 'documentos'
        ruta_catalogo = documentos_dir / 'catalogo_plc_ai.json'
        ruta_xml = documentos_dir / 'ServerManager.dev.xml'
        ruta_excel = documentos_dir / 'Gyllensvans  Comm Biele OA.xlsx'

        if not ruta_xml.exists() or not ruta_excel.exists():
            print(f"\n[❌ ERROR CRÍTICO] Faltan archivos base. Asegúrate de que {ruta_xml} y el Excel existan en la ruta correcta.")
        elif not ruta_catalogo.exists():
            print("\n[INIT] Catálogo PLC no encontrado. Invocando modelo de Azure para mapear (tardará unos minutos)...")
            generar_catalogo_ia(str(ruta_xml), str(ruta_excel), str(ruta_catalogo))
        else:
            print("\n[INIT] Catálogo PLC semántico encontrado. Omitiendo generación IA.")
        # 3. Recargamos para que los Agentes lean todo fresco
        self._configurar_agentes()
        print("\n[SISTEMA HÍBRIDO] Servicios iniciados. Orquestador listo.")

    def detener_servicios(self):
        print("\n[SISTEMA HÍBRIDO] Servicios detenidos.")

    def procesar_consulta_api(self, mensaje: str) -> str:
        chat_result = self.operario.initiate_chat(self.manager, message=mensaje, clear_history=False, summary_method="last_msg")
        return chat_result.summary.replace("TERMINATE", "").strip() if chat_result.summary else "Sin respuesta."

if __name__ == "__main__":
    asistente = AsistenteOperacionalBieleHibrido()
    asistente.iniciar_servicios()
    while True:
        pregunta = input("\nConsulta: ")
        if pregunta.lower() == 'salir': break
        print(asistente.procesar_consulta_api(pregunta))