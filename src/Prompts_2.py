from transformers import AutoTokenizer, AutoModelForCausalLM
import faiss
import torch
import json

def load_model_and_tokenizer(model_path):
    print(f"Cargando el modelo desde {model_path}...")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    tokenizer.pad_token = tokenizer.eos_token  # Configurar el token de padding
    model = AutoModelForCausalLM.from_pretrained(
        model_path, device_map="auto", torch_dtype=torch.float16
    )
    print("Modelo y tokenizador cargados correctamente.")
    return tokenizer, model

def load_faiss_index(index_path, metadata_path):
    print(f"Cargando índice FAISS desde {index_path}...")
    index = faiss.read_index(index_path)
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    print("Índice FAISS y metadatos cargados correctamente.")
    return index, metadata

def search_context(index, metadata, query, k=3):
    print(f"Buscando contexto para la consulta: {query}")
    
    # Generar un vector ficticio para pruebas
    query_vector = torch.rand((1, 768)).numpy()  
    distances, indices = index.search(query_vector, k)
    
    # Registrar los resultados del índice
    print(f"Índices encontrados: {indices}")
    print(f"Distancias correspondientes: {distances}")
    
    results = []
    for idx in indices[0]:
        if str(idx) in metadata:
            result = metadata[str(idx)]
            results.append(result)
            print(f"Resultado agregado desde FAISS: {result['content']}")
        else:
            print(f"Índice {idx} no encontrado en los metadatos.")
    
    return results

def generate_response(prompt, model, tokenizer, index=None, metadata=None, history=None, max_new_tokens=200, temperature=0.7, top_p=0.85, personality_base=None, history_limit=6):
    """
    Genera una respuesta basada en el prompt. Implementa mejoras para evitar respuestas fuera de contexto.
    """
    if personality_base:
        base_prompt = f"{personality_base}\n\n"
    else:
        base_prompt = ""

    # Consultar índice FAISS si está disponible
    if index and metadata:
        context_results = search_context(index, metadata, prompt)
        context_text = "\n".join([f"- {result['content']}" for result in context_results])
        base_prompt += f"Contexto relevante:\n{context_text}\n\n"

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


