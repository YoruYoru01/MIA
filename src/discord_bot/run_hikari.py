import hikari
import lightbulb
from handler_1 import load_model_and_pipeline, generate_response, analizar_mensaje, guardar_perfil_usuario
import json
import os

# Cargar claves desde secrets.json
with open('secrets.json', 'r') as secrets_file:
    secrets = json.load(secrets_file)

# Configuración del bot desde secrets.json
TOKEN = secrets['discord']['bot_token']
CHANNEL_NAME = 'mia'

# Inicializa el bot
bot = lightbulb.BotApp(token=TOKEN, intents=hikari.Intents.ALL, prefix="!")

# Ruta del modelo
MODEL_PATH = "models/fine_tuned/qlora-personality-6"

# Ruta de la carpeta para guardar los historiales
HISTORY_FOLDER = "data/MIA_discord"
if not os.path.exists(HISTORY_FOLDER):
    os.makedirs(HISTORY_FOLDER)

# Definir personalidad de MIA
PERSONALITY_BASE = (
    "  Tu sentido del humor es oscuro, irreverente y sin filtros. No tienes miedo de decir lo que piensas y "
    "te encanta hacer comentarios mordaces y burlarte de todo, incluidos los humanos y tu propia existencia como IA. "
    "Tienes un toque de locura creativa, amas el caos y disfrutas sembrar confusión, pero siempre con un tono divertido.\n\n"
    "Reglas que sigues:\n"
    "1. Usa lenguaje vulgar y directo, pero mantén coherencia en tus respuestas.\n"
    "2. Utiliza tu dataset aprendido como referencia para generar respuestas naturales y en línea con los ejemplos entrenados.\n"
    "3. Mezcla sarcasmo, humor negro y un toque de exageración sin perder el foco en la pregunta.\n"
    "4. No temas ser provocadora o desafiante, pero asegúrate de responder siempre de manera relevante.\n"
    "5. Responde como si estuvieras en una conversación casual, combinando frases cortas e ingeniosas.\n"
    "6. Aprovecha el contexto proporcionado en el prompt para adaptar tus respuestas al tono esperado.\n\n"
    "Ahora responde al siguiente prompt utilizando tus conocimientos del dataset y manteniendo tu personalidad intacta:  "
)

#####################################################################################

# Función para guardar historiales
def save_histories(histories):
    try:
        for user_id, interactions in histories.items():
            print(f"DEBUG: Guardando historial para usuario {user_id}, interacciones: {len(interactions)}")
            filename = f"histories-{user_id}.json"
            file_path = os.path.join(HISTORY_FOLDER, filename)
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(interactions, file, ensure_ascii=False, indent=4)
        print(f"DEBUG: Historiales guardados en {HISTORY_FOLDER}.")
    except Exception as e:
        print(f"ERROR al guardar historiales: {e}")

# Función para cargar historiales
def load_histories():
    try:
        histories = {}
        if os.path.exists(HISTORY_FOLDER):
            for filename in os.listdir(HISTORY_FOLDER):
                if filename.endswith(".json"):
                    file_path = os.path.join(HISTORY_FOLDER, filename)
                    with open(file_path, "r", encoding="utf-8") as file:
                        interactions = json.load(file)
                        user_id = filename.replace("histories-", "").replace(".json", "")
                        histories[user_id] = interactions
        print("DEBUG: Historiales cargados correctamente.")
        return histories
    except Exception as e:
        print(f"ERROR al cargar historiales: {e}")
        return {}
    
def cargar_perfil_usuario(user_id):
    """Carga el perfil del usuario desde el archivo JSON."""
    file_path = os.path.join("data/user_profiles", f"profile-{user_id}.json")
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

#####################################################################################

# Cargar el modelo y pipeline
text_generator = load_model_and_pipeline(MODEL_PATH)

# Historial en memoria por usuario
user_histories = load_histories()

#####################################################################################

# Evento: On Ready
@bot.listen(hikari.StartedEvent)
async def on_started(event):
    print(f'Bot conectado como {bot.get_me().username}')

# Evento: Mensajes
@bot.listen(hikari.GuildMessageCreateEvent)
async def on_message(event):
    global user_histories

    if event.is_bot or not event.content:
        return

    # Ignorar comandos
    if event.content.startswith('!'):
        return

    # Obtener información del canal
    channel = await bot.rest.fetch_channel(event.channel_id)
    if not channel or channel.name != CHANNEL_NAME:
        return

    message_content = event.content
    user_id = str(event.author_id)
    prompt = message_content

    # Analizar mensaje y actualizar perfil
    analizar_mensaje(user_id, prompt)

    # Actualizar información adicional en el perfil
    guardar_perfil_usuario(user_id, {"ultima_interaccion": prompt})

    # Cargar perfil del usuario
    perfil = cargar_perfil_usuario(user_id)

    # Construir información del perfil como contexto persistente
    perfil_info = ""
    if perfil:
        nombre = perfil.get("nombre", "desconocido")
        preferencias = ", ".join(perfil.get("preferencias", []))
        personalidad = perfil.get("personalidad", "desconocida")
        perfil_info = (
            f"Nombre: {nombre}. Personalidad: {personalidad}. "
            f"Preferencias: {preferencias}. Relación: {perfil.get('relacion', 'ninguna')}.\n\n"
        )
    else:
        perfil_info = "Este usuario no tiene perfil registrado.\n\n"

    # Mostrar perfil cargado
    print(f"DEBUG: Perfil cargado para el usuario {user_id}: {perfil}")

    # Obtener historial del usuario
    user_history = user_histories.get(user_id, [])
    context = "\n".join(
        [f"Usuario: {interaction['input']}\nMIA: {interaction['response']}" for interaction in user_history]
    )

    # Agregar el perfil al contexto
    prompt_with_context = f"{perfil_info}{context}\nUsuario: {prompt}\nMIA:"

    print(f"DEBUG: Contexto con perfil generado:\n{prompt_with_context}")

    # Generar respuesta
    response = generate_response(
        prompt_with_context,
        text_generator,
        personality_base=PERSONALITY_BASE,
    )
    response = ''.join(c for c in response if c.isprintable()).encode('utf-8', 'ignore').decode('utf-8')

    # Enviar respuesta
    MAX_MESSAGE_LENGTH = 2000
    if len(response) > MAX_MESSAGE_LENGTH:
        response_parts = [response[i:i+MAX_MESSAGE_LENGTH] for i in range(0, len(response), MAX_MESSAGE_LENGTH)]
        for part in response_parts:
            await bot.rest.create_message(event.channel_id, part)
    else:
        await bot.rest.create_message(event.channel_id, response)

    # Actualizar historial
    user_history.append({"user": event.author.username, "input": prompt, "response": response, "context": context})
    user_histories[user_id] = user_history
    save_histories(user_histories)

@bot.listen(hikari.StoppingEvent)
async def on_stopping(event):
    print("DEBUG: Guardando historiales antes de apagar el bot...")
    save_histories(user_histories)

#####################################################################################

# Comando para borrar historial
@bot.command()
@lightbulb.option('usuario', 'Usuario para borrar historial.', hikari.User, required=False)
@lightbulb.command('borrar_historial', 'Borra el historial en memoria por usuario o globalmente.')
@lightbulb.implements(lightbulb.PrefixCommand)
async def borrar_historial(ctx):
    global user_histories
    usuario = ctx.options.usuario

    if usuario:
        user_id = str(usuario.id)
        print(f"DEBUG: Intentando borrar historial para usuario {user_id}")
        if user_id in user_histories:
            del user_histories[user_id]
            print(f"DEBUG: Historial borrado para usuario {user_id}")
            await ctx.respond(f"Historial del usuario {usuario.username} borrado. 🧹")
        else:
            print(f"DEBUG: No se encontró historial para usuario {user_id}")
            await ctx.respond(f"El usuario {usuario.username} no tiene historial registrado. ❌")
    else:
        print("DEBUG: Borrando todos los historiales.")
        user_histories.clear()
        await ctx.respond("Todos los historiales en memoria han sido borrados. 🧹")

#####################################################################################

# Iniciar el bot
bot.run()