# ATLAS — Hackathon Submission Info
_Archivo local de referencia. NO subir a GitHub._

---

## Project Title
ATLAS — Automated Threat & Liability Analysis System

---

## Short Description
A 4-agent AI forensic pipeline that detects fraud, math errors, and integrity violations in financial documents. Powered by DeepSeek-R1-Distill-Qwen-32B on AMD MI300X via vLLM at 8,000+ tokens/sec.

---

## Long Description

**The problem:** Financial fraud in invoices and contracts costs companies billions annually. Manual auditing is slow, inconsistent, and doesn't scale.

**ATLAS** is an automated multi-agent forensic system that analyzes financial documents end-to-end — from raw PDF to executive audit report — in seconds.

---

### How it works

ATLAS runs 4 specialized AI agents sequentially, each building on the previous one's output:

**Agent 1 — Vision Analyzer**
Extracts structured data from any PDF using OCR (Tesseract + Poppler). Identifies document type, key fields (vendor, amount, date, taxes), and surface anomalies. Returns a confidence score.

**Agent 2 — Reasoning Agent**
Sends extracted data to DeepSeek-R1-Distill-Qwen-32B running on AMD MI300X via vLLM. The model performs step-by-step forensic reasoning — detecting math errors, missing fields, inconsistencies, and policy violations. Outputs a structured reasoning chain with evidence per step.

**Agent 3 — Integrity Gate (Validator)**
Cross-validates the reasoning output: verifies calculations mathematically, checks the document hash against a deduplication registry, and queries a blacklist of known fraudulent vendors. Confirms or rejects the anomaly detected by Agent 2.

**Agent 4 — Explainer Agent**
Generates a human-readable audit report in Markdown: executive summary, financial impact, confidence breakdown per agent, recommended action (AUTO_APPROVE / ESCALATE / AWAIT_HUMAN_DECISION), and next steps for the auditor.

---

### What makes it AMD-native

The AMD MI300X's 192GB HBM3 unified memory lets us run DeepSeek-R1-Distill-Qwen-32B in full FP16 — no quantization, no memory fragmentation. vLLM's continuous batching on ROCm keeps throughput consistent under concurrent requests. What would require 8× A100s fits in a single MI300X card.

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
