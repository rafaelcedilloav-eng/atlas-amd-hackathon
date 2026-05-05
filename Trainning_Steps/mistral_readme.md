---
language:
- es
- en
license: apache-2.0
base_model: mistralai/Mistral-7B-Instruct-v0.2
tags:
- fine-tuned
- legal
- audit
- forensic
- tax
- atlas
- amd
- rocm
- finance
datasets:
- custom
pipeline_tag: text-generation
---

# ATLAS Mistral-7B Legal — Auditoría Forense Fiscal

Fine-tune de **Mistral-7B-Instruct-v0.2** especializado en auditoría forense y cumplimiento fiscal para México y USA, entrenado sobre **AMD Instinct MI300X** con ROCm 7.2.

Parte del ecosistema **ATLAS** — sistema multi-agente de detección de anomalías financieras desarrollado para el AMD Hackathon 2025.

## Métricas de Entrenamiento

| Métrica | Valor |
|---------|-------|
| Train Loss | **0.0584** |
| Eval Loss | **0.0184** |
| Epochs | 3 |
| Tiempo | ~27 minutos |
| Dataset | 3,502 ejemplos legales MX/USA |
| Hardware | AMD Instinct MI300X (205GB VRAM) |

## Especialización

El modelo fue entrenado para razonar sobre casos de auditoría fiscal con base en normativa específica:

**México:**
- Art. 69-B CFF — Operaciones Inexistentes (EFOS/EDOS)
- RESICO — Régimen de Confianza (Personas Físicas)
- Precios de Transferencia (Art. 59-G LISR)
- Auditoría Electrónica y verificación de CFDI

**USA:**
- IRM 4.10 — Examination of Returns
- IRM 4.23 — Employment Tax / Worker Classification
- BSA/FBAR — Anti-Money Laundering
- Bank Deposits Method, Economic Reality Test

## Uso

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "Rafaelcedav/atlas-mistral-7b-legal"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype="bfloat16")

messages = [
    {"role": "system", "content": "Eres ATLAS, auditor forense especializado en derecho fiscal MX/USA."},
    {"role": "user", "content": "Empresa con 1 empleado factura 50MDP en servicios de construcción. ¿Qué artículo aplica?"}
]

input_ids = tokenizer.apply_chat_template(messages, return_tensors="pt", add_generation_prompt=True)
output = model.generate(input_ids, max_new_tokens=512, temperature=0.1)
print(tokenizer.decode(output[0][input_ids.shape[-1]:], skip_special_tokens=True))
```

## Arquitectura ATLAS

Este modelo opera como agente de razonamiento dentro del pipeline multi-agente ATLAS:

```
PDF → [Vision InternVL2-40B] → [Compliance Router] → [Mistral-7B / Reasoning]
    → [Validator] → [Explainer] → Reporte Forense
```

## Hardware & Entorno

- **GPU:** AMD Instinct MI300X VF (205.8 GB VRAM)
- **Framework:** PyTorch 2.5.1 + ROCm 6.2
- **Optimizer:** AdamW (adamw_torch)
- **Precisión:** bfloat16
- **Gradient Checkpointing:** ✅

## Repositorio

Código fuente, scripts de entrenamiento y pipeline completo:
[atlas-amd-hackathon](https://github.com/rafaelcedilloav-eng/atlas-amd-hackathon)

## Modelos Relacionados

- [atlas-r2-qwen3-14b](https://huggingface.co/Rafaelcedav/atlas-r2-qwen3-14b) — Motor principal de razonamiento (14B)
- [atlas-finanzas-deepseek-r1-8b](https://huggingface.co/Rafaelcedav/atlas-finanzas-deepseek-r1-8b) — Análisis financiero profundo
