import threading
import time
import os

class ConectorImpactoCero:
    def __init__(self, ruta_log, intervalo_polling=2.0):
        self.ruta_log = ruta_log
        self.intervalo_polling = intervalo_polling
        self.cache_ram = "Esperando lectura de datos..."  # Aquí se guarda el dato en RAM
        self.lock = threading.Lock() # Protege la memoria para que no haya choques al leer/escribir
        self._detener = threading.Event()
        
        # Hilo en segundo plano que hará el Polling sin bloquear la IA
        self.hilo_polling = threading.Thread(target=self._bucle_lectura, daemon=True)

    def iniciar(self):
        """Arranca el motor de lectura en segundo plano."""
        # Creamos un log falso si no existe para hacer la prueba
        if not os.path.exists(self.ruta_log):
            with open(self.ruta_log, "w", encoding="utf-8") as f:
                f.write("11:00:00 - SISTEMA INICIADO\n")
        
        self.hilo_polling.start()
        print(f"[OT/IT Separador] Polling iniciado. Leyendo '{self.ruta_log}' cada {self.intervalo_polling}s.")

    def detener(self):
        self._detener.set()

    def _bucle_lectura(self):
        """Este es el 'Maquinista'. Lee el dato físico a un ritmo seguro y lo guarda en caché."""
        while not self._detener.is_set():
            try:
                # Simulamos la lectura de la base de datos o el log del OS
                with open(self.ruta_log, "r", encoding="utf-8") as f:
                    lineas = f.readlines()
                    if lineas:
                        ultima_linea = lineas[-1].strip()
                        
                        # Guardamos en la memoria RAM (Caché)
                        with self.lock:
                            self.cache_ram = ultima_linea
            except Exception as e:
                print(f"[Error de lectura] {e}")
            
            # Espera el tiempo exacto antes de volver a molestar al disco/BD
            time.sleep(self.intervalo_polling)

    def obtener_dato_ia(self):
        """Esta es la herramienta (Tool) que usará el Agente Orquestador. ¡Impacto Cero al disco!"""
        with self.lock:
            return self.cache_ram

# ==========================================
# PRUEBA DEL CONECTOR
# ==========================================
if __name__ == "__main__":
    # 1. Instanciamos el conector apuntando a un archivo log simulado
    archivo_prueba = "OS_EventLog.txt"
    conector = ConectorImpactoCero(ruta_log=archivo_prueba, intervalo_polling=2.0)
    
    # 2. Arrancamos el polling en segundo plano
    conector.iniciar()
    
    try:
        print("\n[IA Simulada] El Agente Orquestador está pidiendo datos...")
        # Simulamos que la IA hace peticiones rápidas
        for i in range(5):
            dato_instantaneo = conector.obtener_dato_ia()
            print(f"-> IA lee desde Caché (0ms latencia): {dato_instantaneo}")
            
            # Esperamos 3 segundos. DURANTE ESTE TIEMPO:
            # ¡Abre el archivo 'OS_EventLog.txt' en tu ordenador, escribe una línea nueva, guárdalo y mira la consola!
            time.sleep(3.0) 
            
    except KeyboardInterrupt:
        print("Prueba finalizada.")
    finally:
        conector.detener()