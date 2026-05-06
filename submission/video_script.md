# ATLAS — Video Walkthrough Script
_Duración objetivo: 3–4 minutos. Grabar pantalla + narrar en vivo o añadir voz después._

---

## Antes de grabar — checklist

- [ ] Abrir https://atlas-amd-qs5g4.ondigitalocean.app en Chrome/Arc (modo oscuro si es posible)
- [ ] Tener listo un PDF de prueba (usar cualquiera de `test_documents/`)
- [ ] Resolución: 1920×1080 o 1280×720
- [ ] OBS o Loom corriendo
- [ ] Silencio, micrófono probado

---

## ESCENA 1 — Hook (0:00 – 0:20)
**Pantalla:** Slide de título / página principal de ATLAS en el browser

> *"Financial document fraud is a $4 trillion global problem. Manual auditing is slow. AI can fix that.*
> *This is ATLAS — a 4-agent forensic pipeline running on AMD MI300X. We fine-tuned a Qwen3-14B model on 13,588 real compliance cases, benchmarked it honestly, and built a system that actually works in its domain."*

**Acción:** Mostrar el dashboard con métricas (documentos auditados, fraudes detectados, tiempo promedio)

---

## ESCENA 2 — El problema + arquitectura (0:20 – 0:50)
**Pantalla:** Diagrama de los 4 agentes (puede ser la slide de presentación)

> *"ATLAS chains 4 specialized AI agents:*
> *Vision extracts the data. Reasoning — powered by DeepSeek-R1 on AMD MI300X — detects anomalies step by step.*
> *Validator confirms integrity: no duplicates, no blacklisted vendors.*
> *And Explainer writes the executive audit report — in plain language."*

---

## ESCENA 3 — Demo en vivo: subir un PDF (0:50 – 1:50)
**Pantalla:** Página de Upload en el frontend

> *"Let me show you a real audit. I'm uploading an invoice with a deliberate math error — the subtotal doesn't match the line items."*

**Acción:** Arrastrar el PDF al drop zone → click en Analizar
> *"The pipeline starts immediately. Vision agent extracts vendor, amounts, dates..."*

**Acción:** Mostrar el spinner / estado de procesamiento
> *"Now DeepSeek-R1 on AMD MI300X is reasoning through the document. 32 billion parameters, full FP16 precision — no quantization — thanks to the MI300X's 192GB of HBM3 memory."*

**Acción:** Cuando aparece el resultado...
> *"There it is. Math Error detected. HIGH severity. Confidence: 87%."*

---

## ESCENA 4 — El reporte (1:50 – 2:30)
**Pantalla:** Página de resultado / reporte ejecutivo

> *"Let's open the full audit report."*

**Acción:** Click en el resultado → mostrar el reporte markdown renderizado
> *"Agent 4 — the Explainer — generated this in seconds. Executive summary, evidence chain, financial impact, recommended action: ESCALATE."*

**Acción:** Scroll por el reporte, mostrar la cadena de razonamiento
> *"And here's the reasoning chain — three steps of forensic logic from the LLM. This is the 'thinking' of DeepSeek-R1, structured and auditable."*

---

## ESCENA 5 — Integrity Gate (2:30 – 3:00)
**Pantalla:** Sección Integrity Gate del dashboard

> *"ATLAS also runs an integrity gate on every document. Duplicate detection prevents re-submission of the same PDF. Vendor blacklisting flags known bad actors before the AI even runs."*

**Acción:** Mostrar las stat cards (Documentos Limpios, Duplicados, Proveedores Bloqueados)

---

## ESCENA 6 — Benchmarks + AMD (3:00 – 3:30)
**Pantalla:** Dashboard de resultados (streamlit) o slide de benchmarks

> *"We benchmarked ATLAS R3 honestly. CUAD contract analysis: 96%. MMLU Business Ethics: 81%. Adversarial robustness: 100% pass rate — zero hallucinations, zero jailbreaks.*
> *For generic legal tasks outside its training domain? Near random chance. That's what a specialist looks like."*

> *"The hardware: AMD MI300X. 192GB HBM3 at 5.3 TB/s. Full bf16 training, no quantization compromise.*
> *ROCm 7.2 setup was near-identical to CUDA. That compatibility is underrated — and it's why we could run the models the job actually demands."*

---

## ESCENA 7 — Cierre (3:30 – 4:00)
**Pantalla:** GitHub repo / README

> *"ATLAS is fully open-source.*
> *FastAPI backend. Next.js 15 frontend. Supabase PostgreSQL. Deployed on DigitalOcean App Platform.*
> *The full pipeline, the 4 agents, the deploy config — all in the repo."*

> *"Built in 72 hours for the AMD × lablab.ai Hackathon 2026.*
> *Links in the description."*

---

## Notas de edición post-grabación
- Añadir lower thirds con el nombre del agente cuando cambia de escena
- Música de fondo: lo-fi techno suave, -20dB (no distrae)
- Si usas ElevenLabs: voz "Adam" o "Charlie", velocidad 1.0x, tono profesional
- Exportar en 1080p, formato MP4 H.264

---

## Links para incluir en la descripción del video
- GitHub: https://github.com/rafaelcedilloav-eng/atlas-amd-hackathon
- Demo: https://atlas-amd-qs5g4.ondigitalocean.app
- AMD Developer Cloud: https://developer.amd.com/
- lablab.ai hackathon: https://lablab.ai
