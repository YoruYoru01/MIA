import os
import json
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from sentence_transformers import SentenceTransformer
import soundfile as sf
import torch
from TTS.api import TTS
import pygame

# Configuración inicial
USER_DATA_FOLDER = 'data/MIA_interface'
if not os.path.exists(USER_DATA_FOLDER):
    os.makedirs(USER_DATA_FOLDER)

print("Cargando modelo de embeddings para FAISS...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
print("Modelo de embeddings cargado correctamente.")

try:
    modelo_tts = "tts_models/es/mai/tacotron2-DDC"
    coqui_tts = TTS(model_name=modelo_tts)
    print("Modelo TTS cargado correctamente.")
except Exception as e:
    coqui_tts = None
    print(f"ERROR al cargar el modelo TTS: {e}")

if not coqui_tts:
    raise RuntimeError("Modelo TTS no cargado. Verifique el modelo y la instalación de Coqui TTS.")

# Función para guardar el perfil del usuario
def guardar_perfil(data):
    file_path = "data/MIA_interface/profile.json"
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        print(f"Perfil guardado en {file_path}.")
    except Exception as e:
        print(f"ERROR al guardar el perfil: {e}")

# Función para cargar el perfil del usuario
def cargar_perfil():
    file_path = "data/MIA_interface/profile.json"
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except json.JSONDecodeError:
            print("ERROR: Archivo JSON corrupto. Se creará un perfil predeterminado.")
            os.remove(file_path)
        except Exception as e:
            print(f"ERROR al cargar el perfil: {e}")
    perfil_default = {
        "nombre": "Desconocido",
        "personalidad": "Curioso y observador",
        "preferencias": ["sin preferencias registradas"],
        "relacion": "nuevo usuario"
    }
    guardar_perfil(perfil_default)
    return perfil_default

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
    return pipeline("text-generation", model=model, tokenizer=tokenizer)

# Función para generar respuesta
def generate_response(prompt, pipeline, personality_base=None, history=None, max_new_tokens=150, temperature=0.6, top_p=0.85):
    """
    Genera una respuesta basada en un prompt, historial de conversación y base de personalidad.
    """
    context = ""
    if history:
        try:
            recent_history = [
                h for h in history[-5:] if all(key in h for key in ["input", "response"])
            ]
            context = "\n".join([f"Usuario: {h['input']}\nMIA: {h['response']}" for h in recent_history])
        except Exception as e:
            print(f"ERROR al procesar el historial: {e}")

    # Construir el prompt completo
    full_prompt = f"{personality_base}\n\n{context}\nUsuario: {prompt}\nMIA:" if personality_base else f"{context}\nUsuario: {prompt}\nMIA:"

    print(f"DEBUG: Prompt completo para la generación:\n{full_prompt[:1000]}")

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
        return "Lo siento, no pude generar una respuesta en este momento.", context

    unwanted_phrases = ["Usuario:", "MIA:", "Respuesta:", "Contexto:"]
    response = ''.join(c for c in response if c.isprintable()).strip()

    for phrase in unwanted_phrases:
        response = response.replace(phrase, "").strip()

    response_lines = response.split("\n")
    clean_response = "\n".join(sorted(set(response_lines), key=response_lines.index))

    print(f"DEBUG: Respuesta final generada:\n{clean_response}")
    return clean_response, context

def generar_audio_coqui(texto, output_path="output.wav"):
    try:
        texto = texto.strip()
        if len(texto) > 300:  # Limitar longitud del texto
            texto = texto[:300]
        if not texto:
            raise ValueError("El texto está vacío o no es válido para TTS.")
        if coqui_tts:
            coqui_tts.tts_to_file(text=texto, file_path=output_path)
            print(f"Audio generado y guardado en {output_path}")
        else:
            raise RuntimeError("Modelo TTS no está cargado. Verifique la inicialización.")
    except Exception as e:
        print(f"Error al generar audio con Coqui TTS: {e}")

def reproducir_audio(output_path):
    try:
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"No se encontró el archivo de audio: {output_path}")
        
        pygame.mixer.init()
        pygame.mixer.music.load(output_path)
        pygame.mixer.music.play()
        print(f"Reproduciendo audio: {output_path}")

        # Esperar hasta que termine la reproducción
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.quit()
        print("Reproducción finalizada.")
    except Exception as e:
        print(f"Error al reproducir el archivo de audio: {e}")