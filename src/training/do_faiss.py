import pandas as pd
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle

# Cargar el CSV limpio
csv_file = "data/processed/Datasets/hololive_vtubers_cleaned.csv"
df = pd.read_csv(csv_file)

# Combinar columnas relevantes en un único texto
def create_fragment(row):
    return (
        f"Name: {row['Description']}\n"
        f"Lore: {row['Lore']}\n"
        f"Nickname: {row['Nickname']}\n"
        f"Birthday: {row['Birthday']}\n"
        f"Gender: {row['Gender']}\n"
        f"Likes: {row['Likes']}\n"
        f"Dislikes: {row['Dislikes']}\n"
        f"Achievements: {row['Achievements']}"
    )

df['fragment'] = df.apply(create_fragment, axis=1)

# Configurar el modelo de embeddings
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Generar embeddings
print("Generando embeddings...")
embeddings = embedding_model.encode(df['fragment'].tolist(), show_progress_bar=True)
embeddings = np.array(embeddings).astype('float32')

# Crear el índice FAISS
print("Creando el índice FAISS...")
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# Guardar el índice y los datos procesados
faiss.write_index(index, "vtuber_index.faiss")
with open("vtuber_data.pkl", "wb") as f:
    pickle.dump(df, f)

print("Índice y datos guardados correctamente.")