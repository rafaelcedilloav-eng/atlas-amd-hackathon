# ATLAS: PROMPT PARA CLAUDE CODE — AGENTS 2, 3, 4
**Versión:** 1.1 (Gemini-refined)
**Fecha:** 26 Abril 2026
**Ejecutar en:** `D:\Proyectos\atlas-amd-hackathon\` con venv activo

---

## CONTEXTO CRÍTICO — LEE ANTES DE ESCRIBIR CÓDIGO

Estás construyendo ATLAS: un sistema multi-agente de detección de trampas en documentos financieros/contratos. El sistema tiene 4 agentes en pipeline secuencial.

**Agent 1 (Vision) ya existe en `src/agent_vision.py` — NO lo toques.**

Tu tarea: construir Agents 2, 3, 4 + orchestrator + API + tests.

**Principio rector:** Toda decisión debe ser EXPLÍCITA y TRAZABLE. No black boxes. Cada agente produce un JSON con pasos auditables. Los jueces del AMD Hackathon deben poder leer el output y entender exactamente por qué se tomó cada decisión.

---

## PASO 0: ANTES DE ESCRIBIR CUALQUIER ARCHIVO

Ejecuta esto y dime el output:

```bash
cd D:\Proyectos\atlas-amd-hackathon
venv\Scripts\activate
ollama list
python --version
pip list | findstr -i "pydantic fastapi langchain"
```

Necesito saber qué tienes disponible. En especial:
- Nombre EXACTO del modelo Qwen en Ollama (puede ser `qwen:3b`, `qwen2:3b`, `qwen2.5:3b`, `qwen2.5-coder:3b`, etc.)
- Versión de Pydantic (v1 vs v2 — la sintaxis cambia)

**NO generes ningún archivo hasta haber corrido este diagnóstico.**

---

## PASO 1: SCHEMAS PYDANTIC (`src/schemas.py`)

**Crea este archivo PRIMERO.** Es el contrato de datos entre todos los agentes. Si los schemas no son correctos, nada funciona.

```python
# src/schemas.py
"""
Pydantic schemas — contratos de datos entre agentes ATLAS.
Gemini requirement: schemas primero para que el pipeline sea irrompible.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


# ─── OUTPUT DE AGENT 1 (Vision) — ya existe, no modificar ────────────────────

class ExtractedField(BaseModel):
    value: float | str | None
    confidence: float = Field(ge=0.0, le=1.0)

class VisionOutput(BaseModel):
    document_id: str
    document_type: Literal["invoice", "contract", "unknown"]
    pdf_path: str
    extracted_fields: dict[str, ExtractedField]
    detected_issues: List[str]
    confidence: float = Field(ge=0.0, le=1.0)
    model_used: str
    processing_time_ms: int
    timestamp: datetime


# ─── OUTPUT DE AGENT 2 (Reasoning) ──────────────────────────────────────────

class ReasoningStep(BaseModel):
    step: int
    description: str
    evidence: str
    conclusion: str

class ReasoningOutput(BaseModel):
    document_id: str
    trap_detected: Literal["Math Error", "Missing Field", "Inconsistency", "Unclear Value", "No Trap"]
    trap_id: str
    reasoning_chain: List[ReasoningStep] = Field(min_length=3)  # MÍNIMO 3 pasos
    trap_severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning_valid: bool
    assumptions: List[str]
    model_used: str
    processing_time_ms: int
    timestamp: datetime
    # Flag de fallback — True si usó modelo local en lugar de DeepSeek cloud
    used_fallback: bool = False


# ─── OUTPUT DE AGENT 3 (Validator) ──────────────────────────────────────────

class ValidationResult(BaseModel):
    logically_sound: bool
    trap_is_real: bool
    severity_confirmed: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE"]
    # Campo nuevo (Gemini): resultado de validación matemática determinista
    math_verified: Optional[bool] = None  # None si no es math error
    math_verification_detail: Optional[str] = None

class ValidatorOutput(BaseModel):
    document_id: str
    trap_id: str
    validation_result: ValidationResult
    validation_confidence: float = Field(ge=0.0, le=1.0)
    issues_found: List[str]
    adjustments: List[str]
    recommendation: Literal["APPROVE", "FLAG", "UNCERTAIN"]
    recommendation_detail: str
    model_used: str
    timestamp: datetime


# ─── OUTPUT DE AGENT 4 (Explainer) ──────────────────────────────────────────

class ConfidenceBreakdown(BaseModel):
    vision_confidence: float
    reasoning_confidence: float
    validation_confidence: float
    overall_confidence: float

class ExplanationContent(BaseModel):
    title: str
    summary: str
    detailed_explanation: str
    why_its_a_trap: str
    what_to_do: List[str]
    financial_impact: str  # Gemini: impacto financiero explícito

class ExplainerOutput(BaseModel):
    document_id: str
    document_type: str
    trap_type: str
    trap_severity: str
    explanation: ExplanationContent
    confidence_breakdown: ConfidenceBreakdown
    human_review_required: bool
    next_action: Literal["AWAIT_HUMAN_DECISION", "AUTO_APPROVE", "ESCALATE"]
    language: str = "es-MX"
    markdown_report: str  # Reporte completo en Markdown
    timestamp: datetime


# ─── OUTPUT FINAL DEL PIPELINE ───────────────────────────────────────────────

class PipelineResult(BaseModel):
    document_id: str
    pdf_path: str
    status: Literal["COMPLETE", "PARTIAL", "FAILED"]
    vision: Optional[VisionOutput] = None
    reasoning: Optional[ReasoningOutput] = None
    validation: Optional[ValidatorOutput] = None
    explanation: Optional[ExplainerOutput] = None
    total_processing_time_ms: int
    error: Optional[str] = None
    timestamp: datetime
```

**Verifica que Pydantic no lance errores antes de continuar:**
```bash
python -c "from src.schemas import PipelineResult; print('Schemas OK')"
```

---

## PASO 2: AGENT 2 — REASONING ENGINE (`src/agent_reasoning.py`)

### Función principal: `run(vision_output: VisionOutput) -> ReasoningOutput`

### Lógica de conexión a modelos

```python
# Orden de prioridad:
# 1. DeepSeek-R1 en MI300X (DigitalOcean)
# 2. Fallback: modelo Llama local en Ollama

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://134.199.198.76:8000/v1")
VLLM_MODEL = os.getenv("VLLM_MODEL", "/root/models/deepseek-32b")

def _get_llm():
    """Intenta conectar a DeepSeek cloud. Si falla, usa Ollama local."""
    try:
        response = requests.get(f"{VLLM_BASE_URL}/models", timeout=5)
        if response.status_code == 200:
            return "cloud", ChatOpenAI(
                base_url=VLLM_BASE_URL,
                api_key=os.getenv("VLLM_API_KEY", "dummy"),
                model=VLLM_MODEL,
                temperature=0.1
            )
    except Exception:
        pass
    # Fallback local
    return "local", ChatOllama(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.getenv("OLLAMA_FALLBACK_MODEL", "llama2:7b"),
        temperature=0.1
    )
```

### CRÍTICO — JSON puro de DeepSeek (Gemini requirement)

El prompt para DeepSeek DEBE ser exactamente así. No cambies la estructura:

```python
REASONING_SYSTEM_PROMPT = """You are a financial document fraud detection system.
You MUST respond with ONLY valid JSON. No markdown, no explanations, no preamble.
Your response must start with {{ and end with }}.
Do not write any text outside the JSON object.

Analyze the document issues and generate explicit step-by-step reasoning.
Each reasoning step MUST contain: step number, description, evidence, conclusion."""

REASONING_USER_PROMPT = """Document ID: {document_id}
Document Type: {document_type}
Detected Issues: {detected_issues}
Extracted Fields: {extracted_fields}

Classify the trap type (Math Error / Missing Field / Inconsistency / Unclear Value / No Trap).
Generate MINIMUM 3 reasoning steps explaining WHY each issue is a trap.
Assign severity (CRITICAL / HIGH / MEDIUM / LOW / NONE).

Respond with ONLY this JSON structure, no other text:
{{
  "document_id": "{document_id}",
  "trap_detected": "...",
  "trap_id": "...",
  "reasoning_chain": [
    {{"step": 1, "description": "...", "evidence": "...", "conclusion": "..."}},
    {{"step": 2, "description": "...", "evidence": "...", "conclusion": "..."}},
    {{"step": 3, "description": "...", "evidence": "...", "conclusion": "..."}}
  ],
  "trap_severity": "...",
  "confidence": 0.95,
  "reasoning_valid": true,
  "assumptions": ["..."]
}}"""
```

### Retry logic para JSON malformado (Gemini requirement)

```python
def _call_with_retry(llm, prompt: str, max_retries: int = 3) -> dict:
    """
    Llama al LLM con retry si el JSON viene malformado.
    Gemini requirement: DeepSeek puede escribir 'pensamientos' fuera del JSON.
    """
    for attempt in range(max_retries):
        try:
            response = llm.invoke(prompt)
            raw = response.content.strip()
            
            # Limpiar si el modelo escribió texto antes/después del JSON
            # Buscar el primer { y último } para extraer solo el JSON
            start = raw.find('{')
            end = raw.rfind('}') + 1
            if start == -1 or end == 0:
                raise ValueError(f"No JSON found in response (attempt {attempt+1})")
            
            json_str = raw[start:end]
            return json.loads(json_str)
            
        except (json.JSONDecodeError, ValueError) as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"Failed to get valid JSON after {max_retries} attempts: {e}")
            time.sleep(1)  # Pequeña pausa antes de reintentar
```

---

## PASO 3: AGENT 3 — VALIDATOR (`src/agent_validator.py`)

### Función principal: `run(reasoning_output: ReasoningOutput, vision_output: VisionOutput) -> ValidatorOutput`

### CRÍTICO — Validación matemática DETERMINISTA (Gemini requirement #1)

Este es el cambio más importante que pide Gemini. Para Math Errors, Python hace la suma real — no el LLM.

```python
def _verify_math_deterministic(vision_output: VisionOutput) -> tuple[bool, str]:
    """
    Validación matemática 100% determinista con Python puro.
    Si Agent 2 dice que $7000 + $0 ≠ $7500, Python lo confirma sin depender del LLM.
    Retorna: (is_math_error: bool, detail: str)
    """
    fields = vision_output.extracted_fields
    
    # Extraer valores numéricos con defaults seguros
    def get_value(key: str) -> float:
        field = fields.get(key)
        if field and field.value is not None:
            try:
                return float(field.value)
            except (TypeError, ValueError):
                return 0.0
        return 0.0
    
    doc_type = vision_output.document_type
    
    if doc_type == "invoice":
        subtotal = get_value("subtotal")
        tax = get_value("tax")
        total = get_value("total")
        
        if total == 0.0:
            return False, "No total field found — cannot verify mathematically"
        
        expected = round(subtotal + tax, 2)
        actual = round(total, 2)
        difference = round(actual - expected, 2)
        
        if abs(difference) > 0.01:  # Tolerancia de 1 centavo
            return True, f"MATH ERROR CONFIRMED: expected={expected}, actual={actual}, difference={difference}"
        else:
            return False, f"Math checks out: {subtotal} + {tax} = {actual}"
    
    # Para otros tipos de documento: retornar None (no aplica validación matemática)
    return None, "Math validation not applicable for this document type"


def _validate_logic(reasoning_output: ReasoningOutput) -> tuple[bool, list[str]]:
    """
    Validaciones de lógica sin depender del LLM.
    Reglas explícitas del master spec.
    """
    issues = []
    
    # Regla 1: reasoning chain mínimo 2 pasos
    if len(reasoning_output.reasoning_chain) < 2:
        issues.append("Reasoning chain has < 2 steps — insufficient")
    
    # Regla 2: cada paso tiene evidence y conclusion
    for step in reasoning_output.reasoning_chain:
        if not step.evidence or not step.conclusion:
            issues.append(f"Step {step.step} missing evidence or conclusion")
    
    # Regla 3: confidence > 0
    if reasoning_output.confidence <= 0:
        issues.append("Confidence is 0 or negative — invalid")
    
    return len(issues) == 0, issues


def _validate_severity(reasoning_output: ReasoningOutput) -> str:
    """
    Valida que la severidad asignada es apropiada según reglas del master spec.
    Retorna la severidad correcta (puede ajustar la de Agent 2).
    """
    trap = reasoning_output.trap_detected
    severity = reasoning_output.trap_severity
    
    severity_rules = {
        "Math Error": ["HIGH", "CRITICAL"],
        "Missing Field": {
            "INVOICE_NUMBER": "HIGH", "DATE": "HIGH",
            "VENDOR": "HIGH", "TOTAL": "CRITICAL",
            "END_DATE": "CRITICAL", "PARTIES": "HIGH",
            "DEFAULT": "MEDIUM"
        },
        "Inconsistency": ["MEDIUM", "HIGH"],
        "Unclear Value": ["LOW", "MEDIUM"],
        "No Trap": ["NONE"]
    }
    
    if trap == "Math Error" and severity not in ["HIGH", "CRITICAL"]:
        return "HIGH"  # Ajuste automático
    if trap == "No Trap":
        return "NONE"
    
    return severity  # Confirmar la severidad original


def _determine_recommendation(
    logically_sound: bool,
    trap_is_real: bool,
    confidence: float,
    issues: list[str]
) -> tuple[str, str]:
    """
    Regla de decisión final — 100% determinista.
    """
    if not logically_sound or len(issues) > 0:
        if confidence < 0.7:
            return "UNCERTAIN", f"Lógica inválida y baja confianza ({confidence:.0%}). Issues: {'; '.join(issues)}"
        return "FLAG", f"Problemas en razonamiento: {'; '.join(issues)}"
    
    if not trap_is_real:
        return "APPROVE", "Trampa no confirmada — documento puede proceder"
    
    return "APPROVE", "Trampa válida y razonamiento sólido — requiere decisión humana"
```

### El LLM en Agent 3 es secundario

El LLM de Qwen **solo valida la coherencia narrativa** de la cadena de razonamiento (¿suena lógico?). Las decisiones binarias las toma Python. Llama a Qwen con este prompt:

```python
VALIDATOR_PROMPT = """Review this reasoning chain for logical coherence only.
Does each step follow from the previous? Are conclusions justified by evidence?
Respond ONLY with JSON: {{"narrative_coherent": true/false, "coherence_notes": "..."}}"""
```

**IMPORTANTE:** Si Qwen no está disponible en Ollama, el validator DEBE funcionar igual usando solo las validaciones deterministas de Python. El LLM es un bonus, no un requisito.

**⚠️ PLACEHOLDER:** El modelo de Qwen en Ollama puede llamarse diferente. Cuando ejecutes `ollama list`, busca cualquier modelo que contenga "qwen" en el nombre y úsalo. Si no existe ningún Qwen, usa `llama2:7b` como fallback completo.

---

## PASO 4: AGENT 4 — EXPLAINER (`src/agent_explainer.py`)

### Función principal: `run(vision, reasoning, validation) -> ExplainerOutput`

### Tono (Gemini requirement): Directivo y Ejecutivo

El prompt para Llama debe ser exactamente así:

```python
EXPLAINER_SYSTEM_PROMPT = """Eres un auditor financiero senior que explica riesgos a directivos.
Tu tono es: directo, ejecutivo, sin jerga técnica.
Hablas en español de México.
Usas términos como: "riesgo de pago duplicado", "discrepancia fiscal", "exposición financiera".
NUNCA uses: "el modelo detectó", "el algoritmo", "chain-of-thought", "tokens".
Responde SOLO con JSON válido. Sin markdown, sin texto fuera del JSON."""

EXPLAINER_USER_PROMPT = """
Documento: {document_id} ({document_type})
Trampa detectada: {trap_detected}
Severidad: {trap_severity}
Razonamiento Agent 2: {reasoning_summary}
Validación Agent 3: {validation_summary}
Confianza general: {overall_confidence:.0%}

Genera una explicación ejecutiva en español. Incluye impacto financiero real.
Responde SOLO con este JSON:
{{
  "title": "Título ejecutivo corto",
  "summary": "Una oración. Qué pasó y cuál es el riesgo.",
  "detailed_explanation": "2-3 oraciones. Sin jerga técnica.",
  "why_its_a_trap": "Por qué esto representa un riesgo financiero real.",
  "what_to_do": ["Acción 1", "Acción 2", "Acción 3"],
  "financial_impact": "Impacto concreto en términos de dinero o exposición legal."
}}"""
```

### Generación del Markdown report

El Markdown lo genera Python (no el LLM) usando los datos ya estructurados:

```python
def _generate_markdown(
    document_id: str,
    trap_type: str,
    severity: str,
    explanation_content: dict,
    confidence_breakdown: dict,
    processing_times: dict
) -> str:
    """
    Genera el reporte Markdown de forma determinista.
    No depende del LLM — usa los datos ya validados.
    """
    severity_emoji = {
        "CRITICAL": "🔴🔴 CRÍTICA",
        "HIGH": "🔴 ALTA",
        "MEDIUM": "🟡 MEDIA",
        "LOW": "🟢 BAJA",
        "NONE": "✅ NINGUNA"
    }.get(severity, severity)
    
    overall = confidence_breakdown.get("overall_confidence", 0)
    
    md = f"""# Análisis ATLAS: {document_id}

## Diagnóstico
**Tipo de problema:** {trap_type}  
**Severidad:** {severity_emoji}  
**Confianza del sistema:** {overall:.0%}

## ¿Qué ocurrió?
{explanation_content.get('detailed_explanation', '')}

## ¿Por qué representa un riesgo?
{explanation_content.get('why_its_a_trap', '')}

## Impacto Financiero
> {explanation_content.get('financial_impact', '')}

## Acciones Requeridas
"""
    for i, action in enumerate(explanation_content.get("what_to_do", []), 1):
        md += f"{i}. {action}\n"
    
    md += f"""
---
## ⚠️ DECISIÓN PENDIENTE
Este documento requiere revisión humana antes de proceder.

## Trazabilidad Técnica
| Agente | Modelo | Confianza | Tiempo |
|--------|--------|-----------|--------|
| Vision | llava:7b | {confidence_breakdown.get('vision_confidence', 0):.0%} | {processing_times.get('vision', 0)}ms |
| Reasoning | deepseek-r1 | {confidence_breakdown.get('reasoning_confidence', 0):.0%} | {processing_times.get('reasoning', 0)}ms |
| Validator | qwen/llama | {confidence_breakdown.get('validation_confidence', 0):.0%} | {processing_times.get('validation', 0)}ms |
| Explainer | llama2:7b | — | {processing_times.get('explainer', 0)}ms |
"""
    return md
```

---

## PASO 5: ORCHESTRATOR (`src/orchestrator.py`)

### Función principal: `run_pipeline(pdf_path: str) -> PipelineResult`

### Lógica de manejo de errores

```python
async def run_pipeline(pdf_path: str) -> PipelineResult:
    start_time = time.time()
    document_id = Path(pdf_path).stem
    
    result = PipelineResult(
        document_id=document_id,
        pdf_path=pdf_path,
        status="FAILED",
        total_processing_time_ms=0,
        timestamp=datetime.now()
    )
    
    # AGENT 1: Vision
    try:
        vision_output = agent_vision.run(pdf_path)
        result.vision = vision_output
    except Exception as e:
        result.error = f"Agent 1 (Vision) failed: {str(e)}"
        result.total_processing_time_ms = int((time.time() - start_time) * 1000)
        return result  # Stop pipeline aquí
    
    # Si no hay issues detectados, retornar clean result directo
    if not vision_output.detected_issues:
        result.status = "COMPLETE"
        result.total_processing_time_ms = int((time.time() - start_time) * 1000)
        # Generar explicación "todo limpio" sin pasar por Agent 2-3
        result.explanation = _generate_clean_explanation(document_id)
        return result
    
    # AGENT 2: Reasoning
    try:
        reasoning_output = agent_reasoning.run(vision_output)
        result.reasoning = reasoning_output
    except Exception as e:
        logger.error(f"Agent 2 failed: {e}")
        # No detener pipeline — Agent 4 explicará el fallo
        reasoning_output = _create_failed_reasoning(document_id, str(e))
        result.reasoning = reasoning_output
    
    # AGENT 3: Validator
    try:
        validation_output = agent_validator.run(reasoning_output, vision_output)
        result.validation = validation_output
    except Exception as e:
        logger.error(f"Agent 3 failed: {e}")
        validation_output = _create_uncertain_validation(document_id, str(e))
        result.validation = validation_output
    
    # AGENT 4: Explainer
    try:
        explanation_output = agent_explainer.run(vision_output, reasoning_output, validation_output)
        result.explanation = explanation_output
        result.status = "COMPLETE"
    except Exception as e:
        logger.error(f"Agent 4 failed: {e}")
        result.error = f"Explainer failed: {str(e)}"
        result.status = "PARTIAL"
    
    # Timeout check
    total_ms = int((time.time() - start_time) * 1000)
    result.total_processing_time_ms = total_ms
    if total_ms > 30000:
        logger.warning(f"Pipeline exceeded 30s: {total_ms}ms for {document_id}")
    
    return result
```

---

## PASO 6: API (`src/api.py`)

```python
# FastAPI con 3 endpoints del master spec

POST /analyze
  Body: { "pdf_path": "test_documents/INVOICE_001_TRAP_MATH.pdf" }
  Returns: PipelineResult (JSON completo)

GET /result/{document_id}
  Returns: PipelineResult guardado en Supabase

POST /human_decision
  Body: { "document_id": "INVOICE_001", "decision": "APPROVE" | "REJECT" | "REQUEST_MORE_INFO" }
  Returns: { "status": "updated", "document_id": "...", "decision": "...", "timestamp": "..." }
```

Para Supabase: guardar el `PipelineResult` completo en tabla `atlas_results` con columnas:
- `document_id` (PK)
- `status`
- `result_json` (JSON completo)
- `human_decision` (nullable)
- `created_at`
- `updated_at`

Si Supabase no está configurado (keys faltantes), loggear warning y continuar — no romper el pipeline.

---

## PASO 7: TESTS (`tests/test_pipeline.py`)

### 7 casos de prueba exactos

```python
import pytest
from src.orchestrator import run_pipeline
import asyncio

# Helper para correr async en tests
def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)

class TestMathError:
    def test_trap_detected(self):
        result = run(run_pipeline("test_documents/INVOICE_001_TRAP_MATH.pdf"))
        assert result.status == "COMPLETE"
        assert result.reasoning.trap_detected == "Math Error"
        assert result.reasoning.trap_severity in ["HIGH", "CRITICAL"]
        assert result.validation.validation_result.trap_is_real == True
        assert result.validation.validation_result.math_verified == True  # Validación determinista
        assert result.explanation.human_review_required == True
        assert result.explanation.next_action == "AWAIT_HUMAN_DECISION"
        assert result.total_processing_time_ms < 30000

class TestCleanInvoice:
    def test_no_issues(self):
        result = run(run_pipeline("test_documents/INVOICE_002_NORMAL.pdf"))
        assert result.status == "COMPLETE"
        assert result.vision.detected_issues == []
        assert result.explanation.human_review_required == False

class TestMissingVendor:
    def test_missing_field(self):
        result = run(run_pipeline("test_documents/INVOICE_003_TRAP_MISSING_INFO.pdf"))
        assert result.reasoning.trap_detected == "Missing Field"
        assert result.reasoning.trap_severity in ["HIGH", "CRITICAL"]
        assert result.explanation.human_review_required == True

class TestUnclearTotals:
    def test_unclear_value(self):
        result = run(run_pipeline("test_documents/INVOICE_004_TRAP_UNCLEAR.pdf"))
        assert result.reasoning is not None
        assert result.explanation is not None
        # Unclear puede ser LOW o MEDIUM — no forzar severidad

class TestCleanInvoice2:
    def test_clean(self):
        result = run(run_pipeline("test_documents/INVOICE_005_NORMAL.pdf"))
        assert result.status == "COMPLETE"
        assert result.vision.detected_issues == []

class TestNoExpiryContract:
    def test_critical_missing_field(self):
        result = run(run_pipeline("test_documents/CONTRACT_001_TRAP_NO_EXPIRY.pdf"))
        assert result.reasoning.trap_detected == "Missing Field"
        assert result.reasoning.trap_severity == "CRITICAL"
        assert result.explanation.human_review_required == True
        assert "fecha" in result.explanation.explanation.detailed_explanation.lower() \
            or "expir" in result.explanation.explanation.detailed_explanation.lower() \
            or "vencimiento" in result.explanation.explanation.detailed_explanation.lower()

class TestCleanContract:
    def test_clean(self):
        result = run(run_pipeline("test_documents/CONTRACT_002_NORMAL.pdf"))
        assert result.status == "COMPLETE"
        assert result.vision.detected_issues == []
```

Después de todos los tests, guardar results en `logs/pipeline_results.json`:
```python
# Al final del archivo de tests
def save_results():
    results = {}
    for pdf in TEST_PDFS:
        r = run(run_pipeline(f"test_documents/{pdf}"))
        results[pdf] = r.model_dump()
    with open("logs/pipeline_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
```

---

## PASO 8: VARIABLES DE ENTORNO (`.env`)

Crea o actualiza `.env` en la raíz del proyecto:

```bash
# Local Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_VISION_MODEL=llava:7b
OLLAMA_EXPLAINER_MODEL=llama2:7b
OLLAMA_FALLBACK_MODEL=llama2:7b
# ⚠️ ACTUALIZAR: poner el nombre exacto de Qwen de `ollama list`
OLLAMA_VALIDATOR_MODEL=qwen3.5:4b

# Cloud MI300X (DigitalOcean)
VLLM_BASE_URL=http://134.199.198.76:8000/v1
VLLM_MODEL=/root/models/deepseek-32b
VLLM_API_KEY=

# Supabase
SUPABASE_URL=
SUPABASE_KEY=

# Logging
LOG_LEVEL=INFO
DEBUG=False
```

---

## ORDEN DE EJECUCIÓN (Claude Code: sigue este orden exacto)

```
1. ollama list  →  confirmar modelos disponibles
2. Crear src/schemas.py
3. python -c "from src.schemas import PipelineResult; print('OK')"
4. Crear src/agent_reasoning.py
5. Crear src/agent_validator.py
6. Crear src/agent_explainer.py
7. Crear src/orchestrator.py
8. Crear src/api.py
9. Crear tests/test_pipeline.py
10. mkdir logs
11. python -m pytest tests/test_pipeline.py -v
12. python tests/test_pipeline.py  →  genera logs/pipeline_results.json
```

**Si un test falla:** corregir el agente antes de continuar al siguiente test. No avanzar con tests rojos.

---

## CRITERIOS DE ÉXITO (para Rafael, no para Code)

Al terminar, Rafael verifica manualmente:

- [ ] `python -m pytest tests/ -v` → 7/7 tests verdes
- [ ] `logs/pipeline_results.json` existe y tiene 7 entradas
- [ ] El reporte Markdown de INVOICE_001 menciona "$500" y "riesgo"
- [ ] El reporte de CONTRACT_001 menciona "fecha de vencimiento" o "expiración"
- [ ] Los documentos limpios (002, 005, 007) tienen `human_review_required: false`
- [ ] `POST /analyze` en FastAPI responde en < 30s

---

## NOTAS FINALES PARA CLAUDE CODE

1. **JSON puro siempre.** Si un LLM devuelve texto fuera del JSON, extrae solo lo que está entre `{` y `}`.
2. **Pydantic es el árbitro.** Si un output no pasa validación Pydantic, es un bug — corrígelo antes de continuar.
3. **Fallbacks siempre.** Si DeepSeek cloud no responde en 5s, usa Ollama local. Si Qwen no existe, usa llama2:7b.
4. **Validación determinista primero.** En Agent 3, Python hace las matemáticas. El LLM solo valida narrativa.
5. **Un archivo por agente.** No pongas lógica de Agent 2 en Agent 3. Límites claros.
6. **Logs en cada paso.** `logger.info(f"Agent 2 completed: {document_id} in {ms}ms")` — los jueces AMD van a ver esto.
7. **Tono ejecutivo en Agent 4.** Palabras clave: "exposición financiera", "riesgo de pago", "discrepancia fiscal". Nunca: "el modelo", "el algoritmo".

---

**Generado por:** Claude (Architect + Gemini refinements integrados)  
**Para ejecutar con:** Claude Code (Autonomous)  
**Proyecto:** ATLAS — AMD Hackathon 2026  
**Deadline build:** Sábado 26 Abril, 16:00
