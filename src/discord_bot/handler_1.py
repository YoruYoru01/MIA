import discord
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch
import tempfile
import os
import subprocess
import whisper
from discord import FFmpegPCMAudio
from discord.opus import Encoder
import asyncio

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

def generate_response(prompt, pipeline, personality_base=None, max_new_tokens=200, temperature=0.5, top_p=0.7):
    if personality_base:
        full_prompt = f"{personality_base}\nUsuario: {prompt}\n<|startofresponse|>"
    else:
        full_prompt = f"Usuario: {prompt}\n<|startofresponse|>"

    generated_text = pipeline(
        full_prompt,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_p=top_p,
        repetition_penalty=1.2,  # Penalizar repeticiones
        do_sample=True,
        pad_token_id=pipeline.tokenizer.pad_token_id
    )

    response = generated_text[0]["generated_text"].replace(full_prompt, "").strip()

    # Eliminar fragmentos redundantes
    unwanted_phrases = ["Usuario:", "MIA:", "Respuesta:", "Contexto:"]
    for phrase in unwanted_phrases:
        response = response.split(phrase)[-1].strip()

    response_lines = response.split("\n")
    clean_response = "\n".join(sorted(set(response_lines), key=response_lines.index))

    print("Respuesta completa generada por el modelo:", response)
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
