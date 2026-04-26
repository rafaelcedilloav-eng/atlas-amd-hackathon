"""
ATLAS Orchestrator
Gestiona el flujo secuencial entre agentes y asegura la persistencia final.
Vision -> Reasoning -> Validator -> Explainer -> Supabase
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

logger = logging.getLogger(__name__)

async def run_pipeline(pdf_path: str) -> PipelineResult:
    """
    Ejecuta el pipeline completo de ATLAS.
    """
    start_time = time.time()
    
    # Instanciar agentes
    vision_agent = VisionAnalyzerAgent()
    reasoning_agent = ReasoningAgent()
    validator_agent = ValidatorAgent()
    explainer_agent = ExplainerAgent()
    
    # 1. Vision (Extracción)
    vision_out = await vision_agent.analyze_document(pdf_path)
    
    # Lógica de Short-Circuit: Si no hay texto o falló extracción crítica
    if not vision_out.extracted_fields and vision_out.confidence < 0.1:
        logger.error(f"Short-Circuit: Fallo crítico de visión para {pdf_path}")
        result = PipelineResult(
            document_id=vision_out.document_id,
            pdf_path=pdf_path,
            status="FAILED",
            vision=vision_out,
            total_processing_time_ms=int((time.time() - start_time) * 1000),
            error="Fallo crítico de extracción de texto.",
            timestamp=datetime.now()
        )
        _persist_final_result(result)
        return result

    # 2. Reasoning (Análisis Forense) — con fallback integrado en el agente
    try:
        reasoning_out = await reasoning_agent.reason_about_document(vision_out)
    except Exception as e:
        logger.error(f"Agent 2 falló completamente: {e}")
        from src.schemas import ReasoningOutput, ReasoningStep
        reasoning_out = ReasoningOutput(
            document_id=vision_out.document_id,
            trap_detected="Unclear Value",
            trap_id=f"T-{vision_out.document_id[:8]}-ERR",
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

    # 3. Validator (Gate de Integridad)
    try:
        validator_out = await validator_agent.validate_integrity(vision_out, reasoning_out)
    except Exception as e:
        logger.error(f"Agent 3 falló completamente: {e}")
        from src.schemas import ValidatorOutput, ValidationResult
        from decimal import Decimal
        validator_out = ValidatorOutput(
            document_id=vision_out.document_id,
            trap_id=reasoning_out.trap_id,
            validation_result=ValidationResult(
                logically_sound=False, trap_is_real=False,
                severity_confirmed="MEDIUM", math_verified=None,
                math_verification_detail="Validación no ejecutada — error de sistema",
            ),
            validation_confidence=Decimal("0.3"),
            issues_found=[f"Error de sistema en Agente 3: {str(e)[:100]}"],
            adjustments=[], recommendation="UNCERTAIN",
            recommendation_detail="Error en validación — revisión humana requerida",
            model_used="emergency-fallback", timestamp=datetime.now(),
        )

    # 4. Explainer (Reporte Ejecutivo) — con fallback integrado en el agente
    partial_result = PipelineResult(
        document_id=vision_out.document_id,
        pdf_path=pdf_path,
        status="PARTIAL",
        vision=vision_out,
        reasoning=reasoning_out,
        validation=validator_out,
        total_processing_time_ms=int((time.time() - start_time) * 1000),
        timestamp=datetime.now(),
    )

    try:
        explainer_out = await explainer_agent.generate_report(partial_result)
    except Exception as e:
        logger.error(f"Agent 4 falló completamente: {e}")
        explainer_out = None
    
    # 5. Resultado Final
    final_status = "COMPLETE" if explainer_out is not None else "PARTIAL"
    final_result = PipelineResult(
        document_id=vision_out.document_id,
        pdf_path=pdf_path,
        status=final_status,
        vision=vision_out,
        reasoning=reasoning_out,
        validation=validator_out,
        explanation=explainer_out,
        total_processing_time_ms=int((time.time() - start_time) * 1000),
        timestamp=datetime.now(),
    )
    
    # Persistencia final en Supabase (tabla audit_results)
    _persist_final_result(final_result)
    
    return final_result

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
    """Guarda el resultado consolidado en la tabla audit_results."""
    try:
        issues_str = str(result.validation.issues_found) if result.validation else ""
        # Detectar duplicado/blacklist en issues (escritos en español por el validator)
        is_dup = "DUPLICADO" in issues_str
        is_bl = "LISTA NEGRA" in issues_str

        recommendation = result.validation.recommendation if result.validation else "UNCERTAIN"
        fraud_class = "FRAUDE_CONFIRMADO" if (is_dup or is_bl) else _RECOMMENDATION_TO_FRAUD.get(recommendation, "SOSPECHOSO")
        severity_raw = result.validation.validation_result.severity_confirmed if result.validation else "MEDIUM"
        next_action = result.explanation.next_action if result.explanation else "AWAIT_HUMAN_DECISION"

        # math_validation: True = pasa (sin error), False = falla (error confirmado), None = n/a
        math_raw = result.validation.validation_result.math_verified if result.validation else None
        math_pass = (not math_raw) if math_raw is not None else None

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
            "integrity_passed": not (result.validation.validation_result.trap_is_real) if result.validation else False,
            "final_status": _NEXT_ACTION_TO_STATUS.get(next_action, "FLAG"),
            "executive_report": result.explanation.markdown_report if result.explanation else "Pipeline incompleto",
            "recommended_action": next_action,
            "pipeline_version": "1.0.0",
            "processing_time_ms": result.total_processing_time_ms,
        }
        save_audit_result(data)
    except Exception as e:
        logger.error(f"Error persistiendo resultado final: {e}")
