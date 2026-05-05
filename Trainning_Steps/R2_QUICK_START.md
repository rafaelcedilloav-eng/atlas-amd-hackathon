# ATLAS R2 — MONSTER FINETUNING QUICK START
## Qwen3-30B FullFinetune on AMD MI300X

**Status:** Ready to execute  
**Estimated Training Time:** 3-4 hours (vs R1's 1 hour because we're doing FullFinetune)  
**GPU:** AMD MI300X + ROCm 6.2  
**Goal:** Produce specialized financial/legal model

---

## STEP 0: VERIFICAR AMBIENTE (Pre-flight Check)

```bash
# SSH to MI300X
ssh root@165.245.138.52

# Check GPU
rocm-smi
rocm-smi --showtemp

# Check storage
df -h /data
df -h /home

# List dataset
ls -lh /data/atlas_training_dataset.jsonl
```

**Expected output:**
```
GPU: Instinct MI300X
Memory: 192 GB available
Temperature: < 50°C
Dataset: 3.8 MB atlas_training_dataset.jsonl
```

---

## STEP 1: SETUP GPU (First time only)

```bash
# Download setup script
curl -O https://[your-server]/setup_r2_gpu.sh
chmod +x setup_r2_gpu.sh

# Run setup (takes 15-25 minutes)
bash setup_r2_gpu.sh

# Verify
rocm-smi
nvidia-smi  # Should fail (AMD, not NVIDIA)
python3 -c "import torch; print(torch.cuda.is_available())"
```

**Expected output:**
```
✅ GPU: AMD MI300X detected
✅ ROCm 6.2.0 installed
✅ PyTorch 2.3.0 + ROCm available
✅ All dependencies installed
```

---

## STEP 2: OPTION A — USE JUPYTER (Like R1)

**RECOMMENDED FOR QUICK ITERATION:**

```bash
# 1. SSH to server
ssh root@165.245.138.52

# 2. Activate venv
source /root/atlas_r2_env/bin/activate

# 3. Start Jupyter
jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root

# 4. Open in your browser
# http://165.245.138.52:8888/?token=[TOKEN_FROM_OUTPUT]

# 5. Upload r2_finetune_notebook.ipynb
# Then run cells one by one
```

**Notebook will:**
- ✅ Load dataset
- ✅ Split train/val (90/10)
- ✅ Load Qwen3-30B model
- ✅ Tokenize (ChatML format)
- ✅ Run FullFinetune training
- ✅ Evaluate
- ✅ Save to disk
- ✅ Test inference

---

## STEP 3: OPTION B — COMMAND LINE (Full Automation)

**RECOMMENDED FOR PRODUCTION:**

```bash
# 1. SSH to server
ssh root@165.245.138.52

# 2. Activate venv
source /root/atlas_r2_env/bin/activate

# 3. Download training script
curl -O https://[your-server]/finetune_qwen3_30b_r2.py

# 4. Create data symlink
mkdir -p /data
# (Ensure atlas_training_dataset.jsonl is in /data/)

# 5. Run training (fully automated)
python3 finetune_qwen3_30b_r2.py

# Training output appears in: ./outputs/r2_qwen3_30b_finetuned/
```

**Script will:**
- ✅ Load & split dataset
- ✅ Load model + tokenizer
- ✅ Setup DeepSpeed ZeRO-2
- ✅ Configure Flash-Attention
- ✅ Run 3 epochs
- ✅ Save checkpoints every 100 steps
- ✅ Final evaluation
- ✅ Save finetuned model

---

## STEP 4: MONITOR TRAINING

### Option A: TensorBoard
```bash
# From your LOCAL machine
tensorboard --logdir=outputs/runs --port=6006

# Open: http://localhost:6006
```

### Option B: Watch GPU
```bash
# SSH to server in separate terminal
watch -n 1 'rocm-smi --showtemp --showuse'

# Expected:
# - GPU Util: 80-95%
# - Temperature: 50-70°C
# - Memory: 170-190 GB used
```

### Option C: Tail Logs
```bash
# From server
tail -f training_log.txt
```

---

## STEP 5: EXPECTED METRICS

### R1 Baseline (LoRA)
- Training loss: Started ~2.5, ended ~0.8
- Time: 1 hour
- Model type: LoRA adapter (67 MB)

### R2 Target (FullFinetune)
- Training loss: Should drop faster ~2.5 → ~0.6-0.7
- Time: 3-4 hours (because we're updating all 30B parameters)
- Model type: Full model (62 GB)
- Quality: 15-25% better on legal/financial QA

---

## STEP 6: POST-TRAINING

### Verify Output
```bash
ls -lh outputs/r2_qwen3_30b_finetuned/

# Expected files:
# - config.json (1 KB)
# - model.safetensors (62 GB) ← THE MONSTER
# - tokenizer.json (1 MB)
# - training_args.bin (3 KB)
```

### Test Inference
```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model = AutoModelForCausalLM.from_pretrained(
    "./outputs/r2_qwen3_30b_finetuned",
    torch_dtype=torch.bfloat16,
    attn_implementation="flash_attention_2",
    device_map="auto"
)

tokenizer = AutoTokenizer.from_pretrained(
    "./outputs/r2_qwen3_30b_finetuned"
)

# Test prompt
prompt = "<system>Eres ATLAS auditor forense.</system><user>¿Art. 69-B CFF?</user>"

inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=200, temperature=0.7)
response = tokenizer.decode(outputs[0])

print(response)
```

### Push to Hugging Face (Optional)
```bash
# After training succeeds
huggingface-cli login
huggingface-cli upload Rafaelcedav/atlas-core-30b-r2-finetuned \
    ./outputs/r2_qwen3_30b_finetuned/*
```

---

## STEP 7: TROUBLESHOOTING

### Problem: OOM (Out of Memory)
```
Solution: Reduce batch_size or enable DeepSpeed offloading
Edit config: batch_size=1, gradient_accumulation=16
```

### Problem: Slow Training
```
Solution: Enable Torch Compile
In script: torch_compile=True
Speedup: 10-20%
```

### Problem: GPU Temperature High (>80°C)
```
Solution: Reduce batch size or enable under-clocking
rocm-smi --setsclk 5  # Lower power state
```

### Problem: CUDA Out of Memory during Model Load
```
Solution: Use 8-bit quantization
from bitsandbytes.nn import Linear8bitLt
```

---

## STEP 8: COMPARISON R1 vs R2

| Aspect | R1 (LoRA) | R2 (FullFinetune) |
|--------|-----------|-------------------|
| **Training Time** | 1 hour | 3-4 hours |
| **Model Size** | 67 MB (adapter) | 62 GB (full) |
| **Quality Gain** | Baseline | +15-25% |
| **Inference Speed** | Fast | Same |
| **GPU Memory** | 40 GB | 170 GB |
| **Update Scope** | Adapter layers only | All 30B params |
| **Specialization** | Moderate | Deep |

---

## STEP 9: NEXT PHASE

After R2 succeeds:

### R2.5 — Quantization
```
Take full R2 model → Quantize to Q4 (8 GB)
For faster inference & deployment
```

### R3 — Qwen3-8B-Financial
```
Use R2's knowledge → Train smaller 8B model
Goal: Speed + 90% quality of 30B
```

### R4 — Other Models
```
Apply same process to:
- LLaMA 2 (7B/13B)
- Mistral (7B)
- Phi-3 (3.8B)
```

---

## COMMANDS CHEAT SHEET

```bash
# Full pipeline one-liner
bash setup_r2_gpu.sh && \
  source /root/atlas_r2_env/bin/activate && \
  python3 finetune_qwen3_30b_r2.py && \
  echo "✅ R2 COMPLETE"

# Monitor only
watch -n 1 'rocm-smi --showtemp --showuse'

# Check dataset
head -5 /data/atlas_training_dataset.jsonl | python3 -m json.tool

# Test GPU
python3 -c "import torch; x=torch.randn(1000,1000).cuda(); y=torch.matmul(x,x); print('✅ GPU OK')"

# Kill training (if needed)
pkill -f "finetune_qwen3_30b"
```

---

## 🚀 READY TO RUMBLE?

**Execute this when ready:**

```bash
# Copy to server
scp r2_finetune_notebook.ipynb root@165.245.138.52:/root/

# SSH in
ssh root@165.245.138.52

# Activate & start Jupyter
source /root/atlas_r2_env/bin/activate
jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser

# Or run script directly
python3 finetune_qwen3_30b_r2.py
```

**Estimated completion: 3-4 hours from now**

---

**ATLAS R2 — VAMOS A ROMPERLA** 🚀🔥
