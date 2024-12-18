import faiss
import pickle
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch
from sentence_transformers import SentenceTransformer
import tempfile
import os
import subprocess
import whisper
import asyncio

from discord import FFmpegPCMAudio


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

# Generar respuesta combinando FAISS y modelo de lenguaje
def generate_response(prompt, pipeline, personality_base=None, max_new_tokens=200, temperature=0.3, top_p=0.7, top_k=3):
    # Recuperar fragmentos relevantes usando FAISS
    print("\nDEBUG: Procesando consulta en FAISS...")
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
        combined_context = "\n\n".join(retrieved_docs)
        prompt_with_context = f"Context:\n{combined_context}\n\nQuestion: {prompt}\nAnswer:"
        print(f"\nDEBUG: Contexto combinado:\n{combined_context[:300]}...\n")  # Mostrar solo los primeros 300 caracteres
    else:
        print("\nDEBUG: No se encontraron fragmentos relevantes en FAISS.")
        prompt_with_context = prompt

    # Generar respuesta usando el modelo
    if personality_base:
        full_prompt = f"{personality_base}\n{prompt_with_context}\n<|startofresponse|>"
    else:
        full_prompt = f"{prompt_with_context}\n<|startofresponse|>"

    print(f"\nDEBUG: Prompt completo enviado al modelo:\n{full_prompt[:300]}...\n")  # Mostrar los primeros 300 caracteres

    try:
        generated_text = pipeline(
            full_prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            repetition_penalty=1.2,  # Penalizar repeticiones
            do_sample=True,
            pad_token_id=pipeline.tokenizer.pad_token_id
        )
    except Exception as e:
        print(f"ERROR al generar texto: {e}")
        return "Lo siento, no pude generar una respuesta en este momento."

    response = generated_text[0]["generated_text"].replace(full_prompt, "").strip()

    # Eliminar fragmentos redundantes
    unwanted_phrases = ["Usuario:", "MIA:", "Respuesta:", "Contexto:", "Context:"]
    for phrase in unwanted_phrases:
        response = response.split(phrase)[-1].strip()

    response_lines = response.split("\n")
    clean_response = "\n".join(sorted(set(response_lines), key=response_lines.index))

    print("\nDEBUG: Respuesta generada por el modelo:\n", clean_response)
    return clean_response


def transcribir_audio(audio_path):
    """Transcribe el audio usando Whisper."""
    print(f"Transcribiendo audio desde: {audio_path}")
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, language="es")
    texto_transcrito = result['text']
    print(f"Texto transcrito: {texto_transcrito}")
    return texto_transcrito

async def procesar_audio_y_responder(voice_client, text_generator, personality_base):
    """Captura audio del canal de voz, lo transcribe y genera una respuesta."""
    try:
        while voice_client.is_connected():
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                temp_audio_path = temp_audio.name

            # Capturar el audio con ffmpeg
            process = subprocess.Popen(
                [
                    "ffmpeg", "-y", "-f", "s16le", "-ar", "48000", "-ac", "2", "-i",
                    "pipe:0", temp_audio_path
                ],
                stdin=subprocess.PIPE
            )

            await asyncio.sleep(5)  # Captura un segmento de 5 segundos
            process.stdin.close()
            process.wait()

            # Procesar el audio con Whisper
            if os.path.exists(temp_audio_path):
                texto = transcribir_audio(temp_audio_path)
                os.remove(temp_audio_path)

                if texto:
                    print(f"Texto capturado: {texto}")
                    # Generar respuesta
                    respuesta = generate_response(texto, text_generator, personality_base=personality_base)
                    print(f"Respuesta generada: {respuesta}")
                    # Reproducir respuesta en el canal
                    await reproducir_audio(voice_client, respuesta)
    except Exception as e:
        print(f"Error procesando audio y generando respuesta: {e}")

async def reproducir_audio(voice_client, texto):
    """Convierte texto en audio y lo reproduce en el canal de voz."""
    from gtts import gTTS
    print(f"Convirtiendo texto a audio: {texto}")
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio:
        tts = gTTS(text=texto, lang="es")
        tts.save(temp_audio.name)
        temp_audio_path = temp_audio.name

    audio_source = FFmpegPCMAudio(temp_audio_path)
    voice_client.play(audio_source, after=lambda e: os.remove(temp_audio_path))

    while voice_client.is_playing():
        await asyncio.sleep(1)