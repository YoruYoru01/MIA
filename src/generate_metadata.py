import json
from datasets import load_dataset

# Ruta del dataset y el archivo de metadatos
DATASET_NAME = "Kukedlc/spanish-roleplay-4.5k"
OUTPUT_METADATA_PATH = "D:/Documentos/Code/MIA_project/metadata.json"

# Cargar el dataset
def load_and_prepare_metadata(dataset_name):
    print(f"Cargando el dataset {dataset_name}...")
    dataset = load_dataset(dataset_name, split="train")
    
    metadata = []

    for i, entry in enumerate(dataset):
        content = entry["text"]  # Cambia el campo si usas otro
        metadata.append({
            "id": i,  # Índice único para relacionar con los embeddings
            "content": content,
            "source": "spanish-roleplay-4.5k"
        })

    return metadata

# Guardar metadatos como JSON
def save_metadata(metadata, output_path):
    print(f"Guardando metadatos en {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    metadata = load_and_prepare_metadata(DATASET_NAME)
    save_metadata(metadata, OUTPUT_METADATA_PATH)
    print("Metadatos generados y guardados correctamente.")
