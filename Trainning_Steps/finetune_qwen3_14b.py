#!/usr/bin/env python3
# ============================================================
# ATLAS R2 — Qwen3-14B FullFinetune (single GPU, no DeepSpeed)
# AMD MI300X 205GB | 8-bit Adam via bitsandbytes | ROCm
# Dataset: 6437 examples | 3 epochs
# Memory: ~84GB GPU (model 28 + grad 28 + opt 28)
# ============================================================

import os
import json
import torch
import logging
from pathlib import Path

from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from datasets import load_dataset

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

CONFIG = {
    "model_id": "Rafaelcedav/atlas-r2-qwen3-14b",  # R3: continued training desde R2
    "dataset_path": "/data/atlas_FINAL_v2.jsonl",   # 13,588 registros (todos los batches)
    "output_dir": "/outputs/r3_qwen3_14b_finetuned",

    "learning_rate": 1e-5,             # lr mas bajo para continued training (evita catastrofic forgetting)
    "batch_size_per_gpu": 2,
    "gradient_accumulation_steps": 8,   # effective batch = 16
    "num_epochs": 2,                    # 2 epochs suficientes en continued training
    "warmup_steps": 100,
    "weight_decay": 0.01,
    "max_grad_norm": 1.0,

    "gradient_checkpointing": True,
    "max_seq_length": 2048,

    "logging_steps": 10,
    "eval_steps": 200,
    "save_steps": 200,
    "save_total_limit": 2,
    "validation_split": 0.05,
}


def preprocess_function(examples, tokenizer, max_seq_length):
    input_ids_list = []

    for messages in examples["messages"]:
        full_text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
        )
        tokenized = tokenizer(
            full_text,
            max_length=max_seq_length,
            truncation=True,
            padding=False,
        )
        input_ids_list.append(tokenized["input_ids"])

    return {"input_ids": input_ids_list}


def main():
    logger.info("=" * 60)
    logger.info("  ATLAS R3 — Qwen3-14B ContinuedFinetune (single GPU)")
    logger.info("  AMD MI300X 192GB | adamw_torch | 13588 examples | 2 epochs")
    logger.info("=" * 60)

    if torch.cuda.is_available():
        logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
        logger.info(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

    Path(CONFIG["output_dir"]).mkdir(parents=True, exist_ok=True)

    # ----------------------------------------------------------
    # 1. Tokenizer — load first, tokenize before model (saves RAM)
    # ----------------------------------------------------------
    logger.info(f"Loading tokenizer: {CONFIG['model_id']}")
    tokenizer = AutoTokenizer.from_pretrained(CONFIG["model_id"])
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # ----------------------------------------------------------
    # 2. Dataset — tokenize BEFORE loading model weights
    # ----------------------------------------------------------
    logger.info(f"Loading dataset: {CONFIG['dataset_path']}")
    raw = load_dataset("json", data_files=CONFIG["dataset_path"], split="train")
    logger.info(f"Total: {len(raw)} | splitting 95/5 train/eval")

    split = raw.train_test_split(test_size=CONFIG["validation_split"], seed=42)
    train_ds = split["train"]
    eval_ds = split["test"]

    logger.info("Tokenizing train set...")
    train_ds = train_ds.map(
        lambda x: preprocess_function(x, tokenizer, CONFIG["max_seq_length"]),
        batched=True,
        remove_columns=train_ds.column_names,
        num_proc=1,
        desc="Tokenizing train",
    )
    logger.info("Tokenizing eval set...")
    eval_ds = eval_ds.map(
        lambda x: preprocess_function(x, tokenizer, CONFIG["max_seq_length"]),
        batched=True,
        remove_columns=eval_ds.column_names,
        num_proc=1,
        desc="Tokenizing eval",
    )
    logger.info(f"Train: {len(train_ds)} | Eval: {len(eval_ds)}")

    # ----------------------------------------------------------
    # 3. Model — load after tokenization
    # ----------------------------------------------------------
    logger.info(f"Loading model: {CONFIG['model_id']}")
    model = AutoModelForCausalLM.from_pretrained(
        CONFIG["model_id"],
        dtype=torch.bfloat16,
        attn_implementation="eager",   # sdpa has NaN bug on ROCm + bf16
    )
    model.enable_input_require_grads()
    model.gradient_checkpointing_enable()

    vram_used = torch.cuda.memory_allocated() / 1e9
    logger.info(f"Parameters: {model.num_parameters():,} | VRAM after load: {vram_used:.1f} GB")

    # ----------------------------------------------------------
    # 4. Training arguments — paged_adamw_8bit avoids ~84GB GPU
    # ----------------------------------------------------------
    training_args = TrainingArguments(
        output_dir=CONFIG["output_dir"],
        num_train_epochs=CONFIG["num_epochs"],
        per_device_train_batch_size=CONFIG["batch_size_per_gpu"],
        per_device_eval_batch_size=CONFIG["batch_size_per_gpu"],
        gradient_accumulation_steps=CONFIG["gradient_accumulation_steps"],
        learning_rate=CONFIG["learning_rate"],
        weight_decay=CONFIG["weight_decay"],
        warmup_steps=CONFIG["warmup_steps"],
        max_grad_norm=CONFIG["max_grad_norm"],
        bf16=True,
        gradient_checkpointing=CONFIG["gradient_checkpointing"],
        optim="adamw_torch",             # standard PyTorch AdamW — ROCm compatible
        eval_strategy="steps",
        eval_steps=CONFIG["eval_steps"],
        save_strategy="steps",
        save_steps=CONFIG["save_steps"],
        save_total_limit=CONFIG["save_total_limit"],
        logging_steps=CONFIG["logging_steps"],
        report_to=["tensorboard"],
        dataloader_num_workers=2,
        dataloader_pin_memory=False,
        remove_unused_columns=False,
        seed=42,
    )

    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,          # causal LM, not masked LM
        pad_to_multiple_of=8,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        processing_class=tokenizer,
        data_collator=data_collator,
    )

    # ----------------------------------------------------------
    # 5. Train
    # ----------------------------------------------------------
    logger.info("Starting training...")
    result = trainer.train()

    logger.info(f"Training loss: {result.training_loss:.4f}")
    logger.info(f"Runtime: {result.metrics.get('train_runtime', 0)/3600:.2f} hours")

    # ----------------------------------------------------------
    # 6. Save
    # ----------------------------------------------------------
    logger.info(f"Saving model to {CONFIG['output_dir']}")
    trainer.save_model(CONFIG["output_dir"])
    tokenizer.save_pretrained(CONFIG["output_dir"])

    eval_result = trainer.evaluate()
    logger.info(f"Final eval loss: {eval_result['eval_loss']:.4f}")

    logger.info("=" * 60)
    logger.info("  ATLAS R3 DONE")
    logger.info(f"  Loss: {result.training_loss:.4f}")
    logger.info(f"  Output: {CONFIG['output_dir']}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
