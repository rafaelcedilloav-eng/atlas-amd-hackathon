#!/usr/bin/env python3
# ============================================================
# ATLAS Finanzas — DeepSeek-R1-Distill-Llama-8B FullFinetune
# AMD MI300X 205GB | adamw_torch | ROCm 7.0
# Dataset: 6437 examples | 3 epochs
# Memory: ~111GB GPU (model 16 + grad 16 + opt 64 + act ~15)
# ============================================================

import os
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
    "model_id": "deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
    "dataset_path": "/data/atlas_training_dataset.jsonl",
    "output_dir": "/outputs/atlas_deepseek_r1_8b",

    "learning_rate": 1e-5,              # lower than 14B — R1 distilled models are sensitive
    "batch_size_per_gpu": 4,
    "gradient_accumulation_steps": 4,   # effective batch = 16
    "num_epochs": 3,
    "warmup_steps": 50,
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
    logger.info("  ATLAS Finanzas — DeepSeek-R1-Distill-Llama-8B")
    logger.info("  AMD MI300X | adamw_torch | 6437 examples | 3 epochs")
    logger.info("=" * 60)

    if torch.cuda.is_available():
        logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
        logger.info(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

    Path(CONFIG["output_dir"]).mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading tokenizer: {CONFIG['model_id']}")
    tokenizer = AutoTokenizer.from_pretrained(CONFIG["model_id"])
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    logger.info(f"Loading dataset: {CONFIG['dataset_path']}")
    raw = load_dataset("json", data_files=CONFIG["dataset_path"], split="train")
    logger.info(f"Total: {len(raw)} | splitting 95/5 train/eval")

    split = raw.train_test_split(test_size=CONFIG["validation_split"], seed=42)
    train_ds = split["train"]
    eval_ds  = split["test"]

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

    logger.info(f"Loading model: {CONFIG['model_id']}")
    model = AutoModelForCausalLM.from_pretrained(
        CONFIG["model_id"],
        torch_dtype=torch.bfloat16,
        attn_implementation="eager",    # sdpa has NaN bug on ROCm + bf16
    )
    model.enable_input_require_grads()
    model.gradient_checkpointing_enable()

    vram_used = torch.cuda.memory_allocated() / 1e9
    logger.info(f"Parameters: {model.num_parameters():,} | VRAM after load: {vram_used:.1f} GB")

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
        optim="adamw_torch",            # bitsandbytes has no ROCm support
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
        mlm=False,
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

    logger.info("Starting training...")
    result = trainer.train()

    logger.info(f"Training loss: {result.training_loss:.4f}")
    logger.info(f"Runtime: {result.metrics.get('train_runtime', 0)/3600:.2f} hours")

    logger.info(f"Saving model to {CONFIG['output_dir']}")
    trainer.save_model(CONFIG["output_dir"])
    tokenizer.save_pretrained(CONFIG["output_dir"])

    eval_result = trainer.evaluate()
    logger.info(f"Final eval loss: {eval_result['eval_loss']:.4f}")

    logger.info("=" * 60)
    logger.info("  ATLAS FINANZAS DONE")
    logger.info(f"  Loss: {result.training_loss:.4f}")
    logger.info(f"  Output: {CONFIG['output_dir']}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
