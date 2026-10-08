import ollama

print("Conectando con el motor de inferencia local...")

respuesta = ollama.chat(model='llama3.2', messages=[
  {
    'role': 'user',
    'content': 'Eres el orquestador de una máquina industrial. Responde en una sola frase: ¿Cuál es tu función principal?',
  },
])

print("\nRespuesta de la IA:")
print(respuesta['message']['content'])