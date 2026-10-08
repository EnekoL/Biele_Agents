import os
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import logging

logging.getLogger("pypdf").setLevel(logging.ERROR)

def procesar_documentos():
    print("[RAG] Iniciando ingesta de la carpeta 'documentos'...")
    
    # 1. Configurar Motor y BD
    ollama_ef = embedding_functions.OllamaEmbeddingFunction(
        url="http://localhost:11434/api/embeddings",
        model_name="nomic-embed-text",
    )
    cliente_chroma = chromadb.PersistentClient(path="./memoria_vectorial")
    
    # Creamos las dos colecciones separadas
    col_manuales = cliente_chroma.get_or_create_collection(name="manuales_biele", embedding_function=ollama_ef)
    col_logs = cliente_chroma.get_or_create_collection(name="logs_os", embedding_function=ollama_ef)

    # 2. Configurar el separador de textos
    separador = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)

    ruta_base = "documentos"
    if not os.path.exists(ruta_base):
        os.makedirs(ruta_base)
        print(f"[ERROR] La carpeta '{ruta_base}' no existía. Se ha creado. Mete ahí los archivos y vuelve a ejecutar.")
        return

    # 3. Leer y procesar archivos
    for archivo in os.listdir(ruta_base):
        ruta_archivo = os.path.join(ruta_base, archivo)
        texto_completo = ""
        coleccion_destino = None
        prefijo_id = ""

        if archivo.lower().endswith(".pdf"):
            print(f" -> Procesando Manual PDF: {archivo}")
            lector = PdfReader(ruta_archivo)
            for pagina in lector.pages:
                texto = pagina.extract_text()
                if texto: texto_completo += texto + "\n"
            coleccion_destino = col_manuales
            prefijo_id = "doc_manual_"

        elif archivo.lower().endswith(".txt"):
            print(f" -> Procesando Logs TXT: {archivo}")
            with open(ruta_archivo, "r", encoding="utf-8") as f:
                texto_completo = f.read()
            coleccion_destino = col_logs
            prefijo_id = "doc_log_"
        else:
            continue

        if texto_completo and coleccion_destino is not None:
            fragmentos = separador.split_text(texto_completo)
            ids = [f"{prefijo_id}{archivo}_{i}" for i in range(len(fragmentos))]
            
            # Ingesta por micro-lotes
            tamano_lote = 5
            for i in range(0, len(fragmentos), tamano_lote):
                coleccion_destino.upsert(
                    documents=fragmentos[i : i + tamano_lote],
                    ids=ids[i : i + tamano_lote]
                )
            print(f"    [OK] {len(fragmentos)} fragmentos indexados.")

    print("\n[ÉXITO] ¡Ingesta completada! Manuales y Logs guardados en sus respectivas colecciones.")

if __name__ == "__main__":
    procesar_documentos()