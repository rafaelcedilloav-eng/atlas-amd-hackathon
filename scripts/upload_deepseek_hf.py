#!/usr/bin/env python3
import os, sys
from pathlib import Path
from huggingface_hub import HfApi, create_repo

HF_TOKEN  = os.environ.get('HF_TOKEN', '')
REPO_ID   = 'Rafaelcedav/atlas-finanzas-deepseek-r1-8b'
MODEL_DIR = '/outputs/atlas_deepseek_r1_8b'

README = """---
language:
- es
- en
license: apache-2.0
base_model: deepseek-ai/DeepSeek-R1-Distill-Llama-8B
tags:
- finance
- legal
- atlas
- deepseek-r1
- amd-rocm
- fine-tuned
---

# ATLAS Finanzas — DeepSeek-R1-Distill-Llama-8B Fine-Tuned

Financial-legal reasoning model fine-tuned from DeepSeek-R1-Distill-Llama-8B
on 6,437 curated examples covering MX+USA financial regulations.

Built for the AMD Hackathon (lablab.ai) — trained on AMD MI300X with ROCm 7.0.

| Parameter | Value |
|-----------|-------|
| Base model | deepseek-ai/DeepSeek-R1-Distill-Llama-8B |
| Dataset | 6,437 examples |
| Epochs | 3 |
| Learning rate | 1e-5 |
| Hardware | AMD MI300X 205GB (ROCm 7.0) |
| Training time | 36 minutes |
| Final eval loss | 0.4829 |

Companion model: Rafaelcedav/atlas-r2-qwen3-14b
GitHub: https://github.com/rafaelcedilloav-eng/atlas-amd-hackathon
"""

FILES = [
    'model.safetensors',
    'config.json',
    'generation_config.json',
    'tokenizer.json',
    'tokenizer_config.json',
    'chat_template.jinja',
    'training_args.bin',
]

if not HF_TOKEN:
    sys.exit('HF_TOKEN not set')

api = HfApi(token=HF_TOKEN)
print(f'Creating repo: {REPO_ID}')
create_repo(repo_id=REPO_ID, token=HF_TOKEN, repo_type='model', exist_ok=True, private=False)
print('  Repo ready.')

api.upload_file(path_or_fileobj=README.encode('utf-8'), path_in_repo='README.md',
    repo_id=REPO_ID, token=HF_TOKEN, commit_message='Add model card')
print('README uploaded.')

for fname in FILES:
    fpath = Path(MODEL_DIR) / fname
    if not fpath.exists():
        print(f'  [SKIP] {fname}')
        continue
    size_gb = fpath.stat().st_size / 1e9
    print(f'Uploading {fname} ({size_gb:.1f} GB)...')
    api.upload_file(path_or_fileobj=str(fpath), path_in_repo=fname,
        repo_id=REPO_ID, token=HF_TOKEN, commit_message=f'Upload {fname}')
    print(f'  Done: {fname}')

print(f'\nDONE: https://huggingface.co/{REPO_ID}')
