# CLAUDE CODE — R2 FINETUNING MASTER PROMPT
## Qwen3-30B FullFinetune on AMD MI300X
**Status:** Ready for automation  
**Model:** Qwen3-30B (32.5 GB, GGUF quantized)  
**GPU:** AMD MI300X + PyTorch 2.6.0 + ROCm 7.0  
**Goal:** Train a specialized financial/legal model in 4 hours

---

## YOUR SINGLE PROMPT TO GIVE CLAUDE CODE:

```
Execute ATLAS R2 training pipeline remotely on GPU [IP_ADDRESS].

1. SSH into GPU with private key at D:\Proyectos\atlas-amd-hackathon\.ssh\atlas_r2_key
2. Run setup_r2_gpu.sh (installs all dependencies)
3. Execute finetune_qwen3_30b_r2.py (trains model)
4. Monitor GPU metrics (temperature, utilization, memory)
5. Save outputs to /outputs/r2_qwen3_30b_finetuned/
6. Upload results to Google Drive when complete

Dataset: atlas_training_dataset.jsonl (3.8 MB, ChatML format, MX/US financial + legal)
Training time estimate: 3-4 hours
Final model size: ~62 GB

Report status every 30 minutes with GPU metrics + training loss.
```

---

## FILES INCLUDED IN THIS FOLDER:

```
Training_Steps/
├─ setup_r2_gpu.sh                    ← Install everything
├─ requirements_r2_finetune.txt       ← All Python packages
├─ finetune_qwen3_30b_r2.py           ← Main training script
├─ r2_finetune_notebook.ipynb         ← Alternative (Jupyter)
├─ R2_QUICK_START.md                  ← Execution guide
├─ CLAUDE_CODE_MASTER_PROMPT.md       ← This file
├─ DEPLOYMENT_CHECKLIST.md            ← Pre-flight checks
└─ MONITORING_DASHBOARD.md            ← GPU monitoring setup
```

---

## WHAT CLAUDE CODE WILL DO:

### Phase 1: Connection & Verification (5 min)
```bash
# SSH into GPU
ssh -i /path/to/atlas_r2_key root@[GPU_IP]

# Verify GPU
rocm-smi
rocm-smi --showtemp
rocm-smi --showuse

# Check dataset
ls -lh /data/atlas_training_dataset.jsonl
du -sh /data/
```

### Phase 2: Setup (15-25 min)
```bash
# Run setup script
bash setup_r2_gpu.sh

# This installs:
# - ROCm 6.2/7.0 verification
# - PyTorch 2.3.0/2.6.0
# - DeepSpeed, Flash-Attention, BitsAndBytes
# - All dependencies in requirements_r2_finetune.txt
```

### Phase 3: Training (3-4 hours)
```bash
# Activate venv
source /root/atlas_r2_env/bin/activate

# Download model from HF
huggingface-cli download Rafaelcedav/atlas-core-30b-q8

# Start training
python3 finetune_qwen3_30b_r2.py

# Outputs to: ./outputs/r2_qwen3_30b_finetuned/
```

### Phase 4: Monitoring (every 30 min)
```bash
# GPU status
rocm-smi --showtemp --showuse

# Training logs
tail -50 training.log

# Report:
# - GPU Util: X%
# - Temp: X°C
# - Memory: X GB / 192 GB
# - Training loss: X.XX
# - ETA: X hours remaining
```

### Phase 5: Post-Training (15 min)
```bash
# Verify output
ls -lh ./outputs/r2_qwen3_30b_finetuned/

# Expected files:
# - config.json (1 KB)
# - model.safetensors (62 GB)
# - tokenizer.json (1 MB)
```

---

## CRITICAL INFO FOR CLAUDE CODE:

### GPU Connection
```
IP: [USER PROVIDES THIS]
User: root
Port: 22 (default)
Auth: SSH Key at D:\Proyectos\atlas-amd-hackathon\.ssh\atlas_r2_key
```

### Dataset Location
```
Path: /data/atlas_training_dataset.jsonl
Format: JSONL (ChatML: system/user/assistant roles)
Size: 3.8 MB (~3,800 training examples)
Train/Val split: 90/10 (automatic)
```

### Model Source
```
Hugging Face: Rafaelcedav/atlas-core-30b-q8
Format: GGUF (quantized, 32.5 GB)
Type: Conversational LLM (financial/legal specialized)
License: Check model card
```

### Output Destination
```
Local: ./outputs/r2_qwen3_30b_finetuned/
Google Drive: [USER PROVIDES FOLDER ID IF NEEDED]
```

---

## WHAT HAPPENS IF THERE'S AN ERROR:

### Error: OOM (Out of Memory)
```
Solution: Reduce batch_size in config
Edit: batch_size_per_gpu = 1 (instead of 2)
      gradient_accumulation_steps = 16
Time impact: +30 min training
```

### Error: GPU Temp > 85°C
```
Solution: Reduce batch size OR enable under-clocking
rocm-smi --setsclk 5
Or lower batch_size
Risk: None (just slower training)
```

### Error: Model download fails
```
Solution: Retry download
huggingface-cli download --resume-incomplete Rafaelcedav/atlas-core-30b-q8
Or use mirror: HF_MIRROR=https://huggingface-mirror.com/
```

### Error: Training stops mid-epoch
```
Solution: Resume from checkpoint
Edit: resume_from_checkpoint = "./checkpoints/r2"
Loss will recover from where it left off
```

---

## SUCCESS METRICS:

### R1 Baseline
- Training loss: 2.5 → 0.8 (dropped 0.017/step)
- Time: 1 hour
- Epochs: 3

### R2 Target
- Training loss: 2.5 → 0.6-0.7 (should drop faster)
- Time: 3-4 hours (full params)
- Epochs: 3
- Quality: +15-25% on legal/financial QA

---

## AFTER TRAINING COMPLETES:

### Verification
```bash
# Test inference
python3 << 'EOF'
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model = AutoModelForCausalLM.from_pretrained(
    "./outputs/r2_qwen3_30b_finetuned",
    torch_dtype=torch.bfloat16,
    attn_implementation="flash_attention_2",
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained("./outputs/r2_qwen3_30b_finetuned")

prompt = "<system>Eres ATLAS auditor.</system><user>¿Art. 69-B CFF?</user>"
inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=200)
print(tokenizer.decode(outputs[0]))
EOF
```

### Upload Results (Optional)
```bash
# To Google Drive
rclone copy ./outputs/r2_qwen3_30b_finetuned/ gdrive:atlas_r2_results

# Or to Hugging Face
huggingface-cli upload Rafaelcedav/atlas-core-30b-r2-finetuned \
    ./outputs/r2_qwen3_30b_finetuned/*
```

---

## TIMELINE ESTIMATE:

```
T+0:00    → GPU creation (user does this)
T+0:05    → Claude Code SSH connect
T+0:10    → Setup script starts
T+0:35    → Setup complete, venv ready
T+0:40    → Model download starts
T+0:50    → Model ready, tokenization starts
T+1:00    → Training epoch 1 begins
T+2:30    → Training epoch 2
T+4:00    → Training complete ✅
T+4:15    → Evaluation + save
T+4:20    → Ready for upload/testing
```

---

## FAILSAFE CHECKS CLAUDE CODE SHOULD RUN:

```bash
# 1. GPU available
rocm-smi --json | grep -q "gpu_memory_used" && echo "✅ GPU OK"

# 2. Dataset exists
[ -f /data/atlas_training_dataset.jsonl ] && echo "✅ Dataset OK"

# 3. PyTorch + ROCm
python3 -c "import torch; assert torch.cuda.is_available(), 'GPU not available'" && echo "✅ PyTorch OK"

# 4. Dependencies installed
python3 -c "import transformers, deepspeed, flash_attn" && echo "✅ Deps OK"

# 5. Disk space > 200GB
df /outputs | awk 'NR==2 {if ($4/1024/1024 > 200) print "✅ Storage OK"; else print "❌ Storage LOW"}' 

# 6. Network
curl -I https://huggingface.co > /dev/null && echo "✅ Network OK"
```

---

## THE ONLY COMMAND YOU GIVE CLAUDE CODE:

```
"Execute ATLAS R2 training on [GPU_IP] using the files in Training_Steps/ folder. 
Full automation from setup to final model. Report status every 30 minutes."
```

**That's it. Claude Code does everything else.** 🚀

---

**END OF MASTER PROMPT**
