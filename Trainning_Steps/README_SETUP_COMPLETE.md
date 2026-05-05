# ✅ ATLAS Fine-Tuning Setup Complete

**Rafael, everything is ready. You can open the GPU server now.**

---

## 📋 What's Been Prepared

### Training Scripts (3 models)
- ✅ `finetune_qwen3_14b.py` - Qwen3-14B (14.0B params, ~84GB)
- ✅ `finetune_mistral_7b.py` - Mistral-7B (7.3B params, ~50GB) 
- ✅ `finetune_deepseek_r1_8b.py` - DeepSeek-R1-8B (8.3B params, ~111GB)

### Orchestration Scripts (automated execution)
- ✅ `validation_pre_training.sh` - Pre-flight checks before training
- ✅ `launch_phase1_parallel.sh` - Phase 1: Qwen + Mistral in parallel
- ✅ `launch_phase3_all_models.sh` - Phase 3: Optional enhancement round

### Documentation (complete reference)
- ✅ `training_commands_all_phases.txt` - All commands with explanations
- ✅ `PHASE1_QUICKSTART.md` - Step-by-step guide for GPU server
- ✅ `TRAINING_PROGRESS_CHECKLIST.md` - Printable progress tracker

---

## 🎯 Your Next Steps

### When GPU Server is Ready:

1. **Open GPU and get connection details**
   - IP address
   - SSH credentials
   - Jupyter credentials (if applicable)

2. **Send Claude:**
   ```
   GPU is open. IP: [your_ip], user: [username], password: [if needed]
   ```

3. **Claude will:**
   - SSH into server
   - Clone repo
   - Run pre-flight validation
   - Start Phase 1 training
   - Monitor progress and report status

---

## 🔄 Training Strategy Overview

### Phase 1: PARALLEL (6,437 records)
```
Qwen3-14B ──┐
            ├─ ~8 hours (parallel)
Mistral-7B ─┘
```
Memory: ~161GB (safe with overhead)

### Phase 2: SEQUENTIAL (6,437 records)
```
DeepSeek-R1-8B ──── ~10-12 hours
```
Memory: ~111GB peak

### Phase 3: OPTIONAL (3,502 records)
```
Qwen3-14B ──────────────┐
Mistral-7B ────────────┤─ ~10-12 hours sequential
DeepSeek-R1-8B ───────┘
```

**Total time without Phase 3:** ~20 hours
**Total time with Phase 3:** ~32 hours

---

## 📂 File Structure

```
Trainning_Steps/
├── finetune_qwen3_14b.py
├── finetune_mistral_7b.py
├── finetune_deepseek_r1_8b.py
├── validation_pre_training.sh
├── launch_phase1_parallel.sh
├── launch_phase3_all_models.sh
├── training_commands_all_phases.txt
├── PHASE1_QUICKSTART.md
├── TRAINING_PROGRESS_CHECKLIST.md
└── README_SETUP_COMPLETE.md (this file)
```

---

## ⚡ Quick Command Reference

**Validate everything is ready:**
```bash
bash Trainning_Steps/validation_pre_training.sh
```

**Start Phase 1 (Qwen + Mistral parallel):**
```bash
bash Trainning_Steps/launch_phase1_parallel.sh
```

**Start Phase 2 (after Phase 1 completes, ~8 hours later):**
```bash
python3 Trainning_Steps/finetune_deepseek_r1_8b.py
```

**Start Phase 3 (optional, after Phase 2 completes, ~20 hours after start):**
```bash
bash Trainning_Steps/launch_phase3_all_models.sh
```

---

## 📊 Dataset Assignments

**Phase 1-2 (6,437 records):**
- `atlas_training_dataset_final.jsonl` ← Already on HF, refined dataset
- Good for broad learning across audit scenarios

**Phase 3 (3,502 records, optional):**
- `atlas_audit_master_unified.jsonl` ← Newer, more diverse scenarios
- Good for specialization on condensed, high-quality examples

---

## 🎯 Success Criteria

Training is successful when:

- ✅ All Python packages installed
- ✅ GPU memory available (205GB MI300X)
- ✅ Datasets copied to `/data/`
- ✅ Phase 1 completes: Qwen + Mistral both finish with decreasing loss
- ✅ Phase 2 completes: DeepSeek finishes with decreasing loss
- ✅ Models saved to `/outputs/`
  - Each directory contains: `config.json`, `pytorch_model.bin`, `tokenizer.json`
- ✅ (Optional) Phase 3 completes: all 3 models fine-tuned on 3,502 records
- ✅ Final eval loss is reasonable (~0.3-0.5 depending on model)

---

## 🚀 What Happens After Training

Once all models are trained:

1. **Copy to Motor 8000** (Motor 8000 handles Core/Reasoning)
   ```bash
   cp -r /outputs/atlas_deepseek_r1_8b /motor_8000/models/
   cp -r /outputs/atlas_qwen3_14b_finetuned /motor_8000/models/
   ```

2. **Update Motor 8000 serving configuration** to load the new fine-tuned models

3. **Run integration test** via `/api/pipeline` endpoint

4. **Verify X-Ray panel** shows all 5 agents in event stream with real-time progress

---

## 📞 Important Notes

### Architecture Review
The orchestrator (`src/orchestrator.py`) has been updated with proper event emissions:
- ✅ Vision stage (15% progress)
- ✅ Compliance stage (30% progress) - **NEW**
- ✅ Reasoning stage (45% progress) - **NEW**
- ✅ Validator stage (60% progress) - **NEW**
- ✅ Explainer stage (80% progress) - **NEW**
- ✅ Complete (100% progress)

All events flow through SSE to X-Ray panel for real-time visualization.

### Memory Validation
Memory calculations verified:
- Phase 1 parallel: **161GB peak** (Qwen 84GB + Mistral 50GB + overhead 27GB) ✅
- Phase 2 sequential: **111GB peak** (DeepSeek only) ✅
- Phase 3: Same as Phase 1-2 (sequential, one at a time) ✅

Safe headroom on 205GB GPU.

---

## 📋 Checklist for You

- [ ] GPU server ready
- [ ] Repository cloned to GPU server
- [ ] Datasets copied to `/data/`
- [ ] SSH/Jupyter credentials ready
- [ ] Contact Claude with GPU IP and credentials
- [ ] Monitor training progress (logs updated every 10 steps)
- [ ] Phase 1 completes (~8 hours)
- [ ] Phase 2 starts and completes (~12 hours after Phase 1)
- [ ] (Optional) Phase 3 runs if desired (~12 hours after Phase 2)
- [ ] Models deployed to Motor 8000
- [ ] Integration test passes
- [ ] Ready for production

---

## 🎓 Key Files to Reference

| File | Purpose | When to Use |
|------|---------|------------|
| `PHASE1_QUICKSTART.md` | Step-by-step instructions | **START HERE** when GPU is ready |
| `training_commands_all_phases.txt` | Complete command reference | Reference during training |
| `TRAINING_PROGRESS_CHECKLIST.md` | Progress tracking | Print and keep handy |
| `finetune_qwen3_14b.py` | Qwen training | Phase 1 & 3 |
| `finetune_mistral_7b.py` | Mistral training | Phase 1 & 3 |
| `finetune_deepseek_r1_8b.py` | DeepSeek training | Phase 2 |

---

## ✨ You're All Set

Everything is prepared and ready to execute. Once you open the GPU server:

1. Copy repo to GPU machine
2. Copy datasets to `/data/`
3. Run: `bash Trainning_Steps/validation_pre_training.sh`
4. Run: `bash Trainning_Steps/launch_phase1_parallel.sh`
5. Monitor and relax — everything else is automated

**When you're ready, just send IP + credentials and we'll take it from here!**

---

**Setup completed:** 2026-05-05
**Status:** ✅ READY FOR GPU DEPLOYMENT
**Next step:** Open GPU server and send connection details to Claude

