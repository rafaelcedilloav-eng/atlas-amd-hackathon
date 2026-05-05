#!/bin/bash
# ============================================================
# ATLAS Phase 3: Sequential All 3 Models (3,502 RECORDS)
# Dataset: atlas_audit_master_unified.jsonl
# OPTIONAL: Only run after Phase 1-2 successfully complete
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "============================================================"
echo "  ATLAS PHASE 3: ALL 3 MODELS ON CONDENSED DATASET"
echo "  Dataset: atlas_audit_master_unified.jsonl (3,502 records)"
echo "============================================================"
echo ""

# Check if dataset exists
if [ ! -f "/data/atlas_audit_master_unified.jsonl" ]; then
    echo "[ERROR] Phase 3 dataset not found: /data/atlas_audit_master_unified.jsonl"
    exit 1
fi

# Verify Phase 1-2 models exist
if [ ! -d "/outputs/atlas_qwen3_14b_finetuned" ]; then
    echo "[WARN] Qwen3-14B from Phase 1 not found. Training fresh copy."
fi

if [ ! -d "/outputs/atlas_mistral_7b_finetuned" ]; then
    echo "[WARN] Mistral-7B from Phase 1 not found. Training fresh copy."
fi

if [ ! -d "/outputs/atlas_deepseek_r1_8b" ]; then
    echo "[WARN] DeepSeek-R1-8B from Phase 2 not found. Training fresh copy."
fi

echo ""
echo "This script will fine-tune all 3 models SEQUENTIALLY on Phase 3 dataset:"
echo "  1. Qwen3-14B (3,502 records) - ~3-4 hours"
echo "  2. Mistral-7B (3,502 records) - ~2-3 hours"
echo "  3. DeepSeek-R1-8B (3,502 records) - ~4-5 hours"
echo ""
echo "Total time: ~10-12 hours sequential"
echo ""
read -p "Continue with Phase 3 training? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

# Log directory
LOG_DIR="logs/phase3_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

echo ""
echo "[INFO] Phase 3 logs: $LOG_DIR"
echo ""

# Helper function to update dataset path in training script
update_dataset() {
    local script=$1
    local dataset=$2
    local temp_script="${script}.tmp"

    # Create modified copy with correct dataset path
    sed "s|/data/atlas_training_dataset_final.jsonl|$dataset|g" "$script" > "$temp_script"
    mv "$temp_script" "$script"
}

# Phase 3.1: Qwen3-14B on 3,502 records
echo "============================================================"
echo "  PHASE 3.1: QWEN3-14B (3,502 RECORDS)"
echo "============================================================"
echo ""

QWEN_LOG="$LOG_DIR/qwen3_14b_phase3.log"
cp Trainning_Steps/finetune_qwen3_14b.py Trainning_Steps/finetune_qwen3_14b_phase3.py
update_dataset "Trainning_Steps/finetune_qwen3_14b_phase3.py" "/data/atlas_audit_master_unified.jsonl"

echo "[START] Qwen3-14B fine-tuning on Phase 3 dataset..."
python3 Trainning_Steps/finetune_qwen3_14b_phase3.py > "$QWEN_LOG" 2>&1
QWEN_EXIT=$?

if [ $QWEN_EXIT -eq 0 ]; then
    echo "[✓] Qwen3-14B Phase 3 training completed"
else
    echo "[✗] Qwen3-14B Phase 3 training failed with exit code $QWEN_EXIT"
    tail -20 "$QWEN_LOG"
    exit 1
fi

# Cleanup temp script
rm Trainning_Steps/finetune_qwen3_14b_phase3.py

sleep 30

# Phase 3.2: Mistral-7B on 3,502 records
echo ""
echo "============================================================"
echo "  PHASE 3.2: MISTRAL-7B (3,502 RECORDS)"
echo "============================================================"
echo ""

MISTRAL_LOG="$LOG_DIR/mistral_7b_phase3.log"
cp Trainning_Steps/finetune_mistral_7b.py Trainning_Steps/finetune_mistral_7b_phase3.py
update_dataset "Trainning_Steps/finetune_mistral_7b_phase3.py" "/data/atlas_audit_master_unified.jsonl"

echo "[START] Mistral-7B fine-tuning on Phase 3 dataset..."
python3 Trainning_Steps/finetune_mistral_7b_phase3.py > "$MISTRAL_LOG" 2>&1
MISTRAL_EXIT=$?

if [ $MISTRAL_EXIT -eq 0 ]; then
    echo "[✓] Mistral-7B Phase 3 training completed"
else
    echo "[✗] Mistral-7B Phase 3 training failed with exit code $MISTRAL_EXIT"
    tail -20 "$MISTRAL_LOG"
    exit 1
fi

# Cleanup temp script
rm Trainning_Steps/finetune_mistral_7b_phase3.py

sleep 30

# Phase 3.3: DeepSeek-R1-8B on 3,502 records
echo ""
echo "============================================================"
echo "  PHASE 3.3: DEEPSEEK-R1-8B (3,502 RECORDS)"
echo "============================================================"
echo ""

DEEPSEEK_LOG="$LOG_DIR/deepseek_r1_8b_phase3.log"
cp Trainning_Steps/finetune_deepseek_r1_8b.py Trainning_Steps/finetune_deepseek_r1_8b_phase3.py
update_dataset "Trainning_Steps/finetune_deepseek_r1_8b_phase3.py" "/data/atlas_audit_master_unified.jsonl"

echo "[START] DeepSeek-R1-8B fine-tuning on Phase 3 dataset..."
python3 Trainning_Steps/finetune_deepseek_r1_8b_phase3.py > "$DEEPSEEK_LOG" 2>&1
DEEPSEEK_EXIT=$?

if [ $DEEPSEEK_EXIT -eq 0 ]; then
    echo "[✓] DeepSeek-R1-8B Phase 3 training completed"
else
    echo "[✗] DeepSeek-R1-8B Phase 3 training failed with exit code $DEEPSEEK_EXIT"
    tail -20 "$DEEPSEEK_LOG"
    exit 1
fi

# Cleanup temp script
rm Trainning_Steps/finetune_deepseek_r1_8b_phase3.py

echo ""
echo "============================================================"
echo "  PHASE 3 COMPLETE"
echo "============================================================"
echo ""
echo "All models have been fine-tuned on Phase 3 dataset (3,502 records):"
echo "  ✓ Qwen3-14B: /outputs/atlas_qwen3_14b_finetuned/ (updated)"
echo "  ✓ Mistral-7B: /outputs/atlas_mistral_7b_finetuned/ (updated)"
echo "  ✓ DeepSeek-R1-8B: /outputs/atlas_deepseek_r1_8b/ (updated)"
echo ""
echo "Log files: $LOG_DIR"
echo ""
echo "READY FOR DEPLOYMENT!"
echo "Next step: Deploy to Motor 8000 and run integration tests."
echo ""
