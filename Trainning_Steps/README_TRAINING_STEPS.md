# ATLAS R2 TRAINING_STEPS
## Complete automation package for Claude Code

**Status:** Ready for deployment  
**Model:** Qwen3-30B FullFinetune on AMD MI300X  
**Total Runtime:** ~4.5 hours  
**User Action Required:** Just give Claude Code the GPU IP + one prompt  

---

## 📁 WHAT'S IN THIS FOLDER:

```
Training_Steps/
│
├─ 🔧 CORE TRAINING FILES (5)
│  ├─ setup_r2_gpu.sh                    [7.4 KB]  ← Install everything
│  ├─ requirements_r2_finetune.txt       [1.9 KB]  ← Python packages
│  ├─ finetune_qwen3_30b_r2.py          [13 KB]   ← Main training script
│  ├─ r2_finetune_notebook.ipynb        [12 KB]   ← Jupyter alternative
│  └─ R2_QUICK_START.md                 [6.9 KB]  ← Execution guide
│
├─ 📋 AUTOMATION GUIDES (3)
│  ├─ CLAUDE_CODE_MASTER_PROMPT.md      [This tells Claude Code what to do]
│  ├─ DEPLOYMENT_CHECKLIST.md           [Pre-flight verification]
│  └─ MONITORING_DASHBOARD.md           [GPU metrics to expect]
│
└─ 📄 README.md                         [This file]
```

---

## 🚀 QUICKSTART — 3 SIMPLE STEPS:

### Step 1: Create GPU
```
Go to DigitalOcean → Create GPU
Select: PyTorch 2.6.0 - ROCm 7.0
Wait for it to boot
Note the IP address
```

### Step 2: Prepare
```
1. Add SSH public key to DigitalOcean (during GPU creation)
2. Upload atlas_training_dataset.jsonl to GPU at /data/
3. Verify all files in Training_Steps/ folder exist locally
4. Fill out DEPLOYMENT_CHECKLIST.md
```

### Step 3: Execute
```
Give Claude Code this prompt:

"GPU IP: [INSERT_IP]
SSH Key: D:\Proyectos\atlas-amd-hackathon\.ssh\atlas_r2_key
Dataset: /data/atlas_training_dataset.jsonl

Execute ATLAS R2 training with files from Training_Steps folder.
Full automation from setup to final model. Report every 30 minutes."

Then Claude Code does EVERYTHING else.
```

---

## 📊 WHAT CLAUDE CODE WILL DO:

### Automatically (no user input needed):

✅ SSH into GPU using your private key  
✅ Verify GPU is ready (ROCm, storage, network)  
✅ Run `setup_r2_gpu.sh` (installs all dependencies in 15-25 min)  
✅ Download Qwen3-30B model from Hugging Face (10 min)  
✅ Execute `finetune_qwen3_30b_r2.py` (trains for 3-4 hours)  
✅ Monitor GPU temperature, memory, utilization every 30 minutes  
✅ Report training loss, validation loss, ETA every 30 minutes  
✅ Save final model to `/outputs/r2_qwen3_30b_finetuned/`  
✅ Verify model integrity (can run inference)  
✅ Alert on any errors or anomalies  

### You just sit back and watch the reports come in.

---

## 📈 EXPECTED RESULTS:

### Training Metrics
```
R1 Baseline (LoRA):
  - Loss: 2.5 → 0.8
  - Time: 1 hour
  - Quality: Baseline

R2 Target (FullFinetune):
  - Loss: 2.5 → 0.6-0.7 ✅
  - Time: 3-4 hours
  - Quality: +15-25% on legal/financial QA
```

### Model Output
```
Location: /outputs/r2_qwen3_30b_finetuned/
Files:
  - config.json (1 KB)
  - model.safetensors (62 GB) ← The trained model
  - tokenizer.json (1 MB)
  - training_args.bin (3 KB)

Ready for immediate inference/deployment
```

---

## 🔍 HOW TO USE EACH FILE:

### `setup_r2_gpu.sh`
```
What: Installation script
How: Claude Code runs automatically
Time: 15-25 minutes
Does: 
  - Installs ROCm drivers
  - Installs PyTorch 2.3.0
  - Installs DeepSpeed, Flash-Attention, BitsAndBytes
  - Verifies all dependencies
```

### `requirements_r2_finetune.txt`
```
What: Python package list
How: Read by setup_r2_gpu.sh
Contains:
  - PyTorch ecosystem
  - Training optimizers (DeepSpeed, BitsAndBytes)
  - Monitoring tools (Weights & Biases, TensorBoard)
```

### `finetune_qwen3_30b_r2.py`
```
What: Main training script
How: Claude Code executes this after setup
Does:
  - Loads dataset from /data/
  - Loads Qwen3-30B model from HF
  - Runs FullFinetune (all 30B parameters)
  - Uses DeepSpeed ZeRO-2 for memory efficiency
  - Uses Flash-Attention-2 for speed
  - Evaluates after each epoch
  - Saves model to /outputs/
```

### `r2_finetune_notebook.ipynb`
```
What: Alternative Jupyter notebook version
How: Manual execution (if you prefer step-by-step)
Identical to: finetune_qwen3_30b_r2.py
Use if: You want to see each step individually
Note: Claude Code will use the .py script for automation
```

### `R2_QUICK_START.md`
```
What: Quick reference guide
Use for: Manual commands if Claude Code disconnects
Contains:
  - Step-by-step execution
  - Troubleshooting
  - Manual monitoring commands
```

### `CLAUDE_CODE_MASTER_PROMPT.md`
```
What: Instructions for Claude Code
Who reads it: Claude Code (you don't)
Contains:
  - All commands Claude Code will execute
  - Error handling procedures
  - Success metrics
  - Timeline estimates
```

### `DEPLOYMENT_CHECKLIST.md`
```
What: Pre-flight verification
When: Before giving Claude Code the prompt
Do:
  - Verify GPU is created
  - Verify SSH key is set up
  - Verify dataset is uploaded
  - Verify all files exist
  - Fill out the checklist
Only then: Give Claude Code the prompt
```

### `MONITORING_DASHBOARD.md`
```
What: What metrics Claude Code will track
Reference: When reading Claude Code's 30-min reports
Shows:
  - Expected temperature ranges
  - Expected loss curves
  - Alert thresholds
  - Anomaly descriptions
```

---

## 🎯 YOUR EXACT WORKFLOW:

```
DAY 1:
  T+0:00    Create GPU in DigitalOcean
  T+0:05    Add SSH key to GPU
  T+0:10    Upload dataset to GPU /data/
  T+0:15    Fill out DEPLOYMENT_CHECKLIST.md
  T+0:20    ✅ Ready to execute

DAY 1-2:
  T+0:20    Give Claude Code the prompt + GPU IP
  T+0:25    Claude Code SSH into GPU
  T+0:35    Claude Code runs setup
  T+1:00    Setup complete, model downloading
  T+1:10    Training begins (Epoch 1)
  T+1:40    First 30-min report from Claude Code
  T+2:10    Second report
  ...
  T+4:30    Training complete
  T+4:45    Claude Code reports success ✅

DAY 2:
  Download model from GPU to your machine (optional)
  Test inference locally
  Push to Hugging Face (optional)
```

---

## 🚨 ERROR HANDLING:

### Claude Code will automatically handle:

```
❌ OOM (Out of Memory)
   → Reduce batch_size from 2 to 1
   → Resume from checkpoint
   → No user action needed

❌ GPU Disconnect
   → Wait 30 seconds, reconnect
   → Resume from checkpoint
   → Continue training

❌ Network Timeout
   → Retry model download (up to 3 times)
   → Resume training
   → No user action needed

❌ Training Loss NaN
   → Load from last checkpoint
   → Reduce learning rate
   → Retry

⚠️ GPU Temperature > 85°C
   → Reduce batch size automatically
   → Alert user in report
   → Continue (slower but safe)
```

### If Claude Code is stuck:
```
Check: Latest report status
Action: Read MONITORING_DASHBOARD.md to understand metrics
Manual override: Use R2_QUICK_START.md to resume manually
```

---

## 📞 WHAT TO DO IF SOMETHING GOES WRONG:

### Problem: "SSH Connection refused"
```
Solution: 
  1. Verify GPU IP is correct
  2. Verify SSH key path is correct
  3. Wait 2 minutes (GPU may still be booting)
  4. Try again
```

### Problem: "Dataset not found"
```
Solution:
  1. SSH into GPU manually: ssh -i atlas_r2_key root@[IP]
  2. Upload dataset: scp atlas_training_dataset.jsonl root@[IP]:/data/
  3. Verify: ssh root@[IP] "ls -lh /data/atlas_training_dataset.jsonl"
  4. Resume Claude Code
```

### Problem: "Training loss NaN"
```
Normal because: Floating point arithmetic edge case
Claude Code will: Load from checkpoint and continue
Your job: Wait for next report, should recover
```

### Problem: "GPU runs out of memory"
```
Claude Code will: Reduce batch_size automatically
Time impact: +30-45 minutes
Your job: Monitor report, should complete successfully
```

---

## ✅ SUCCESS CHECKLIST:

Training succeeded when you see:

```
✅ Final report shows:
   - Training loss: 0.6-0.7
   - Validation loss: 0.7-0.9
   - All 3 epochs completed
   - Model files saved: config.json, model.safetensors, tokenizer.json
   - Size: 62 GB
   - Training time: ~4 hours
   - No errors reported
```

---

## 🎓 NEXT STEPS AFTER R2 COMPLETES:

### Immediate (1-2 hours)
```
1. Download model from GPU to local machine
2. Test inference locally
3. Document improvements vs R1
```

### Short-term (1-2 days)
```
1. Quantize model to 8-bit (62GB → 8GB) for faster inference
2. Push model to Hugging Face (optional)
3. Benchmark vs R1 on test set
```

### Medium-term (1-2 weeks)
```
1. R2.5: Quantize and optimize
2. R3: Train Qwen3-8B-Financial using R2's knowledge
3. R4+: Train other models (LLaMA, Mistral, Phi)
```

---

## 📚 REFERENCE DOCUMENTS:

Read these in order:
1. **DEPLOYMENT_CHECKLIST.md** ← Do this FIRST (before giving Claude Code prompt)
2. **CLAUDE_CODE_MASTER_PROMPT.md** ← Claude Code reads this
3. **MONITORING_DASHBOARD.md** ← Reference when reading 30-min reports
4. **R2_QUICK_START.md** ← If you need to manually intervene

---

## 🎉 YOU'RE ALL SET!

Everything is ready. Claude Code will handle the entire training pipeline.

**Your only job:** 
1. Create GPU
2. Upload dataset
3. Fill out checklist
4. Give Claude Code the prompt

**Then watch the magic happen.** 🚀✨

---

**Questions? Check the relevant MD file for that section.**

**Ready to execute? Go to DEPLOYMENT_CHECKLIST.md**
