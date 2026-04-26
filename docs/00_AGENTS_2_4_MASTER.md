# ATLAS AGENTS 2-4: MASTER SPECIFICATION
**Generado:** Viernes 25 Abril 2026, 23:50
**Deadline:** Agents 2-4 COMPLETADOS Sábado 26, 08:00-16:00
**Objetivo:** Pipeline completo Vision → Reasoning → Validator → Explainer

---

## CONTEXTO CRÍTICO

- **Agent 1 (Vision):** ✅ COMPLETADO. Entrega JSON estructurado con `extracted_fields`, `detected_issues`, `confidence`
- **Criterio de éxito ATLAS:** Flujo seamless + detecta trampas + explica + human-in-the-loop
- **Deployment:** Agent 2 (DeepSeek-R1 en MI300X cloud), Agents 3-4 (Ollama local)
- **Testing:** 7 PDFs con trampas conocidas deben pasar por pipeline completo

---

## AGENT 2: REASONING ENGINE

### Propósito
Recibe análisis de Agent 1 + PDF original. Genera razonamiento explícito (chain-of-thought) para explicar POR QUÉ cada cosa detectada ES una trampa.

### Input
```json
{
  "document_id": "INVOICE_001",
  "document_type": "invoice",
  "pdf_path": "test_documents/INVOICE_001_TRAP_MATH.pdf",
  "extracted_fields": {
    "total": {"value": 7500, "confidence": 0.85},
    "subtotal": {"value": 7000, "confidence": 0.85},
    "tax": {"value": 0, "confidence": 0.95}
  },
  "detected_issues": ["⚠️ TRAP: Total ($7,500) doesn't match subtotal ($7,000)"]
}
```

### Lógica (Explícita, No Black Box)

**PASO 1: Clasificar tipo de trampa**
- Math error: Números que no suman
- Missing field: Campo crítico ausente (vendor, date, expiration)
- Unclear value: Valor ambiguo o fuera de contexto
- Inconsistency: Fechas, rangos, o valores contradictorios

**PASO 2: Generar cadena de razonamiento**
```
ASSUMPTION: Total debe = Subtotal + Tax
EVIDENCE: 
  - subtotal: $7,000
  - tax: $0
  - expected_total: $7,000
  - actual_total: $7,500
  - difference: $500
CONCLUSION: Total es incorrecto (+$500 más alto de lo que debe ser)
SEVERITY: HIGH (error matemático directo)
```

**PASO 3: Validar lógica interna**
- ¿La cadena es coherente?
- ¿Hay supuestos cuestionables?
- ¿Hay casos edge que cambian la conclusión?

### Output Requerido
```json
{
  "document_id": "INVOICE_001",
  "trap_detected": "Math Error",
  "trap_id": "MATH_TOTAL_MISMATCH",
  "reasoning_chain": [
    {
      "step": 1,
      "description": "Extract relevant values from invoice",
      "evidence": "subtotal=$7000, tax=$0, total=$7500",
      "conclusion": "Expected total = $7000 + $0 = $7000"
    },
    {
      "step": 2,
      "description": "Compare expected vs actual",
      "evidence": "expected=$7000, actual=$7500",
      "conclusion": "Mismatch detected: +$500 difference"
    },
    {
      "step": 3,
      "description": "Classify severity",
      "evidence": "Direct math error in financial document",
      "conclusion": "HIGH severity - affects payment amount"
    }
  ],
  "trap_severity": "HIGH",
  "confidence": 0.95,
  "reasoning_valid": true,
  "assumptions": [
    "Total must equal Subtotal + Tax (standard accounting)",
    "No hidden fees or adjustments in document"
  ],
  "model_used": "deepseek-r1",
  "processing_time_ms": 2500,
  "timestamp": "2026-04-26T08:15:00"
}
```

### Restricciones
- NO usar web search (local reasoning only)
- Reasoning DEBE tener mínimo 3 pasos
- Confidence 0.0-1.0 (refleja coherencia de la cadena)
- Cada paso DEBE incluir evidence + conclusion

### Modelo
- **Preferencia:** DeepSeek-R1 en MI300X (mejor chain-of-thought)
- **Fallback:** Llama 2 7B local (si MI300X no disponible)
- **Prompt:** Instruir explícitamente "Show step-by-step reasoning"

---

## AGENT 3: VALIDATOR

### Propósito
Recibe razonamiento de Agent 2. Valida que:
1. La lógica es válida (no hay contradicciones internas)
2. La trampa es real (no es falso positivo)
3. La severidad es correcta

### Input
```json
{
  "document_id": "INVOICE_001",
  "trap_detected": "Math Error",
  "reasoning_chain": [...],
  "confidence": 0.95
}
```

### Lógica de Validación

**VALIDACIÓN 1: Coherencia lógica**
- ¿Cada paso sigue del anterior?
- ¿Hay contradicciones?
- ¿Las conclusiones son justificadas por la evidencia?
- Resultado: boolean `logically_sound`

**VALIDACIÓN 2: Realidad de la trampa**
- Para math errors: ¿Los números definitivamente no suman?
- Para missing fields: ¿El campo es realmente crítico?
- Para inconsistencies: ¿Son realmente incompatibles?
- Resultado: boolean `trap_is_real`

**VALIDACIÓN 3: Severidad apropiada**
- Math error en monto total: HIGH/CRITICAL
- Missing vendor: HIGH
- Missing expiration (contract): CRITICAL
- Unclear but recoverable: MEDIUM/LOW
- Resultado: string `severity_confirmed` or `severity_adjusted`

### Output Requerido
```json
{
  "document_id": "INVOICE_001",
  "trap_id": "MATH_TOTAL_MISMATCH",
  "validation_result": {
    "logically_sound": true,
    "trap_is_real": true,
    "severity_confirmed": "HIGH"
  },
  "validation_confidence": 0.92,
  "issues_found": [],
  "adjustments": [],
  "recommendation": "APPROVE - Trap is valid and reasoning is sound",
  "model_used": "qwen-coder-3b",
  "timestamp": "2026-04-26T08:16:00"
}
```

### Reglas de validación (Explícitas)

```
IF reasoning_chain is empty OR has < 2 steps:
  → logically_sound = false
  
IF trap_type == "MATH_ERROR":
  → Verify numbers mathematically
  → If they actually balance, trap_is_real = false
  
IF trap_type == "MISSING_FIELD":
  → Check if field is in critical_fields list:
    - invoice: [invoice_number, date, vendor, total]
    - contract: [parties, start_date, END_DATE, amount]
  → If not critical, severity = LOW
  
IF trap_type == "INCONSISTENCY":
  → Check date logic: start < end
  → Check value ranges: amounts > 0
  → If passes, severity adjusted lower

FINAL RULE:
  IF any validation fails AND confidence < 0.7:
    → recommendation = "UNCERTAIN - Requires human review"
  ELSE IF all pass:
    → recommendation = "APPROVE"
  ELSE IF any fails:
    → recommendation = "FLAG - Review reasoning"
```

### Modelo
- **Preferencia:** Qwen3-Coder-3B local (small, fast, logical)
- **Fallback:** Llama 2 7B
- **Prompt:** "Validate this reasoning chain. Is it logically sound? Is the trap real?"

---

## AGENT 4: EXPLAINER

### Propósito
Recibe resultado validado de Agent 3. Genera explicación EN ESPAÑOL legible para humano que revise la decisión.

### Input
```json
{
  "document_id": "INVOICE_001",
  "document_type": "invoice",
  "trap_detected": "Math Error",
  "reasoning_chain": [...],
  "validation_result": {...},
  "validation_confidence": 0.92
}
```

### Output Requerido (Markdown + JSON)

**MARKDOWN (Legible para humano):**
```markdown
# Análisis: INVOICE_001_TRAP_MATH.pdf

## Trampa Detectada
**Tipo:** Error Matemático  
**Severidad:** 🔴 ALTA  
**Confianza:** 95%

## ¿Qué pasó?
La factura declara un total de **$7,500 USD**, pero si sumamos los items:
- Subtotal: $7,000
- Impuesto: $0
- **Suma correcta: $7,000**

Hay una diferencia de **$500** que no está justificada.

## ¿Por qué es trampa?
En documentos financieros, el total DEBE ser la suma exacta de subtotal + impuestos. 
Esta discrepancia puede ser:
1. **Error involuntario** (typo, cálculo erróneo)
2. **Manipulación deliberada** (inflar el total para pedir más dinero)

En ambos casos, el documento es **no confiable** para procesar pagos.

## ¿Qué deberías hacer?
✋ **DETENER** el procesamiento de este documento.  
📧 **CONTACTAR** al vendedor (ACME Corp) para aclarar el monto correcto.  
✔️ **PEDIR** una factura corregida antes de pagar.

## Información Técnica
- **Modelo Vision:** llava:7b
- **Modelo Reasoning:** deepseek-r1
- **Modelo Validator:** qwen-coder-3b
- **Confianza General:** 92%
- **Procesamiento:** 2500ms + 1200ms + 800ms = 4500ms total
```

**JSON (Para base de datos/streaming):**
```json
{
  "document_id": "INVOICE_001",
  "document_type": "invoice",
  "trap_type": "MATH_ERROR",
  "trap_severity": "HIGH",
  "explanation": {
    "title": "Error Matemático en Factura",
    "summary": "El total declarado ($7,500) no coincide con la suma de items ($7,000)",
    "detailed_explanation": "En documentos financieros, el total DEBE ser la suma exacta de subtotal + impuestos...",
    "why_its_a_trap": "Esta discrepancia puede ser error involuntario o manipulación deliberada",
    "what_to_do": [
      "Detener procesamiento del documento",
      "Contactar al vendedor para aclarar",
      "Pedir factura corregida antes de pagar"
    ],
    "impact": "Sin resolver, el documento no es confiable para procesamiento de pagos"
  },
  "confidence_breakdown": {
    "vision_confidence": 0.85,
    "reasoning_confidence": 0.95,
    "validation_confidence": 0.92,
    "overall_confidence": 0.91
  },
  "human_review_required": true,
  "next_action": "AWAIT_HUMAN_DECISION",
  "language": "es-MX",
  "timestamp": "2026-04-26T08:17:00"
}
```

### Restricciones
- **Idioma:** Español (México preferred, o neutral)
- **Claridad:** Debe ser entendible en < 2 minutos de lectura
- **Sin jerga:** Explicar conceptos técnicos en lenguaje simple
- **Accionable:** Incluir siempre "¿Qué deberías hacer?"
- **Audit trail:** Incluir modelo usado, tiempos, confianzas

### Modelo
- **Preferencia:** Llama 2 7B local (rápido, multilingüe)
- **Prompt:** "Explain this trap in simple Spanish. What should a human do? Be clear and direct."

---

## ORCHESTRATION (FastAPI + Pipeline)

### Estructura de carpetas necesaria
```
src/
├── agent_vision.py          ✅ (ya existe)
├── chains.py                ✅ (ya existe)
├── agent_reasoning.py        ← GENERAR
├── agent_validator.py        ← GENERAR
├── agent_explainer.py        ← GENERAR
├── orchestrator.py           ← GENERAR
└── api.py                    ← GENERAR (FastAPI endpoints)
```

### API Endpoints
```
POST /analyze
  Input: { pdf_path: str }
  Output: Complete JSON pipeline result
  Process: Vision → Reasoning → Validator → Explainer

GET /result/{document_id}
  Retrieve stored result from Supabase

POST /human_decision
  Input: { document_id, decision: "APPROVE" | "REJECT" | "REQUEST_MORE_INFO" }
  Output: { status: "updated", next_action: ... }
```

### Error Handling
```python
IF Agent 1 fails:
  → Return error, stop pipeline
  
IF Agent 2 fails:
  → Mark as "UNABLE_TO_REASON", pass to Agent 4 with flag
  → Agent 4 explains: "No se pudo generar razonamiento"
  
IF Agent 3 fails:
  → Mark as "UNCERTAIN", pass to Agent 4
  → Agent 4 recommends human review immediately
  
IF Agent 4 fails:
  → Return raw JSON + error message
  
IF any timeout (> 30s total):
  → Return partial results with error flag
```

---

## TESTING (7 PDFs)

### Test Cases
```
1. INVOICE_001_TRAP_MATH.pdf
   Expected: Math error detected, HIGH severity, validated ✅
   
2. INVOICE_002_NORMAL.pdf
   Expected: No issues, passes all agents clean ✅
   
3. INVOICE_003_TRAP_MISSING_INFO.pdf
   Expected: Missing vendor, HIGH severity ✅
   
4. INVOICE_004_TRAP_UNCLEAR.pdf
   Expected: Unclear totals, flagged ✅
   
5. INVOICE_005_NORMAL.pdf
   Expected: Clean ✅
   
6. CONTRACT_001_TRAP_NO_EXPIRY.pdf
   Expected: NO EXPIRATION DATE, CRITICAL severity ✅
   
7. CONTRACT_002_NORMAL.pdf
   Expected: Clean ✅
```

### Test Assertion Format
```python
def test_math_error():
    result = pipeline.run("INVOICE_001_TRAP_MATH.pdf")
    assert result["trap_detected"] == "Math Error"
    assert result["trap_severity"] == "HIGH"
    assert result["validation_result"]["trap_is_real"] == True
    assert result["human_review_required"] == True
    assert "next_action" in result
    
def test_clean_invoice():
    result = pipeline.run("INVOICE_002_NORMAL.pdf")
    assert result["detected_issues"] == []
    assert result["human_review_required"] == False
```

---

## ENVIRONMENT VARIABLES REQUERIDAS

```bash
# Local Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_VISION_MODEL=llava:7b
OLLAMA_EXPLAINER_MODEL=llama2:7b

# Cloud MI300X (DeepSeek-R1)
VLLM_BASE_URL=http://[DIGITALOCEAN_IP]:8000/v1
VLLM_MODEL=deepseek-r1
VLLM_API_KEY=[si aplica]

# Supabase
SUPABASE_URL=https://[PROJECT_ID].supabase.co
SUPABASE_KEY=[ANON_KEY]

# Logging
LOG_LEVEL=INFO
DEBUG=False
```

---

## DELIVERABLES FINALES (para Sábado 26, 16:00)

- ✅ `src/agent_reasoning.py` — Agent 2 completo
- ✅ `src/agent_validator.py` — Agent 3 completo
- ✅ `src/agent_explainer.py` — Agent 4 completo
- ✅ `src/orchestrator.py` — Pipeline coordinator
- ✅ `src/api.py` — FastAPI endpoints
- ✅ `tests/test_pipeline.py` — Test suite completo (7 PDFs)
- ✅ `logs/pipeline_results.json` — Results después de tests

---

## NOTAS CRÍTICAS

1. **Lógica EXPLÍCITA siempre.** Gemini pidió esto. No usar "black box" LLM reasoning sin paso-a-paso.
2. **Human-in-the-loop es CORE.** Output SIEMPRE debe decir "espera decisión humana".
3. **Fallbacks.** Si DeepSeek cae, usar Llama local. Pipeline debe ser resiliente.
4. **Speed matters.** Target: < 30s por documento (Vision 5s + Reasoning 10s + Validator 3s + Explainer 5s + buffer).
5. **Español preferido.** Narrativa Rafa es español. Agent 4 output DEBE ser en español.

---

**Generado por:** Claude (Architect)  
**Para ejecutar con:** Claude Code (Autonomous)  
**Revisión por:** Gemini (Infrastructure validation)  
**Testing por:** Rafael (Manual verification + human review)

