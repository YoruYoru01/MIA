from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch
import tempfile
import os
import subprocess
import whisper
from discord import FFmpegPCMAudio
from discord.opus import Encoder
import asyncio
import json

# Diccionario global para mantener los historiales de conversación por usuario
user_histories = {}

# Ruta para guardar información de usuarios
USER_DATA_FOLDER = 'data/MIA_facts'
if not os.path.exists(USER_DATA_FOLDER):
    os.makedirs(USER_DATA_FOLDER)

print("Cargando modelo NER preentrenado...")
ner_pipeline = pipeline("ner", model="PlanTL-GOB-ES/roberta-large-bne", device=0 if torch.cuda.is_available() else -1)
print("Modelo NER cargado correctamente.")

def guardar_perfil_usuario(user_id, data):
    """Guarda o actualiza el perfil del usuario."""
    file_path = os.path.join(USER_DATA_FOLDER, f"profile-{user_id}.json")
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                perfil = json.load(file)
        else:
            perfil = {}

        # Actualizar perfil
        for key, value in data.items():
            perfil[key] = value

        # Guardar en archivo
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(perfil, file, ensure_ascii=False, indent=4)
        print(f"Perfil actualizado para el usuario {user_id} en {file_path}.")
    except Exception as e:
        print(f"ERROR al guardar el perfil del usuario {user_id}: {e}")

def cargar_perfil_usuario(user_id):
    """Carga el perfil del usuario desde el archivo JSON en la carpeta correcta."""
    file_path = os.path.join(USER_DATA_FOLDER, f"profile-{user_id}.json")
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
        # Crear perfil predeterminado si no existe
        perfil_default = {
            "nombre": "Desconocido",
            "personalidad": "Curioso y observador",
            "preferencias": ["sin preferencias registradas"],
            "relacion": "nuevo usuario"
        }
        guardar_perfil_usuario(user_id, perfil_default)
        return perfil_default

def analizar_mensaje(user_id, mensaje):
    """Analiza un mensaje para extraer información relevante."""
    print(f"Analizando mensaje del usuario {user_id}: {mensaje}")
    entidades = ner_pipeline(mensaje)

    # Procesar entidades extraídas
    perfil_actualizado = {}
    for entidad in entidades:
        texto = entidad['word']
        etiqueta = entidad['entity']

        if etiqueta == 'B-PER':  # Nombre propio (persona)
            perfil_actualizado['nombre'] = texto
        elif etiqueta == 'B-ORG':  # Organización (posible contexto)
            perfil_actualizado['organizacion'] = texto
        elif etiqueta == 'B-LOC':  # Ubicación
            perfil_actualizado['ubicacion'] = texto
        elif etiqueta == 'B-MISC':  # Otros (gustos, términos especiales)
            perfil_actualizado.setdefault('preferencias', []).append(texto)

    # Guardar datos procesados
    if perfil_actualizado:
        guardar_perfil_usuario(user_id, perfil_actualizado)

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

def generate_response(prompt, pipeline, personality_base=None, history=None, max_new_tokens=150, temperature=0.6, top_p=0.85):
    """
    Genera una respuesta basada en un prompt y el historial de conversación.
    """
    # Construir el contexto del historial
    context = ""
    if history:
        # Limitar el historial a los últimos 5 mensajes para mantener eficiencia
        recent_history = history[-5:]
        context = "\n".join([f"Usuario: {h['input']}\nMIA: {h['response']}" for h in recent_history])

    # Construir el prompt completo
    if personality_base:
        full_prompt = (
            f"{personality_base}\n\n{context}\nUsuario: {prompt}\nMIA:"
        )
    else:
        full_prompt = (
            f"{context}\nUsuario: {prompt}\nMIA:"
        )

    print(f"DEBUG: Prompt completo para la generación:\n{full_prompt}")

    try:
        # Generar texto utilizando el pipeline
        generated_text = pipeline(
            full_prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            repetition_penalty=1.2,
            pad_token_id=pipeline.tokenizer.pad_token_id,
            do_sample=True
        )
        response = generated_text[0]["generated_text"].replace(full_prompt, "").strip()
    except Exception as e:
        print(f"ERROR al generar texto: {e}")
        return "Lo siento, no pude generar una respuesta en este momento."

    unwanted_phrases = ["Usuario:", "MIA:", "Respuesta:", "Contexto:"]
    for phrase in unwanted_phrases:
        response = response.replace(phrase, "").strip()

    response_lines = response.split("\n")
    clean_response = "\n".join(sorted(set(response_lines), key=response_lines.index))

    print(f"DEBUG: Respuesta final generada:\n{clean_response}")
    return clean_response



def transcribir_audio(audio_path):
    """Transcribe el audio usando Whisper."""
    print(f"Transcribiendo audio desde: {audio_path}")
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, language="es")
    texto_transcrito = result['text']
    print(f"Texto transcrito: {texto_transcrito}")
    return texto_transcrito

async def procesar_audio_y_responder(voice_client, text_generator, personality_base, user_id):
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
                    respuesta = generate_response(texto, text_generator, user_id, personality_base=personality_base)
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