import faiss
import pickle
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch
from sentence_transformers import SentenceTransformer
import tempfile
import os
from gtts import gTTS



# Configurar FAISS
print("Cargando índice FAISS y datos procesados...")
index = faiss.read_index("data/processed/Faiss/vtuber_index.faiss")
with open("data/processed/Faiss/vtuber_data.pkl", "rb") as f:
    df = pickle.load(f)
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
print("Índice y datos cargados correctamente.")

# Función para cargar el modelo y pipeline
def load_model_and_pipeline(model_path):
    print(f"Cargando el modelo desde {model_path}...")
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4"
    )

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        quantization_config=quantization_config,
        device_map="auto"
    )

    print("Modelo y tokenizador cargados correctamente.")
    text_generator = pipeline("text-generation", model=model, tokenizer=tokenizer)
    print("Pipeline de generación de texto creado.")
    return text_generator

# Función para buscar fragmentos relevantes en FAISS
def query_vtubers(question, top_k=3):
    print("\nProcesando consulta en FAISS...")
    question_embedding = embedding_model.encode([question]).astype('float32')
    distances, indices = index.search(question_embedding, top_k)

    retrieved_docs = []
    for idx in indices[0]:
        if idx != -1:
            fragment = df.iloc[idx]['fragment']
            retrieved_docs.append(fragment)
    return retrieved_docs

def generate_response(prompt, pipeline, personality_base=None, max_new_tokens=150, temperature=0.6, top_p=0.85, top_k=3):
    """
    Genera una respuesta combinando el contexto recuperado con FAISS y la generación del modelo.
    """
    print("\nDEBUG: Generando respuesta para el prompt...")
    retrieved_docs = []
    try:
        question_embedding = embedding_model.encode([prompt]).astype('float32')
        distances, indices = index.search(question_embedding, top_k)

        for idx, dist in zip(indices[0], distances[0]):
            if idx != -1:
                fragment = df.iloc[idx]['fragment']
                print(f"DEBUG: Fragmento recuperado (índice: {idx}, distancia: {dist}): {fragment[:100]}...")
                retrieved_docs.append(fragment)
    except Exception as e:
        print(f"ERROR en FAISS: {e}")

    # Crear contexto combinado
    if retrieved_docs:
        combined_context = "\n".join(retrieved_docs[:top_k])
        prompt_with_context = f"Contexto:\n{combined_context}\n\nUsuario: {prompt}\nMIA:"
        print(f"DEBUG: Contexto agregado:\n{combined_context[:300]}...")
    else:
        prompt_with_context = f"Usuario: {prompt}\nMIA:"
        print("DEBUG: Sin contexto relevante recuperado de FAISS.")

    # Construir el prompt completo
    if personality_base:
        full_prompt = f"{personality_base}\n\n{prompt_with_context}"
    else:
        full_prompt = prompt_with_context

    print(f"DEBUG: Prompt completo:\n{full_prompt[:300]}...")

    # Generar respuesta usando el modelo
    try:
        generated_text = pipeline(
            full_prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            repetition_penalty=1.2,  # Evitar repeticiones
            pad_token_id=pipeline.tokenizer.pad_token_id,
            do_sample=True
        )
        response = generated_text[0]["generated_text"].replace(full_prompt, "").strip()
    except Exception as e:
        print(f"ERROR al generar texto: {e}")
        return "Lo siento, no pude generar una respuesta en este momento."

    # Filtrar contenido redundante o no estándar
    unwanted_phrases = ["Usuario:", "MIA:", "Respuesta:", "Contexto:"]
    for phrase in unwanted_phrases:
        response = response.split(phrase)[-1].strip()

    response_lines = response.split("\n")
    clean_response = "\n".join(sorted(set(response_lines), key=response_lines.index))

    print(f"DEBUG: Respuesta final generada:\n{clean_response}")
    return clean_response

def reproducir_audio(texto):
    """Convierte texto a audio y lo reproduce en el sistema."""
    
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio:
            tts = gTTS(text=texto, lang="es")
            tts.save(temp_audio.name)
            temp_audio_path = temp_audio.name
        os.system(f"start {temp_audio_path}")
    except Exception as e:
        print(f"Error al reproducir audio: {e}")
