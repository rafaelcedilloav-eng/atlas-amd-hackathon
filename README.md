# ATLAS — Automated Threat & Liability Analysis System
### AMD × lablab.ai Hackathon 2026

A 4-agent AI forensic pipeline that detects fraud, tax violations, and compliance breaches in financial documents. Powered by a fine-tuned Qwen3-14B (ATLAS R3) trained on AMD MI300X with ROCm.

**Live demo:** https://atlas-amd-qs5g4.ondigitalocean.app
**Model:** [Rafaelcedav/atlas-r3-qwen3-14b](https://huggingface.co/Rafaelcedav/atlas-r3-qwen3-14b)

---

## Benchmark Results

| Benchmark | Task | Score |
|-----------|------|-------|
| MMLU | Business Ethics | **81.0%** |
| MMLU | Professional Accounting | **66.7%** |
| MMLU | Professional Law | 56.3% |
| LegalBench (CUAD) | Anti-Assignment Clauses | **96.0%** |
| AEF Custom | Financial / Tax Cases (50) | 58% semantic |
| AEF Custom | Adversarial Robustness (20) | **77% / 100% pass** |

ATLAS is a domain specialist. It excels at contract analysis and financial compliance (its training domain) and underperforms on out-of-scope legal tasks — by design.

---

## Architecture

```
PDF Upload
    │
    ▼
Agent 1 — Vision Analyzer
    OCR extraction (Tesseract + Poppler)
    Structured fields: vendor, amounts, dates, document type
    │
    ▼
Agent 2 — Reasoning Agent  ◄── AMD MI300X (vLLM + ROCm)
    ATLAS R3 (Qwen3-14B fine-tuned)
    Step-by-step forensic reasoning
    Detects: math errors, missing fields, policy violations, tax exposure
    │
    ▼
Agent 3 — Integrity Gate (Validator)
    Math verification
    Duplicate detection (document hash registry)
    Vendor blacklist lookup
    │
    ▼
Agent 4 — Explainer Agent
    Executive audit report (Markdown)
    Evidence chain per finding
    Decision: AUTO_APPROVE / ESCALATE / AWAIT_HUMAN_DECISION
    Financial impact estimate
```

---

## Model: ATLAS R3

Fine-tuned Qwen3-14B on 13,588 MX+US financial compliance cases:

- **Jurisdictions:** Mexico (LISR, CFF, RMF, LFPIORPI, CNBV) + United States (IRC, BSA, FinCEN, SEC, FATCA/FBAR)
- **Domains:** Transfer pricing (BEPS/§482), AML, CFA ethics, FCPA, Basel III, Pillar Two
- **Training:** AMD MI300X · ROCm 7.2 · PyTorch 2.5.1+rocm6.2 · QLoRA 4-bit · bf16
- **Final loss:** 0.1238 (R3, third iteration)
- **Context window:** 8,192 tokens

```
R1 (DeepSeek-R1 8B)  →  loss 0.45
R2 (Qwen3-14B)       →  loss 0.28
R3 (Qwen3-14B)       →  loss 0.1238  ← current
```

---

## Stack

| Layer | Technology |
|-------|-----------|
| LLM | Qwen3-14B fine-tuned (ATLAS R3) |
| Inference | vLLM · AMD MI300X · ROCm 7.2 |
| Backend | FastAPI + Python 3.12 + Pydantic v2 |
| Database | Supabase PostgreSQL + Row Level Security |
| Frontend | Next.js 15 (App Router) + Tailwind CSS |
| Deploy | DigitalOcean App Platform (Docker) |
| OCR | Tesseract 5 + Poppler |

---

## Why AMD MI300X

The 192GB HBM3 unified memory at 5.3 TB/s bandwidth lets us run Qwen3-14B in full bf16 with 8K context — no quantization compromise during training or inference. ROCm 7.2 setup was near-identical to CUDA. The stack just worked.

---

## Quick Start

```bash
git clone https://github.com/rafaelcedilloav-eng/atlas-amd-hackathon
cd atlas-amd-hackathon

# Backend
pip install -r requirements.txt
uvicorn src.api:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

Required env vars: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `HF_TOKEN`, `VLLM_ENDPOINT` (optional).

---

## Evaluation

```bash
cd docs/Pruebas
python run_atlas_eval.py          # AEF 120-case benchmark
python rescore_semantic.py        # Semantic re-scoring
python run_legalbench.py          # LegalBench tasks

cd ../../submission/dashboard
streamlit run atlas_results_dashboard.py   # Results dashboard
```

---

## Team

**Rafael Cedillo** — Builder
Built for the AMD × lablab.ai Hackathon 2026 · Deadline: May 10, 2026

---

MIT License · Build in Public: @lablabai @AIatAMD
