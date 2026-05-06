# ATLAS — Vision & Strategic Roadmap
_Where we're going and why it matters._

---

## The Problem ATLAS Solves

Cross-border financial compliance is broken. A Mexican holding company with US subsidiaries, offshore accounts, and intercompany loans operates under simultaneous obligations to:

- **Mexico:** LISR, CFF, RMF, LFPIORPI (AML), CNBV
- **United States:** IRC, BSA, FinCEN, SEC, FINRA, FATCA/FBAR
- **International:** BEPS Pillar Two, OECD Transfer Pricing Guidelines, Basel III/IV
- **Professional standards:** CFA Institute Standards of Conduct, GAAP, IFRS

No human auditor holds all of this in working memory simultaneously. Mistakes cost $50K–$5M+ in penalties per incident. Most companies discover violations *after* the fact, during an IRS or SAT audit.

**ATLAS flips the model**: continuous, real-time forensic analysis before violations become liabilities.

---

## What ATLAS Is (and Isn't)

**ATLAS is:** A specialized forensic auditor AI — a domain expert trained on the specific intersection of financial documents, tax law, and compliance frameworks where most errors occur.

**ATLAS is not:** A general legal AI, a chatbot, a document search engine, or a compliance checklist generator.

The distinction matters. A system that knows everything about law but nothing about numbers misses the math errors. A system that knows numbers but not the regulatory context misses the exposure. ATLAS sits at that intersection.

---

## Current State (R3 — May 2026)

### What works in production
- 4-agent pipeline: Vision → Reasoning → Validator → Explainer
- Fine-tuned Qwen3-14B on 13,588 MX+US compliance cases
- AMD MI300X inference via vLLM (ROCm 7.2)
- PDF ingestion, OCR, structured extraction
- Supabase audit trail with Row Level Security
- Real-time SSE streaming of audit results
- Adversarial robustness: 100% pass rate (no hallucinations, no jailbreaks)

### Benchmark confirmation
- Contract clause analysis: **96%** (CUAD anti-assignment)
- Business ethics MCQ: **81%** (MMLU)
- Financial/tax case detection: **58%** semantic score (custom AEF, 50 hard cases)
- Adversarial defense: **77%** avg / **100%** pass (20 adversarial probes)

---

## The Roadmap

### R4 — Depth (Q3 2026, ~90 days)

**Goal:** Close the ethics/risk gap. Push AEF ethics from 29% → 55%+

- Curate 2,500 CFA ethics cases with reasoning chains
- Add SAT audit decision tree (Mexican tax authority patterns)
- Tree-of-thought fine-tuning for multi-step ethical reasoning
- Expand FCPA + international bribery corpus
- Target: LegalBench avg 65%+ (from current 55%)

**Infrastructure:** Keep AMD MI300X for training. Add ROCm-based inference cluster with 3 replicas for production load.

---

### R5 — Memory & Retrieval (Q4 2026, ~60 days)

**Goal:** Connect ATLAS to live regulatory reality

- **Regulatory RAG**: Live feeds from SAT DOF publications, IRS Rev. Rulings, SEC releases, CNBV circulares
- **Case memory**: pgvector store of historical audit decisions → "This intercompany loan structure appeared in case AEF-REAL-023 — here's how the SAT treated it"
- **Precedent linking**: When ATLAS flags a violation, it cites the most relevant resolved cases from its memory
- **Staleness detection**: Auto-flag when the regulation cited in a document was superseded

---

### R6 — Multi-Entity Intelligence (Q1 2027, ~120 days)

**Goal:** From single-document audit to entity-level forensics

- **Graph layer**: Map beneficial ownership, intercompany transactions, and jurisdiction exposure across an entire corporate group
- **Pattern detection**: Identify transfer pricing manipulation across multiple related-party transactions
- **Scenario modeling**: "If this subsidiary books this royalty, here's the combined MX+US+Pillar Two exposure"
- **Audit calendar**: Proactive alerts when statutory deadlines approach for specific filings

---

### Product Vision (2027+)

**ATLAS as the compliance co-pilot layer** embedded in:

1. **ERP integrations** (SAP, Oracle Financials): Real-time audit flag on every journal entry above threshold
2. **Law firm tooling**: First-pass analysis for M&A due diligence — flag cross-border tax exposure before LOI
3. **Regulatory reporting**: Auto-draft FBAR, FATCA reports, BEPS Country-by-Country reports from raw financial data
4. **Whistleblower support**: Confidential analysis of internal financial data for employees who suspect fraud

---

## The Market Opportunity

| Segment | TAM | ATLAS fit |
|---------|-----|-----------|
| Cross-border SME compliance (MX+US) | $2.8B | **Core market** |
| M&A due diligence tax analysis | $4.1B | R5+ |
| Financial audit augmentation (Big 4) | $12B | R6+ |
| Regulatory tech (RegTech) platforms | $21B | Partnership/API |

The near-term wedge is **cross-border MX+US businesses** — a massive underserved segment. Mexican companies doing business in the US and American companies operating in Mexico navigate two entirely different tax systems simultaneously, with treaty interactions that most accountants don't fully understand. That's ATLAS's home territory.

---

## Why AMD Matters Long-Term

The financial compliance AI stack has a fundamental problem: the most capable models require enormous memory bandwidth for inference. Regulatory analysis involves long contexts (full tax returns, multi-page contracts), multi-step reasoning chains, and concurrent processing of multiple documents.

AMD MI300X's 192GB HBM3 at 5.3 TB/s memory bandwidth is architected exactly for this. Running DeepSeek-R1-32B or Qwen3-72B in full precision (not quantized) for legal/financial reasoning is not possible on consumer-grade GPUs. The MI300X makes it possible at a cost structure that a compliance AI startup can actually sustain.

ROCm 7.2 + vLLM + PyTorch 2.5.1: the stack works. The setup was near-identical to CUDA. The performance is real.

**This is not a demo system that happens to run on AMD. AMD MI300X is why ATLAS can run the models it needs to run.**

---

## One-Line Pitch

> ATLAS is the AI forensic auditor that reads the financial documents, knows the tax law, and catches the violations before your regulators do — trained and deployed on AMD MI300X because the job demands real compute.

---

_ATLAS R3 · AMD × lablab.ai Hackathon 2026_
_Model: Rafaelcedav/atlas-r3-qwen3-14b_
_Demo: https://atlas-amd-qs5g4.ondigitalocean.app_
