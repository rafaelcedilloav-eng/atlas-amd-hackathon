"""
ATLAS Orchestrator v2.0
Gestiona el flujo secuencial entre agentes con Compliance Router y Audit Events.
Vision -> Compliance -> Reasoning -> Validator -> Explainer -> Supabase
"""
import time
import logging
from datetime import datetime
from typing import Optional, List

from src.agent_vision import VisionAnalyzerAgent
from src.agent_reasoning import ReasoningAgent
from src.agent_validator import ValidatorAgent
from src.agent_explainer import ExplainerAgent
from src.schemas import PipelineResult, MarketData
from src.supabase_persistence import save_audit_result
from src.compliance_router import run_compliance_check
from src.pipeline_gates import gate_1_2, gate_2_3, gate_3_4, GateDecision
from src.anomaly_logger import log_anomaly
from src.audit_emitter import (
    event_bus,
    emit_vision_start, emit_vision_complete,
    emit_compliance_start, emit_compliance_findings,
    emit_reasoning_start, emit_reasoning_step, emit_reasoning_complete,
    emit_validator_start, emit_validator_gate, emit_validator_complete,
    emit_explainer_start, emit_explainer_complete,
    emit_pipeline_complete, emit_error
)

logger = logging.getLogger(__name__)

async def run_pipeline(pdf_path: str, audit_id: Optional[str] = None) -> PipelineResult:
    """
    Ejecuta el pipeline completo de ATLAS v2.0 con Compliance y X-Ray.
    """
    start_time = time.time()
    
    # Instanciar agentes
    vision_agent = VisionAnalyzerAgent()
    reasoning_agent = ReasoningAgent()
    validator_agent = ValidatorAgent()
    explainer_agent = ExplainerAgent()

    # ── 1. VISION (Extracción) ──────────────────────────────────────────────
    await emit_vision_start(audit_id or "pending")
    
    vision_out = await vision_agent.analyze_document(pdf_path)
    audit_id = vision_out.document_id
    
    # Register SSE stream
    event_bus.get_or_create_stream(audit_id)
    
    # Quality Gate 1→2
    g12 = gate_1_2(vision_out)
    log_anomaly(g12)
    if g12.decision == GateDecision.ESCALATE:
        return await _handle_critical_failure(audit_id, pdf_path, vision_out, f"Gate 1→2 ESCALATE: {g12.anomalies}", start_time)

    await emit_vision_complete(audit_id, vision_out.confidence, len(vision_out.extracted_fields))
    
    # Short-Circuit
    if not vision_out.extracted_fields and vision_out.confidence < 0.1:
        return await _handle_critical_failure(audit_id, pdf_path, vision_out, "Fallo crítico de extracción de texto.", start_time)

    # ── 2. COMPLIANCE (Nuevo: Router de 11 países) ──────────────────────────
    await emit_compliance_start(audit_id, "detectando país...")
    
    compliance_result = run_compliance_check(
        raw_text=vision_out.raw_text or "",
        xml_content=None,
        extracted_fields=vision_out.extracted_fields,
        filename=pdf_path
    )
    
    await emit_compliance_findings(
        audit_id,
        len(compliance_result.findings),
        compliance_result.compliance_score,
        compliance_result.country_detected
    )

    # ── 3. REASONING (Análisis Forense) ─────────────────────────────────────
    await emit_reasoning_start(audit_id)
    
    try:
        # El razonador ahora recibe los hallazgos de compliance para cruzar datos
        reasoning_out = await reasoning_agent.reason_about_document(vision_out, compliance_result)
        
        # Quality Gate 2→3
        g23 = gate_2_3(vision_out, reasoning_out)
        log_anomaly(g23)
        
        for i, step in enumerate(reasoning_out.reasoning_chain[:3]):
            await emit_reasoning_step(audit_id, step.step, step.conclusion)
        await emit_reasoning_complete(audit_id, reasoning_out.trap_detected, reasoning_out.trap_severity)
    except Exception as e:
        logger.error(f"Agent 2 falló: {e}")
        await emit_error(audit_id, "reasoning", str(e))
        from src.schemas import ReasoningOutput, ReasoningStep
        reasoning_out = ReasoningOutput(
            document_id=audit_id, trap_detected="Unclear Value", trap_id=f"T-ERR",
            reasoning_chain=[ReasoningStep(step=1, description="Error", evidence=str(e), conclusion="Fallido")],
            trap_severity="MEDIUM", confidence=0.3, reasoning_valid=False, assumptions=[],
            model_used="fallback", processing_time_ms=0, timestamp=datetime.now()
        )

    # ── 4. VALIDATOR (Gate de Integridad) ───────────────────────────────────
    await emit_validator_start(audit_id)
    
    try:
        validator_out = await validator_agent.validate_integrity(vision_out, reasoning_out)
        
        # Quality Gate 3→4
        g34 = gate_3_4(reasoning_out, validator_out)
        log_anomaly(g34)
        
        math_pass = validator_out.validation_result.math_verified
        await emit_validator_gate(audit_id, "math", math_pass or False,
            validator_out.validation_result.math_verification_detail or "N/A")
        
        is_dup = "DUPLICADO" in str(validator_out.issues_found)
        await emit_validator_gate(audit_id, "duplicate", not is_dup, "Doc único")
        
        is_bl = "LISTA NEGRA" in str(validator_out.issues_found)
        await emit_validator_gate(audit_id, "blacklist", not is_bl, "Proveedor limpio")
        
        await emit_validator_complete(audit_id, validator_out.recommendation)
    except Exception as e:
        logger.error(f"Agent 3 falló: {e}")
        await emit_error(audit_id, "validator", str(e))
        validator_out = None

    # ── 5. EXPLAINER (Reporte Ejecutivo) ────────────────────────────────────
    partial_result = PipelineResult(
        document_id=audit_id, pdf_path=pdf_path, status="PARTIAL",
        vision=vision_out, compliance=compliance_result, reasoning=reasoning_out,
        validation=validator_out, total_processing_time_ms=int((time.time() - start_time) * 1000),
        timestamp=datetime.now(),
    )

    await emit_explainer_start(audit_id)
    
    try:
        explainer_out = await explainer_agent.generate_report(partial_result)
        await emit_explainer_complete(audit_id, explainer_out.next_action)
    except Exception as e:
        logger.error(f"Agent 4 falló: {e}")
        await emit_error(audit_id, "explainer", str(e))
        explainer_out = None

    # ── 6. MARKET INTELLIGENCE (Dynamic from Explainer) ─────────────────────
    market_intel = getattr(explainer_out, "market_intelligence", []) if explainer_out else []

    # ── 7. RESULTADO FINAL ──────────────────────────────────────────────────
    final_status = "COMPLETE" if explainer_out is not None else "PARTIAL"
    final_result = PipelineResult(
        document_id=audit_id, pdf_path=pdf_path, status=final_status,
        vision=vision_out, compliance=compliance_result, reasoning=reasoning_out,
        validation=validator_out, explanation=explainer_out,
        market_intelligence=market_intel,
        total_processing_time_ms=int((time.time() - start_time) * 1000),
        timestamp=datetime.now(),
    )

    _persist_final_result(final_result)
    await emit_pipeline_complete(audit_id, final_status, final_result.total_processing_time_ms)

    return final_result

async def _handle_critical_failure(audit_id, pdf_path, vision, error, start_time):
    await emit_error(audit_id, "orchestrator", error)
    result = PipelineResult(
        document_id=audit_id, pdf_path=pdf_path, status="FAILED",
        vision=vision, total_processing_time_ms=int((time.time() - start_time) * 1000),
        error=error, timestamp=datetime.now()
    )
    _persist_final_result(result)
    await emit_pipeline_complete(audit_id, "FAILED", result.total_processing_time_ms)
    return result

_NEXT_ACTION_TO_STATUS = {
    "AUTO_APPROVE": "APPROVE",
    "ESCALATE": "ESCALATE",
    "AWAIT_HUMAN_DECISION": "FLAG",
}
_RECOMMENDATION_TO_FRAUD = {
    "APPROVE": "LIMPIO",
    "FORWARD_FOR_REVIEW": "FRAUDE_CONFIRMADO",
    "FLAG": "SOSPECHOSO",
    "UNCERTAIN": "SOSPECHOSO",
}
_SEVERITY_ES = {
    "CRITICAL": "CRÍTICO", "HIGH": "ALTO",
    "MEDIUM": "MEDIO", "LOW": "BAJO", "NONE": "NINGUNO",
}

def _persist_final_result(result: PipelineResult):
    """Guarda el resultado consolidado en la tabla audit_results."""
    try:
        issues_str = str(result.validation.issues_found) if result.validation else ""
        is_dup = "DUPLICADO" in issues_str
        is_bl = "LISTA NEGRA" in issues_str

        recommendation = result.validation.recommendation if result.validation else "UNCERTAIN"
        fraud_class = "FRAUDE_CONFIRMADO" if (is_dup or is_bl) else _RECOMMENDATION_TO_FRAUD.get(recommendation, "SOSPECHOSO")
        severity_raw = result.validation.validation_result.severity_confirmed if result.validation else "MEDIUM"
        next_action = result.explanation.next_action if result.explanation else "AWAIT_HUMAN_DECISION"
        
        data = {
            "doc_id": result.document_id,
            "result_json": result.model_dump(mode="json"),
            "fraud_type": result.reasoning.trap_detected if result.reasoning else "Unknown",
            "fraud_classification": fraud_class,
            "severity": _SEVERITY_ES.get(severity_raw, "MEDIO"),
            "reasoning_chain": "; ".join(f"[{s.step}] {s.conclusion}" for s in result.reasoning.reasoning_chain) if result.reasoning else "",
            "confidence_score": float(result.explanation.confidence_breakdown.overall_confidence) if result.explanation else 0.0,
            "math_validation": result.validation.validation_result.math_verified if result.validation else None,
            "is_duplicate": is_dup,
            "is_blacklisted": is_bl,
            "integrity_passed": not (result.validation.validation_result.trap_is_real) if result.validation else False,
            "final_status": _NEXT_ACTION_TO_STATUS.get(next_action, "FLAG"),
            "executive_report": result.explanation.markdown_report if result.explanation else "Pipeline incompleto",
            "recommended_action": next_action,
            "pipeline_version": "2.0.0",
            "processing_time_ms": result.total_processing_time_ms,
        }
        save_audit_result(data)
    except Exception as e:
        logger.error(f"Error persistiendo resultado final: {e}")
