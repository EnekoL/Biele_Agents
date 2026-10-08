import os
import json
import pyodbc

# Diccionario central de conexiones
CONEXIONES_BD = {
    "local": "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=B4571;UID=sa;PWD=Biele1234!;",
    "ClientTraceability": "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=B4571_Trace_sim;UID=sa;PWD=Biele1234!;",
    "ClientMonitor": "DRIVER={SQL Anywhere 17};UID=DBA;PWD=sqldemo;ENG=monitor;DBN=monitor;LINKS=shmem;"
}

def generar_mapa_bd(archivo_json: str = "Agentes/documentos/estado_bd.json"):
    print("\n[INIT] Escaneando múltiples bases de datos y generando mapa de estado...")
    mapa_global = {}
    
    for db_id, cadena_sql in CONEXIONES_BD.items():
        print(f"  -> Escaneando BD: {db_id}...")
        mapa_global[db_id] = {}
        
        try:
            with pyodbc.connect(cadena_sql, timeout=5) as conn:
                cursor = conn.cursor()
                
                # Adaptación para SQL Anywhere (ODBC genérico) o SQL Server
                if "SQL Anywhere" in cadena_sql:
                    # Usamos la API estándar de ODBC que esquiva los bloqueos de permisos
                    for row_tabla in cursor.tables(tableType='TABLE'):
                        tabla = row_tabla.table_name
                        
                        # Filtramos las tablas del sistema que el driver pueda colar
                        if tabla.upper().startswith('SYS') or tabla.upper().startswith('RS_') or tabla.upper() == 'DUMMY':
                            continue
                            
                        try:
                            # 1. Contar filas
                            cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
                            filas = cursor.fetchone()[0]
                            
                            # 2. Obtener columnas por la vía oficial ODBC
                            columnas = []
                            for row_col in cursor.columns(table=tabla):
                                columnas.append(f"{row_col.column_name} ({row_col.type_name})")
                                
                            mapa_global[db_id][tabla] = {"filas": filas, "columnas": columnas}
                        except Exception:
                            # Si alguna tabla concreta de monitorización está capada, la saltamos silenciosamente
                            pass
                else:
                    # Query optimizada para SQL Server
                    query_tablas = """
                    SELECT s.Name AS SchemaName, t.NAME AS TableName, p.rows AS RowCounts
                    FROM sys.tables t
                    INNER JOIN sys.indexes i ON t.OBJECT_ID = i.object_id
                    INNER JOIN sys.partitions p ON i.object_id = p.OBJECT_ID AND i.index_id = p.index_id
                    INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                    WHERE t.is_ms_shipped = 0 AND i.OBJECT_ID > 255 AND i.index_id <= 1
                    """
                    cursor.execute(query_tablas)
                    for row in cursor.fetchall():
                        nombre_completo = f"[{row.SchemaName}].[{row.TableName}]"
                        mapa_global[db_id][nombre_completo] = {"filas": int(row.RowCounts), "columnas": []}
                    
                    query_columnas = "SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS"
                    cursor.execute(query_columnas)
                    for row in cursor.fetchall():
                        nombre_completo = f"[{row.TABLE_SCHEMA}].[{row.TABLE_NAME}]"
                        if nombre_completo in mapa_global[db_id]:
                            mapa_global[db_id][nombre_completo]["columnas"].append(f"{row.COLUMN_NAME} ({row.DATA_TYPE})")
                            
        except Exception as e:
            print(f"[❌ INIT] Error escaneando {db_id}: {e}")

    # Asegurar que el directorio exista
    os.makedirs(os.path.dirname(archivo_json), exist_ok=True)
    with open(archivo_json, "w", encoding="utf-8") as f:
        json.dump(mapa_global, f, indent=4)
    print(f"[✅ INIT] Mapa global de BDs guardado en '{archivo_json}'.")

def cargar_contexto_sql(archivo_json: str = "Agentes/documentos/estado_bd.json") -> str:
    contexto = "ESQUEMA MULTI-BASE DE DATOS (Solo tablas con datos):\n"
    if os.path.exists(archivo_json):
        try:
            with open(archivo_json, "r", encoding="utf-8") as f:
                mapa_global = json.load(f)
                for db_id, tablas in mapa_global.items():
                    contexto += f"\n--- DATABASE ID: '{db_id}' ---\n"
                    for tabla, info in tablas.items():
                        filas = info.get('filas', 0)
                        if filas > 0:
                            columnas = info.get('columnas', [])
                            columnas_str = ", ".join(columnas) if columnas else "Columnas no escaneadas aún"
                            contexto += f"- Tabla {tabla} ({filas} filas). Columnas: {columnas_str}\n"
        except Exception:
            contexto += "El mapa JSON está obsoleto o corrupto.\n"
    return contexto