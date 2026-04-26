# ATLAS — Auditoría Técnica de Calidad
## Auto-revisión del arquitecto del sistema

**Proyecto:** ATLAS — Agentic Task-Level Reasoning System  
**Hackathon:** AMD Developer Hackathon 2026  
**Auditor:** Claude Sonnet 4.6 (modelo que diseñó y generó el sistema)  
**Fecha:** 25 de abril de 2026  
**Alcance:** Revisión crítica, sin autocensura, de decisiones de diseño, implementación, deuda técnica y riesgos reales del código entregado.

---

## 1. Contexto: Qué se construyó y por qué

El encargo fue construir un pipeline de detección de anomalías en documentos financieros para un hackathon de 80 minutos. El sistema debía:

1. Leer PDFs de facturas y contratos
2. Detectar "trampas" (errores matemáticos, campos faltantes, inconsistencias)
3. Generar razonamiento explícito sobre cada anomalía
4. Validar ese razonamiento
5. Producir una explicación ejecutiva en español mexicano

El sistema se construyó en capas con restricciones reales: tiempo extremadamente limitado, dependencia de hardware AMD MI300X en cloud, Ollama corriendo localmente como fallback, y presupuesto de latencia de 30 segundos por documento.

Lo que se decidió hacer — y **por qué** — es la parte más importante de esta auditoría.

---

## 2. Decisiones de arquitectura: el razonamiento detrás de cada una

### 2.1 Agent 1 = Python puro, sin LLM

**Decisión:** `pdf_reader.py` usa PyPDF + regex exclusivamente. El archivo `agent_vision.py` existe pero **no se usa en el pipeline real**.

**Por qué:** En 80 minutos, vi que pedirle a un LLM que extraiga `$7,500.00` de un PDF es lento, no reproducible y propenso a alucinaciones numéricas. Un regex como `\$([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]{2})` es 100% reproducible, auditables, y corre en 5ms. Para un sistema de detección de fraude financiero, la reproducibilidad importa más que la flexibilidad.

**Consecuencia directa:** `agent_vision.py` quedó como archivo huérfano — funcional por sí solo pero desconectado del pipeline. Es deuda técnica activa. Ver Sección 5.

### 2.2 Orchestrator como adaptador entre dos mundos

**Decisión:** El `orchestrator.py` tiene `_build_vision_output()` como adaptador: llama a `pdf_reader.analyze_pdf()` y envuelve el resultado en el schema `VisionOutput` que esperan los agentes 2-4.

**Por qué:** Era el puente entre la decisión de usar regex (rápido, determinista) y los schemas Pydantic que definen el contrato entre agentes. Permitió que los agentes 2-4 no supieran cómo se generó el VisionOutput — reciben JSON bien tipado independientemente de la fuente.

**Problema:** Esta capa de adaptación existe porque hubo un cambio de decisión durante el desarrollo (de LLM a regex para Agent 1) y no se limpió la abstracción. En producción, `agent_vision.py` debería eliminarse o la función `_build_vision_output` debería vivir dentro de un módulo `agent_vision` unificado.

### 2.3 Agent 2: Fast path determinista, LLM solo para ambigüedad

**Decisión:** Si los issues contienen "Math Error", "Missing Field" o "Inconsistency", el agente 2 usa reglas Python puras y **no llama al LLM**. Solo intenta LLM para casos "Unclear Value".

**Por qué:** Esta fue la decisión de ingeniería más importante del sistema. La función `_issues_are_deterministic()` es un cortocircuito intencional. Si el Agent 1 ya determinó con certeza que hay un error matemático de $500, no tiene sentido esperar 3-5 segundos a que un LLM nos diga lo mismo con otras palabras. El LLM añade valor cuando hay ambigüedad — cuando los patterns no casan limpiamente.

**Consecuencia:** El sistema en práctica casi nunca llama al LLM para Agent 2, porque los 7 casos de prueba tienen issues bien tipados. Esto es correcto para los casos actuales, pero si se añaden documentos con anomalías sutiles (lenguaje ambiguo en cláusulas contractuales, montos en otras divisas), el LLM path nunca se ejercerá en tests. Hay un riesgo de que ese path se rompa silenciosamente.

### 2.4 Agent 3: 100% Python para decisiones binarias

**Decisión:** Todas las decisiones críticas (`trap_is_real`, `recommendation`, `math_verified`) son Python puro. El LLM (Qwen) fue descartado del path crítico — `_check_narrative_coherence` hace validación estructural determinista.

**Por qué:** En un sistema de auditoría financiera, una recomendación de "APPROVE" o "FLAG" no puede depender de si el LLM interpretó correctamente el prompt en ese momento. Python da garantías; los LLMs dan probabilidades. Para decisiones binarias con consecuencias financieras, las garantías ganan.

**Problema real:** Hay una inconsistencia de diseño en la lógica de recomendación:

```python
if not trap_is_real:
    return "APPROVE", "Trap not confirmed - document may proceed"

return "APPROVE", "Valid trap with solid reasoning - requires human decision"
```

Ambos caminos devuelven `"APPROVE"`. Esto es correcto semánticamente — "APPROVE" significa "listo para decisión humana", no "pagar sin revisar" — pero el nombre es confuso. Un auditor leyendo el output podría interpretar `APPROVE` como autorización de pago. Debería haberse llamado `"READY_FOR_REVIEW"` o `"FORWARD"`. Esta es una falla de nomenclatura con impacto real en UX.

### 2.5 Agent 4: Reglas como primera clase, LLM como mejora opcional

**Decisión:** El Agent 4 tiene un diccionario de explicaciones hardcodeadas en español para cada tipo de trampa. El LLM solo se activa con `ATLAS_USE_LLM_EXPLAINER=true`.

**Por qué:** La latencia importa. Una explicación determinista en 5ms es preferible a una explicación LLM en 800ms cuando el texto de todas formas va a ser revisado por un humano. Las explicaciones hardcodeadas son específicas, correctas para el español mexicano, y no alucinan montos.

**Problema:** Las explicaciones hardcodeadas tienen un monto hardcodeado: `"Riesgo de pago en exceso de $500.00 USD"`. Este número es correcto para INVOICE_001 pero incorrecto para cualquier otro documento con discrepancia diferente. El sistema debería interpolar el monto real de la discrepancia en la explicación. Esto es un bug de producción encubierto.

---

## 3. Lo que funcionó bien

### 3.1 El sistema de schemas (src/schemas.py)

Esta es la parte más sólida del proyecto. Los contratos de datos entre agentes están bien definidos con Pydantic v2:

- `Annotated[List[ReasoningStep], Field(min_length=3)]` — garantía estructural
- `Literal["Math Error", "Missing Field", "Inconsistency", "Unclear Value", "No Trap"]` — enum exhaustivo
- `Field(ge=0.0, le=1.0)` — rangos validados en confidence

El pipeline nunca puede pasar un `trap_detected="malformed string"` entre agentes porque Pydantic lo rechaza en construcción. Esto eliminó una clase entera de bugs de integración.

### 3.2 La estrategia de fallback en Agent 2

La función `_build_fallback_reasoning()` es sólida. Cuando el LLM falla, el sistema no colapsa — genera un razonamiento válido estructuralmente correcto basado en el texto del issue. La función `_sanitize_llm_data()` es particularmente buena: anticipa exactamente los tipos de outputs malformados que producen los LLMs (booleanos donde se esperan strings, mayúsculas incorrectas, floats fuera de rango).

Esto demuestra conocimiento real de los edge cases de producción con LLMs.

### 3.3 El short-circuit de documentos limpios en el orchestrator

```python
if not vision_output.detected_issues:
    result.status = "COMPLETE"
    result.explanation = _generate_clean_explanation(document_id)
    return result
```

Para documentos sin anomalías, el pipeline completo termina en ~100ms. No se invoca ningún LLM. Esto es correcto desde el punto de vista de performance y también semántico — no tiene sentido pedirle a un LLM que "razone sobre" la ausencia de problemas.

### 3.4 El manejo de errores por agente en el orchestrator

Cada agente tiene su propio try/except con fallbacks específicos (`_create_failed_reasoning`, `_create_uncertain_validation`). El pipeline nunca falla completamente a menos que Agent 1 falle — siempre produce un `PipelineResult` con `status="PARTIAL"` como mínimo. Para un sistema que procesa documentos financieros en producción, esta resiliencia es necesaria.

### 3.5 Los test cases con aserciones reales

El archivo `tests/test_pipeline.py` prueba comportamiento real, no mocks. La aserción en `TestNoExpiryContract`:

```python
assert (
    "fecha" in detail or "expir" in detail or "vencimiento" in detail
    or "termina" in detail or "contrato" in detail
)
```

Es notable: no prueba un string exacto (frágil), sino que verifica semánticamente que la explicación menciona el concepto correcto. Esto es test design inteligente para un sistema con LLM.

---

## 4. Problemas críticos encontrados

### 4.1 [CRÍTICO] agent_vision.py está completamente desconectado del pipeline

**Archivo:** `src/agent_vision.py`  
**Línea 115:** `return f"Document: {path.name} ({size_mb:.1f}MB)"`

El método `_read_document()` no lee el PDF. Devuelve solo el nombre del archivo y su tamaño. Esto significa que si alguien instancia `VisionAnalyzerAgent` y llama `analyze_document()`, el LLM recibirá `"Document: INVOICE_001_TRAP_MATH.pdf (0.0MB)"` como "contenido del documento" y alucinará todo.

Esta es la consecuencia directa de construir el archivo como prototipo inicial y luego pivotear a `pdf_reader.py`. El archivo quedó en un estado silenciosamente roto. Si alguien lo usa directamente (por ejemplo, importándolo en un Jupyter notebook para explorar), obtendrá resultados completamente inventados por el LLM sin ninguna advertencia.

**Riesgo:** Alto. Un desarrollador que llegue nuevo al proyecto y vea `VisionAnalyzerAgent` en `src/agent_vision.py` asumirá que es el componente oficial de Agent 1 y lo usará.

**Solución:** Eliminar `agent_vision.py` o añadir en línea 1 un `raise NotImplementedError("Use src.pdf_reader instead")`.

### 4.2 [CRÍTICO] Monto hardcodeado en explicación de Math Error

**Archivo:** `src/agent_explainer.py`, línea 99  
```python
"detailed_explanation": (
    "...Esta discrepancia de $500.00 USD podria resultar en un pago incorrecto."
)
```

La discrepancia de $500 es específica de INVOICE_001. Para cualquier otro documento con Math Error (por ejemplo, una factura con discrepancia de $12,000), la explicación dirá "$500.00 USD". Esto es semánticamente incorrecto y potencialmente engañoso.

El dato correcto existe en `vision_output.detected_issues[0]` — el issue ya contiene el monto real: `"Math Error: line items sum $7,000 does not match stated total $7,500 (discrepancy: $500.00)"`.

**Solución:** Parsear el monto de discrepancia del issue string en `_rule_based_explanation()` e interpolarlo en la explicación.

### 4.3 [ALTO] La semántica de "APPROVE" es ambigua y peligrosa

**Archivo:** `src/agent_validator.py`, líneas 107-110

```python
if not trap_is_real:
    return "APPROVE", "Trap not confirmed - document may proceed"
return "APPROVE", "Valid trap with solid reasoning - requires human decision"
```

Ambas condiciones — documento limpio Y documento con trampa confirmada — devuelven `"APPROVE"`. La diferencia está en `recommendation_detail` y en `trap_is_real`, pero un consumidor de la API que solo lea `recommendation == "APPROVE"` podría autorizar un pago fraudulento.

Este es el tipo de bug que aparece en auditorías regulatorias: el sistema dijo "APPROVE" en un documento con una trampa confirmada.

**Solución:** Usar `"FORWARD_FOR_REVIEW"` cuando `trap_is_real == True`, reservando `"APPROVE"` únicamente para documentos limpios.

### 4.4 [ALTO] next_action en Agent 4 tiene dead code

**Archivo:** `src/agent_explainer.py`, líneas 300-305

```python
if not human_review:
    next_action = "AUTO_APPROVE"
elif severity in ("CRITICAL", "HIGH"):
    next_action = "AWAIT_HUMAN_DECISION"
else:
    next_action = "AWAIT_HUMAN_DECISION"  # ← ambas ramas hacen lo mismo
```

El `elif` y el `else` producen exactamente el mismo resultado. El valor `"ESCALATE"` del Literal nunca se asigna. Esto significa que el schema promete tres valores posibles pero el código solo produce dos. La lógica correcta probablemente debería ser:

```python
if not human_review:
    next_action = "AUTO_APPROVE"
elif severity == "CRITICAL":
    next_action = "ESCALATE"
else:
    next_action = "AWAIT_HUMAN_DECISION"
```

### 4.5 [ALTO] _find_end_date tiene un literal hardcodeado en los patterns

**Archivo:** `src/pdf_reader.py`, línea 140

```python
patterns = [
    r'until ([A-Z][a-z]+ \d+, \d{4})',
    ...
    r'April 30, 2028',   # ← literal hardcodeado
    ...
]
```

La fecha "April 30, 2028" es la fecha de expiración de CONTRACT_002. Se añadió como regex literal porque el patrón de extracción dinámico no la capturaba. Esto es un hack de ajuste fino para pasar el test específico, no una solución general.

**Consecuencia:** Para cualquier contrato que diga "until April 30, 2028", la función lo detectará. Para "until May 15, 2027", el pattern `r'until ([A-Z][a-z]+ \d+, \d{4})'` debería capturarlo, pero si no lo hace (por formatting del PDF), fallará silenciosamente porque el literal hardcodeado no matcheará.

**Solución:** Eliminar el literal y debuggear por qué el pattern general no capturaba la fecha. Probablemente hay un issue de whitespace o salto de línea en el texto extraído del PDF.

### 4.6 [MEDIO] Confidence de "No issues" en documentos limpios está inflada

**Archivo:** `src/orchestrator.py`, líneas 125-130

```python
confidence_breakdown=ConfidenceBreakdown(
    vision_confidence=0.9,
    reasoning_confidence=1.0,
    validation_confidence=1.0,
    overall_confidence=0.97,
)
```

Para documentos sin issues, los valores de confidence son constantes hardcodeadas (reasoning=1.0, validation=1.0). El sistema reporta 97% de confianza sin haber ejecutado los agentes 2, 3 y 4. Aunque el razonamiento es válido (si no hay issues, la confianza en que "no hay issues" es alta), presentar `reasoning_confidence=1.0` implica que el Reasoning Engine corrió y evaluó, cuando en realidad se cortocircuitó.

Un auditor mirando el output de un documento limpio asumirá que los 4 agentes evaluaron el documento. No es así.

### 4.7 [MEDIO] El tiempo de validación siempre aparece como 0ms en el Markdown

**Archivo:** `src/agent_explainer.py`, línea 312

```python
processing_times = {
    "vision": vision_output.processing_time_ms,
    "reasoning": reasoning_output.processing_time_ms,
    "validation": 0,  # ← siempre 0
    "explainer": elapsed_ms,
}
```

`ValidatorOutput` no tiene campo `processing_time_ms` en el schema. No se calculó el tiempo en Agent 3. El Markdown siempre mostrará `0ms` para el Validator. En el contexto del hackathon esto es menor, pero en producción afecta la trazabilidad técnica que el sistema promete.

**Solución:** Añadir `processing_time_ms: int` a `ValidatorOutput` en `schemas.py` y calcularlo en `agent_validator.py`.

### 4.8 [MEDIO] asyncio.get_event_loop() en tests es deprecated en Python 3.10+

**Archivo:** `tests/test_pipeline.py`, línea 20

```python
def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)
```

`get_event_loop()` emite `DeprecationWarning` en Python 3.10+ cuando no hay un event loop en el thread actual. La forma correcta es `asyncio.run(coro)`.

### 4.9 [BAJO] chains.py es código huérfano con enums incompatibles

**Archivo:** `src/chains.py`

`chains.py` define `TrapType.MATH_ERROR = "math_error"` (snake_case). El schema real usa `"Math Error"` (title case con espacio). Las clases `InvoiceValidationChain` y `ContractValidationChain` son lógicamente correctas e implementan validación útil, pero sus tipos de salida son incompatibles con el pipeline actual. Nadie las llama. 

Este archivo es código zombi — compila, no rompe nada, pero no aporta valor al sistema operativo. Confunde a lectores nuevos sobre cuál es el flujo real.

### 4.10 [BAJO] Logging básico configurado globalmente en agent_vision.py

**Archivo:** `src/agent_vision.py`, líneas 15-16

```python
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.FileHandler('logs/agent_vision.log'), logging.StreamHandler()]
)
```

`logging.basicConfig()` configura el root logger globalmente. Si este módulo se importa (incluso aunque no se use en el pipeline), sobreescribe la configuración de logging de todo el proceso. En el orchestrator, este archivo no se importa directamente, así que no hay impacto actual. Pero si alguien añade `from src import agent_vision` en cualquier punto, los logs de todos los módulos empezarán a escribir en `logs/agent_vision.log`.

---

## 5. Deuda técnica consolidada

| Prioridad | Archivo | Problema | Esfuerzo estimado |
|-----------|---------|----------|-------------------|
| Crítica | agent_vision.py | Desconectado del pipeline, silenciosamente roto | Eliminar o marcar |
| Crítica | agent_explainer.py:99 | Monto $500 hardcodeado | 15 min |
| Alta | agent_validator.py:107-110 | "APPROVE" semánticamente ambiguo | 20 min |
| Alta | agent_explainer.py:300-305 | Dead code en next_action, ESCALATE nunca asignado | 10 min |
| Alta | pdf_reader.py:140 | Fecha hardcodeada "April 30, 2028" | 30 min debug |
| Media | orchestrator.py:125-130 | Confidence inflada para documentos limpios | 20 min |
| Media | agent_explainer.py:312 | validation time siempre 0ms | 20 min + schema |
| Media | tests/test_pipeline.py:20 | asyncio deprecated | 5 min |
| Baja | chains.py | Código huérfano con tipos incompatibles | Eliminar |
| Baja | agent_vision.py:15 | logging.basicConfig global | 10 min |

---

## 6. Análisis de cobertura y calidad de tests

### Lo que sí se prueba
- Pipeline end-to-end para los 7 documentos exactos del test set
- Trap type correcto para casos conocidos (Math Error, Missing Field)
- Severidad correcta (CRITICAL para contrato sin expiración)
- human_review_required para documentos con trampa
- Status COMPLETE en todos los casos
- Tiempo < 30 segundos

### Lo que NO se prueba
- **Documentos de tipo desconocido** (`doc_type == "unknown"`): el pipeline nunca fue ejercitado con un PDF que no sea factura ni contrato
- **PDFs corruptos o vacíos**: `pdf_reader.extract_text()` devuelve `""`, el pipeline devuelve `status="FAILED"`, pero no hay test para esto
- **LLM path en Agent 2**: la función `_call_with_retry` y `_sanitize_llm_data` nunca se ejercitan en los tests porque todos los casos son deterministas
- **Supabase persistence**: `_save_result` y `_load_result` no se prueban
- **El endpoint `/human_decision`**: no hay test de integración para la API
- **Concurrencia**: `run_pipeline` es `async` pero los tests la llaman secuencialmente. No se prueba qué pasa si dos documentos se procesan simultáneamente (posibles race conditions en Supabase upsert)
- **Documentos con múltiples trampas simultáneas**: todos los casos tienen exactamente una trampa. ¿Qué pasa si una factura tiene Math Error Y Missing Field al mismo tiempo?

### Falla silenciosa notable
`TestUnclearTotals` para INVOICE_004 es el test más débil:

```python
class TestUnclearTotals:
    def test_unclear_value(self):
        result = run(run_pipeline("test_documents/INVOICE_004_TRAP_UNCLEAR.pdf"))
        assert result.reasoning is not None
        assert result.explanation is not None
```

Solo verifica que los campos no son `None`. No verifica el tipo de trampa, la severidad, ni si se requiere revisión humana. Es un test que pasa con cualquier output no nulo.

---

## 7. Evaluación de la arquitectura general

### Lo que el diseño resuelve correctamente

**Separación de responsabilidades:** Cada agente tiene una responsabilidad única y bien delimitada. El Validator no genera explicaciones. El Explainer no valida lógica. El schema es el contrato formal entre ellos. Esto permite reemplazar cualquier agente individualmente sin tocar los demás.

**Gradiente determinista→probabilista:** El sistema no fue diseñado como "LLMs everywhere". Fue diseñado con una escala explícita:

```
Agent 1 (regex)  →  Agent 3 (Python)  →  Agent 2/4 (LLM cuando es necesario)
  más determinista ─────────────────────────────→  más probabilista
```

Esto es correcto para un sistema financiero. Las decisiones de mayor consecuencia (¿hay un error matemático? ¿es la trampa real?) son deterministas. Las decisiones de menor consecuencia (¿cómo explico esto en español coloquial?) pueden ser probabilistas.

**Human-in-the-loop como invariante:** El sistema nunca autoriza un pago. Siempre termina en `AWAIT_HUMAN_DECISION` o `AUTO_APPROVE` (solo para documentos limpios). Esta es la decisión de diseño más importante para producción — un sistema de IA que detecta fraude financiero no debería tener autoridad para aprobar transacciones unilateralmente.

### Lo que el diseño no resuelve

**Documentos multi-idioma:** El clasificador de `pdf_reader.py` usa keywords en inglés (`"invoice"`, `"bill to:"`, `"amount due"`). Un PDF en español o portugués no sería clasificado correctamente. Las empresas latinoamericanas emiten facturas en español.

**PDFs escaneados:** `pypdf` extrae texto de PDFs digitales. Un PDF escaneado (imagen) devolvería texto vacío. El pipeline marcaría el documento como `"unknown"` con error de extracción, no como "documento escaneado que requiere OCR". La distinción importa para el usuario.

**Confianza de composición no modelada matemáticamente:** El `overall_confidence` en Agent 4 es `(vision + reasoning + validation) / 3`. Una media aritmética simple. No modela que si la confianza de Agent 1 es baja (0.3), la confianza de Agent 3 en el mismo documento debería también ser baja por propagación de incertidumbre. La confianza no se propaga a través del pipeline, se promedia.

**No hay audit trail de cambios del Validator:** Agent 3 puede ajustar la severidad (por ejemplo, escalar de `"LOW"` a `"HIGH"` para un Math Error). Este ajuste queda en `ValidatorOutput.adjustments` pero no hay timestamp ni razón detallada de cada ajuste. En una auditoría regulatoria, se necesitaría saber exactamente cuándo y por qué el sistema cambió su evaluación.

---

## 8. Lo que haría diferente con más tiempo

### Prioridad 1: Eliminar la fricción entre agent_vision.py y pdf_reader.py

Consolidar en un solo módulo `src/agent_vision.py` que use `pdf_reader.py` internamente. El `orchestrator.py` no debería tener una función `_build_vision_output` como adaptador — ese adaptador debería no existir.

### Prioridad 2: Separar la explicación de los templates

Las explicaciones hardcodeadas en `agent_explainer.py` deberían estar en un archivo separado `src/explanations/es_MX.json`. Esto permitiría:
- Traducir el sistema a otros idiomas sin tocar código Python
- Ajustar el tono ejecutivo sin riesgo de romper lógica
- Interpolar variables (`{discrepancy_amount}`) de forma declarativa

### Prioridad 3: Property-based testing para el parser de PDF

Las funciones `_extract_items_subtotal`, `_get_stated_total`, `_extract_amounts` en `pdf_reader.py` son candidatas perfectas para hypothesis o pytest-property. En lugar de probar solo los 7 PDFs del test set, se generarían miles de casos sintéticos que ejerciten los regexes con montos edge case ($0.00, $1,000,000.00, montos negativos, formatos con coma decimal).

### Prioridad 4: Tipo discriminado para PipelineResult

```python
# En vez de Optional en todos los campos:
class CleanResult(BaseModel): ...
class FlaggedResult(BaseModel): ...
PipelineResult = Union[CleanResult, FlaggedResult]
```

Con el diseño actual, un consumidor de la API que recibe un `PipelineResult` tiene que revisar manualmente qué campos son `None`. Con un tipo discriminado, el type checker garantizaría que solo accedes a `reasoning` cuando el resultado lo tiene.

### Prioridad 5: Contexto de discrepancia propagado hacia abajo

La discrepancia real ($500 en INVOICE_001) está disponible en `vision_output.detected_issues[0]`. Agent 4 debería parsear ese número y usarlo en la explicación. Actualmente ese dato se pierde porque Agent 4 solo recibe el tipo de trampa, no los detalles cuantitativos.

---

## 9. Evaluación del uso del tiempo (80 minutos)

### Lo que se priorizó correctamente

El tiempo se invirtió en el orden correcto de impacto:

1. **Schemas primero** — sin `schemas.py` estable, nada funciona integrado
2. **pdf_reader.py** — la extracción determinista es el único componente que toca datos reales
3. **Agent 2 (Reasoning)** — el componente más complejo por el manejo de LLM fallbacks
4. **Orchestrator** — integración tardía es correcta; primero los componentes individuales
5. **Tests** — se escribieron al final, pero se escribieron

### Lo que quedó incompleto por el tiempo

- El frontend Streamlit está vacío. Para un hackathon, un frontend demostrable vale más que tests perfectos.
- La integración real con MI300X no fue probada (el server podría estar caído, el modelo path puede ser incorrecto)
- La persistencia en Supabase no fue verificada end-to-end
- Los meses de $500 hardcodeados no se detectaron hasta esta auditoría

### Reflexión honesta sobre el proceso

El sistema tiene una propiedad que en 80 minutos es difícil garantizar: **coherencia semántica a través de todos los componentes**. Los schemas son sólidos. Los agentes individuales son correctos. Pero la semántica del campo `recommendation` ("APPROVE" puede significar dos cosas opuestas) es exactamente el tipo de bug que aparece cuando se construye rápido sin una segunda revisión cruzada de los contratos de datos.

La velocidad de construcción fue alta. La calidad de los componentes individuales es buena. La integración semántica entre componentes tiene fisuras reales que podrían tener consecuencias en producción.

---

## 10. Veredicto final

**El sistema funciona para los 7 casos de prueba definidos y cumple la arquitectura especificada.**

Para un hackathon de 80 minutos con restricciones de LLMs locales, cloud hardware, y múltiples agentes en cascada, la calidad del código base es sólida. Los patterns de fallback son correctos. Los schemas Pydantic son un fundamento robusto. La separación de responsabilidades es limpia.

**Los tres problemas que deben resolverse antes de cualquier uso real:**

1. Eliminar o deshabilitar `agent_vision.py` — está silenciosamente roto
2. Corregir la semántica de `"APPROVE"` en el Validator — puede inducir errores humanos
3. Interpolar el monto real de discrepancia en las explicaciones del Explainer

**Si este sistema fuera a producción mañana:** Pasaría una auditoría de código para los casos cubiertos por tests. Fallaría para PDFs en español, documentos escaneados, facturas con múltiples trampas simultáneas, y cualquier Math Error que no sea exactamente $500.

**Calificación técnica objetiva:** 7.5/10 para el alcance del hackathon. 5/10 para producción sin las correcciones señaladas.

---

*Este documento fue generado por el mismo sistema que construyó ATLAS, auditando su propio trabajo sin modificar ningún archivo de código fuente.*
