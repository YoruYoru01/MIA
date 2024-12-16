from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM

def load_model_and_pipeline(model_path):
    """
    Carga el modelo y crea un pipeline de generación de texto.
    """
    print(f"Cargando el modelo desde {model_path}...")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    tokenizer.pad_token = tokenizer.eos_token  # Configurar el token de padding
    model = AutoModelForCausalLM.from_pretrained(
        model_path, device_map="auto", torch_dtype="auto"
    )
    print("Modelo y tokenizador cargados correctamente.")
    
    # Crear pipeline sin especificar el dispositivo
    text_generator = pipeline("text-generation", model=model, tokenizer=tokenizer)
    print("Pipeline de generación de texto creado.")
    return text_generator

def generate_response(prompt, pipeline, personality_base=None, max_new_tokens=200, temperature=0.6, top_p=0.8):
    """
    Genera una respuesta usando el pipeline de Hugging Face.
    """
    if personality_base:
        full_prompt = f"{personality_base}\nUsuario: {prompt}\nMIA:"
    else:
        full_prompt = f"Usuario: {prompt}\nMIA:"

    # Generar texto usando el pipeline
    generated_text = pipeline(
        full_prompt,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_p=top_p,
        do_sample=True,
        pad_token_id=pipeline.tokenizer.eos_token_id
    )

    # Extraer solo la parte generada como respuesta
    response = generated_text[0]["generated_text"].replace(full_prompt, "").strip()

     # Eliminar cualquier parte redundante del prompt generado
    if "Usuario:" in response or "MIA:" in response:
        response = response.split("Usuario:")[-1].strip()
        response = response.split("MIA:")[-1].strip()
        response = response.split("Respuesta:")[-1].strip()
        response = response.split("Contexto:")[-1].strip()

    # Postprocesamiento: Filtrar respuestas repetidas
    response_lines = response.split("\n")

    clean_response = "\n".join(sorted(set(response_lines), key=response_lines.index))

    print("Respuesta completa generada por el modelo:", response)

    return clean_response