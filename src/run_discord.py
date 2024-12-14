import discord
from discord.ext import commands
from handler_1 import generate_response, load_model_and_tokenizer

# Configuración del bot
TOKEN = 'MTI5NTA2OTk0NzEwOTcwNzg4OQ.GpQgcE.yqnvFPBRCeJZaDFdik66rsTZqPyINJC7be4zxw'
CHANNEL_NAME = 'mia'

# Inicializa el bot
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

# Ruta del modelo
MODEL_PATH = "models/fine_tuned/qlora-personality"

# Definir personalidad de MIA
PERSONALITY_BASE = (
    ""
)

# Cargar modelo y tokenizador
tokenizer, model = load_model_and_tokenizer(MODEL_PATH)

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
        
        response = generate_response(
            prompt, model, tokenizer,
            personality_base=PERSONALITY_BASE
        )

        # Filtra caracteres especiales o emojis problemáticos
        response = ''.join(c for c in response if c.isprintable())

        # Limpia caracteres no estándar
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

# Iniciar el bot
bot.run(TOKEN)