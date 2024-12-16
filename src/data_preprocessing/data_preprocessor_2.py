import json
from datasets import load_dataset

def process_dataset_for_rag(dataset_name, output_file):
    """
    Procesa el dataset para uso en RAG, extrayendo documentos desde el campo json_parseado.
    """
    print(f"Cargando el dataset {dataset_name}...")
    dataset = load_dataset(dataset_name)

    # Lista para almacenar documentos procesados
    documents = []

    for entry in dataset["train"]:
        if "json_parseado" not in entry:
            print("No se encontró 'json_parseado' en una entrada. Saltando...")
            continue

        try:
            parsed_data = json.loads(entry["json_parseado"])

            # Unir todas las interacciones en un solo texto como documento
            document_content = ""
            for interaction in parsed_data:
                role = interaction.get("role", "").capitalize()
                content = interaction.get("content", "")
                if role and content:
                    document_content += f"{role}: {content}\n"

            # Crear un documento para RAG
            documents.append({
                "content": document_content.strip(),
                "metadata": {
                    "source": "spanish-roleplay-4.5k"
                }
            })

        except json.JSONDecodeError:
            print("Error al decodificar 'json_parseado'. Saltando entrada...")
            continue

    # Guardar documentos procesados en un archivo JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=4)

    print(f"Documentos procesados guardados en {output_file}. Total: {len(documents)}")

if __name__ == "__main__":
    dataset_name = "Kukedlc/spanish-roleplay-4.5k"
    output_file = "processed_documents.json"
    process_dataset_for_rag(dataset_name, output_file)