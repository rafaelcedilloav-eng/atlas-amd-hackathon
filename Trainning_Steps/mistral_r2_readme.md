---
language:
- es
- en
license: mit
tags:
- forensic-audit
- legal
- finance
- tax
- compliance
- mistral
- amd-mi300x
- rocm
- atlas
base_model: mistralai/Mistral-7B-Instruct-v0.2
datasets:
- Rafaelcedav/atlas-audit-master
pipeline_tag: text-generation
---

# atlas-mistral-7b-legal-r2

**ATLAS Forensic Audit System — Mistral-7B Extended Corpus (Round 2)**  
Trained on AMD MI300X · 6,437 records · Production Deployment

---

## What is this?

This is the production-scale fine-tune of `mistralai/Mistral-7B-Instruct-v0.2` on the full ATLAS audit corpus.
While [`atlas-mistral-7b-legal`](https://huggingface.co/Rafaelcedav/atlas-mistral-7b-legal) validated the architecture on 3,502 curated records (eval loss 0.018), **this model was trained on the complete 6,437-record dataset** — 83% more examples, broader normativa coverage, and higher scenario diversity.

This is the version deployed in production for ATLAS v2.0.

---

## Training Configuration

| Parameter | Value |
|-----------|-------|
| Base model | `mistralai/Mistral-7B-Instruct-v0.2` |
| Dataset | `atlas_training_dataset_final.jsonl` |
| Training records | **6,437** |
| Epochs | 3 |
| Learning rate | 2e-5 |
| Batch size | 4 (grad_accum=4, effective=16) |
| Precision | bfloat16 |
| Hardware | AMD Instinct MI300X (205.8 GB VRAM) |
| Framework | PyTorch 2.5.1 + ROCm 6.2 |
| Optimizer | adamw_torch |
| attn_implementation | eager (SDPA disabled for ROCm stability) |
| Estimated runtime | ~50 min |

---

## Dataset: What changed from Round 1

The expanded corpus (`atlas_audit_master_unified.jsonl`, 6,437 records) includes:

- **All 3,502 records** from Round 1 (verified, high-confidence)
- **+2,935 records** covering edge cases, multi-jurisdiction scenarios, and complex RFC validation chains
- Broader distribution across: `factura_electronica`, `comprobante_fiscal`, `contrato_servicios`, `estado_cuenta`, `declaracion_anual`
- More examples of compound anomalies (e.g., RFC inválido + IVA incorrecto + fecha inconsistente simultaneously)

> Round 1 optimized for precision. Round 2 optimized for production recall.

---

## Normativa Coverage

| Domain | Key Articles |
|--------|-------------|
| **MX — SAT/CFF** | Art. 17-H Bis, Art. 69-B (EFOS/EDOS), Art. 29/29-A CFF |
| **MX — IVA** | 16% (general), Art. 18-J (plataformas digitales), exenciones |
| **MX — ISR** | Personas morales, retenciones, deducciones autorizadas |
| **MX — CFDI** | v4.0, complementos, PAC validation, UUID trazabilidad |
| **USA — IRS** | Form 1099, W-8BEN, FATCA reportable accounts |
| **USA — SEC** | AI washing enforcement, disclosure requirements |
| **CROSS** | OECD Pillar Two GloBE, CRS reporting, FATCA cross-validation |

---

## Usage

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_id = "Rafaelcedav/atlas-mistral-7b-legal-r2"

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
    attn_implementation="eager",
    device_map="auto"
)

prompt = """AUDITORÍA FORENSE REQUERIDA.
DOCUMENTO: factura_electronica

--- CAMPOS EXTRAÍDOS ---
{
  "rfc_emisor": {"value": "XAXX010101000", "confidence": 0.99},
  "total": {"value": 11600.00, "confidence": 0.98},
  "iva": {"value": 1600.00, "confidence": 0.97},
  "subtotal": {"value": 10000.00, "confidence": 0.99}
}

INSTRUCCIÓN: Analiza buscando errores matemáticos, RFCs inválidos o términos inusuales. Responde en JSON."""

messages = [
    {"role": "system", "content": "Eres un Auditor Forense Senior especializado en normativa fiscal MX/USA."},
    {"role": "user", "content": prompt}
]

inputs = tokenizer.apply_chat_template(messages, return_tensors="pt").to(model.device)
output = model.generate(inputs, max_new_tokens=1024, temperature=0.1, do_sample=True)
print(tokenizer.decode(output[0][inputs.shape[-1]:], skip_special_tokens=True))
```

**Expected output:**
```json
{
  "trap_detected": "RFC genérico XAXX010101000 — válido para CFDI pero indica operación con público general, no con persona específica. Verificar si aplica complemento carta porte.",
  "trap_severity": "LOW",
  "reasoning_chain": [
    {"step": 1, "thought": "IVA matemáticamente correcto: 10000 × 0.16 = 1600 ✓"},
    {"step": 2, "thought": "Total correcto: 10000 + 1600 = 11600 ✓"},
    {"step": 3, "thought": "RFC XAXX010101000 es RFC genérico — no representa una persona física/moral identificada"}
  ],
  "confidence": 0.91,
  "reasoning_valid": true
}
```

---

## ATLAS Pipeline Position

```
PDF/Image
    │
    ▼
[Agent 1: Vision]  ← InternVL2-40B (OCR + field extraction)
    │
    ▼
[Agent 2: Reasoning] ← atlas-mistral-7b-legal-r2  ← YOU ARE HERE
    │                   (anomaly detection, math validation)
    ▼
[Agent 3: Validator] ← Rule engine (RFC regex, SAT blacklists)
    │
    ▼
[Agent 4: Explainer] ← Qwen3-14B (executive-grade report)
    │
    ▼
Forensic Report (PDF) + SSE Real-time X-Ray
```

---

## Round 1 vs Round 2 — Comparison

| Metric | Round 1 (3,502 records) | Round 2 (6,437 records) |
|--------|------------------------|------------------------|
| Training records | 3,502 | **6,437** (+83%) |
| Train loss | 0.0584 | Lower bound established by Round 1 |
| Eval loss | 0.0184 | Broader generalization target |
| Training time | 27 min | ~50 min |
| Use case | Validation + research | **Production deployment** |
| Scenario diversity | Curated core | Full production corpus |

---

## Hardware Note

Trained entirely on AMD Instinct MI300X (205.8 GB HBM3 VRAM) using ROCm 6.2.
Full-parameter fine-tuning (no LoRA/QLoRA) — maximum weight absorption from the regulatory corpus.

---

## Related Models in the ATLAS Ecosystem

| Model | Role | Records | Notes |
|-------|------|---------|-------|
| [atlas-mistral-7b-legal](https://huggingface.co/Rafaelcedav/atlas-mistral-7b-legal) | Reasoning v1 | 3,502 | Research baseline |
| **atlas-mistral-7b-legal-r2** | **Reasoning v2** | **6,437** | **← Production** |
| [atlas-r2-qwen3-14b](https://huggingface.co/Rafaelcedav/atlas-r2-qwen3-14b) | Explainer + Sandbox | 3,502 | 14B, thinking mode |
| [atlas-finanzas-deepseek-r1-8b](https://huggingface.co/Rafaelcedav/atlas-finanzas-deepseek-r1-8b) | Chain-of-thought | 6,437 | Distilled R1 |

---

## License

MIT — Free to use, fine-tune, and deploy.

---

*Part of the ATLAS Forensic Audit System — AMD Hackathon 2026*  
*Trained on AMD MI300X. Zero cloud API calls. 100% open-source.*
