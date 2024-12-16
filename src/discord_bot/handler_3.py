from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch


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
