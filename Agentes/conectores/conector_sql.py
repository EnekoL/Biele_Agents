import pyodbc
import threading
import time

class ConectorSQLImpactoCero:
    def __init__(self, connection_string, intervalo_polling=5.0):
        self.conn_str = connection_string
        self.intervalo_polling = intervalo_polling
        self.cache_ram = "Esperando primera lectura de SQL Server..."
        self.lock = threading.Lock()
        self._detener = threading.Event()
        
        self.hilo_polling = threading.Thread(target=self._bucle_lectura, daemon=True)

    def iniciar(self):
        self.hilo_polling.start()
        print(f"[OT/IT Separador] Polling SQL iniciado cada {self.intervalo_polling}s. (Filtro de alarmas activado)")

    def detener(self):
        self._detener.set()

    def _bucle_lectura(self):
        """El 'Maquinista' SQL: Consulta la BD filtrando el ruido y actualiza la caché."""
        
        # OPTIMIZACIÓN: Se añade la cláusula WHERE para excluir eventos de mantenimiento 
        # (IdEvent = 9001) o filtrar directamente por la familia de alarmas de Biele.
        query = """
            SELECT TOP 1 
                CONVERT(varchar(40), [EventHistory].[DateEvent], 127) AS DateEvent
                ,[Info], DefEvent.[IdEvent], DefEvent.Name, Description
            FROM [B4571].[dbo].[EventHistory] 
            INNER JOIN [B4571].[dbo].DefEvent ON [EventHistory].[IdEvent] = DefEvent.[IdEvent]
            WHERE DefEvent.Name NOT IN ('DBDataClean', 'UserLogin', 'UserLogout') 
            -- Opcional si tenéis tabla de familias: AND DefEvent.IdEventFamily = 1 (Alarmas)
            ORDER BY [EventHistory].[DateEvent] DESC
        """
        
        while not self._detener.is_set():
            try:
                with pyodbc.connect(self.conn_str, timeout=3) as conn:
                    cursor = conn.cursor()
                    cursor.execute(query)
                    row = cursor.fetchone()
                    
                    if row:
                        dato_formateado = (
                            f"{row.DateEvent} - ALARMA/EVENTO CRÍTICO: {row.Name} - {row.Description} "
                            f"(Info extra: {row.Info}, Código ID: {row.IdEvent})"
                        )
                        
                        with self.lock:
                            self.cache_ram = dato_formateado
                            
            except pyodbc.Error as e:
                # Silenciamos el error exacto para no inundar el log si hay un microcorte de red
                pass
            except Exception as e:
                print(f"[Error de Conector SQL] {e}")
            
            time.sleep(self.intervalo_polling)

    def obtener_dato_ia(self) -> str:
        """La herramienta Tool que usará AutoGen."""
        with self.lock:
            return self.cache_ram

# ==========================================
# PRUEBA DIRECTA DEL CONECTOR
# ==========================================
if __name__ == "__main__":
    CADENA_CONEXION = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost\\SQLEXPRESS;"
        "DATABASE=B4571;"
        "UID=sa;"
        "PWD=Biele1234!;"
    )
    
    conector_db = ConectorSQLImpactoCero(CADENA_CONEXION)
    conector_db.iniciar()
    
    try:
        print("\nEsperando datos reales (sin DBDataClean)... Pulsa Ctrl+C para salir.\n")
        for _ in range(5):
            time.sleep(3)
            print(f"Caché actual -> {conector_db.obtener_dato_ia()}")
    except KeyboardInterrupt:
        pass
    finally:
        conector_db.detener()