import os
import chromadb
from chromadb.utils import embedding_functions

class MotorRAG:
    def __init__(self):
        dir_actual = os.path.dirname(os.path.abspath(__file__))
        ruta_db = os.path.normpath(os.path.join(dir_actual, "..", "..", "memoria_vectorial"))
        
        print(f"[SISTEMA] Conectando a BD Vectorial en: {ruta_db}")
        
        self.ollama_ef = embedding_functions.OllamaEmbeddingFunction(
            url="http://localhost:11434/api/embeddings",
            model_name="nomic-embed-text",
        )
        self.cliente = chromadb.PersistentClient(path=ruta_db)
        
        # Conectamos a las dos colecciones
        self.col_manuales = self.cliente.get_or_create_collection(
            name="manuales_biele", 
            embedding_function=self.ollama_ef
        )
        self.col_logs = self.cliente.get_or_create_collection(
            name="logs_os", 
            embedding_function=self.ollama_ef
        )
        
        print(f"[SISTEMA] RAG Listo -> Manuales: {self.col_manuales.count()} frags | Logs: {self.col_logs.count()} frags")

    def consultar_manual(self, consulta: str) -> str:
        """Busca solo en la colección de manuales PDF."""
        print(f"\n[RAG] Buscando en Manuales: '{consulta}'...")
        return self._buscar_en_coleccion(self.col_manuales, consulta, "manual técnico")

    def consultar_logs_os(self, consulta: str) -> str:
        """Busca solo en la colección de logs del sistema operativo."""
        print(f"\n[RAG] Buscando en Logs OS: '{consulta}'...")
        return self._buscar_en_coleccion(self.col_logs, consulta, "logs del sistema operativo")

    def _buscar_en_coleccion(self, coleccion, consulta: str, tipo_doc: str) -> str:
        """Motor de búsqueda interno reutilizable."""
        # 1. Intento de búsqueda exacta
        resultados = coleccion.query(
            query_texts=[consulta],
            n_results=5,
            where_document={"$contains": consulta} 
        )
        
        # 2. Si falla, búsqueda semántica
        if not resultados["documents"][0]:
            print(f"[RAG] Búsqueda exacta fallida. Activando búsqueda semántica en {tipo_doc}...")
            resultados = coleccion.query(query_texts=[consulta], n_results=10)
        
        # 3. Formateo de respuesta
        if not resultados["documents"][0]:
            return f"No se encontraron resultados relevantes en los {tipo_doc}."
            
        contexto = "\n\n".join(resultados["documents"][0])
        return f"Extractos relevantes de los {tipo_doc}:\n{contexto}"