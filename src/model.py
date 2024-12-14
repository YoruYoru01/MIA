from huggingface_hub import snapshot_download

# Ruta para almacenar el modelo
local_dir = "models/llama_models/Llama-3.2-3B-Instruct"
model_name = "meta-llama/Llama-3.2-3B-Instruct"

print(f"Descargando el modelo {model_name}...")
snapshot_download(repo_id=model_name, local_dir=local_dir, local_dir_use_symlinks=False)
print(f"Modelo descargado en: {local_dir}")