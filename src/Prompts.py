from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

def load_model_and_tokenizer(model_path):
    print(f"Cargando el modelo desde {model_path}...")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    tokenizer.pad_token = tokenizer.eos_token  # Configurar el token de padding
    model = AutoModelForCausalLM.from_pretrained(
        model_path, device_map="auto", torch_dtype=torch.float16
    )
    print("Modelo y tokenizador cargados correctamente.")
    return tokenizer, model

def generate_response(prompt, model, tokenizer, history=None, max_new_tokens=200, temperature=0.7, top_p=0.8, personality_base=None, history_limit=6):
    """
    Genera una respuesta basada en el prompt, sin usar FAISS.
    """
    if personality_base:
        base_prompt = f"{personality_base}\n\n"
    else:
        base_prompt = ""

    # Limitar el historial a un número máximo de interacciones
    if history:
        history = history[-history_limit:]
        history_prompt = "\n".join([
            f"Usuario: {h['input']}\nMIA: {h['response']}" for h in history if "response" in h
        ])
        full_prompt = f"{base_prompt}Historial de conversación:\n{history_prompt}\n\nUsuario: {prompt}\nMIA:"
    else:
        full_prompt = f"{base_prompt}Usuario: {prompt}\nMIA:"

    # Crear inputs y generar respuesta
    inputs = tokenizer(full_prompt, return_tensors="pt", padding=True, truncation=True).to("cuda")
    outputs = model.generate(
        inputs["input_ids"],
        attention_mask=inputs["attention_mask"],
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_k=50,
        top_p=top_p,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id
    )
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Eliminar cualquier parte redundante del prompt generado
    if "Usuario:" in response or "MIA:" in response:
        response = response.split("Usuario:")[-1].strip()
        response = response.split("MIA:")[-1].strip()

    # Postprocesamiento: Filtrar respuestas repetidas
    response_lines = response.split("\n")
    clean_response = "\n".join(sorted(set(response_lines), key=response_lines.index))

    return clean_response


