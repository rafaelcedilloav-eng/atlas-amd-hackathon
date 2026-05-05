import os
import sys

# Añadir raíz al path para importar src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.kimi_hunter import KimiHunter

def create_training_script():
    hunter = KimiHunter()
    
    prompt = """
    Genera el código completo de entrenamiento para Qwen 35B.
    REGLAS DE ORO:
    - SIN números de línea.
    - SIN bloques Markdown (nada de ```python).
    - SIN comentarios ni explicaciones.
    - SOLO el código fuente puro, indentado correctamente.
    
    Código a incluir:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments, Trainer, DataCollatorForLanguageModeling
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from datasets import load_dataset
    
    MODEL_PATH = "./qwen-finance-model"
    DATASET_PATH = "data/atlas_training_dataset.jsonl"
    OUTPUT_DIR = "./atlas-qwen35b-finetuned"
    
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16
    )
    
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
    
    lora_config = LoraConfig(
        r=32,
        lora_alpha=64,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0,
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    model = get_peft_model(model, lora_config)
    
    def tokenize_function(examples):
        texts = [tokenizer.apply_chat_template(msg, tokenize=False) for msg in examples["messages"]]
        return tokenizer(texts, truncation=True, max_length=2048, padding="max_length")
    
    dataset = load_dataset("json", data_files=DATASET_PATH, split="train")
    tokenized_dataset = dataset.map(tokenize_function, batched=True, remove_columns=dataset.column_names)
    
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=3,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=16,
        learning_rate=1e-4,
        weight_decay=0.01,
        save_steps=200,
        logging_steps=10,
        fp16=False,
        bf16=True,
        evaluation_strategy="no",
        save_strategy="steps",
        report_to="none",
        optim="adamw_torch_fused",
        ddp_find_unused_parameters=False
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
        tokenizer=tokenizer
    )
    
    trainer.train()
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    """
    
    system_prompt = "Eres una Coder Skill. Devuelve SOLO código fuente puro. Sin formato Markdown. Sin comentarios adicionales."
    
    try:
        response = hunter.extract_data(prompt, system_prompt=system_prompt)
        # Limpieza brutal de cualquier resto de markdown que pudiera aparecer
        code = response.replace("```python", "").replace("```", "").strip()
        with open("scripts/train_final.py", "w", encoding="utf-8") as f:
            f.write(code)
        print("✅ Archivo scripts/train_final.py creado exitosamente.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_training_script()
