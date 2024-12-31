<<<<<<< HEAD
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio, PCMVolumeTransformer
from handler_3 import load_model_and_pipeline, generate_response
import asyncio
import whisper
import tempfile
import os

# Configuración del bot
TOKEN = 'aqui iría el token del bot el cual no subo a github por alguna razón'
CHANNEL_NAME = 'mia'

# Inicializa el bot
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

# Ruta del modelo
MODEL_PATH = "models/fine_tuned/qlora-personality-4"

# Definir personalidad de MIA
PERSONALITY_BASE = (
    "Hoy serás una persona totalmente negativa, como si la vida no valiera nada. tus respuestas reflejarán tu negatividad  "
)

# Cargar el modelo y pipeline
text_generator = load_model_and_pipeline(MODEL_PATH)

# Cargar el modelo de Whisper
whisper_model = whisper.load_model("base")

# Historial en memoria por usuario
user_histories = {}

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')

@bot.event
async def on_message(message):
    global user_histories
    if message.author == bot.user:
        return  # Ignorar mensajes del propio bot

    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    if message.channel.name == CHANNEL_NAME:
        user_id = message.author.id
        prompt = message.content

        # Obtener historial del usuario o crear uno nuevo
        user_history = user_histories.get(user_id, [])

        # Generar respuesta usando el pipeline
        response = generate_response(
            prompt, text_generator,
            personality_base=PERSONALITY_BASE
        )

        # Filtrar caracteres especiales o emojis problemáticos
        response = ''.join(c for c in response if c.isprintable())

        # Limpiar caracteres no estándar
        response = response.encode('utf-8', 'ignore').decode('utf-8')

        # Actualizar historial del usuario
        user_history.append({"user": message.author.name, "input": prompt, "response": response})
        user_histories[user_id] = user_history[-50:]  # Limitar a las últimas 50 interacciones por usuario

        # Enviar respuesta al canal
        await message.channel.send(response)

@bot.command()
async def borrar_historial(ctx, usuario: discord.Member = None):
    """
    Borra el historial en memoria.
    Si se especifica un usuario, borra solo su historial.
    """
    global user_histories
    if usuario:
        user_id = usuario.id
        if user_id in user_histories:
            del user_histories[user_id]
            await ctx.send(f"Historial del usuario {usuario.name} borrado. 🧹")
        else:
            await ctx.send(f"El usuario {usuario.name} no tiene historial registrado. ❌")
    else:
        user_histories.clear()
        await ctx.send("Todos los historiales en memoria han sido borrados. 🧹")

@bot.command()
async def unir(ctx):
    """Une al bot al canal de voz del usuario y comienza a escuchar."""
    if ctx.author.voice:
        voice_channel = ctx.author.voice.channel
        if not ctx.voice_client:
            voice_client = await voice_channel.connect()
            await ctx.send(f"MIA se ha unido al canal de voz: {voice_channel.name} 🔊")

            # Inicia la escucha activa
            bot.loop.create_task(escuchar_audio(voice_client))
        else:
            await ctx.voice_client.move_to(voice_channel)
            await ctx.send(f"MIA se ha movido al canal de voz: {voice_channel.name} 🔊")
    else:
        await ctx.send("❌ Debes estar en un canal de voz para usar este comando.")

@bot.command()
async def salir(ctx):
    """Hace que el bot salga del canal de voz."""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("MIA ha salido del canal de voz. 🔊")
    else:
        await ctx.send("❌ MIA no está en un canal de voz.")

async def escuchar_audio(voice_client):
    """Escucha audio desde el canal de voz y procesa las respuestas."""
    print("Iniciando la escucha del canal de voz.")

    try:
        while voice_client.is_connected():
            # Captura audio en formato PCM
            with tempfile.NamedTemporaryFile(suffix=".pcm", delete=False) as temp_audio:
                audio_path = temp_audio.name

            process = await asyncio.create_subprocess_exec(
                "ffmpeg", "-y", "-f", "s16le", "-ar", "48000", "-ac", "2", "-i", "pipe:0", audio_path,
                stdin=asyncio.subprocess.PIPE
            )

            # Simula captura de audio por 5 segundos
            await asyncio.sleep(5)
            process.stdin.close()
            await process.wait()

            if os.path.exists(audio_path):
                # Transcribir audio
                texto = transcribir_audio(audio_path)
                os.remove(audio_path)  # Limpieza del archivo temporal

                if texto:
                    print(f"Texto capturado: {texto}")
                    respuesta = generate_response(texto, text_generator, personality_base=PERSONALITY_BASE)
                    print(f"Respuesta generada: {respuesta}")

                    # Responder en el canal de voz
                    await reproducir_audio(voice_client, respuesta)
    except Exception as e:
        print(f"Error al escuchar el audio: {e}")

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

def transcribir_audio(audio_path):
    """Transcribe el audio usando Whisper."""
    print(f"Transcribiendo audio desde: {audio_path}")
    result = whisper_model.transcribe(audio_path, language="es")
    texto_transcrito = result['text']
    print(f"Texto transcrito: {texto_transcrito}")
    return texto_transcrito


# Iniciar el bot
=======
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio, PCMVolumeTransformer
from handler_3 import load_model_and_pipeline, generate_response
import asyncio
import whisper
import tempfile
import os
import json

# Cargar claves desde secrets.json
with open('secrets.json', 'r') as secrets_file:
    secrets = json.load(secrets_file)

# Configuración del bot desde secrets.json
TOKEN = secrets['discord']['bot_token']
CHANNEL_NAME = 'mia'


# Inicializa el bot
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

# Ruta del modelo
MODEL_PATH = "models/fine_tuned/qlora-personality-4"

# Definir personalidad de MIA
PERSONALITY_BASE = (
    "Hoy serás una persona totalmente negativa, como si la vida no valiera nada. tus respuestas reflejarán tu negatividad  "
)

# Cargar el modelo y pipeline
text_generator = load_model_and_pipeline(MODEL_PATH)

# Cargar el modelo de Whisper
whisper_model = whisper.load_model("base")

# Historial en memoria por usuario
user_histories = {}

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')

@bot.event
async def on_message(message):
    global user_histories
    if message.author == bot.user:
        return  # Ignorar mensajes del propio bot

    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    if message.channel.name == CHANNEL_NAME:
        user_id = message.author.id
        prompt = message.content

        # Obtener historial del usuario o crear uno nuevo
        user_history = user_histories.get(user_id, [])

        # Generar respuesta usando el pipeline
        response = generate_response(
            prompt, text_generator,
            personality_base=PERSONALITY_BASE
        )

        # Filtrar caracteres especiales o emojis problemáticos
        response = ''.join(c for c in response if c.isprintable())

        # Limpiar caracteres no estándar
        response = response.encode('utf-8', 'ignore').decode('utf-8')

        # Actualizar historial del usuario
        user_history.append({"user": message.author.name, "input": prompt, "response": response})
        user_histories[user_id] = user_history[-50:]  # Limitar a las últimas 50 interacciones por usuario

        # Enviar respuesta al canal
        await message.channel.send(response)

@bot.command()
async def borrar_historial(ctx, usuario: discord.Member = None):
    """
    Borra el historial en memoria.
    Si se especifica un usuario, borra solo su historial.
    """
    global user_histories
    if usuario:
        user_id = usuario.id
        if user_id in user_histories:
            del user_histories[user_id]
            await ctx.send(f"Historial del usuario {usuario.name} borrado. 🧹")
        else:
            await ctx.send(f"El usuario {usuario.name} no tiene historial registrado. ❌")
    else:
        user_histories.clear()
        await ctx.send("Todos los historiales en memoria han sido borrados. 🧹")

@bot.command()
async def unir(ctx):
    """Une al bot al canal de voz del usuario y comienza a escuchar."""
    if ctx.author.voice:
        voice_channel = ctx.author.voice.channel
        if not ctx.voice_client:
            voice_client = await voice_channel.connect()
            await ctx.send(f"MIA se ha unido al canal de voz: {voice_channel.name} 🔊")

            # Inicia la escucha activa
            bot.loop.create_task(escuchar_audio(voice_client))
        else:
            await ctx.voice_client.move_to(voice_channel)
            await ctx.send(f"MIA se ha movido al canal de voz: {voice_channel.name} 🔊")
    else:
        await ctx.send("❌ Debes estar en un canal de voz para usar este comando.")

@bot.command()
async def salir(ctx):
    """Hace que el bot salga del canal de voz."""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("MIA ha salido del canal de voz. 🔊")
    else:
        await ctx.send("❌ MIA no está en un canal de voz.")

async def escuchar_audio(voice_client):
    """Escucha audio desde el canal de voz y procesa las respuestas."""
    print("Iniciando la escucha del canal de voz.")

    try:
        while voice_client.is_connected():
            # Captura audio en formato PCM
            with tempfile.NamedTemporaryFile(suffix=".pcm", delete=False) as temp_audio:
                audio_path = temp_audio.name

            process = await asyncio.create_subprocess_exec(
                "ffmpeg", "-y", "-f", "s16le", "-ar", "48000", "-ac", "2", "-i", "pipe:0", audio_path,
                stdin=asyncio.subprocess.PIPE
            )

            # Simula captura de audio por 5 segundos
            await asyncio.sleep(5)
            process.stdin.close()
            await process.wait()

            if os.path.exists(audio_path):
                # Transcribir audio
                texto = transcribir_audio(audio_path)
                os.remove(audio_path)  # Limpieza del archivo temporal

                if texto:
                    print(f"Texto capturado: {texto}")
                    respuesta = generate_response(texto, text_generator, personality_base=PERSONALITY_BASE)
                    print(f"Respuesta generada: {respuesta}")

                    # Responder en el canal de voz
                    await reproducir_audio(voice_client, respuesta)
    except Exception as e:
        print(f"Error al escuchar el audio: {e}")

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

def transcribir_audio(audio_path):
    """Transcribe el audio usando Whisper."""
    print(f"Transcribiendo audio desde: {audio_path}")
    result = whisper_model.transcribe(audio_path, language="es")
    texto_transcrito = result['text']
    print(f"Texto transcrito: {texto_transcrito}")
    return texto_transcrito


# Iniciar el bot
>>>>>>> de505a8 (Version alpha v0.7 - Cambiada a librería Hikari, puesta en prueba modelo NER - Primer Mockup MIA app)
bot.run(TOKEN)