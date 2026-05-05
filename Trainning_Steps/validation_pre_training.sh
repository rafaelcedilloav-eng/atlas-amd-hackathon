#!/bin/bash
# ============================================================
# ATLAS Pre-Training Validation Script
# Validates GPU, datasets, and environment before training starts
# ============================================================

set -e

echo "============================================================"
echo "  ATLAS PRE-TRAINING VALIDATION"
echo "============================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0

# Helper functions
check_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASS++))
}

check_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAIL++))
}

check_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo "1. Checking GPU availability..."
if command -v rocm-smi &> /dev/null; then
    GPU_COUNT=$(rocm-smi --showproductname | grep -c "MI300" || echo "0")
    if [ "$GPU_COUNT" -gt 0 ]; then
        check_pass "AMD GPU detected (MI300X)"
        rocm-smi --showmeminfo
    else
        check_fail "No MI300X GPU found"
    fi
else
    check_fail "rocm-smi not found (ROCm not installed)"
fi
echo ""

echo "2. Checking VRAM availability..."
if command -v rocm-smi &> /dev/null; then
    TOTAL_VRAM=$(rocm-smi --showmeminfo | grep "Total Memory" | head -1 | grep -oP '\d+' | head -1)
    if [ ! -z "$TOTAL_VRAM" ]; then
        TOTAL_GB=$((TOTAL_VRAM / 1024))
        if [ "$TOTAL_GB" -ge 205 ]; then
            check_pass "VRAM sufficient ($TOTAL_GB GB available, need ~161GB max)"
        else
            check_fail "VRAM insufficient ($TOTAL_GB GB available, need 205GB)"
        fi
    fi
else
    check_warn "Could not read VRAM info (rocm-smi unavailable)"
fi
echo ""

echo "3. Checking required Python packages..."
PACKAGES=("torch" "transformers" "datasets" "peft" "scipy")
for pkg in "${PACKAGES[@]}"; do
    if python3 -c "import $pkg" 2>/dev/null; then
        check_pass "$pkg installed"
    else
        check_fail "$pkg not installed - run: pip install $pkg"
    fi
done
echo ""

echo "4. Checking training datasets..."
DATASET1="/data/atlas_training_dataset_final.jsonl"
DATASET2="/data/atlas_audit_master_unified.jsonl"

if [ -f "$DATASET1" ]; then
    LINES1=$(wc -l < "$DATASET1")
    check_pass "Dataset 1 found: $DATASET1 ($LINES1 records)"
else
    check_fail "Dataset 1 missing: $DATASET1"
fi

if [ -f "$DATASET2" ]; then
    LINES2=$(wc -l < "$DATASET2")
    check_pass "Dataset 2 found: $DATASET2 ($LINES2 records)"
else
    check_fail "Dataset 2 missing: $DATASET2"
fi
echo ""

echo "5. Checking output directories..."
OUTPUT_DIRS=(
    "/outputs/atlas_qwen3_14b_finetuned"
    "/outputs/atlas_mistral_7b_finetuned"
    "/outputs/atlas_deepseek_r1_8b"
)

for dir in "${OUTPUT_DIRS[@]}"; do
    parent_dir=$(dirname "$dir")
    if mkdir -p "$parent_dir" 2>/dev/null; then
        check_pass "Output directory accessible: $parent_dir"
    else
        check_fail "Cannot create output directory: $parent_dir"
    fi
done
echo ""

echo "6. Checking HuggingFace model access..."
MODELS=("Qwen/Qwen3-14B" "mistralai/Mistral-7B-Instruct-v0.2" "deepseek-ai/DeepSeek-R1-Distill-Llama-8B")
for model in "${MODELS[@]}"; do
    if python3 -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('$model')" 2>/dev/null; then
        check_pass "Model accessible: $model"
    else
        check_warn "Model may need download on first run: $model"
    fi
done
echo ""

echo "7. Checking training scripts..."
SCRIPTS=(
    "Trainning_Steps/finetune_qwen3_14b.py"
    "Trainning_Steps/finetune_mistral_7b.py"
    "Trainning_Steps/finetune_deepseek_r1_8b.py"
)

for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        check_pass "Training script found: $script"
    else
        check_fail "Training script missing: $script"
    fi
done
echo ""

echo "8. Checking environment variables..."
if [ -z "$HF_TOKEN" ]; then
    check_warn "HF_TOKEN not set (optional, needed for private models)"
else
    check_pass "HF_TOKEN is set"
fi

if [ -z "$ROCR_VISIBLE_DEVICES" ]; then
    check_warn "ROCR_VISIBLE_DEVICES not set (will use all GPUs)"
else
    check_pass "ROCR_VISIBLE_DEVICES is set to: $ROCR_VISIBLE_DEVICES"
fi
echo ""

echo "============================================================"
echo "  VALIDATION SUMMARY"
echo "============================================================"
echo -e "Passed: ${GREEN}$PASS${NC} | Failed: ${RED}$FAIL${NC}"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Ready to start training.${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Phase 1: bash launch_phase1_parallel.sh"
    echo "   (Qwen3-14B + Mistral-7B in parallel on 6,437 records)"
    echo ""
    echo "2. Phase 2: python3 Trainning_Steps/finetune_deepseek_r1_8b.py"
    echo "   (DeepSeek-R1-8B on 6,437 records)"
    echo ""
    echo "3. Phase 3: bash launch_phase3_all_models.sh"
    echo "   (All 3 models on 3,502 records)"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Validation failed. Fix issues above and retry.${NC}"
    exit 1
fi
