from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Función para cargar el modelo y el tokenizador
def load_model_and_tokenizer(model_path):
    print(f"Cargando el modelo desde {model_path}...")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    tokenizer.pad_token = tokenizer.eos_token  # Configurar el token de padding
    model = AutoModelForCausalLM.from_pretrained(
        model_path, device_map="auto", torch_dtype=torch.float16
    )
    print("Modelo y tokenizador cargados correctamente.")
    return tokenizer, model

# Generar respuesta desde el modelo
def generate_response(prompt, model, tokenizer, max_new_tokens=150, temperature=0.7, top_p=0.9):


    full_prompt = f"Usuario: {prompt}\nMIA:"

    # Tokenización y generación
    inputs = tokenizer(full_prompt, return_tensors="pt").to("cuda")
    outputs = model.generate(
        inputs["input_ids"],
        attention_mask=inputs["attention_mask"],
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_p=top_p,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id
    )
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

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