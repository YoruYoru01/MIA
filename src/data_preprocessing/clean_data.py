from datasets import load_from_disk
import re
import os
import json
from tqdm import tqdm
import random

def clean_text(text):
    """
    Limpia un texto dado, eliminando caracteres no deseados, etiquetas HTML, y normalizando.
    :param text: Texto sin procesar.
    :return: Texto limpio.
    """
    if not text:
        return ""  # Si el texto es None o vacío, devolver cadena vacía

    text = text.lower()  # Convertir a minúsculas
    text = re.sub(r'\s+', ' ', text)  # Eliminar espacios múltiples y saltos de línea
    text = re.sub(r'<.*?>', '', text)  # Eliminar etiquetas HTML
    text = re.sub(r'[^\w\s,.!?¿¡]', '', text)  # Eliminar caracteres especiales no deseados
    return text

def contains_too_much_code(text):
    """
    Verifica si el texto contiene demasiado código.
    :param text: Texto a verificar.
    :return: True si el texto contiene demasiado código, False en caso contrario.
    """
    code_symbols = ["{", "}", "def ", "func ", "import ", "return", "class ", "->", "<-", "#", "/*", "*/", "console.log", "public ", "private "]
    code_lines = sum(1 for symbol in code_symbols if symbol in text)
    return code_lines > 5

def clean_big_spanish(input_path, output_path):
    """
    Limpia y filtra los datos de Big-Spanish-1.2M.
    :param input_path: Carpeta que contiene los datos sin procesar en formato `.arrow`.
    :param output_path: Carpeta donde se guardarán los datos limpios en formato `.txt`.
    """
    dataset = load_from_disk(input_path)
    output_file_path = os.path.join(output_path, "big_spanish_cleaned.txt")

    with open(output_file_path, 'w', encoding='utf-8') as outfile:
        for example in tqdm(dataset['train'], desc="Limpieza del dataset 'big_spanish'", unit="ejemplo"):
            if 'instruction' in example and 'output' in example:
                instruction_clean = clean_text(example.get('instruction'))
                output_clean = clean_text(example.get('output'))

                if contains_too_much_code(instruction_clean) or contains_too_much_code(output_clean):
                    continue  # Saltar ejemplos que contienen demasiado código

                if instruction_clean and output_clean:
                    outfile.write(f"Instruction: {instruction_clean}\nOutput: {output_clean}\n\n")

def clean_spanish_jokes(input_path, output_path):
    """
    Limpia los datos de CHISTES_spanish_jokes y los formatea en pares `Instruction` y `Output`.
    :param input_path: Ruta del archivo con los chistes limpios.
    :param output_path: Ruta donde se guardarán los chistes con contexto.
    """
    joke_prompts = [
        "Cuéntame un chiste.",
        "Dime algo gracioso.",
        "Necesito reírme, ¿tienes algún chiste?",
        "¿Sabes algún chiste?",
        "Hazme reír con un chiste.",
    ]

    with open(input_path, 'r', encoding='utf-8') as infile:
        lines = infile.readlines()

    output_file_path = os.path.join(output_path, "spanish_jokes_cleaned.txt")

    with open(output_file_path, 'w', encoding='utf-8') as outfile:
        for line in lines:
            if line.strip():
                prompt = random.choice(joke_prompts)
                outfile.write(f"Instruction: {prompt}\nOutput: {line.strip()}\n\n")

def clean_spanish_roleplay(input_path, output_path):
    """
    Limpia y guarda los datos del campo `json_parseado` del dataset Spanish-Roleplay.
    :param input_path: Carpeta que contiene los datos sin procesar en formato `.arrow`.
    :param output_path: Carpeta donde se guardarán los datos limpios en formato `.txt`.
    """
    dataset = load_from_disk(input_path)
    output_file_path = os.path.join(output_path, "spanish_roleplay_cleaned.txt")

    with open(output_file_path, 'w', encoding='utf-8') as outfile:
        for example in tqdm(dataset['train'], desc="Limpieza del dataset 'spanish_roleplay'", unit="ejemplo"):
            if 'json_parseado' in example:
                try:
                    parsed_json = json.loads(example['json_parseado'])
                    cleaned_text_parts = []

                    for entry in parsed_json:
                        if 'content' in entry:
                            cleaned_text = clean_text(entry['content'])
                            if cleaned_text:
                                cleaned_text_parts.append(cleaned_text)

                    if cleaned_text_parts:
                        outfile.write("\n".join(cleaned_text_parts) + '\n\n')

                except json.JSONDecodeError:
                    continue

if __name__ == "__main__":
    output_data_path = "D:\Documentos\Code\MIA_project\data\processed"

    # Ejecutar las limpiezas desde este script según lo necesitemos
    # Limpiar el dataset Big-Spanish-1.2M
    #clean_big_spanish("D:\Documentos\Code\MIA_project\data/raw/big_spanish", output_data_path)
    
    # Limpiar el dataset de chistes
    clean_spanish_jokes("D:/Documentos/Code/MIA_project/data/raw/spanish_jokes", output_data_path)
    
    # Limpiar el dataset Spanish Roleplay
    #clean_spanish_roleplay("D:/Documentos/Code/MIA_project/data/raw/spanish_roleplay", output_data_path)