import praw
import json
import langdetect
from langdetect import DetectorFactory
from prawcore.exceptions import Redirect

# Configuración del detector de idioma
DetectorFactory.seed = 0

def detect_spanish(text):
    try:
        return langdetect.detect(text) == "es"
    except:
        return False

def fetch_reddit_examples(client_id, client_secret, user_agent, subreddits, num_posts_per_subreddit):
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )

    print("Conectado a Reddit. Extrayendo ejemplos...")

    examples = []

    for subreddit_name in subreddits:
        try:
            print(f"Extrayendo de r/{subreddit_name}...")
            subreddit = reddit.subreddit(subreddit_name)

            for post in subreddit.hot(limit=num_posts_per_subreddit * 2):
                if detect_spanish(post.title) and detect_spanish(post.selftext):
                    examples.append({
                        "subreddit": subreddit_name,
                        "title": post.title,
                        "content": post.selftext,
                        "type": "post"
                    })

                post.comments.replace_more(limit=0)
                for comment in post.comments:
                    if detect_spanish(comment.body):
                        examples.append({
                            "subreddit": subreddit_name,
                            "content": comment.body,
                            "type": "comment"
                        })
                
                if len([e for e in examples if e['subreddit'] == subreddit_name]) >= num_posts_per_subreddit:
                    break

        except Redirect:
            print(f"Error: r/{subreddit_name} no existe o no está disponible. Saltando...")

    print(f"Ejemplos extraídos: {len(examples)}")
    return examples

def save_to_json(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Datos guardados en {filename}")

if __name__ == "__main__":
    # Configuración de la API de Reddit
    CLIENT_ID = "358jojknUSWgYE-ViIvcEQ"
    CLIENT_SECRET = "8HRN3YvxYq6-1vYwam7-3dkFBtPmWw"
    USER_AGENT = "script:MIA:v1.0 (by CourseThen5919)"

    SUBREDDITS = ["AskRedditespanol", "Mexico", "ShitpostESP", "MemesESP"]
    NUM_POSTS_PER_SUBREDDIT = 200
    OUTPUT_FILE = "reddit_esp.json"

    examples = fetch_reddit_examples(CLIENT_ID, CLIENT_SECRET, USER_AGENT, SUBREDDITS, NUM_POSTS_PER_SUBREDDIT)
    save_to_json(examples, OUTPUT_FILE)