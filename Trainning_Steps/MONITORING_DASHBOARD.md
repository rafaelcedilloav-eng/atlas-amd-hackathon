# ATLAS R2 — GPU MONITORING DASHBOARD
## Real-time metrics Claude Code will track

---

## CLAUDE CODE WILL MONITOR THESE METRICS EVERY 30 MINUTES:

### GPU Health
```
rocm-smi --showtemp --showuse --showmeminfo=vram

Output parsed:
├─ Temperature: XX°C (target: < 75°C, critical: > 85°C)
├─ GPU Utilization: XX% (target: > 80%)
├─ Memory Used: XXX GB / 192 GB (target: 170-190 GB during training)
└─ Memory Temperature: XX°C
```

### Training Metrics
```
From training logs:
├─ Training Loss: X.XXXX (should decrease every epoch)
├─ Validation Loss: X.XXXX (should match training loss ±0.1)
├─ Current Epoch: X/3
├─ Current Step: XXX/XXXX
├─ Learning Rate: 5e-5 (constant)
└─ Gradient Norm: X.X (should stay < 1.0)
```

### System Resources
```
From server:
├─ Disk Usage: XXX GB / YYY GB available
├─ CPU Usage: XX%
├─ Network (HF download): XX MB/s
├─ ROCm Version: 6.2.0 or 7.0
└─ PyTorch Version: 2.3.0 or 2.6.0
```

---

## SAMPLE OUTPUT — WHAT YOU'LL SEE:

```
╔══════════════════════════════════════════════════════════════╗
║         ATLAS R2 TRAINING — Status Report                    ║
║         Timestamp: 2026-05-05 14:30:45 UTC                  ║
╚══════════════════════════════════════════════════════════════╝

GPU Status:
  ├─ Temperature: 62°C ✅ (Normal)
  ├─ Utilization: 92% ✅ (Excellent)
  ├─ Memory: 182 GB / 192 GB ✅ (Healthy)
  └─ Health: ✅ All systems nominal

Training Progress:
  ├─ Epoch: 1/3 (33%)
  ├─ Step: 245/2145 (11%)
  ├─ Training Loss: 1.8742 ⬇️ (decreasing)
  ├─ Validation Loss: 1.9103 ✅ (tracking well)
  ├─ Learning Rate: 5.0e-05 📌 (stable)
  └─ Gradient Norm: 0.87 ✅ (healthy)

Performance:
  ├─ Tokens/sec: 1245 🚀 (excellent)
  ├─ Steps/min: 3.2
  ├─ Est. time/epoch: 45 minutes
  └─ Total ETA: 2h 15m remaining

System:
  ├─ Disk Used: 125 GB / 200 GB ✅
  ├─ CPU Load: 14% ✅
  ├─ Network: 45 MB/s (model weights)
  └─ Uptime: 45 minutes

Next Report: 2026-05-05 15:00:45 UTC ⏰
```

---

## EXPECTED METRICS BY PHASE:

### Phase 1: Setup (First 30 min)
```
GPU Temp: Ramping up 30°C → 50°C ✅
GPU Util: 0% (installing dependencies) ✅
Memory: Increasing as packages install ✅
Training Loss: N/A (not started yet)
Status: Setup in progress — Normal
```

### Phase 2: Model Download (30-50 min)
```
GPU Temp: 45-55°C ✅
GPU Util: 0-10% (downloading 32.5 GB) ✅
Memory: Increasing as model loads ✅
Network: 40-80 MB/s (downloading model)
Status: Model loading — Normal, may show "Downloading..." for 15-20 min
```

### Phase 3: Epoch 1 (50 min - 2h)
```
GPU Temp: 60-70°C ✅
GPU Util: 85-95% ✅
Memory: 170-185 GB (stable)
Training Loss: 2.5 → 1.8 ✅ (decreasing rapidly)
Val Loss: ~2.0 ✅ (tracking training loss)
Status: Training — Everything normal
```

### Phase 4: Epoch 2 (2h - 3h 45m)
```
GPU Temp: 65-72°C ✅
GPU Util: 90-95% ✅
Memory: 180-190 GB ✅
Training Loss: 1.8 → 1.2 ✅ (still decreasing)
Val Loss: ~1.3 ✅
Status: Training — On track
```

### Phase 5: Epoch 3 (3h 45m - 4h 30m)
```
GPU Temp: 68-73°C ✅
GPU Util: 90-95% ✅
Memory: 185-190 GB ✅
Training Loss: 1.2 → 0.8 ✅ (good convergence)
Val Loss: ~0.9 ✅
Status: Training — Final epoch, performance excellent
```

### Phase 6: Post-Training (4h 30m - 4h 45m)
```
GPU Temp: Dropping 70°C → 50°C ✅
GPU Util: 0% (evaluation only)
Memory: Stable at 100 GB (saving model)
Training Loss: Final = 0.8 ✅
Val Loss: Final = 0.9 ✅
Status: Saving model — Normal
```

---

## ALERT THRESHOLDS CLAUDE CODE MONITORS:

### 🟢 GREEN (All Good)
```
✅ Temperature < 75°C
✅ GPU Utilization > 80%
✅ Memory 160-190 GB (during training)
✅ Training Loss decreasing
✅ No CUDA errors
✅ Network stable
```

### 🟡 YELLOW (Watch)
```
⚠️ Temperature 75-80°C → Reduce batch size
⚠️ GPU Utilization < 70% → Check processes
⚠️ Memory > 190 GB → Could cause swapping
⚠️ Training Loss flat → May resume improvement
⚠️ Network < 10 MB/s → HF API slow, retrying
```

### 🔴 RED (Action Required)
```
❌ Temperature > 85°C → STOP, cool down
❌ GPU Utilization = 0% for 5 min → Training hung
❌ Memory > 192 GB → OOM imminent
❌ Training Loss NaN → Exploding gradients
❌ CUDA Error → Resume from checkpoint
❌ Network timeout → Retry model download
```

---

## LOSS CURVE EXPECTATIONS:

### Training Loss
```
Epoch 1:  2.50 → 1.80 ⬇️⬇️⬇️ (fast drop)
Epoch 2:  1.80 → 1.15 ⬇️⬇️⬇️ (fast drop)
Epoch 3:  1.15 → 0.70 ⬇️⬇️ (slower drop)

Target: 0.6-0.7
Success: Final < 0.7
```

### Validation Loss
```
Epoch 1:  2.10 → 1.95
Epoch 2:  1.95 → 1.35
Epoch 3:  1.35 → 0.85

Should track training loss within ±0.15
If val loss >> train loss: Possible overfitting (but OK for specialization)
```

### GPU Memory Usage
```
Start:     20 GB (model load)
Training:  185 GB (gradients + activations + optimizer states)
Peak:      190 GB (checkpointing artifacts)

Should remain stable — if growing linearly = memory leak
```

---

## HOW TO READ CLAUDE CODE REPORTS:

### Training Speed
```
Current: "3.2 steps/min, 1245 tokens/sec"
This means: Good performance (normal = 2-5 steps/min)
Benchmark: R1 achieved 1.8 steps/min, so R2 FullFinetune is faster due to optimization
```

### Temperature Trends
```
Warming up: 30°C → 70°C (first 30 min, normal)
Stable: 65-72°C (entire training, healthy)
Cooling: 72°C → 50°C (post-training, normal)
```

### Memory Growth
```
Linear growth = Normal (optimizer states, checkpoints)
Exponential growth = Problem, likely memory leak
Sudden jump = Checkpoint saved
Sudden drop = Checkpoint loaded from resume
```

### Loss Plateau Alert
```
If loss stays same for 100 steps: Normal (learning rate adjustment)
If loss same for 500+ steps: Potential issue, reduce LR or restart
If loss increasing: Exploding gradients, reduce batch size
If loss = NaN: Critical, resume from last checkpoint
```

---

## LIVE MONITORING COMMANDS (If you want to manually check):

### SSH into GPU During Training
```bash
ssh -i atlas_r2_key root@[GPU_IP]

# Quick status
rocm-smi --showtemp --showuse

# Full GPU details
rocm-smi --json

# Training logs (last 50 lines)
tail -50 training.log

# Memory details
rocm-smi --showmeminfo=vram

# Process watching
watch -n 1 'rocm-smi --showtemp --showuse'

# Kill training if needed
pkill -f "finetune_qwen3_30b"
```

---

## EXPECTED TIMELINE VISUALIZATION:

```
Time  GPU Temp  GPU Util  Memory    Training Loss  Status
────────────────────────────────────────────────────────────
 0:00   30°C      0%      20GB     ────────────   Setup
15:00   45°C      5%      50GB     ────────────   Installing
30:00   50°C     10%     100GB     ────────────   Model Download
45:00   55°C     50%     160GB     ────────────   Tokenization
50:00   62°C     88%     180GB     2.50 ⬇️⬇️⬇️  Epoch 1
1:30    68°C     92%     185GB     1.80 ⬇️⬇️⬇️  Epoch 1/2
2:00    70°C     94%     188GB     1.30 ⬇️⬇️⬇️  Epoch 2
3:00    71°C     93%     187GB     1.15 ⬇️⬇️   Epoch 2/3
4:00    72°C     91%     186GB     0.95 ⬇️⬇️   Epoch 3
4:30    70°C     10%     150GB     0.70 ✅    Saving Model
4:45    50°C      0%     120GB     ────────────  Complete ✅
```

---

## ANOMALIES TO WATCH FOR:

### Loss Not Decreasing
```
Symptom: Training loss stays at 2.5 after 100 steps
Cause: Learning rate too low / Model not engaging
Fix: Claude Code will continue (loss may resume decreasing)
Timeline: If flat after 500 steps, may need restart
```

### Memory Leak
```
Symptom: GPU Memory 180GB → 189GB → 191GB → OOM
Cause: Checkpoint accumulation / Buffer not freed
Fix: Claude Code stops and resumes from checkpoint
Recovery: Automatic
```

### Temperature Spike
```
Symptom: 65°C → 75°C → 82°C in 2 minutes
Cause: Room temperature / GPU throttling activation
Fix: Claude Code reduces batch size automatically
Impact: +15-30 min training time
```

### CUDA/ROCm Error
```
Error: "RuntimeError: CUDA out of memory"
Cause: OOM triggered
Fix: Claude Code loads from checkpoint, reduces batch size
Recovery: Automatic resumption
```

---

## POST-TRAINING VERIFICATION:

Claude Code will verify:
```bash
# File existence
ls -lh /outputs/r2_qwen3_30b_finetuned/config.json  ✅ 1 KB
ls -lh /outputs/r2_qwen3_30b_finetuned/model.safetensors  ✅ 62 GB
ls -lh /outputs/r2_qwen3_30b_finetuned/tokenizer.json  ✅ 1 MB

# Model integrity
python3 -c "from transformers import AutoModelForCausalLM; \
    AutoModelForCausalLM.from_pretrained('./outputs/r2_qwen3_30b_finetuned')" ✅

# Inference test
python3 << 'EOF'
from transformers import AutoModelForCausalLM, AutoTokenizer
model = AutoModelForCausalLM.from_pretrained(
    "./outputs/r2_qwen3_30b_finetuned"
)
tokenizer = AutoTokenizer.from_pretrained("./outputs/r2_qwen3_30b_finetuned")
prompt = "<system>Eres ATLAS.</system><user>Test</user>"
inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=50)
print(tokenizer.decode(outputs[0]))
EOF
✅ Response generated (model works)
```

---

**Claude Code will automatically track all of this.**

**Your job: Sit back and read the 30-minute status reports.** 🚀

