#!/usr/bin/env python3
"""
Upload ATLAS R2 Qwen3-14B fine-tuned model to HuggingFace.
Creates repo if it doesn't exist, uploads model + docs.

Usage:
  HF_TOKEN=hf_xxx python3 upload_to_hf.py
"""
import os
import sys
from pathlib import Path
from huggingface_hub import HfApi, create_repo

HF_TOKEN    = os.environ.get("HF_TOKEN", "")
HF_USERNAME = "Rafaelcedav"
REPO_NAME   = "atlas-r2-qwen3-14b"
REPO_ID     = f"{HF_USERNAME}/{REPO_NAME}"
MODEL_DIR   = "/outputs/r2_qwen3_14b_finetuned"

README = """---
language:
- es
- en
license: apache-2.0
base_model: Qwen/Qwen3-14B
tags:
- finance
- legal
- audit
- atlas
- amd-rocm
- fine-tuned
- hackathon
---

# ATLAS R2 — Qwen3-14B Fine-Tuned

**ATLAS** (Auditor Forense Especializado en Regulaciones Financieras MX-USA) is a
multi-agent AI pipeline built for the AMD Hackathon (lablab.ai).

This model is the core reasoning engine: Qwen3-14B fully fine-tuned on 6,437 curated
financial-audit training examples covering Mexican and US financial regulations.

## Training Details

| Parameter | Value |
|-----------|-------|
| Base model | Qwen/Qwen3-14B |
| Dataset | 6,437 examples (MX+USA financial regulations) |
| Epochs | 3 |
| Learning rate | 2e-5 |
| Batch size (effective) | 16 (2 per GPU × 8 grad accum) |
| Hardware | AMD MI300X 205GB (ROCm 7.0) |
| Training time | ~1h 11min |
| Final eval loss | 0.2697 |
| Attention | `eager` (SDPA has NaN bug on ROCm + bf16) |
| Optimizer | `adamw_torch` (bitsandbytes has no ROCm support) |

## ATLAS Pipeline

The ATLAS system consists of 4 specialized agents:

1. **Vision Agent** — OCR + document parsing (vLLM)
2. **Reasoning Agent** — This model — financial audit reasoning
3. **Validator Agent** — Cross-checks findings against regulations
4. **Explainer Agent** — Generates human-readable audit reports

## Usage

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_id = "Rafaelcedav/atlas-r2-qwen3-14b"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
    device_map="auto",
)

messages = [
    {"role": "system", "content": (
        "Eres ATLAS, auditor forense especializado en regulaciones financieras MX-USA. "
        "Responde con precisión legal, citando artículos y fuentes oficiales."
    )},
    {"role": "user", "content": "¿Cuál es el plazo para conservar documentación fiscal según el CFF?"},
]

text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(text, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=512, temperature=0.1)
print(tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True))
```

## Regulations Covered

**Mexico:** CFF, LISR, LIVA, LGTOC, Ley AML, CNBV circulares, DOF
**USA:** IRS Code, BSA, FinCEN, Patriot Act, OCC guidelines

## AMD Hackathon

Built for the AMD GPU Challenge on lablab.ai. Trained entirely on AMD MI300X
with ROCm 7.0 — no NVIDIA hardware used.

GitHub: https://github.com/rafaelcedilloav-eng/atlas-amd-hackathon
"""

FILES_TO_UPLOAD = [
    "model.safetensors",
    "config.json",
    "generation_config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "chat_template.jinja",
    "training_args.bin",
]


def main():
    if not HF_TOKEN:
        sys.exit("HF_TOKEN not set. Run: HF_TOKEN=hf_xxx python3 upload_to_hf.py")

    api = HfApi(token=HF_TOKEN)

    print(f"Creating repo: {REPO_ID}")
    create_repo(
        repo_id=REPO_ID,
        token=HF_TOKEN,
        repo_type="model",
        exist_ok=True,
        private=False,
    )
    print("  Repo ready.")

    print("Uploading README...")
    api.upload_file(
        path_or_fileobj=README.encode("utf-8"),
        path_in_repo="README.md",
        repo_id=REPO_ID,
        token=HF_TOKEN,
        commit_message="Add model card",
    )

    for fname in FILES_TO_UPLOAD:
        fpath = Path(MODEL_DIR) / fname
        if not fpath.exists():
            print(f"  [SKIP] {fname} not found")
            continue
        size_gb = fpath.stat().st_size / 1e9
        print(f"Uploading {fname} ({size_gb:.1f} GB)...")
        api.upload_file(
            path_or_fileobj=str(fpath),
            path_in_repo=fname,
            repo_id=REPO_ID,
            token=HF_TOKEN,
            commit_message=f"Upload {fname}",
        )
        print(f"  Done: {fname}")

    print(f"\nDONE. Model live at: https://huggingface.co/{REPO_ID}")


if __name__ == "__main__":
    main()
