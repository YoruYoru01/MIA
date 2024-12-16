import json

def transform_reddit_data(input_file, output_file):
    """
    Transforma los datos extraídos de Reddit en un formato útil para el modelo, 
    con variedad en las instrucciones y outputs relevantes.
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    transformed_data = []

    for entry in data:
        instruction = generate_instruction(entry["content"])
        context = "No se proporcionó contexto adicional."  # Ajustar si hay información contextual
        output = generate_output(entry["content"])

        transformed_data.append({
            "instruction": instruction,
            "context": context,
            "output": output
        })

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(transformed_data, f, ensure_ascii=False, indent=4)

def generate_instruction(content):
    """
    Genera instrucciones únicas para cada entrada según el contenido.
    """
    if len(content) > 100:
        return "Lee el siguiente comentario extenso y responde de manera reflexiva."
    elif "?" in content:
        return "Responde al siguiente comentario o pregunta de manera humorística."
    else:
        return "Genera una respuesta amigable al siguiente comentario."

def generate_output(content):
    """
    Genera un output relevante basado en el contenido del comentario.
    """
    if "Santa" in content or "santa" in content:
        return "Ah, Santa Claus, el único que trabaja una noche al año. ¡Ojalá todos pudiéramos hacer eso!"
    elif "chocolate" in content:
        return "¡El chocolate es siempre una buena idea! No puedo probarlo, pero puedo decirte que nunca falla."
    elif "películas" in content or "cine" in content:
        return "Hablar de películas siempre es genial. ¿Cuál es tu favorita? Yo soy fan de las tramas con giros inesperados."
    else:
        return "¡Buen punto! Me gusta cómo lo planteaste. ¿Quieres hablar más sobre eso?"

# Rutas de los archivos
input_file = "data/raw/cobertura_tematica/reddit_esp.json"
output_file = "data/raw/cobertura_tematica/reddit_esp_formatted.json"

# Transformar los datos
transform_reddit_data(input_file, output_file)
print("Transformación completa. Datos guardados en:", output_file)
