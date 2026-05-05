#!/bin/bash
export HF_TOKEN=***REMOVED***
pip3 install huggingface_hub --break-system-packages -q

upload_model() {
    local path=$1
    local repo=$2
    echo "Uploading $path to $repo..."
    python3 -c "
from huggingface_hub import HfApi
api = HfApi(token='***REMOVED***')
api.create_repo('$repo', exist_ok=True)
api.upload_folder(folder_path='$path', repo_id='$repo')
print('Uploaded: $repo')
" 2>&1 | tee -a /root/atlas/logs/upload.log
}

# 1. Esperar Mistral (3502) — ya corriendo en tmux:mistral
echo '[1/4] Waiting for Mistral (3502)...'
while tmux has-session -t mistral 2>/dev/null; do sleep 30; done
echo '[1/4] Mistral DONE! Uploading...'
upload_model /outputs/atlas_mistral_7b_finetuned Rafaelcedav/atlas-mistral-7b-legal

# 2. Qwen (3502)
echo '[2/4] Starting Qwen (3502)...'
tmux new-session -d -s qwen "cd /root/atlas && python3 Trainning_Steps/finetune_qwen3_14b.py 2>&1 | tee logs/qwen_training.log"
while tmux has-session -t qwen 2>/dev/null; do sleep 30; done
echo '[2/4] Qwen DONE! Uploading...'
upload_model /outputs/atlas_qwen3_14b_finetuned Rafaelcedav/atlas-qwen3-14b-legal

# 3. DeepSeek (3502)
echo '[3/4] Starting DeepSeek (3502)...'
tmux new-session -d -s deepseek "cd /root/atlas && python3 Trainning_Steps/finetune_deepseek_r1_8b.py 2>&1 | tee logs/deepseek_training.log"
while tmux has-session -t deepseek 2>/dev/null; do sleep 30; done
echo '[3/4] DeepSeek DONE! Uploading...'
upload_model /outputs/atlas_deepseek_r1_8b Rafaelcedav/atlas-deepseek-r1-8b-legal

# 4. Mistral R2 (6437)
echo '[4/4] Starting Mistral R2 (6437)...'
tmux new-session -d -s mistral_r2 "cd /root/atlas && python3 Trainning_Steps/finetune_mistral_7b_r2.py 2>&1 | tee logs/mistral_r2_training.log"
while tmux has-session -t mistral_r2 2>/dev/null; do sleep 30; done
echo '[4/4] Mistral R2 DONE! Uploading...'
upload_model /outputs/atlas_mistral_7b_finetuned_r2 Rafaelcedav/atlas-mistral-7b-legal-r2

echo '========================================='
echo 'ALL PIPELINE DONE! 4 modelos en HF.'
echo '========================================='
