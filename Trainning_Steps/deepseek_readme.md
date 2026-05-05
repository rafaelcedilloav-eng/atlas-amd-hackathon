---
language:
- es
- en
license: mit
base_model: deepseek-ai/DeepSeek-R1-Distill-Llama-8B
tags:
- fine-tuned
- legal
- audit
- forensic
- tax
- reasoning
- atlas
- amd
- rocm
- finance
- deepseek
datasets:
- custom
pipeline_tag: text-generation
---

# ATLAS DeepSeek-R1 Finanzas — Razonamiento Forense Fiscal

Fine-tune de **DeepSeek-R1-Distill-Llama-8B** especializado en detección de anomalías financieras y auditoría fiscal forense para México y USA.

Entrenado sobre **AMD Instinct MI300X** con ROCm como parte del sistema **ATLAS** para el AMD Hackathon 2025.

## ¿Por qué DeepSeek-R1 para auditoría forense?

DeepSeek-R1 fue diseñado con capacidades de razonamiento encadenado (chain-of-thought). En el contexto de auditoría fiscal, esto es crítico: un auditor no solo emite un veredicto — **razona, pondera evidencia, descarta hipótesis alternativas y construye un argumento legal sólido**.

Este fine-tune aprovecha exactamente esa arquitectura de razonamiento para:
- Identificar patrones de operaciones inexistentes (EFOS/EDOS)
- Cruzar referencias normativas entre CFF, LISR y regulación americana
- Emitir conclusiones con trazabilidad argumental explícita

## Métricas de Entrenamiento

| Métrica | Valor |
|---------|-------|
| Base Model | DeepSeek-R1-Distill-Llama-8B |
| Train Loss | **0.4829** |
| Epochs | 3 |
| Dataset | 6,437 ejemplos financiero-legales |
| Hardware | AMD Instinct MI300X (205GB VRAM) |
| Tiempo | ~36 minutos |

## Dominio de Conocimiento

**México — Código Fiscal de la Federación:**
- Art. 69-B — Operaciones Inexistentes (presunción y desvirtúo)
- Art. 42 — Facultades de comprobación del SAT
- Auditoría Electrónica (revisión de CFDI, e.firma, buzón tributario)
- RESICO — Régimen Simplificado de Confianza
- Precios de Transferencia (Art. 59-G LISR)

**USA — Internal Revenue Manual:**
- IRM 4.10 — Examination of Returns (Bank Deposits Method)
- IRM 4.23 — Employment Tax / Worker Classification
- BSA/FBAR — Anti-Money Laundering (FinCEN 114)
- Common Law Test / Economic Reality Test

## Uso

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_id = "Rafaelcedav/atlas-finanzas-deepseek-r1-8b"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

messages = [
    {
        "role": "system",
        "content": "Eres ATLAS, auditor forense especializado en detección de anomalías fiscales. Razona paso a paso antes de emitir conclusiones."
    },
    {
        "role": "user",
        "content": "Empresa con 1 empleado factura 50MDP en servicios de construcción especializada. Domicilio fiscal en zona residencial. ¿Qué indica esto y qué procedimiento aplica?"
    }
]

inputs = tokenizer.apply_chat_template(messages, return_tensors="pt", add_generation_prompt=True)
output = model.generate(inputs, max_new_tokens=1024, temperature=0.1, do_sample=True)
print(tokenizer.decode(output[0][inputs.shape[-1]:], skip_special_tokens=True))
```

## Rol en el Pipeline ATLAS

```
[Vision] → [Compliance] → [DeepSeek-R1 Reasoning] → [Validator] → [Explainer]
                                    ↑
                         Analiza hallazgos de visión
                         Cruza con normativa aplicable
                         Construye hipótesis de riesgo
                         Emite veredicto con evidencia
```

## Hardware & Entorno

- **GPU:** AMD Instinct MI300X VF — 205.8 GB VRAM
- **Framework:** PyTorch 2.5.1 + ROCm 6.2
- **Optimizer:** AdamW (`adamw_torch`) — única opción estable en ROCm
- **Precisión:** bfloat16 — nativo en MI300X
- **Attention:** `eager` — SDPA genera NaN en ROCm + bf16

## Modelos Relacionados

- [atlas-mistral-7b-legal](https://huggingface.co/Rafaelcedav/atlas-mistral-7b-legal) — Agente legal MX/USA
- [atlas-r2-qwen3-14b](https://huggingface.co/Rafaelcedav/atlas-r2-qwen3-14b) — Motor principal de razonamiento
- [atlas-qwen3-14b-legal](https://huggingface.co/Rafaelcedav/atlas-qwen3-14b-legal) — Segunda ronda especialización legal
