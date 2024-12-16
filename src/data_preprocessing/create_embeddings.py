from sentence_transformers import SentenceTransformer
import json
import numpy as np

def generate_embeddings(input_file, output_file, model_name="sentence-transformers/all-mpnet-base-v2"):
    """
    Genera embeddings para los documentos procesados y los guarda en un archivo JSON.
    """
    print("Cargando modelo de embeddings...")
    model = SentenceTransformer(model_name)

    print(f"Cargando documentos desde {input_file}...")
    with open(input_file, "r", encoding="utf-8") as f:
        documents = json.load(f)

    for doc in documents:
        # Generar embeddings para el contenido
        doc["embedding"] = model.encode(doc["content"]).tolist()

    # Guardar documentos con embeddings
    print(f"Guardando documentos con embeddings en {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=4)

    print("Embeddings generados y guardados con éxito.")

if __name__ == "__main__":
    input_file = "processed_documents.json"  # Archivo generado previamente
    output_file = "documents_with_embeddings.json"
    generate_embeddings(input_file, output_file)