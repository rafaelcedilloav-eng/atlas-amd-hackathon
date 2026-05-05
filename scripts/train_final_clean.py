import os
os.environ["PYTORCH_HIP_ALLOC_CONF"] = "expandable_segments:True,max_split_size_mb:512"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
import json
import time
import gc
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from trl import SFTTrainer, SFTConfig
from datasets import Dataset

BASE_MODEL = "./qwen-finance-model"
ADAPTER_V1 = "/workspace/checkpoints/atlas-core-30b/final"
DATASET_PATH = r"D:\Proyectos\atlas-amd-hackathon\data\atlas_training_dataset.jsonl"
OUTPUT_DIR = "./atlas-core-30b-v2"

print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

gc.collect()
torch.cuda.empty_cache()

tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

raw_data = []
with open(DATASET_PATH, "r", encoding="utf-8") as f:
    for line in f:
        raw_data.append(json.loads(line.strip()))

def format_chatml(item):
    messages = item["messages"]
    if messages[0]["role"] != "system":
        messages.insert(0, {"role": "system", "content": "Eres ATLAS, auditor forense especializado en regulaciones financieras MX-USA."})
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
    return {"text": text}

dataset = [format_chatml(item) for item in raw_data]
hf_dataset = Dataset.from_list(dataset)
hf_dataset = hf_dataset.train_test_split(test_size=0.02, seed=42)

print(f"Train: {len(hf_dataset['train'])} | Val: {len(hf_dataset['test'])}")

model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True,
    attn_implementation="sdpa",
)

model = PeftModel.from_pretrained(model, ADAPTER_V1, is_trainable=True)

model.gradient_checkpointing_enable()
model.enable_input_require_grads()

training_args = SFTConfig(
    output_dir=OUTPUT_DIR,
    num_train_epochs=1,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=16,
    optim="adamw_torch",
    learning_rate=5e-5,
    warmup_steps=50,
    weight_decay=0.01,
    max_grad_norm=0.3,
    logging_steps=10,
    save_strategy="epoch",
    fp16=True,
    dataloader_num_workers=0,
    remove_unused_columns=False,
    report_to="none",
    max_length=1024,
    dataset_text_field="text",
    packing=False,
    eval_strategy="no",
)

trainer = SFTTrainer(
    model=model,
    processing_class=tokenizer,
    train_dataset=hf_dataset["train"],
    args=training_args,
)

print("=" * 60)
print("ENTRENAMIENTO INICIADO")
print("=" * 60)

start = time.time()
trainer.train()

trainer.save_model(f"{OUTPUT_DIR}/final")
tokenizer.save_pretrained(f"{OUTPUT_DIR}/final")

torch.cuda.empty_cache()
gc.collect()

print("LISTO!")
