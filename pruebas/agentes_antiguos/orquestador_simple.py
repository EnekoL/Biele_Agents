import ollama
import time
from conector_logs import ConectorImpactoCero

# 1. Arrancamos el conector en segundo plano (Impacto Cero)
archivo_prueba = "OS_EventLog.txt"
conector = ConectorImpactoCero(ruta_log=archivo_prueba, intervalo_polling=2.0)
conector.iniciar()

try:
    print("\n[Sistema] Dando tiempo al conector para la primera lectura...")
    time.sleep(3) 

    # 2. El Orquestador extrae el dato instantáneo desde la RAM
    dato_actual = conector.obtener_dato_ia()
    print(f"[Sistema] Dato extraído de la Caché: {dato_actual}")

    # 3. Le pasamos el contexto a Llama 3.2
    print("\n[Agente Orquestador] Analizando la situación con Llama 3.2...")
    
    prompt = f"""
    Eres el asistente de Inteligencia Artificial del Operation Supervisor en una línea de producción de Biele.
    El sistema ha registrado este último evento en los logs: "{dato_actual}"
    
    Dirígete al operario de forma directa, breve y profesional. Explícale qué significa este evento y sugiere una acción rápida.
    """

    respuesta = ollama.chat(model='llama3.2', messages=[
        {'role': 'user', 'content': prompt}
    ])

    print("\n================ RESPUESTA DE LA IA ================")
    print(respuesta['message']['content'])
    print("====================================================")

except KeyboardInterrupt:
    print("\n[Sistema] Apagando...")
finally:
    conector.detener()