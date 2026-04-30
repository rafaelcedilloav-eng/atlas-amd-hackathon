"""
ATLAS Orchestrator v2.0
Vision -> Compliance -> Reasoning -> Validator -> Explainer -> Supabase
Includes SSE event emission via audit_emitter for the X-Ray Panel.
"""
import time
import logging
from datetime import datetime
from typing import Optional

from src.agent_vision import VisionAnalyzerAgent
from src.agent_reasoning import ReasoningAgent
from src.agent_validator import ValidatorAgent
from src.agent_explainer import ExplainerAgent
from src.schemas import PipelineResult
from src.supabase_persistence import save_audit_result
from src.compliance_router import run_compliance_check
from src.audit_emitter import (
    event_bus,
    emit_vision_start, emit_vision_complete,
    emit_compliance_start, emit_compliance_findings,
    emit_reasoning_start, emit_reasoning_step, emit_reasoning_complete,
    emit_validator_start, emit_validator_gate, emit_validator_complete,
    emit_explainer_start, emit_explainer_complete,
    emit_pipeline_complete, emit_error,
)

logger = logging.getLogger(__name__)


async def run_pipeline(pdf_path: str) -> PipelineResult:
    start_time = time.time()

    vision_agent    = VisionAnalyzerAgent()
    reasoning_agent = ReasoningAgent()
    validator_agent = ValidatorAgent()
    explainer_agent = ExplainerAgent()

    # ── 1. VISION ─────────────────────────────────────────────────────────────
    vision_out = await vision_agent.analyze_document(pdf_path)
    audit_id   = vision_out.document_id

    # Create SSE stream now that we have the real audit_id
    event_bus.create_audit_stream(audit_id)

    # Emit vision events (for SSE history replay)
    await emit_vision_start(audit_id)
    await emit_vision_complete(audit_id, vision_out.confidence, len(vision_out.extracted_fields))

    # Short-circuit on critical vision failure
    if not vision_out.extracted_fields and vision_out.confidence < 0.1:
        logger.error(f"Short-Circuit: critical vision failure for {pdf_path}")
        await emit_error(audit_id, "vision", "Fallo crítico de extracción de texto")
        result = PipelineResult(
            document_id=audit_id, pdf_path=pdf_path, status="FAILED",
            vision=vision_out,
            total_processing_time_ms=int((time.time() - start_time) * 1000),
            error="Fallo crítico de extracción de texto.", timestamp=datetime.now(),
        )
        _persist_final_result(result)
        await emit_pipeline_complete(audit_id, "FAILED", result.total_processing_time_ms)
        return result

    # ── 2. COMPLIANCE ─────────────────────────────────────────────────────────
    compliance_result = None
    try:
        from src.agent_vision_extractor import extract_document_robust
        extraction = extract_document_robust(pdf_path)
        raw_text   = extraction.get("raw_text", "")
        xml_content = extraction.get("structured_text") if extraction.get("extraction_method") == "pymupdf4llm" else None

        await emit_compliance_start(audit_id, "detectando...")
        compliance_result = run_compliance_check(
            raw_text=raw_text,
            xml_content=xml_content,
            extracted_fields=vision_out.extracted_fields,
            filename=pdf_path,
        )
        await emit_compliance_findings(
            audit_id,
            len(compliance_result.findings),
            compliance_result.compliance_score,
            compliance_result.country_detected,
        )
    except Exception as e:
        logger.warning(f"Compliance check failed (non-blocking): {e}")
        await emit_error(audit_id, "compliance", str(e))

    # ── 3. REASONING ──────────────────────────────────────────────────────────
    await emit_reasoning_start(audit_id)
    try:
        reasoning_out = await reasoning_agent.reason_about_document(vision_out)
        for step in reasoning_out.reasoning_chain[:3]:
            await emit_reasoning_step(audit_id, step.step, step.conclusion)
        await emit_reasoning_complete(audit_id, reasoning_out.trap_detected, reasoning_out.trap_severity)
    except Exception as e:
        logger.error(f"Agent 2 failed: {e}")
        await emit_error(audit_id, "reasoning", str(e))
        from src.schemas import ReasoningOutput, ReasoningStep
        reasoning_out = ReasoningOutput(
            document_id=audit_id,
            trap_detected="Unclear Value",
            trap_id=f"T-{audit_id[:8]}-ERR",
            reasoning_chain=[
                ReasoningStep(step=1, description="Agente 2 falló", evidence=str(e)[:100], conclusion="Análisis incompleto"),
                ReasoningStep(step=2, description="Fallback de emergencia", evidence="Error de sistema", conclusion="Revisión humana requerida"),
                ReasoningStep(step=3, description="Escalamiento", evidence="Sistema no disponible", conclusion="Escalar al equipo de auditoría"),
            ],
            trap_severity="MEDIUM", confidence=0.3, reasoning_valid=False,
            assumptions=["Error de sistema — análisis no confiable"],
            model_used="emergency-fallback", processing_time_ms=0,
            timestamp=datetime.now(), used_fallback=True,
        )

    # ── 4. VALIDATOR ──────────────────────────────────────────────────────────
    await emit_validator_start(audit_id)
    try:
        validator_out = await validator_agent.validate_integrity(vision_out, reasoning_out)

        math_pass = validator_out.validation_result.math_verified
        await emit_validator_gate(audit_id, "math", bool(math_pass),
            validator_out.validation_result.math_verification_detail or "N/A")

        is_dup = "DUPLICADO" in str(validator_out.issues_found)
        await emit_validator_gate(audit_id, "duplicate", not is_dup,
            "Documento duplicado detectado" if is_dup else "Documento único confirmado")

        is_bl = "LISTA NEGRA" in str(validator_out.issues_found)
        await emit_validator_gate(audit_id, "blacklist", not is_bl,
            "Proveedor en lista negra" if is_bl else "Proveedor limpio")

        await emit_validator_complete(audit_id, validator_out.recommendation)
    except Exception as e:
        logger.error(f"Agent 3 failed: {e}")
        await emit_error(audit_id, "validator", str(e))
        from src.schemas import ValidatorOutput, ValidationResult
        from decimal import Decimal
        validator_out = ValidatorOutput(
            document_id=audit_id, trap_id=reasoning_out.trap_id,
            validation_result=ValidationResult(
                logically_sound=False, trap_is_real=False, severity_confirmed="MEDIUM",
                math_verified=None, math_verification_detail="Validación no ejecutada",
            ),
            validation_confidence=Decimal("0.3"),
            issues_found=[f"Error en Agente 3: {str(e)[:100]}"],
            adjustments=[], recommendation="UNCERTAIN",
            recommendation_detail="Error en validación — revisión humana requerida",
            model_used="emergency-fallback", timestamp=datetime.now(),
        )

    # ── 5. EXPLAINER ──────────────────────────────────────────────────────────
    partial_result = PipelineResult(
        document_id=audit_id, pdf_path=pdf_path, status="PARTIAL",
        vision=vision_out, compliance=compliance_result,
        reasoning=reasoning_out, validation=validator_out,
        total_processing_time_ms=int((time.time() - start_time) * 1000),
        timestamp=datetime.now(),
    )

    await emit_explainer_start(audit_id)
    try:
        explainer_out = await explainer_agent.generate_report(partial_result)
        await emit_explainer_complete(audit_id, explainer_out.next_action)
    except Exception as e:
        logger.error(f"Agent 4 failed: {e}")
        await emit_error(audit_id, "explainer", str(e))
        explainer_out = None

    # ── 6. FINAL RESULT ───────────────────────────────────────────────────────
    final_status = "COMPLETE" if explainer_out is not None else "PARTIAL"
    final_result = PipelineResult(
        document_id=audit_id, pdf_path=pdf_path, status=final_status,
        vision=vision_out, compliance=compliance_result,
        reasoning=reasoning_out, validation=validator_out,
        explanation=explainer_out,
        total_processing_time_ms=int((time.time() - start_time) * 1000),
        timestamp=datetime.now(),
    )

    _persist_final_result(final_result)
    await emit_pipeline_complete(audit_id, final_status, final_result.total_processing_time_ms)

    return final_result


# ── Mapping tables ────────────────────────────────────────────────────────────

_NEXT_ACTION_TO_STATUS = {
    "AUTO_APPROVE": "APPROVE",
    "ESCALATE": "ESCALATE",
    "AWAIT_HUMAN_DECISION": "FLAG",
}
_RECOMMENDATION_TO_FRAUD = {
    "APPROVE": "LIMPIO",
    "FLAG": "SOSPECHOSO",
    "UNCERTAIN": "SOSPECHOSO",
}
_SEVERITY_ES = {
    "CRITICAL": "CRÍTICO", "HIGH": "ALTO",
    "MEDIUM": "MEDIO", "LOW": "BAJO", "NONE": "NINGUNO",
}


def _persist_final_result(result: PipelineResult):
    """Persists consolidated result to audit_results table."""
    try:
        issues_str = str(result.validation.issues_found) if result.validation else ""
        is_dup = "DUPLICADO" in issues_str
        is_bl  = "LISTA NEGRA" in issues_str

        recommendation = result.validation.recommendation if result.validation else "UNCERTAIN"
        fraud_class    = "FRAUDE_CONFIRMADO" if (is_dup or is_bl) else _RECOMMENDATION_TO_FRAUD.get(recommendation, "SOSPECHOSO")
        severity_raw   = result.validation.validation_result.severity_confirmed if result.validation else "MEDIUM"
        next_action    = result.explanation.next_action if result.explanation else "AWAIT_HUMAN_DECISION"
        math_pass      = result.validation.validation_result.math_verified if result.validation else None

        data = {
            "doc_id": result.document_id,
            "result_json": result.model_dump(mode="json"),
            "fraud_type": result.reasoning.trap_detected if result.reasoning else "Unknown",
            "fraud_classification": fraud_class,
            "severity": _SEVERITY_ES.get(severity_raw, "MEDIO"),
            "reasoning_chain": "; ".join(
                f"[{s.step}] {s.conclusion}" for s in result.reasoning.reasoning_chain
            ) if result.reasoning else "",
            "confidence_score": float(result.explanation.confidence_breakdown.overall_confidence) if result.explanation else 0.0,
            "math_validation": math_pass,
            "is_duplicate": is_dup,
            "is_blacklisted": is_bl,
            "integrity_passed": not result.validation.validation_result.trap_is_real if result.validation else False,
            "final_status": _NEXT_ACTION_TO_STATUS.get(next_action, "FLAG"),
            "executive_report": result.explanation.markdown_report if result.explanation else "Pipeline incompleto",
            "recommended_action": next_action,
            "pipeline_version": "2.0.0",
            "processing_time_ms": result.total_processing_time_ms,
        }
        save_audit_result(data)
    except Exception as e:
        logger.error(f"Error persisting final result: {e}")
