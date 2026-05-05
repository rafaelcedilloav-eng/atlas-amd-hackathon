# R2 DEPLOYMENT CHECKLIST
## Pre-flight verification before Claude Code execution

---

## BEFORE GIVING CLAUDE CODE THE PROMPT:

### ✅ GPU Creation
- [ ] Created GPU in DigitalOcean with PyTorch 2.6.0 + ROCm 7.0
- [ ] GPU is RUNNING (not off/suspended)
- [ ] Note the IP address: `________________`
- [ ] Port 22 (SSH) is open
- [ ] Region: `________________` (preferably US-East or US-West)

### ✅ SSH Key Setup
- [ ] SSH key created: `D:\Proyectos\atlas-amd-hackathon\.ssh\atlas_r2_key`
- [ ] Public key added to DigitalOcean SSH keys
- [ ] Private key exists locally (don't share)
- [ ] Permissions: `chmod 600 atlas_r2_key` (if on Linux/Mac)

### ✅ Dataset Preparation
- [ ] Dataset uploaded to GPU at: `/data/atlas_training_dataset.jsonl`
- [ ] File size: **3.8 MB** ✓
- [ ] Format verified: JSONL (ChatML: system/user/assistant)
- [ ] Sample check: `head -1 /data/atlas_training_dataset.jsonl` returns valid JSON

```bash
# Verify dataset (Claude Code will check this)
head -1 /data/atlas_training_dataset.jsonl | jq '.' > /dev/null && echo "✅ Dataset valid"
```

### ✅ GPU Specs Confirmation
- [ ] GPU Type: AMD MI300X (192 GB VRAM)
- [ ] Available Storage: > 250 GB (for model + training artifacts)
- [ ] Available Memory: > 200 GB (for training)
- [ ] Temperature: < 50°C (idle)

```bash
# Claude Code will verify on first connection
rocm-smi --showid --showtemp --showmeminfo=vram
df -h /
```

### ✅ Files in Training_Steps Folder

**Verify all 5 core files exist in `D:\Proyectos\atlas-amd-hackathon\Training_Steps\`:**

- [ ] `setup_r2_gpu.sh` (7.4 KB)
  - [ ] Contains ROCm install
  - [ ] Contains PyTorch install
  - [ ] Contains dependency install
  - [ ] Has verification script at end

- [ ] `requirements_r2_finetune.txt` (1.9 KB)
  - [ ] PyTorch 2.3.0 listed
  - [ ] DeepSpeed included
  - [ ] Flash-Attention included
  - [ ] BitsAndBytes included

- [ ] `finetune_qwen3_30b_r2.py` (13 KB)
  - [ ] FullFinetune configuration
  - [ ] DeepSpeed ZeRO-2 config embedded
  - [ ] Training loop complete
  - [ ] Evaluation code present
  - [ ] Model save code present

- [ ] `r2_finetune_notebook.ipynb` (12 KB)
  - [ ] Jupyter notebook format (backup option)
  - [ ] Step-by-step cells
  - [ ] Inference test cell at end

- [ ] `R2_QUICK_START.md` (6.9 KB)
  - [ ] Contains quick execution guide
  - [ ] Contains troubleshooting section
  - [ ] Contains monitoring commands

**Optional supporting files:**

- [ ] `CLAUDE_CODE_MASTER_PROMPT.md` (this file's parent)
- [ ] `DEPLOYMENT_CHECKLIST.md` (this file)
- [ ] `MONITORING_DASHBOARD.md` (GPU monitoring guide)

---

## CLAUDE CODE PRE-EXECUTION CHECKS:

Claude Code will automatically verify before starting:

```bash
# 1. SSH Connection
ssh -i [key] root@[IP] "echo 'SSH OK'"

# 2. GPU Status
ssh -i [key] root@[IP] "rocm-smi"

# 3. Dataset Presence
ssh -i [key] root@[IP] "ls -lh /data/atlas_training_dataset.jsonl"

# 4. Disk Space
ssh -i [key] root@[IP] "df -h / | tail -1"

# 5. Network (HF access)
ssh -i [key] root@[IP] "curl -I https://huggingface.co"

# 6. ROCm Version
ssh -i [key] root@[IP] "rocm-smi --version"
```

**All must return success before training starts.**

---

## YOUR EXACT PROMPT TO GIVE CLAUDE CODE:

```
GPU IP: [INSERT_IP_HERE]
SSH Key: D:\Proyectos\atlas-amd-hackathon\.ssh\atlas_r2_key
Dataset: /data/atlas_training_dataset.jsonl
Model: Rafaelcedav/atlas-core-30b-q8

Execute ATLAS R2 FullFinetune training pipeline:
1. SSH into GPU using key
2. Run setup_r2_gpu.sh
3. Execute finetune_qwen3_30b_r2.py
4. Monitor GPU every 30 minutes
5. Save final model to /outputs/r2_qwen3_30b_finetuned/
6. Report training metrics and ETA

Training files are in: Training_Steps folder
```

---

## WHAT CLAUDE CODE WILL OUTPUT:

### Every 30 Minutes:
```
[TIMESTAMP] ATLAS R2 Training Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GPU Temperature: XX°C
GPU Utilization: XX%
GPU Memory: XXX GB / 192 GB
Training Loss: X.XXXX
Epoch: X/3
Step: XXX/XXXX
ETA: X hours X minutes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### At Completion:
```
✅ ATLAS R2 TRAINING COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Final Training Loss: X.XXX
Validation Loss: X.XXX
Total Time: 3h 45m
Model Location: /outputs/r2_qwen3_30b_finetuned/
Model Size: 62 GB
Files: config.json, model.safetensors, tokenizer.json
Ready for inference/deployment
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## AFTER TRAINING COMPLETES:

### Download Model (Optional)
```bash
# From GPU to your local machine
scp -r -i D:\Proyectos\atlas-amd-hackathon\.ssh\atlas_r2_key \
    root@[GPU_IP]:/outputs/r2_qwen3_30b_finetuned/ \
    D:\Proyectos\atlas-amd-hackathon\Models\r2_finetuned\
```

### Test Inference
```bash
# Quick test to verify model works
python3 << 'EOF'
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_path = "./outputs/r2_qwen3_30b_finetuned"
model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.bfloat16, device_map="auto")
tokenizer = AutoTokenizer.from_pretrained(model_path)

prompt = "<system>Eres ATLAS.</system><user>¿Art. 69-B?</user>"
inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=100)
print(tokenizer.decode(outputs[0]))
EOF
```

### Quantize for Deployment (Optional - R2.5)
```bash
# Reduce 62GB → 8GB for faster inference
python3 << 'EOF'
from transformers import AutoModelForCausalLM, AutoTokenizer
from bitsandbytes.nn import Linear8bitLt

# Load and quantize
model_path = "./outputs/r2_qwen3_30b_finetuned"
model = AutoModelForCausalLM.from_pretrained(model_path, load_in_8bit=True)
model.save_pretrained("./outputs/r2_qwen3_30b_quantized_8bit/")
EOF
```

---

## TROUBLESHOOTING DURING TRAINING:

If Claude Code reports an issue:

### GPU Out of Memory
```
Claude Code action: Reduce batch_size from 2 to 1
Time impact: +30-45 minutes
Solution automatic: Yes
```

### Training Loss Not Decreasing
```
Claude Code action: Continue training (loss may plateau temporarily)
Check: Is it stuck at step 50+? This is normal.
Timeline: Loss should decrease significantly by epoch 2
```

### Network Timeout
```
Claude Code action: Retry model download automatically (up to 3 times)
If persistent: Check HuggingFace API status
Fallback: Use local model if available
```

### Disk Space Low
```
Claude Code action: Pause training and alert
Solution: Free 50GB+ and resume from checkpoint
```

---

## SUCCESS CRITERIA:

Training is successful when:

- ✅ All 3 epochs complete without errors
- ✅ Training loss < 0.7 (target: 0.6-0.7)
- ✅ Validation loss < 0.8
- ✅ Model file saved: `model.safetensors` (62 GB)
- ✅ Config saved: `config.json`
- ✅ Tokenizer saved: `tokenizer.json`
- ✅ Inference test returns valid response

---

## CLAUDE CODE EXECUTION FLOW DIAGRAM:

```
┌─────────────────────────────────────┐
│ User: GPU IP + SSH Key + Prompt     │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ Claude Code: Connect + Verify       │
│ - SSH into GPU                      │
│ - Check GPU/Dataset/Storage         │
│ - Validate all files                │
└────────────┬────────────────────────┘
             ↓ (if all OK)
┌─────────────────────────────────────┐
│ Phase 1: Setup (15-25 min)          │
│ - bash setup_r2_gpu.sh              │
│ - Install ROCm/PyTorch/DeepSpeed    │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ Phase 2: Training (3-4 hours)       │
│ - python3 finetune_qwen3_30b_r2.py  │
│ - Monitor GPU every 30 min          │
│ - 3 epochs of FullFinetune          │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ Phase 3: Post-Training (15 min)     │
│ - Evaluation metrics                │
│ - Save model + tokenizer            │
│ - Verify outputs                    │
│ - Ready for inference               │
└─────────────────────────────────────┘
```

---

## FINAL CHECKLIST BEFORE EXECUTION:

- [ ] GPU IP noted: `________________________`
- [ ] SSH key exists: `D:\Proyectos\atlas-amd-hackathon\.ssh\atlas_r2_key`
- [ ] Dataset uploaded to GPU: `/data/atlas_training_dataset.jsonl`
- [ ] All 5 files in `Training_Steps/` folder
- [ ] This checklist completed
- [ ] Ready to give Claude Code the prompt

---

**Once you check everything above, give Claude Code this prompt:**

```
Execute ATLAS R2 training on GPU [YOUR_IP_HERE] with full automation.
Files in Training_Steps/ folder. Report every 30 minutes.
```

**Then sit back and watch the magic happen.** 🚀✨
