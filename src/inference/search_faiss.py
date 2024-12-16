import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer

def index_documents(embedding_file, faiss_index_file):
    """
    Indexa los embeddings en FAISS.
    """
    print(f"Cargando embeddings desde {embedding_file}...")
    with open(embedding_file, "r", encoding="utf-8") as f:
        documents = json.load(f)

    # Extraer embeddings y sus IDs
    embeddings = np.array([doc["embedding"] for doc in documents]).astype("float32")
    ids = list(range(len(embeddings)))

    # Crear índice FAISS
    index = faiss.IndexFlatL2(embeddings.shape[1])  # Para similitud de coseno
    index.add(embeddings)

    # Guardar índice FAISS
    faiss.write_index(index, faiss_index_file)
    print(f"Índice FAISS guardado en {faiss_index_file}.")

def search_faiss(query, embedding_model, faiss_index_file, top_k=5):
    """
    Realiza una búsqueda en el índice FAISS.
    """
    print("Cargando índice FAISS...")
    index = faiss.read_index(faiss_index_file)

    print("Generando embedding de consulta...")
    query_embedding = embedding_model.encode(query).reshape(1, -1).astype("float32")

    print("Buscando documentos más similares...")
    distances, indices = index.search(query_embedding, top_k)
    return distances, indices

if __name__ == "__main__":
    embedding_file = "documents_with_embeddings.json"
    faiss_index_file = "faiss_index.bin"

    # Indexar documentos
    index_documents(embedding_file, faiss_index_file)

    # Buscar en el índice
    query = "¿Cómo abordas un nuevo caso?"
    embedding_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
    distances, indices = search_faiss(query, embedding_model, faiss_index_file)

    print("Resultados de búsqueda:")
    print("Distancias:", distances)
    print("Índices:", indices)