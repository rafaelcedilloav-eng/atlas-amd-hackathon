#!/bin/bash
# DO User Data — ATLAS eval droplet
# Paste this in the "User Data" field when creating the droplet.
# Runs in background on first boot; pip install takes ~3-4 min.

exec > /var/log/atlas_startup.log 2>&1

pip install -q \
    vllm \
    "lm_eval[api]" \
    datasets \
    huggingface_hub \
    requests \
    tqdm

echo "ATLAS startup complete: $(date)" >> /var/log/atlas_startup.log
