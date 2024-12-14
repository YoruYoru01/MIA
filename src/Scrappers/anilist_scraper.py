import requests
from googletrans import Translator

# URL base de la API de AniList
API_URL = "https://graphql.anilist.co"

# Inicializar el traductor
translator = Translator()

def translate_to_spanish(text):
    """
    Traduce texto al español utilizando Google Translate.
    """
    try:
        translation = translator.translate(text, src="en", dest="es")
        return translation.text
    except Exception as e:
        print("Error al traducir:", e)
        return text

def fetch_anime_details(title):
    """
    Busca detalles de un anime en AniList según su título.
    """
    query = """
    query ($search: String) {
        Media(search: $search, type: ANIME) {
            id
            title {
                romaji
                english
                native
            }
            description(asHtml: false)
            episodes
            genres
            averageScore
            popularity
        }
    }
    """
    variables = {"search": title}

    response = requests.post(API_URL, json={"query": query, "variables": variables})
    if response.status_code == 200:
        data = response.json()["data"]["Media"]
        # Traducir al español
        data["description"] = translate_to_spanish(data["description"])
        data["genres"] = [translate_to_spanish(genre) for genre in data["genres"]]
        return data
    else:
        print("Error al conectar con AniList API:", response.status_code)
        return None

if __name__ == "__main__":
    anime_title = "Attack on Titan"
    print(f"Buscando detalles de '{anime_title}'...")
    anime_details = fetch_anime_details(anime_title)
    if anime_details:
        print("Detalles del anime en español:")
        print(f"Título: {anime_details['title']['romaji']} ({anime_details['title']['english']})")
        print(f"Géneros: {', '.join(anime_details['genres'])}")
        print(f"Episodios: {anime_details['episodes']}")
        print(f"Puntuación: {anime_details['averageScore']}")
        print(f"Popularidad: {anime_details['popularity']}")
        print(f"Descripción: {anime_details['description']}")