#!/bin/bash
# ATLAS — GPU Benchmark Runner (AMD MI300X / ROCm)
# Runs: MMLU + LegalBench (lm-evaluation-harness) + AEF custom eval
# Usage: bash gpu_run_all.sh
# Expects: HF_TOKEN env var set before running

set -e

HF_TOKEN="${HF_TOKEN:?'Set HF_TOKEN before running'}"
MODEL_ID="Rafaelcedav/atlas-r3-qwen3-14b"
RESULTS_DIR="/root/atlas_eval_results"
VLLM_PORT=8000
VLLM_PID=""

mkdir -p "$RESULTS_DIR"

log() { echo "[$(date '+%H:%M:%S')] $*"; }

cleanup() {
    if [ -n "$VLLM_PID" ]; then
        log "Stopping vLLM server (PID $VLLM_PID)..."
        kill "$VLLM_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

# ── 1. Install dependencies ───────────────────────────────────────────────────
log "Installing dependencies..."
pip install -q \
    vllm \
    "lm_eval[api]" \
    datasets \
    huggingface_hub \
    requests \
    tqdm

# ── 2. Download model weights to local cache ──────────────────────────────────
log "Downloading $MODEL_ID from HuggingFace..."
huggingface-cli download "$MODEL_ID" \
    --token "$HF_TOKEN" \
    --local-dir /root/atlas_r3_model \
    --local-dir-use-symlinks False

# ── 3. Start vLLM server ──────────────────────────────────────────────────────
log "Starting vLLM server on port $VLLM_PORT..."
python -m vllm.entrypoints.openai.api_server \
    --model /root/atlas_r3_model \
    --dtype bfloat16 \
    --max-model-len 8192 \
    --port $VLLM_PORT \
    --gpu-memory-utilization 0.85 \
    --disable-log-requests \
    &
VLLM_PID=$!

log "Waiting for vLLM to be ready..."
for i in $(seq 1 60); do
    if curl -sf "http://localhost:$VLLM_PORT/health" > /dev/null 2>&1; then
        log "vLLM ready."
        break
    fi
    sleep 5
    if [ $i -eq 60 ]; then
        log "ERROR: vLLM did not start in 5 minutes. Check logs."
        exit 1
    fi
done

# ── 4. MMLU — 3 professional subsets (5-shot) ─────────────────────────────────
log "Running MMLU (professional_law, professional_accounting, business_ethics)..."
lm_eval \
    --model local-completions \
    --model_args \
        "base_url=http://localhost:$VLLM_PORT/v1,model=/root/atlas_r3_model,tokenizer_backend=huggingface,max_length=8192" \
    --tasks \
        hendrycksTest-professional_law,\
hendrycksTest-professional_accounting,\
hendrycksTest-business_ethics \
    --num_fewshot 5 \
    --batch_size 8 \
    --output_path "$RESULTS_DIR/mmlu" \
    --log_samples \
    2>&1 | tee "$RESULTS_DIR/mmlu_run.log"

log "MMLU complete. Results in $RESULTS_DIR/mmlu"

# ── 5. LegalBench — compliance subsets (0-shot) ───────────────────────────────
log "Running LegalBench..."
lm_eval \
    --model local-completions \
    --model_args \
        "base_url=http://localhost:$VLLM_PORT/v1,model=/root/atlas_r3_model,tokenizer_backend=huggingface,max_length=8192" \
    --tasks \
        legalbench_contract_nli_explicit_identification,\
legalbench_contract_nli_breach_of_contract,\
legalbench_cuad_anti_assignment,\
legalbench_opp115_data_retention \
    --num_fewshot 0 \
    --batch_size 8 \
    --output_path "$RESULTS_DIR/legalbench" \
    --log_samples \
    2>&1 | tee "$RESULTS_DIR/legalbench_run.log"

log "LegalBench complete. Results in $RESULTS_DIR/legalbench"

# ── 6. AEF — ATLAS custom benchmark (120 cases) ───────────────────────────────
log "Running ATLAS Evaluation Framework (AEF)..."

# Copy eval scripts to GPU
cp /root/atlas_amd_hackathon/docs/Pruebas/run_atlas_eval.py   /root/
cp /root/atlas_amd_hackathon/docs/Pruebas/atlas_real_cases.jsonl        /root/
cp /root/atlas_amd_hackathon/docs/Pruebas/atlas_real_cases_2.jsonl      /root/
cp /root/atlas_amd_hackathon/docs/Pruebas/atlas_casos_adversariales.jsonl /root/

LOCAL_ENDPOINT="http://localhost:$VLLM_PORT" \
    python /root/run_atlas_eval.py \
    2>&1 | tee "$RESULTS_DIR/aef_run.log"

log "AEF complete. Results in /root/docs/Pruebas/results/"

# ── 7. Print summary ──────────────────────────────────────────────────────────
log ""
log "======================================================"
log "  ALL BENCHMARKS COMPLETE"
log "======================================================"
log ""
log "MMLU log     : $RESULTS_DIR/mmlu_run.log"
log "LegalBench log: $RESULTS_DIR/legalbench_run.log"
log "AEF report   : /root/docs/Pruebas/results/atlas_eval_report.json"
log ""
log "To copy results back to your machine:"
log "  scp -r -i .ssh/atlas_r2_key root@<DROPLET_IP>:$RESULTS_DIR ./docs/Pruebas/results/"
log "  scp -r -i .ssh/atlas_r2_key root@<DROPLET_IP>:/root/docs/Pruebas/results/ ./docs/Pruebas/results/"
