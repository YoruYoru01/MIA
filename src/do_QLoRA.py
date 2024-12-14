from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import get_peft_model, LoraConfig, TaskType
from transformers import TrainingArguments, Trainer, DataCollatorForLanguageModeling
from datasets import load_dataset, DatasetDict, Dataset

# Cargar el dataset JSON
dataset = load_dataset("json", data_files="data/raw/Personalidad_estilo/personality_dataset.json")

# Dividir en conjuntos de entrenamiento y evaluación (90% train, 10% eval)
train_test_split = dataset["train"].train_test_split(test_size=0.1)
train_dataset = train_test_split["train"]
eval_dataset = train_test_split["test"]

# Ruta del modelo base
model_name = "models/llama_models/Llama-3.2-3B-Instruct"

# Cargar modelo y tokenizador
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
tokenizer.pad_token = tokenizer.eos_token  
model = AutoModelForCausalLM.from_pretrained(
    model_name, load_in_8bit=True, device_map="auto"
)

# Configuración de LoRA
lora_config = LoraConfig(
    r=16,  # Dimensiones del "rank"
    lora_alpha=32,  # Escala de LoRA
    target_modules=["q_proj", "v_proj"],  # Capas objetivo
    lora_dropout=0.1,  # Dropout
    bias="none",  # Sin bias adicional
    task_type=TaskType.CAUSAL_LM,  # Tarea específica
)

# Convertir el modelo base en un modelo LoRA
model = get_peft_model(model, lora_config)

# Configuración del entrenamiento
training_args = TrainingArguments(
    output_dir="./qlora-personality",  # Carpeta para guardar los resultados
    per_device_train_batch_size=4,
    gradient_accumulation_steps=8,
    learning_rate=2e-4,
    num_train_epochs=3,
    logging_dir="./logs",
    save_strategy="epoch",
    save_total_limit=2,
    evaluation_strategy="epoch",  # Activar evaluación al final de cada época
    eval_steps=None,  # Evalúa al final de cada época, no durante
    bf16=True,  # Utilizar FP16 o BF16 según tu GPU
    report_to="none",
)

# Función para tokenizar
def tokenize_function(examples):
    inputs = examples["instruction"]
    outputs = examples["output"]
    # Combina input y output en un solo texto
    combined = [f"Instrucción: {inp}\nRespuesta: {out}" for inp, out in zip(inputs, outputs)]
    return tokenizer(combined, truncation=True, padding="max_length", max_length=512)

# Tokenización del dataset
tokenized_train = train_dataset.map(tokenize_function, batched=True, remove_columns=["instruction", "output"])
tokenized_eval = eval_dataset.map(tokenize_function, batched=True, remove_columns=["instruction", "output"])
data_collator = DataCollatorForLanguageModeling(tokenizer, mlm=False)

# Inicializar el Trainer con dataset de evaluación
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_train,
    eval_dataset=tokenized_eval, 
    tokenizer=tokenizer,
    data_collator=data_collator,
)

trainer.train()

# Guardar el modelo ajustado y el tokenizador
model.save_pretrained("models/fine_tuned/qlora-personality")
tokenizer.save_pretrained("models/fine_tuned/qlora-personality")