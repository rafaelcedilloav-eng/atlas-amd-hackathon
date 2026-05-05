# ATLAS Phase 1 Quick Start Guide

**GPU Server Ready? You have everything set up. Follow these steps.**

---

## ✓ What's Already Prepared

- ✓ `finetune_qwen3_14b.py` - Qwen3-14B training script (14.0B params, ~84GB)
- ✓ `finetune_mistral_7b.py` - Mistral-7B training script (7.3B params, ~50GB)
- ✓ `finetune_deepseek_r1_8b.py` - DeepSeek-R1 training script (8.3B params, ~111GB)
- ✓ `validation_pre_training.sh` - Pre-flight checks
- ✓ `launch_phase1_parallel.sh` - Automated orchestration for Phase 1
- ✓ `launch_phase3_all_models.sh` - Optional Phase 3 (3,502 records)
- ✓ `training_commands_all_phases.txt` - Complete reference

---

## 🚀 Step-by-Step Execution

### Step 1: Copy This Repo to GPU Server

```bash
# On GPU server
git clone <ATLAS_REPO_URL> /home/atlas-user/atlas
cd /home/atlas-user/atlas
```

### Step 2: Copy Datasets to /data

```bash
# Datasets should be at:
# /data/atlas_training_dataset_final.jsonl (6,437 records) - FOR PHASE 1-2
# /data/atlas_audit_master_unified.jsonl (3,502 records) - FOR PHASE 3

# If not copied, do it now:
cp /source/path/atlas_training_dataset_final.jsonl /data/
cp /source/path/atlas_audit_master_unified.jsonl /data/

# Verify:
ls -lh /data/*.jsonl
```

### Step 3: Run Pre-Flight Validation

```bash
bash Trainning_Steps/validation_pre_training.sh
```

**Expected output:**
```
[PASS] AMD GPU detected (MI300X)
[PASS] VRAM sufficient (205+ GB available)
[PASS] torch installed
[PASS] transformers installed
[PASS] datasets installed
[PASS] peft installed
[PASS] scipy installed
[PASS] Dataset 1 found: /data/atlas_training_dataset_final.jsonl (6437 records)
[PASS] Dataset 2 found: /data/atlas_audit_master_unified.jsonl (3502 records)
...
All checks passed! Ready to start training.
```

**If validation fails:** Fix issues and retry. Do not proceed until all checks pass.

### Step 4: Start Phase 1 (Parallel Qwen + Mistral)

```bash
# Option A: Automatic orchestration (RECOMMENDED)
bash Trainning_Steps/launch_phase1_parallel.sh

# Option B: Manual execution (if needed)
# Terminal 1:
python3 Trainning_Steps/finetune_qwen3_14b.py

# Terminal 2 (after 30 seconds):
python3 Trainning_Steps/finetune_mistral_7b.py
```

**Expected duration:** 6-8 hours each (parallel = ~8 hours total)

**What to expect:**
```
============================================================
  ATLAS PHASE 1: PARALLEL QWEN + MISTRAL
  Dataset: atlas_training_dataset_final.jsonl (6,437 records)
============================================================

[START] Qwen3-14B fine-tuning (Motor 8000)...
  PID: 12345

[START] Mistral-7B fine-tuning (Motor 8000)...
  PID: 12346

[MONITOR] Waiting for both training jobs to complete...
[✓] Qwen3-14B training completed (PID: 12345)
[✓] Mistral-7B training completed (PID: 12346)
```

**Monitor progress:**
```bash
# Real-time GPU usage
watch -n 1 'rocm-smi --showmeminfo'

# Real-time training loss (in separate window)
tail -f logs/phase1_*/qwen3_14b.log | grep "loss"
tail -f logs/phase1_*/mistral_7b.log | grep "loss"
```

### Step 5: Start Phase 2 (DeepSeek)

**Run AFTER Phase 1 completes (after ~8 hours)**

```bash
python3 Trainning_Steps/finetune_deepseek_r1_8b.py
```

**Expected duration:** 10-12 hours

**Monitor:**
```bash
tail -f logs/phase2_*/deepseek_r1_8b.log | grep "loss"
watch -n 1 'rocm-smi --showmeminfo'
```

### Step 6 (Optional): Start Phase 3 (All 3 Models on 3,502 Records)

**Run AFTER Phase 2 completes (optional enhancement)**

```bash
bash Trainning_Steps/launch_phase3_all_models.sh
```

**Expected duration:** ~10-12 hours sequential

---

## 📊 Timeline

| Phase | Models | Records | Duration | Start Time | End Time |
|-------|--------|---------|----------|-----------|----------|
| Validation | - | - | 5 min | Hour 0:00 | Hour 0:05 |
| Phase 1 | Qwen + Mistral (parallel) | 6,437 | ~8 hours | Hour 0:05 | Hour 8:05 |
| Phase 2 | DeepSeek | 6,437 | ~12 hours | Hour 8:05 | Hour 20:05 |
| **Phase 3** | **All 3 (optional)** | **3,502** | **~12 hours** | **Hour 20:05** | **Hour 32:05** |

**Without Phase 3:** ~20 hours total
**With Phase 3:** ~32 hours total

---

## ⚠️ Troubleshooting

### "rocm-smi not found"
Your ROCm installation is incomplete. Install with:
```bash
apt-get update && apt-get install rocm-core rocm-opencl
```

### "VRAM insufficient"
If you have less than 205GB:
- Phase 1 can still run (need ~161GB)
- Reduce `batch_size_per_gpu` from 4 to 2 in scripts
- Or run Phase 1 sequentially (not parallel)

### Training crashes mid-way
Check GPU memory:
```bash
rocm-smi --showmeminfo
free -h  # System RAM
```

Restart and try with lower batch size.

### Models not found after training
Check output directories exist:
```bash
ls -lah /outputs/atlas_*_finetuned/
```

Should see: `config.json`, `pytorch_model.bin`, `tokenizer.json`, `training_args.bin`

---

## ✅ After Training Complete

When all phases finish:

1. **Verify models exist:**
   ```bash
   du -sh /outputs/atlas_*_finetuned/
   ```

2. **Copy to deployment location** (Motor 8000):
   ```bash
   cp -r /outputs/atlas_deepseek_r1_8b /motor_8000/models/
   cp -r /outputs/atlas_qwen3_14b_finetuned /motor_8000/models/
   cp -r /outputs/atlas_mistral_7b_finetuned /model_backup/
   ```

3. **Run integration test:**
   ```bash
   # Full pipeline test
   curl -X POST http://localhost:8000/api/pipeline \
     -H "Content-Type: application/json" \
     -d '{"pdf_path": "test.pdf", "audit_id": "test-001"}'
   ```

4. **Notify platform team:** Models ready for deployment

---

## 📞 Quick Reference

| Command | Purpose |
|---------|---------|
| `bash Trainning_Steps/validation_pre_training.sh` | Pre-flight checks |
| `bash Trainning_Steps/launch_phase1_parallel.sh` | Phase 1 auto-orchestration |
| `python3 Trainning_Steps/finetune_qwen3_14b.py` | Qwen training (manual) |
| `python3 Trainning_Steps/finetune_mistral_7b.py` | Mistral training (manual) |
| `python3 Trainning_Steps/finetune_deepseek_r1_8b.py` | DeepSeek training |
| `bash Trainning_Steps/launch_phase3_all_models.sh` | Phase 3 all models |
| `watch -n 1 'rocm-smi --showmeminfo'` | Monitor GPU in real-time |
| `tail -f logs/phase*/*.log` | Watch training loss |

---

## 📝 Files Location

All training scripts are in: `Trainning_Steps/`

```
Trainning_Steps/
├── finetune_qwen3_14b.py           ← Qwen training script
├── finetune_mistral_7b.py          ← Mistral training script  
├── finetune_deepseek_r1_8b.py      ← DeepSeek training script
├── validation_pre_training.sh       ← Pre-flight checks
├── launch_phase1_parallel.sh        ← Phase 1 orchestration
├── launch_phase3_all_models.sh      ← Phase 3 orchestration
├── training_commands_all_phases.txt ← Complete reference
└── PHASE1_QUICKSTART.md            ← This file
```

Datasets: `/data/atlas_training_dataset_final.jsonl` (6,437 records)
          `/data/atlas_audit_master_unified.jsonl` (3,502 records)

Outputs: `/outputs/atlas_qwen3_14b_finetuned/`
         `/outputs/atlas_mistral_7b_finetuned/`
         `/outputs/atlas_deepseek_r1_8b/`

Logs: `logs/phase{1,2,3}_TIMESTAMP/`

---

**Ready? Run validation first, then Phase 1!**

```bash
cd /home/atlas-user/atlas
bash Trainning_Steps/validation_pre_training.sh
# If all pass:
bash Trainning_Steps/launch_phase1_parallel.sh
```

Good luck! 🚀
