#!/usr/bin/env python3
# ============================================================
# ATLAS R2 FINETUNE — Qwen3-30B FullFinetune
# AMD MI300X + DeepSpeed + Flash-Attention + ROCm 6.2
# ============================================================

import os
import sys
import json
import torch
import logging
from datetime import datetime
from pathlib import Path

from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
)
from datasets import load_dataset
from deepspeed import init_distributed

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# CONFIG
# ============================================================

CONFIG = {
    "model_id": "Rafaelcedav/atlas-core-30b-q8",
    "dataset_path": "/data/atlas_training_dataset.jsonl",
    "output_dir": "./outputs/r2_qwen3_30b_finetuned",
    "checkpoint_dir": "./checkpoints/r2",
    
    # Training hyperparameters
    "learning_rate": 5e-5,
    "batch_size_per_gpu": 2,  # Adjust if OOM
    "gradient_accumulation_steps": 8,  # Effective batch = 2*8=16
    "num_epochs": 3,
    "max_steps": -1,  # Use epochs instead
    "warmup_steps": 500,
    "weight_decay": 0.01,
    "adam_beta1": 0.9,
    "adam_beta2": 0.999,
    "adam_epsilon": 1e-8,
    "max_grad_norm": 1.0,
    
    # Optimization
    "use_flash_attention_2": True,
    "torch_compile": False,  # Enable later for speed
    "gradient_checkpointing": True,  # Save memory
    "mixed_precision": "bf16",  # Better for MI300X
    
    # DeepSpeed
    "deepspeed": "./deepspeed_config.json",
    "ddp_find_unused_parameters": False,
    
    # Validation
    "eval_strategy": "steps",
    "eval_steps": 100,
    "save_strategy": "steps",
    "save_steps": 100,
    "save_total_limit": 3,
    
    # Logging
    "logging_steps": 10,
    "log_level": "info",
    "report_to": ["tensorboard", "wandb"],
    
    # Data
    "max_seq_length": 2048,
    "preprocessing_num_workers": 4,
    "validation_split_percentage": 10,
}

# ============================================================
# DEEPSPEED CONFIG
# ============================================================

DEEPSPEED_CONFIG = {
    "train_batch_size": 16,
    "train_micro_batch_size_per_gpu": 2,
    "gradient_accumulation_steps": 8,
    
    "steps_per_print": 10,
    "gradient_clipping": 1.0,
    
    "optimizer": {
        "type": "AdamW",
        "params": {
            "lr": 5e-5,
            "betas": [0.9, 0.999],
            "eps": 1e-8,
            "weight_decay": 0.01
        }
    },
    
    "scheduler": {
        "type": "WarmupLinear",
        "params": {
            "warmup_min_lr": 0,
            "warmup_max_lr": 5e-5,
            "warmup_num_steps": 500
        }
    },
    
    "fp16": {
        "enabled": False,  # Use bf16 instead on MI300X
    },
    
    "bf16": {
        "enabled": True,
    },
    
    "activation_checkpointing": {
        "partition_activations": True,
        "cpu_checkpointing": False,
        "contiguous_memory_optimization": False,
        "number_checkpoints": 4,
    },
    
    "zero_optimization": {
        "stage": 2,  # Stage 2: Gradient partitioning
        "offload_optimizer": {
            "device": "cpu"
        },
        "overlap_comm": True,
        "contiguous_gradients": True,
        "reduce_scatter": True,
        "reduce_bucket_size": 5e7,
        "allgather_bucket_size": 5e7,
        "sub_group_size": 1e9,
    },
    
    "wall_clock_breakdown": True,
    "always_output_loss": True,
}

# ============================================================
# DATA LOADING
# ============================================================

def load_and_prepare_data(config):
    """Load JSONL dataset and prepare for training."""
    
    logger.info(f"Loading dataset from {config['dataset_path']}")
    
    # Load JSONL
    dataset = load_dataset(
        "json",
        data_files=config['dataset_path'],
        split="train"
    )
    
    logger.info(f"Dataset size: {len(dataset)} examples")
    
    # Split into train/val
    split_data = dataset.train_test_split(
        test_size=config['validation_split_percentage']/100
    )
    train_dataset = split_data['train']
    eval_dataset = split_data['test']
    
    logger.info(f"Train set: {len(train_dataset)}")
    logger.info(f"Eval set: {len(eval_dataset)}")
    
    return train_dataset, eval_dataset

# ============================================================
# TOKENIZATION
# ============================================================

def preprocess_function(examples, tokenizer, max_seq_length):
    """Convert messages to tokens."""
    
    texts = []
    for messages in examples['messages']:
        text = ""
        for msg in messages:
            role = msg.get('role', '')
            content = msg.get('content', '')
            if role == 'system':
                text += f"<system>{content}</system>"
            elif role == 'user':
                text += f"<user>{content}</user>"
            elif role == 'assistant':
                text += f"<assistant>{content}</assistant>"
        texts.append(text)
    
    # Tokenize
    tokenized = tokenizer(
        texts,
        max_length=max_seq_length,
        truncation=True,
        padding="max_length",
        return_tensors=None,
    )
    
    # Set labels = input_ids for causal LM
    tokenized['labels'] = tokenized['input_ids'].copy()
    
    return tokenized

# ============================================================
# MAIN TRAINING
# ============================================================

def main():
    logger.info("╔════════════════════════════════════════════════════════╗")
    logger.info("║   ATLAS R2 - QWEN3-30B FINETUNE START                  ║")
    logger.info("║   FullFinetune + DeepSpeed + Flash-Attention          ║")
    logger.info("║   GPU: AMD MI300X + ROCm 6.2.0                         ║")
    logger.info("╚════════════════════════════════════════════════════════╝")
    
    # Verify GPU
    logger.info(f"GPU Available: {torch.cuda.is_available()}")
    logger.info(f"GPU Count: {torch.cuda.device_count()}")
    if torch.cuda.is_available():
        logger.info(f"GPU Name: {torch.cuda.get_device_name(0)}")
        logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    
    # Create output directories
    Path(CONFIG['output_dir']).mkdir(parents=True, exist_ok=True)
    Path(CONFIG['checkpoint_dir']).mkdir(parents=True, exist_ok=True)
    
    # Save DeepSpeed config
    with open(CONFIG['deepspeed'], 'w') as f:
        json.dump(DEEPSPEED_CONFIG, f, indent=2)
    logger.info(f"DeepSpeed config saved: {CONFIG['deepspeed']}")
    
    # ============================================================
    # 1. Load Model & Tokenizer
    # ============================================================
    logger.info("Loading model & tokenizer...")
    
    model = AutoModelForCausalLM.from_pretrained(
        CONFIG['model_id'],
        torch_dtype=torch.bfloat16,
        attn_implementation="flash_attention_2" if CONFIG['use_flash_attention_2'] else "eager",
        device_map="auto",
    )
    
    tokenizer = AutoTokenizer.from_pretrained(CONFIG['model_id'])
    tokenizer.pad_token = tokenizer.eos_token
    
    logger.info(f"Model params: {model.num_parameters():,}")
    logger.info(f"Model dtype: {next(model.parameters()).dtype}")
    
    # ============================================================
    # 2. Load & Prepare Dataset
    # ============================================================
    logger.info("Loading and preparing dataset...")
    
    train_dataset, eval_dataset = load_and_prepare_data(CONFIG)
    
    # Tokenize
    train_dataset = train_dataset.map(
        lambda x: preprocess_function(x, tokenizer, CONFIG['max_seq_length']),
        batched=True,
        remove_columns=train_dataset.column_names,
        num_proc=CONFIG['preprocessing_num_workers'],
    )
    
    eval_dataset = eval_dataset.map(
        lambda x: preprocess_function(x, tokenizer, CONFIG['max_seq_length']),
        batched=True,
        remove_columns=eval_dataset.column_names,
        num_proc=CONFIG['preprocessing_num_workers'],
    )
    
    logger.info(f"Train dataset (tokenized): {len(train_dataset)}")
    logger.info(f"Eval dataset (tokenized): {len(eval_dataset)}")
    
    # ============================================================
    # 3. Training Arguments
    # ============================================================
    logger.info("Setting up training arguments...")
    
    training_args = TrainingArguments(
        output_dir=CONFIG['output_dir'],
        learning_rate=CONFIG['learning_rate'],
        per_device_train_batch_size=CONFIG['batch_size_per_gpu'],
        per_device_eval_batch_size=CONFIG['batch_size_per_gpu'],
        gradient_accumulation_steps=CONFIG['gradient_accumulation_steps'],
        num_train_epochs=CONFIG['num_epochs'],
        warmup_steps=CONFIG['warmup_steps'],
        weight_decay=CONFIG['weight_decay'],
        max_grad_norm=CONFIG['max_grad_norm'],
        
        eval_strategy=CONFIG['eval_strategy'],
        eval_steps=CONFIG['eval_steps'],
        save_strategy=CONFIG['save_strategy'],
        save_steps=CONFIG['save_steps'],
        save_total_limit=CONFIG['save_total_limit'],
        
        logging_steps=CONFIG['logging_steps'],
        log_level=CONFIG['log_level'],
        report_to=CONFIG['report_to'],
        
        bf16=True,
        gradient_checkpointing=CONFIG['gradient_checkpointing'],
        ddp_find_unused_parameters=CONFIG['ddp_find_unused_parameters'],
        
        deepspeed=CONFIG['deepspeed'],
        
        seed=42,
        dataloader_pin_memory=True,
        dataloader_num_workers=4,
    )
    
    # ============================================================
    # 4. Trainer
    # ============================================================
    logger.info("Creating trainer...")
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        tokenizer=tokenizer,
    )
    
    # ============================================================
    # 5. Train
    # ============================================================
    logger.info("╔════════════════════════════════════════════════════════╗")
    logger.info("║                 TRAINING START                         ║")
    logger.info("╚════════════════════════════════════════════════════════╝")
    
    train_result = trainer.train()
    
    logger.info("╔════════════════════════════════════════════════════════╗")
    logger.info("║                 TRAINING COMPLETE                      ║")
    logger.info("╚════════════════════════════════════════════════════════╝")
    logger.info(f"Final loss: {train_result.training_loss:.4f}")
    
    # ============================================================
    # 6. Save Model
    # ============================================================
    logger.info("Saving model...")
    
    model.save_pretrained(CONFIG['output_dir'])
    tokenizer.save_pretrained(CONFIG['output_dir'])
    
    logger.info(f"Model saved to: {CONFIG['output_dir']}")
    
    # ============================================================
    # 7. Evaluate
    # ============================================================
    logger.info("Running final evaluation...")
    
    eval_result = trainer.evaluate()
    logger.info(f"Eval loss: {eval_result['eval_loss']:.4f}")
    
    logger.info("╔════════════════════════════════════════════════════════╗")
    logger.info("║              ✅ R2 FINETUNE SUCCESSFUL                 ║")
    logger.info("╚════════════════════════════════════════════════════════╝")
    
    return model, tokenizer

if __name__ == "__main__":
    main()
