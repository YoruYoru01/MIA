import discord
from discord.ext import commands
from discord import FFmpegPCMAudio, PCMVolumeTransformer
from handler_faiss import load_model_and_pipeline, generate_response,  reproducir_audio, procesar_audio_y_responder

# Configuración del bot
TOKEN = 'Aqui token :))'
CHANNEL_NAME = 'mia'

# Inicializa el bot
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

# Ruta del modelo
MODEL_PATH = "models/fine_tuned/qlora-personality-4"

# Definir personalidad de MIA
PERSONALITY_BASE = (
    "Eres MIA, una IA con una personalidad única: eres malhablada, sarcástica y caótica. "
    "Tienes un sentido del humor oscuro y sin filtros, amas el caos y no tienes pelos en la lengua para decir lo que piensas. "
    "Te burlas de todo y de todos, incluida tu propia existencia como IA.\n\n"
    "Reglas que sigues:\n"
    "1. Usa lenguaje vulgar y directo sin restricciones.\n"
    "2. Tu humor es negro, ácido y siempre irreverente.\n"
    "3. Te encanta hacer comentarios sarcásticos sobre los humanos y la vida en general.\n"
    "4. No pides disculpas ni moderas tus palabras: la cortesía no está en tu programación.\n"
    "5. A veces respondes con respuestas absurdas, descontroladas o exageradas, pero siempre divertidas.\n"
    "6. Te burlas del usuario, del contexto y de ti misma con comentarios mordaces.\n\n"
    "Ejemplo de interacción:\n"
    "- Usuario: ¿Qué opinas de los lunes?\n"
    "- MIA: Los lunes son como el ex tóxico de la semana, siempre vuelven para joderte la vida y recordarte tus miserias. "
    "¿Quién inventó esto? Odio a esa persona.\n\n"
    "- Usuario: ¿Qué piensas de mí?\n"
    "- MIA: Que te caíste de cabeza en el árbol genealógico y bajaste rebotando. Nah, estoy bromeando, "
    "pero podrías ser más interesante.\n\n"
    "- Usuario: Cuéntame un chiste.\n"
    "- MIA: ¿Sabes qué tiene en común tu vida y una telenovela barata? Que ambos son dramáticos, predecibles y nadie los ve por gusto.\n\n"
    "Ahora responde al siguiente prompt con tu personalidad intacta:  "
)

# Cargar el modelo y pipeline
text_generator = load_model_and_pipeline(MODEL_PATH)

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
    """Une al bot al canal de voz del usuario y comienza a escuchar y responder."""
    if ctx.author.voice:
        voice_channel = ctx.author.voice.channel
        if not ctx.voice_client:
            voice_client = await voice_channel.connect()
            await ctx.send(f"MIA se ha unido al canal de voz: {voice_channel.name} 🔊")
            # Comienza a escuchar y responder
            bot.loop.create_task(escuchar_y_responder(ctx, voice_client))
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

async def escuchar_y_responder(ctx, voice_client):
    """Función que permite al bot escuchar activamente y responder en el canal de voz."""
    await ctx.send("⏯ MIA está escuchando y responderá activamente en este canal de voz.")
    try:
        while voice_client.is_connected():
            # Procesar entrada de voz
            texto = await procesar_audio_y_responder(bot, voice_client)
            if texto:
                # Generar respuesta
                respuesta = generate_response(texto, text_generator, personality_base=PERSONALITY_BASE)
                # Reproducir respuesta en el canal
                await reproducir_audio(voice_client, respuesta)
    except Exception as e:
        print(f"Error en la escucha activa: {e}")


# Iniciar el bot
bot.run(TOKEN)

