# Plan de Correcciones ATLAS

## Contexto

Durante la auditoría técnica del sistema ATLAS (25 de abril 2026) se identificaron 10 problemas en el código generado durante el hackathon AMD. Este plan cubre la corrección ordenada de todos ellos, priorizados por impacto en producción. Ningún cambio debe hacerse "en la marcha" — este documento es la referencia de qué tocar, en qué orden, y cómo verificar que funcionó.

Archivos principales involucrados:
- `src/schemas.py`
- `src/agent_vision.py`
- `src/agent_validator.py`
- `src/agent_explainer.py`
- `src/agent_reasoning.py` (solo lectura de referencia)
- `src/pdf_reader.py`
- `src/orchestrator.py`
- `src/chains.py`
- `tests/test_pipeline.py`

---

## Fase 1 — Bugs críticos (bloquean producción)

### 1.1 Corregir semántica ambigua de `recommendation` en Agent 3

**Problema:** `agent_validator.py` líneas 107-110 devuelve `"APPROVE"` tanto para documentos limpios como para documentos con trampa confirmada. Un consumidor de la API que lea solo `recommendation == "APPROVE"` podría autorizar un pago fraudulento.

**Archivos a modificar:**
- `src/schemas.py` — Añadir `"FORWARD_FOR_REVIEW"` al Literal de `recommendation` en `ValidatorOutput`
- `src/agent_validator.py` — Función `_determine_recommendation()`: cuando `trap_is_real == True`, devolver `"FORWARD_FOR_REVIEW"` en lugar de `"APPROVE"`
- `tests/test_pipeline.py` — Actualizar cualquier assert que espere `recommendation == "APPROVE"` en casos con trampa

**Cambio exacto en `_determine_recommendation()`:**
```python
# Antes (ambiguo):
return "APPROVE", "Valid trap with solid reasoning - requires human decision"

# Después (claro):
return "FORWARD_FOR_REVIEW", "Valid trap confirmed - awaiting human decision"
```

**Schema actualizado:**
```python
recommendation: Literal["APPROVE", "FORWARD_FOR_REVIEW", "FLAG", "UNCERTAIN"]
```

---

### 1.2 Interpolar el monto real de discrepancia en Agent 4

**Problema:** `agent_explainer.py` línea 99 tiene `"$500.00 USD"` hardcodeado. Para cualquier documento con Math Error diferente a INVOICE_001, la explicación menciona el monto incorrecto.

**Archivos a modificar:**
- `src/agent_explainer.py` — Función `_rule_based_explanation()` y su llamador

**Cambio exacto:**
1. Modificar la firma de `_rule_based_explanation`:
```python
def _rule_based_explanation(
    doc_id: str, doc_type: str, trap_detected: str,
    trap_severity: str, issues: list[str]  # ← añadir parámetro
) -> dict:
```

2. Parsear el monto del string de issue al inicio de la función:
```python
import re as _re
discrepancy = "$500.00 USD"  # default seguro
if issues:
    m = _re.search(r'discrepancy: (\$[\d,]+\.\d{2})', issues[0])
    if m:
        discrepancy = m.group(1)
```

3. Reemplazar todas las ocurrencias de `$500.00 USD` en el diccionario `explanations` con `{discrepancy}` usando f-string o `.format()`.

4. Actualizar la llamada en `_get_llm_explanation()` para pasar `issues` hacia abajo, y en `run()` pasar `vision_output.detected_issues`.

---

### 1.3 Neutralizar `agent_vision.py`

**Problema:** `_read_document()` en línea 115 devuelve solo el nombre del archivo, nunca lee el PDF. Silenciosamente produce alucinaciones si alguien lo usa.

**Acción:** No eliminar (preservar historial git). Añadir al inicio del archivo:

```python
raise NotImplementedError(
    "agent_vision.py es un prototipo inactivo. "
    "El pipeline usa src/pdf_reader.py + src/orchestrator._build_vision_output(). "
    "Ver docs/ATLAS_AUDIT_REPORT.md para contexto."
)
```

**Alternativa preferida:** Mover físicamente a `docs/archive/agent_vision_prototype.py` y verificar que ningún `import` en el proyecto lo referencia (hacer grep antes de mover).

---

## Fase 2 — Bugs funcionales (output incorrecto pero no bloquean)

### 2.1 Debuggear y eliminar la fecha hardcodeada en `pdf_reader.py`

**Problema:** `pdf_reader.py` línea 140 tiene `r'April 30, 2028'` como pattern literal en `_find_end_date()`. Es un parche para que CONTRACT_002 pase el test.

**Proceso de corrección:**
1. Añadir temporalmente un `logger.debug(repr(text))` en `_find_end_date()` y correr contra CONTRACT_002 para ver el texto raw extraído del PDF.
2. Identificar si hay saltos de línea (`\n`) o espacios extra que impiden que `r'until ([A-Z][a-z]+ \d+, \d{4})'` capture la fecha.
3. Corregir el pattern general (probablemente cambiar a `r'until\s+([A-Z][a-z]+\s+\d+,\s*\d{4})'` para tolerar whitespace variable).
4. Eliminar el literal hardcodeado.
5. Verificar que `TestCleanContract` sigue pasando.

---

### 2.2 Corregir dead code en `next_action` de Agent 4

**Problema:** `agent_explainer.py` líneas 300-305: ambas ramas del `elif`/`else` devuelven `"AWAIT_HUMAN_DECISION"`. `"ESCALATE"` nunca se asigna aunque el schema lo declara.

**Archivos a modificar:**
- `src/agent_explainer.py` líneas 300-305

**Cambio exacto:**
```python
# Antes (dead code):
if not human_review:
    next_action = "AUTO_APPROVE"
elif severity in ("CRITICAL", "HIGH"):
    next_action = "AWAIT_HUMAN_DECISION"
else:
    next_action = "AWAIT_HUMAN_DECISION"

# Después (lógica real):
if not human_review:
    next_action = "AUTO_APPROVE"
elif severity == "CRITICAL":
    next_action = "ESCALATE"
else:
    next_action = "AWAIT_HUMAN_DECISION"
```

**Impacto en tests:** `TestNoExpiryContract` debe actualizar su assert para esperar `next_action == "ESCALATE"` (CONTRACT_001 tiene severidad CRITICAL).

---

### 2.3 Añadir `processing_time_ms` a `ValidatorOutput`

**Problema:** El Markdown del Agent 4 siempre muestra `0ms` para el Validator porque `ValidatorOutput` no tiene ese campo.

**Archivos a modificar:**
- `src/schemas.py` — Añadir `processing_time_ms: int` a `ValidatorOutput`
- `src/agent_validator.py` — Calcular `elapsed_ms` en `run()` y añadirlo al return
- `src/agent_explainer.py` — En `processing_times`, leer `validation_output.processing_time_ms`

---

## Fase 3 — Calidad de tests

### 3.1 Fortalecer `TestUnclearTotals`

**Problema:** El test actual solo verifica que los campos no son `None`. Pasa con cualquier output.

**Archivo:** `tests/test_pipeline.py` clase `TestUnclearTotals`

**Asserts a añadir:**
```python
assert result.status == "COMPLETE"
assert result.explanation.human_review_required is True
assert result.total_processing_time_ms < 30000
```

---

### 3.2 Añadir test para PDF inválido

**Archivo:** `tests/test_pipeline.py`

**Nuevo test:**
```python
class TestInvalidPDF:
    def test_nonexistent_file(self):
        result = run(run_pipeline("test_documents/NONEXISTENT.pdf"))
        assert result.status == "FAILED"
        assert result.error is not None
        assert result.vision is None
```

---

### 3.3 Corregir `asyncio.get_event_loop()` deprecado

**Archivo:** `tests/test_pipeline.py` línea 20

```python
# Antes:
def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)

# Después:
def run(coro):
    return asyncio.run(coro)
```

---

### 3.4 Añadir test que ejercite el path LLM de Agent 2

**Contexto:** Todos los tests actuales activan el fast path determinista. El código LLM de Agent 2 (`_call_with_retry`, `_sanitize_llm_data`) nunca se ejercita en tests.

**Opción A (sin mock):** Crear `test_documents/INVOICE_006_AMBIGUOUS.pdf` con texto ambiguo que no active keywords deterministas.

**Opción B (con mock, preferida):** En el test, parchear `agent_reasoning._issues_are_deterministic` para devolver `False` y verificar que el sistema aún produce output válido vía la ruta fallback LLM/reglas.

---

## Fase 4 — Limpieza de deuda técnica

### 4.1 Eliminar `chains.py`

**Acción:** Mover a `docs/archive/chains_prototype.py`. Sus clases tienen buena lógica pero tipos incompatibles con el pipeline (`TrapType.MATH_ERROR = "math_error"` vs `"Math Error"`). No hay imports activos que lo usen.

**Verificación previa (obligatoria):**
```bash
grep -r "from src.chains\|import chains\|from src import chains" src/ tests/
```

---

### 4.2 Corregir confidence inflada para documentos limpios

**Archivo:** `src/orchestrator.py` función `_generate_clean_explanation()` líneas 125-130

**Cambio:** Recibir `vision_output` como parámetro y usar su confidence real en lugar de `1.0` hardcodeado. Añadir nota en el markdown indicando que Agents 2-4 no fueron ejecutados.

---

## Fase 5 — Gates de calidad entre agentes + anomaly log

### Contexto de la decisión

En lugar de un 5° agente LLM que audite en tiempo real (lo cual duplicaría latencia en cada transición), se implementan **Gates deterministas** entre cada paso del pipeline más un **log estructurado de anomalías** que sirve como memoria de aprendizaje controlada y auditada.

```
Agent 1 → Gate(1→2) → Agent 2 → Gate(2→3) → Agent 3 → Gate(3→4) → Agent 4
                ↓                     ↓                     ↓
          anomaly_log.jsonl     anomaly_log.jsonl     anomaly_log.jsonl
```

La "evolución" no es automática ni modifica código en caliente — es un ciclo humano-supervisado: los Gates acumulan patrones, un humano los revisa, y actualiza los templates de reglas. Esto preserva el audit trail regulatorio.

---

### 5.1 Crear `src/pipeline_gates.py`

**Archivo nuevo:** `src/pipeline_gates.py`

Cada Gate recibe el output del agente anterior y devuelve una decisión: `PASS`, `RETRY` (con prompt ajustado), o `ESCALATE` (al humano sin continuar el pipeline).

**Estructura del módulo:**

```python
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
import json, logging
from pathlib import Path

from src.schemas import VisionOutput, ReasoningOutput, ValidatorOutput

class GateDecision(str, Enum):
    PASS = "PASS"
    RETRY = "RETRY"
    ESCALATE = "ESCALATE"

@dataclass
class GateResult:
    gate_id: str              # "gate_1_2", "gate_2_3", "gate_3_4"
    decision: GateDecision
    anomalies: list[str]      # lista de lo que encontró raro
    retry_hint: Optional[str] # contexto para el reintento si decision == RETRY
    document_id: str
    timestamp: str
```

**Gate 1→2** valida que el `VisionOutput` tiene sentido antes de entregarlo al Reasoning Engine:
- ¿Los `detected_issues` usan keywords reconocidos ("Math Error", "Missing Field", etc.)?
- ¿`confidence` > 0.3? (si es menor, el PDF probablemente no se leyó bien)
- ¿`document_type` no es `"unknown"` para un PDF que claramente tiene estructura financiera?

**Gate 2→3** valida que el `ReasoningOutput` no degradó la calidad:
- ¿`reasoning_chain` tiene ≥ 3 pasos con `evidence` y `conclusion` no vacíos?
- ¿`trap_detected` es consistente con los issues que venían del VisionOutput? (si Vision dijo "Math Error" y Reasoning dice "No Trap", es una anomalía grave)
- ¿`confidence` no bajó más de 0.3 puntos respecto a `vision_output.confidence` sin justificación?

**Gate 3→4** valida que el `ValidatorOutput` no contradice evidencia matemática:
- Si `math_verified == True` (error confirmado), ¿`trap_is_real == True`? (si no, es contradicción)
- Si `recommendation == "APPROVE"` y `trap_is_real == True`, registrar como anomalía (este era el bug 1.1)
- ¿`validation_confidence` es razonable dado el `reasoning_confidence` de entrada?

---

### 5.2 Crear `src/anomaly_logger.py`

**Archivo nuevo:** `src/anomaly_logger.py`

Log estructurado en `logs/anomaly_log.jsonl` (una línea JSON por evento). Formato append-only para no perder historial.

```python
def log_anomaly(gate_result: GateResult) -> None:
    """Append gate result to anomaly_log.jsonl."""
    Path("logs").mkdir(exist_ok=True)
    entry = {**asdict(gate_result), "logged_at": datetime.now().isoformat()}
    with open("logs/anomaly_log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def get_anomaly_patterns(last_n: int = 100) -> dict:
    """
    Lee las últimas N entradas del log y agrupa anomalías por tipo.
    Útil para revisión humana periódica.
    Returns: {anomaly_text: count} ordenado por frecuencia.
    """
```

---

### 5.3 Integrar Gates en `src/orchestrator.py`

**Archivo a modificar:** `src/orchestrator.py`

Importar los gates e insertarlos en `run_pipeline()` entre cada llamada de agente:

```python
from src.pipeline_gates import gate_1_2, gate_2_3, gate_3_4, GateDecision
from src.anomaly_logger import log_anomaly

# Entre Agent 1 y Agent 2:
gate_result = gate_1_2(vision_output)
log_anomaly(gate_result)
if gate_result.decision == GateDecision.ESCALATE:
    result.status = "PARTIAL"
    result.error = f"Gate 1→2 escalated: {gate_result.anomalies}"
    return result
# Si RETRY: ajustar parámetros y reintentar Agent 1 (máx 1 vez)
# Si PASS: continuar normal
```

**Política de reintentos:** máximo 1 reintento por gate. Si el segundo intento también falla el gate, se escala. Esto evita loops infinitos y mantiene el presupuesto de 30s.

---

### 5.4 Añadir tests para los Gates

**Archivo:** `tests/test_gates.py` (nuevo)

```python
# Test: Gate 1→2 detecta inconsistencia de trap_type
def test_gate_2_3_detects_contradiction():
    # Vision dice Math Error, Reasoning dice No Trap → anomalía
    ...

# Test: Gate 3→4 detecta math_verified=True con trap_is_real=False
def test_gate_3_4_detects_math_contradiction():
    ...

# Test: PASS en documentos correctos no genera entradas en anomaly_log
def test_gates_pass_on_clean_pipeline():
    ...
```

---

### 5.5 Script de revisión de patrones (herramienta humana)

**Archivo nuevo:** `tools/review_anomalies.py`

Script de línea de comandos para que un humano revise qué anomalías se han acumulado:

```bash
python tools/review_anomalies.py --last 50
# Output:
# Gate 2→3 anomalías (últimas 50 entradas):
#   "Trap type inconsistency: Vision=Math Error, Reasoning=No Trap" → 3 veces
#   "Confidence drop > 0.3 between agents" → 1 vez
#
# Acción sugerida: revisar _build_fallback_reasoning() para casos edge
```

Este script es el punto de entrada para la "evolución controlada": el humano lee los patrones, decide si ajustar los templates de reglas o los prompts LLM, y hace el cambio de forma explícita y versionada en git.

---

## Orden de ejecución (actualizado)

```
1.1 → 1.2 → 1.3              (críticos, sin dependencias entre sí)
     ↓
2.1 → 2.2 → 2.3              (2.1 debug regex primero)
     ↓
3.1 → 3.2 → 3.3 → 3.4       (tests validan el estado ya corregido)
     ↓
4.1 → 4.2                    (limpieza de deuda técnica)
     ↓
5.1 → 5.2 → 5.3 → 5.4 → 5.5 (gates + anomaly log — nueva funcionalidad)
```

Las Fases 1-4 corrigen lo que está roto. La Fase 5 añade la capa de calidad nueva. Se hace al final para no mezclar correcciones con nueva funcionalidad en el mismo commit.

---

## Verificación final

Una vez aplicadas todas las correcciones, correr en orden:

```bash
# 1. Verificar que no hay imports rotos
python -c "from src import schemas, pdf_reader, agent_reasoning, agent_validator, agent_explainer, orchestrator, api, pipeline_gates, anomaly_logger"

# 2. Correr test suite completa
pytest tests/ -v

# 3. Generar resultados de los 7 documentos
python tests/test_pipeline.py

# 4. Verificar semántica de recommendation
python -c "
import asyncio
from src.orchestrator import run_pipeline
r = asyncio.run(run_pipeline('test_documents/INVOICE_001_TRAP_MATH.pdf'))
assert r.validation.recommendation == 'FORWARD_FOR_REVIEW', r.validation.recommendation
assert r.explanation.next_action == 'AWAIT_HUMAN_DECISION'
print('1.1 OK')
"

# 5. Verificar monto dinámico en explicación
python -c "
import asyncio
from src.orchestrator import run_pipeline
r = asyncio.run(run_pipeline('test_documents/INVOICE_001_TRAP_MATH.pdf'))
assert '500' in r.explanation.explanation.financial_impact
print('1.2 OK')
"

# 6. Verificar ESCALATE para CRITICAL
python -c "
import asyncio
from src.orchestrator import run_pipeline
r = asyncio.run(run_pipeline('test_documents/CONTRACT_001_TRAP_NO_EXPIRY.pdf'))
assert r.explanation.next_action == 'ESCALATE', r.explanation.next_action
print('2.2 OK')
"

# 7. Verificar documentos limpios siguen siendo AUTO_APPROVE
python -c "
import asyncio
from src.orchestrator import run_pipeline
r = asyncio.run(run_pipeline('test_documents/INVOICE_002_NORMAL.pdf'))
assert r.explanation.next_action == 'AUTO_APPROVE'
print('clean OK')
"

# 8. Verificar que los gates pasan para documentos correctos
python -c "
import asyncio, os
from src.orchestrator import run_pipeline
os.remove('logs/anomaly_log.jsonl') if os.path.exists('logs/anomaly_log.jsonl') else None
r = asyncio.run(run_pipeline('test_documents/INVOICE_002_NORMAL.pdf'))
assert not os.path.exists('logs/anomaly_log.jsonl') or open('logs/anomaly_log.jsonl').read() == ''
print('5.x gates clean OK')
"

# 9. Revisar anomalías acumuladas del run completo
python tools/review_anomalies.py --last 100
```

---

## Estimación de tiempo

| Fase | Tareas | Tiempo estimado |
|------|--------|-----------------|
| 1 — Críticos | 1.1, 1.2, 1.3 | 45 min |
| 2 — Funcionales | 2.1, 2.2, 2.3 | 60 min |
| 3 — Tests | 3.1, 3.2, 3.3, 3.4 | 30 min |
| 4 — Limpieza | 4.1, 4.2 | 20 min |
| 5 — Gates + anomaly log | 5.1, 5.2, 5.3, 5.4, 5.5 | 90 min |
| **Total** | | **~4 horas** |
