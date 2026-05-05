import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset

# RUTA LOCAL DEL MODELO
MODEL_PATH = "./qwen-finance-model"
DATASET_PATH = "data/atlas_training_dataset.jsonl"
OUTPUT_DIR = "./atlas-qwen35b-finetuned"

# Configuración 4-bit optimizada para MI300X (CDNA3)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16
)

# Cargar Modelo y Tokenizer desde la ruta local
print(f"Loading Qwen 35B from {MODEL_PATH}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    quantization_config=bnb_config,
    device_map="auto",
    torch_dtype=torch.bfloat16,
    trust_remote_code=True
)

model = prepare_model_for_kbit_training(model)

# Configuración LoRA ajustada para 35B
lora_config = LoraConfig(
    r=32,
    lora_alpha=64,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Preparación de Datos
def tokenize_function(examples):
    texts = [tokenizer.apply_chat_template(msg, tokenize=False) for msg in examples["messages"]]
    return tokenizer(texts, truncation=True, max_length=2048, padding="max_length")

dataset = load_dataset("json", data_files=DATASET_PATH, split="train")
tokenized_dataset = dataset.map(tokenize_function, batched=True, remove_columns=dataset.column_names)

# Entrenamiento optimizado para 35B en cluster
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=3,
    per_device_train_batch_size=1,     # 35B es masivo, batch 1 + grad_accum es necesario
    gradient_accumulation_steps=16,    # Para simular batch size 16
    learning_rate=1e-4,
    weight_decay=0.01,
    save_steps=200,
    logging_steps=10,
    fp16=False,
    bf16=True,                         # MI300X standard
    evaluation_strategy="no",
    save_strategy="steps",
    report_to="none",
    optim="adamw_torch_fused",
    ddp_find_unused_parameters=False
)

data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    data_collator=data_collator,
    tokenizer=tokenizer
)

trainer.train()
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
