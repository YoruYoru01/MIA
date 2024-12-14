import os
import random

def verify_cleaned_data(file_path, num_samples=5):
    """
    Verifica el contenido de un archivo de datos limpios mostrando una muestra aleatoria de ejemplos.
    :param file_path: Ruta del archivo con los datos limpios.
    :param num_samples: Número de ejemplos a mostrar.
    """
    if not os.path.exists(file_path):
        print(f"El archivo '{file_path}' no existe.")
        return

    with open(file_path, 'r', encoding='utf-8') as infile:
        lines = infile.readlines()

    if len(lines) == 0:
        print(f"El archivo '{file_path}' está vacío.")
        return

    # Mostrar algunas muestras aleatorias del archivo
    print(f"\nVerificando contenido del archivo: {file_path}")
    print(f"Total de líneas en el archivo: {len(lines)}\n")
    
    # Seleccionar muestras aleatorias sin reemplazo
    sampled_lines = random.sample(lines, min(num_samples, len(lines)))

    for idx, line in enumerate(sampled_lines):
        print(f"Muestra {idx + 1}:\n{line}\n{'-' * 50}")

if __name__ == "__main__":
    # Rutas a los archivos procesados
    processed_files = [
        "D:\Documentos\Code\MIA_project\data\processed\spanish_jokes_cleaned.txt",
        "D:\Documentos\Code\MIA_project\data\processed\spanish_roleplay_cleaned.txt",
        "D:\Documentos\Code\MIA_project\data\processed/big_spanish_cleaned.txt"
    ]

    # Número de muestras a verificar
    num_samples = 5

    # Verificar cada archivo de datos limpios
    for file_path in processed_files:
        verify_cleaned_data(file_path, num_samples)