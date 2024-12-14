from datasets import load_dataset

def download_datasets():
    """
    Descarga los datasets seleccionados desde Hugging Face y los guarda en la carpeta correspondiente.
    """
    datasets = {
        "big_spanish": "Kukedlc/Big-Spanish-1.2M",
        "spanish_jokes": "mrm8488/CHISTES_spanish_jokes",
        "spanish_roleplay": "Kukedlc/spanish-roleplay-4.5k"
    }
    
    for name, path in datasets.items():
        print(f"Descargando {name} desde {path}...")
        dataset = load_dataset(path)
        dataset.save_to_disk(f"D:/Documentos/Code/MIA_project/data/raw/{name}")
        print(f"{name} descargado y guardado en ../../data/raw/{name}")

if __name__ == "__main__":
    #download_datasets()
    from datasets import load_dataset

    # Cargar el dataset desde Hugging Face
    dataset_name = "Kukedlc/spanish-roleplay-4.5k"
    print(f"Cargando el dataset {dataset_name}...")
    dataset = load_dataset(dataset_name)

    # Inspeccionar la estructura de los datos
    print("\nEstructura del dataset:")
    print(dataset)

    # Mostrar las primeras entradas del dataset
    print("\nPrimeras entradas:")
    print(dataset["train"][0])  # Cambiar "train" si hay otros splits