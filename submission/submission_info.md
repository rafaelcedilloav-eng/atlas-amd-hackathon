# ATLAS — Hackathon Submission Info
_Archivo local de referencia. NO subir a GitHub._

---

## Project Title
ATLAS — Automated Threat & Liability Analysis System

---

## Short Description
A 4-agent AI forensic pipeline that detects fraud, tax violations, and compliance breaches in financial documents. Powered by ATLAS R3 — a fine-tuned Qwen3-14B trained on 13,588 MX+US compliance cases — running on AMD MI300X via vLLM with ROCm 7.2.

---

## Long Description

**The problem:** Cross-border financial compliance is broken. A company operating between Mexico and the US simultaneously faces LISR, CFF, IRC, FATCA, BEPS Pillar Two, AML regulations, and CFA ethics standards. No human auditor holds all of this in working memory. Most violations are discovered *after* the fact — during an IRS or SAT audit. Penalties run $50K–$5M+ per incident.

**ATLAS** is an automated multi-agent forensic system that analyzes financial documents end-to-end — from raw PDF to executive audit report — in seconds. It doesn't replace auditors; it gives them a tireless first-pass analyst that never misses a LISR article or an IRC section.

**Benchmarked honestly:** 96% on CUAD contract clause analysis (Stanford/Yale benchmark), 81% MMLU Business Ethics, 100% adversarial robustness pass rate. For generic out-of-domain legal tasks, ATLAS scores near chance — because it's a specialist, not an encyclopedia.

---

### How it works

ATLAS runs 4 specialized AI agents sequentially, each building on the previous one's output:

**Agent 1 — Vision Analyzer**
Extracts structured data from any PDF using OCR (Tesseract + Poppler). Identifies document type, key fields (vendor, amount, date, taxes), and surface anomalies. Returns a confidence score.

**Agent 2 — Reasoning Agent**
Sends extracted data to ATLAS R3 — a Qwen3-14B fine-tuned on 13,588 MX+US compliance cases — running on AMD MI300X via vLLM with ROCm 7.2. The model performs step-by-step forensic reasoning: detecting math errors, missing fields, tax law violations (LISR/IRC), AML red flags, and transfer pricing issues. Outputs a structured reasoning chain with evidence per step.

**Agent 3 — Integrity Gate (Validator)**
Cross-validates the reasoning output: verifies calculations mathematically, checks the document hash against a deduplication registry, and queries a blacklist of known fraudulent vendors. Confirms or rejects the anomaly detected by Agent 2.

**Agent 4 — Explainer Agent**
Generates a human-readable audit report in Markdown: executive summary, financial impact, confidence breakdown per agent, recommended action (AUTO_APPROVE / ESCALATE / AWAIT_HUMAN_DECISION), and next steps for the auditor.

---

### What makes it AMD-native

ATLAS R3 was **trained** on AMD MI300X (ROCm 7.2, PyTorch 2.5.1+rocm6.2, QLoRA 4-bit, bf16) — not just inferred on it. The 192GB HBM3 unified memory enabled full bf16 training on 13,588 examples with 8K context windows, reaching a final loss of 0.1238. Three training iterations (R1 → R2 → R3) were all AMD-native.

At inference time, vLLM's continuous batching on ROCm keeps throughput consistent under concurrent audit requests. The MI300X's memory bandwidth (5.3 TB/s) handles the long-context financial documents ATLAS processes without quantization compromise.

---

### Stack
- **LLM:** DeepSeek-R1-Distill-Qwen-32B on AMD MI300X (AMD Developer Cloud, Oregon)
- **Inference:** vLLM with ROCm backend
- **Backend:** FastAPI + Python 3.12 + Pydantic v2
- **Database:** Supabase PostgreSQL with Row Level Security
- **Frontend:** Next.js 15 (App Router) + Tailwind CSS + TanStack Query
- **Deploy:** DigitalOcean App Platform (Docker, 2 services)
- **OCR:** Tesseract 5 + Poppler

---

### Security
All endpoints protected with API key authentication. File uploads validated by magic bytes, sanitized against path traversal, capped at 20MB. Supabase RLS enabled — frontend never touches the database directly.

Open-source under MIT. Full technical walkthrough in the repository.

---

## Technology & Category Tags
AMD MI300X, ROCm, vLLM, DeepSeek-R1, Multi-Agent AI, LLM Inference, FastAPI, Next.js, Python, TypeScript, Supabase, PostgreSQL, OCR, Document Analysis, Financial AI, Fraud Detection, DigitalOcean, Docker, Open Source

---

## App Hosting & Code Repository
| Campo | Valor |
|---|---|
| GitHub | https://github.com/rafaelcedilloav-eng/atlas-amd-hackathon |
| Demo Platform | DigitalOcean App Platform |
| App URL | https://atlas-amd-qs5g4.ondigitalocean.app |
