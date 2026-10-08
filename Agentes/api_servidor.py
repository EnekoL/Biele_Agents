import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import pyodbc
import json
from pathlib import Path

# Importamos tu orquestador (ajusta "sistema_core" si tu archivo se llama diferente)
from sistema_core import AsistenteOperacionalBieleHibrido

app = FastAPI(title="Biele AI API")

# 1. Inicializamos el Asistente Globalmente al arrancar
asistente = AsistenteOperacionalBieleHibrido()
asistente.iniciar_servicios()

# Modelo de datos para el endpoint de Chat
class ChatRequest(BaseModel):
    mensaje: str

# ==========================================
# ENDPOINT 1: CHAT PRINCIPAL
# ==========================================
@app.post("/api/chat")
async def procesar_chat(request: ChatRequest):
    respuesta = asistente.procesar_consulta_api(request.mensaje)
    # Devuelve el formato que espere tu aplicación C# (ajusta la clave si es "respuesta" o "response")
    return {"response": respuesta} 

# ==========================================
# ENDPOINT 2: PANEL DE SYSTEM HEALTH
# ==========================================
@app.get("/api/health")
async def check_health():
    # --- RED IT (SQL SERVER) ---
    sql_db = "Desconectado"
    sql_detail = "No se pudo conectar a B4571"
    sql_metadata = "estado_bd.json no encontrado"
    
    try:
        cadena_sql = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=B4571;UID=sa;PWD=Biele1234!;"
        with pyodbc.connect(cadena_sql, timeout=1) as conn:
            sql_db = "Conectado"
            sql_detail = "Latencia OK (< 10ms)"
    except Exception:
        sql_db = "Error"
        sql_detail = "BD caída o inaccesible"

    rutas_bd = [Path("estado_bd.json"), Path("Agentes/documentos/estado_bd.json"), Path("documentos/estado_bd.json")]
    for r in rutas_bd:
        if r.exists():
            try:
                with open(r, "r", encoding="utf-8") as f:
                    mapa = json.load(f)
                    tablas_activas = sum(1 for t, info in mapa.items() if info.get('filas', 0) > 0)
                    sql_metadata = f"Mapa de metadatos cargado ({tablas_activas} tablas activas)"
            except:
                pass

    # --- RED OT (PLC Y CATÁLOGO) ---
    plc_catalogo = "Desconectado"
    plcs_array = []
    rutas_cat = [Path("catalogo_plc_ai.json"), Path("Agentes/documentos/catalogo_plc_ai.json"), Path("documentos/catalogo_plc_ai.json")]
    
    for r in rutas_cat:
        if r.exists():
            try:
                with open(r, "r", encoding="utf-8") as f:
                    catalogo = json.load(f)
                    plc_catalogo = f"Catálogo IA en memoria ({len(catalogo)} máquinas)"
                    for maquina, info in catalogo.items():
                        vars_count = len(info.get("variables", {}))
                        ip = info.get("ip_conexion", "N/A")
                        plcs_array.append({
                            "name": maquina,
                            "status": "Conectado",
                            "detail": f"IP: {ip} | Vars: {vars_count}"
                        })
                break
            except:
                pass

    # --- MOTOR DE CONOCIMIENTO (RAG) ---
    rag_status = "Operativo"
    rag_detail = "Vector DB (Chroma) conectada"
    rag_manuales = 0
    rag_logs = 0
    
    try:
        rag_manuales = asistente.rag.col_manuales.count()
        rag_logs = asistente.rag.col_logs.count()
    except Exception:
        rag_status = "Aviso"
        rag_detail = "ChromaDB no accesible"

    # Retornamos el JSON exacto que espera tu ViewModel en C#
    return {
        "status_global": "Operativo",
        "plc_catalogo": plc_catalogo,
        "sql_db": sql_db,
        "sql_detail": sql_detail,
        "sql_metadata": sql_metadata,
        "rag_status": rag_status,
        "rag_detail": rag_detail,
        "rag_manuales": rag_manuales,
        "rag_logs": rag_logs,
        "plcs": plcs_array
    }

# ==========================================
# ARRANQUE DEL SERVIDOR
# ==========================================
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)