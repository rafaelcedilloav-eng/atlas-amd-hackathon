# ATLAS 3-Phase Fine-Tuning Progress Checklist

**Print this page or keep it open while training runs.**

---

## PRE-TRAINING (Day 0)

- [ ] GPU server opened and SSH access confirmed
- [ ] Repository cloned to `/home/atlas-user/atlas`
- [ ] Datasets copied to `/data/`
  - [ ] `/data/atlas_training_dataset_final.jsonl` (6,437 records)
  - [ ] `/data/atlas_audit_master_unified.jsonl` (3,502 records)
- [ ] Validation script executed: `bash Trainning_Steps/validation_pre_training.sh`
  - [ ] All checks PASS (no [FAIL] items)
  - [ ] GPU detected (MI300X with 205GB VRAM)
  - [ ] All Python packages installed
  - [ ] Datasets verified
  - [ ] Output directories created

**Estimated time:** 5-10 minutes
**Status:** ______________________

---

## PHASE 1: Parallel Qwen3-14B + Mistral-7B (6,437 records)

**Start time:** ___________ (Date/Time)

### Execution

- [ ] Validation passed
- [ ] Phase 1 started: `bash Trainning_Steps/launch_phase1_parallel.sh`
- [ ] Both processes spawned:
  - [ ] Qwen3-14B (PID: _______) - Process 1
  - [ ] Mistral-7B (PID: _______) - Process 2

### Monitoring (watch during training)

- [ ] GPU memory usage stable (should show 150-180GB in use)
- [ ] Both processes show training loss decreasing
- [ ] No CUDA out-of-memory errors
- [ ] No GPU kernel crashes

**Check with:**
```bash
watch -n 1 'rocm-smi --showmeminfo'
tail -f logs/phase1_*/qwen3_14b.log
tail -f logs/phase1_*/mistral_7b.log
```

### Completion

- [ ] Qwen3-14B training completed
  - [ ] No errors in final output
  - [ ] Output saved to: `/outputs/atlas_qwen3_14b_finetuned/`
  - [ ] Final eval loss: __________ (note actual value)
  
- [ ] Mistral-7B training completed
  - [ ] No errors in final output
  - [ ] Output saved to: `/outputs/atlas_mistral_7b_finetuned/`
  - [ ] Final eval loss: __________ (note actual value)

**End time:** ___________ (Date/Time)
**Duration:** ~8 hours (Qwen + Mistral parallel)
**Status:** ______________________

**Verification:**
```bash
ls -lah /outputs/atlas_qwen3_14b_finetuned/    # Should show model files
ls -lah /outputs/atlas_mistral_7b_finetuned/   # Should show model files
```

---

## PHASE 2: Sequential DeepSeek-R1-8B (6,437 records)

**Start time:** ___________ (Date/Time)
*(Usually ~8 hours after Phase 1 starts)*

### Execution

- [ ] Phase 1 fully completed (both models finished)
- [ ] GPU memory cleared from Phase 1
- [ ] Phase 2 started: `python3 Trainning_Steps/finetune_deepseek_r1_8b.py`
- [ ] DeepSeek process spawned (PID: _________)

### Monitoring (watch during training)

- [ ] GPU memory usage shows ~100-120GB (normal for DeepSeek)
- [ ] Training loss decreasing over epochs
- [ ] No out-of-memory errors
- [ ] System RAM usage stable (check: `free -h`)

**Check with:**
```bash
tail -f logs/phase2_*/deepseek_r1_8b.log
watch -n 1 'rocm-smi --showmeminfo'
```

### Completion

- [ ] DeepSeek-R1-8B training completed
  - [ ] No errors in final output
  - [ ] Output saved to: `/outputs/atlas_deepseek_r1_8b/`
  - [ ] Final eval loss: __________ (note actual value)

**End time:** ___________ (Date/Time)
**Duration:** ~10-12 hours
**Status:** ______________________

**Verification:**
```bash
ls -lah /outputs/atlas_deepseek_r1_8b/    # Should show model files
```

---

## PHASE 3: Optional (All 3 Models on 3,502 records)

⚠️ **OPTIONAL** - Only run if you want to further fine-tune on condensed dataset

**Start time:** ___________ (Date/Time)
*(Usually ~20 hours after overall start)*

- [ ] Phase 2 fully completed
- [ ] Decision made: YES, run Phase 3 / NO, skip Phase 3

### If YES:

- [ ] Phase 3 started: `bash Trainning_Steps/launch_phase3_all_models.sh`

**Sub-phases (sequential):**

- [ ] 3.1 Qwen3-14B on 3,502 records
  - [ ] Started
  - [ ] Completed (Final eval loss: _________)
  - [ ] Duration: ~3-4 hours

- [ ] 3.2 Mistral-7B on 3,502 records
  - [ ] Started
  - [ ] Completed (Final eval loss: _________)
  - [ ] Duration: ~2-3 hours

- [ ] 3.3 DeepSeek-R1-8B on 3,502 records
  - [ ] Started
  - [ ] Completed (Final eval loss: _________)
  - [ ] Duration: ~4-5 hours

**End time (if Phase 3 run):** ___________ (Date/Time)
**Duration:** ~12 hours sequential
**Status:** ______________________

---

## POST-TRAINING DEPLOYMENT

### Model Verification

- [ ] All output directories exist:
  - [ ] `/outputs/atlas_qwen3_14b_finetuned/`
  - [ ] `/outputs/atlas_mistral_7b_finetuned/`
  - [ ] `/outputs/atlas_deepseek_r1_8b/`

**Check with:**
```bash
du -sh /outputs/atlas_*_finetuned/
```

Expected sizes:
- Qwen: ~28-32 GB
- Mistral: ~14-18 GB
- DeepSeek: ~16-20 GB

- [ ] Each directory contains:
  - [ ] `config.json`
  - [ ] `pytorch_model.bin` (or `.safetensors`)
  - [ ] `tokenizer.json` or `tokenizer_config.json`
  - [ ] `training_args.bin`

### Backup & Deployment Prep

- [ ] Models backed up to external storage (if available)
- [ ] Permissions set correctly:
  ```bash
  chmod -R 755 /outputs/atlas_*_finetuned/
  ```
- [ ] Copy to Motor 8000 location:
  ```bash
  cp -r /outputs/atlas_deepseek_r1_8b /motor_8000/models/
  cp -r /outputs/atlas_qwen3_14b_finetuned /motor_8000/models/
  ```

### Integration Testing

- [ ] Motor 8000 restarted with new models
- [ ] Model loading verification:
  ```bash
  python3 -c "from transformers import AutoTokenizer; \
    AutoTokenizer.from_pretrained('/motor_8000/models/atlas_deepseek_r1_8b')"
  ```
- [ ] Pipeline test passed:
  ```bash
  curl -X POST http://localhost:8000/api/pipeline \
    -H "Content-Type: application/json" \
    -d '{"pdf_path": "test.pdf", "audit_id": "test-001"}'
  ```
- [ ] X-Ray panel shows all 5 agents in event stream
- [ ] Inference latency acceptable (< 5 seconds per 500 tokens)

**Test result:** ______________________

### Final Sign-Off

- [ ] Phase 1 complete and verified
- [ ] Phase 2 complete and verified
- [ ] Phase 3 complete (if run) and verified
- [ ] All models deployed to Motor 8000
- [ ] Integration tests passed
- [ ] Ready for production deployment

**Overall Status:** ______________________

**Training completed on:** ___________ (Date/Time)

**Total time spent:**
- Phase 1: _____ hours
- Phase 2: _____ hours
- Phase 3: _____ hours (if run)
- **Total: _____ hours**

---

## QUICK METRICS

### Final Training Loss Values

| Model | Phase 1 Dataset | Phase 1 Loss | Phase 3 Dataset | Phase 3 Loss |
|-------|-----------------|--------------|-----------------|--------------|
| Qwen3-14B | 6,437 | __________ | 3,502 | __________ |
| Mistral-7B | 6,437 | __________ | 3,502 | __________ |
| DeepSeek-R1 | 6,437 | __________ | 3,502 | __________ |

### Performance Notes

GPU Peak Memory: ___________ GB
Training Stability: [ ] Excellent  [ ] Good  [ ] OK  [ ] Issues
Errors Encountered: [ ] None  [ ] Minor  [ ] Major

### Issues Log

If any issues occurred, document them here:

```
Issue 1: 
Resolution:

Issue 2:
Resolution:

Issue 3:
Resolution:
```

---

## CONTACTS & RESOURCES

**If you encounter issues:**

1. Check `training_commands_all_phases.txt` for troubleshooting section
2. Monitor with: `rocm-smi`, `htop`, `free -h`
3. Check logs in: `logs/phase{1,2,3}_*/`

**Key files location:**
- Training scripts: `Trainning_Steps/`
- Datasets: `/data/`
- Models: `/outputs/`
- Logs: `logs/`

---

**Generated:** 2026-05-05
**Last Updated:** __________

