#!/bin/bash
# ============================================================
# ATLAS Phase 1: Parallel Qwen3-14B + Mistral-7B Training
# Dataset: atlas_training_dataset_final.jsonl (6,437 records)
# Memory: ~161GB total (84GB Qwen + 50GB Mistral + overhead)
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "============================================================"
echo "  ATLAS PHASE 1: PARALLEL QWEN + MISTRAL"
echo "  Dataset: atlas_training_dataset_final.jsonl (6,437 records)"
echo "============================================================"
echo ""

# Check if both training scripts exist
if [ ! -f "Trainning_Steps/finetune_qwen3_14b.py" ]; then
    echo "[ERROR] finetune_qwen3_14b.py not found"
    exit 1
fi

if [ ! -f "Trainning_Steps/finetune_mistral_7b.py" ]; then
    echo "[ERROR] finetune_mistral_7b.py not found"
    exit 1
fi

# Check if dataset exists
if [ ! -f "/data/atlas_training_dataset_final.jsonl" ]; then
    echo "[ERROR] Training dataset not found: /data/atlas_training_dataset_final.jsonl"
    exit 1
fi

# Create output directories
mkdir -p /outputs/atlas_qwen3_14b_finetuned
mkdir -p /outputs/atlas_mistral_7b_finetuned

# Log files
LOG_DIR="logs/phase1_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"
QWEN_LOG="$LOG_DIR/qwen3_14b.log"
MISTRAL_LOG="$LOG_DIR/mistral_7b.log"

echo "[INFO] Starting parallel training..."
echo "[INFO] Logs will be written to:"
echo "  - Qwen3-14B: $QWEN_LOG"
echo "  - Mistral-7B: $MISTRAL_LOG"
echo ""

# Start Qwen3-14B training (non-blocking)
echo "[START] Qwen3-14B fine-tuning (Motor 8000)..."
python3 Trainning_Steps/finetune_qwen3_14b.py > "$QWEN_LOG" 2>&1 &
QWEN_PID=$!
echo "  PID: $QWEN_PID"

# Give Qwen a 30-second head start to avoid memory collision during model load
sleep 30

# Start Mistral-7B training (non-blocking)
echo "[START] Mistral-7B fine-tuning (Motor 8000)..."
python3 Trainning_Steps/finetune_mistral_7b.py > "$MISTRAL_LOG" 2>&1 &
MISTRAL_PID=$!
echo "  PID: $MISTRAL_PID"
echo ""

# Monitor both processes
echo "[MONITOR] Waiting for both training jobs to complete..."
echo "  Type: Ctrl+C to interrupt both processes"
echo ""

QWEN_DONE=0
MISTRAL_DONE=0

while [ $QWEN_DONE -eq 0 ] || [ $MISTRAL_DONE -eq 0 ]; do
    if [ $QWEN_DONE -eq 0 ] && ! kill -0 $QWEN_PID 2>/dev/null; then
        QWEN_DONE=1
        QWEN_EXIT=$(wait $QWEN_PID 2>/dev/null; echo $?)
        if [ $QWEN_EXIT -eq 0 ]; then
            echo "[✓] Qwen3-14B training completed (PID: $QWEN_PID)"
        else
            echo "[✗] Qwen3-14B training failed with exit code $QWEN_EXIT"
        fi
    fi

    if [ $MISTRAL_DONE -eq 0 ] && ! kill -0 $MISTRAL_PID 2>/dev/null; then
        MISTRAL_DONE=1
        MISTRAL_EXIT=$(wait $MISTRAL_PID 2>/dev/null; echo $?)
        if [ $MISTRAL_EXIT -eq 0 ]; then
            echo "[✓] Mistral-7B training completed (PID: $MISTRAL_PID)"
        else
            echo "[✗] Mistral-7B training failed with exit code $MISTRAL_EXIT"
        fi
    fi

    sleep 5
done

echo ""
echo "============================================================"
echo "  PHASE 1 SUMMARY"
echo "============================================================"
echo "Qwen3-14B: /outputs/atlas_qwen3_14b_finetuned/"
echo "Mistral-7B: /outputs/atlas_mistral_7b_finetuned/"
echo ""
echo "Log files: $LOG_DIR"
echo ""

# Check both exist
if [ -d "/outputs/atlas_qwen3_14b_finetuned" ] && [ -d "/outputs/atlas_mistral_7b_finetuned" ]; then
    echo "[✓] Phase 1 complete. Ready for Phase 2."
    echo ""
    echo "Next: python3 Trainning_Steps/finetune_deepseek_r1_8b.py"
    exit 0
else
    echo "[✗] Phase 1 failed - output directories missing"
    exit 1
fi
