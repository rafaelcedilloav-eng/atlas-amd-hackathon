"""
ATLAS Orchestrator v3.0 FINAL
Orquestador Multi-Backend con Pipeline Gates Atómicos.
Optimizado para AMD MI300X - 8000/8002/11434 multi-port architecture.
"""

import asyncio
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.config import settings
from src.utils import generate_audit_id
from src.vllm_client import core_vllm, vision_vllm, router_vllm
from src.schemas import PipelineResult, VisionOutput, ReasoningOutput, ValidatorOutput, ExplainerOutput, AuditEvent
from src.audit_emitter import event_bus

# Agentes
from src.agent_vision import VisionAnalyzerAgent
from src.agent_reasoning import ReasoningAgent
from src.agent_validator import ValidatorAgent
from src.agent_explainer import ExplainerAgent
from src.compliance_router import run_compliance_check
from src.pipeline_gates import gate_0_1, gate_1_2, gate_2_3, gate_3_4, gate_4_final, GateDecision
from src.anomaly_logger import log_anomaly
from src.db_mock import save_audit_result, get_client

logger = logging.getLogger(__name__)

class PipelineState:
    def __init__(self, audit_id: str):
        self.audit_id = audit_id
        self.status = "initialized"
        self.rollback_triggered = False
        self.start_time = time.time()

async def execute_pipeline(pdf_path: str, audit_id: Optional[str] = None) -> PipelineResult:
    """Ejecuta pipeline v3.0 con gates atómicos y trazabilidad UUIDv7."""
    audit_id = audit_id or generate_audit_id()
    state = PipelineState(audit_id)
    event_bus.get_or_create_stream(audit_id)
    
    logger.info(f"Pipeline v3.0 iniciado: {audit_id} para {pdf_path}")
    
    # Instanciar agentes
    vision_agent = VisionAnalyzerAgent()
    reasoning_agent = ReasoningAgent()
    validator_agent = ValidatorAgent()
    explainer_agent = ExplainerAgent()

    try:
        # ── 0. PRE-GATE (G00) ────────────────────────────────────────────────
        g00 = gate_0_1(pdf_path)
        if g00.decision == GateDecision.ROLLBACK:
            return await _handle_atomic_failure(state, f"G00 Rollback: {g00.reason}")

        # ── 1. VISION (Motor 8002) ──────────────────────────────────────────────
        await event_bus.emit(AuditEvent(
            event_id=f"{audit_id}-v3-vision",
            audit_id=audit_id,
            timestamp=datetime.now().isoformat(),
            agent="vision",
            stage="start",
            message="Analizando con InternVL2-40B (8002)",
            progress_pct=15
        ))
        
        vision_out = await vision_agent.analyze_document(pdf_path)
        vision_out.document_id = audit_id
        
        # GATE G12
        g12 = gate_1_2(vision_out)
        if g12.decision == GateDecision.ESCALATE:
             logger.warning(f"G12 Escalation: {g12.reason}")
        elif g12.decision == GateDecision.ROLLBACK:
             return await _handle_atomic_failure(state, f"G12 Rollback: {g12.reason}", vision_out)

        # ── 2. COMPLIANCE (Motor 11434) ──────────────────────────────────────────
        await event_bus.emit(AuditEvent(
            event_id=f"{audit_id}-compliance-start",
            audit_id=audit_id,
            timestamp=datetime.now().isoformat(),
            agent="compliance",
            stage="start",
            message="Analizando compliance determinista (Motor 11434)",
            progress_pct=30
        ))

        compliance_result = run_compliance_check(
            raw_text=vision_out.raw_text or "",
            extracted_fields=vision_out.extracted_fields,
            filename=pdf_path
        )

        # ── 3. REASONING (Motor 8000) ─────────────────────────────────────────────
        await event_bus.emit(AuditEvent(
            event_id=f"{audit_id}-reasoning-start",
            audit_id=audit_id,
            timestamp=datetime.now().isoformat(),
            agent="reasoning",
            stage="start",
            message="Razonamiento forense con Qwen3-14B atlas-r3 (Motor 8000)",
            progress_pct=45
        ))

        reasoning_out = await reasoning_agent.reason_about_document(vision_out, compliance_result)
        reasoning_out.document_id = audit_id
        
        # GATE G23
        g23 = gate_2_3(vision_out, reasoning_out)
        if g23.decision == GateDecision.ROLLBACK:
             return await _handle_atomic_failure(state, f"G23 Rollback: {g23.reason}", vision_out, reasoning_out)

        # ── 4. VALIDATOR (Integridad) ───────────────────────────────────────────
        await event_bus.emit(AuditEvent(
            event_id=f"{audit_id}-validator-start",
            audit_id=audit_id,
            timestamp=datetime.now().isoformat(),
            agent="validator",
            stage="start",
            message="Validando integridad forense y consistencias",
            progress_pct=60
        ))

        validator_out = await validator_agent.validate_integrity(vision_out, reasoning_out)
        validator_out.document_id = audit_id

        # GATE G34
        g34 = gate_3_4(reasoning_out, validator_out)
        if g34.decision == GateDecision.ROLLBACK:
             return await _handle_atomic_failure(state, f"G34 Rollback: {g34.reason}", vision_out, reasoning_out, validator_out)

        # ── 5. EXPLAINER (Motor 8000) ───────────────────────────────────────────
        await event_bus.emit(AuditEvent(
            event_id=f"{audit_id}-explainer-start",
            audit_id=audit_id,
            timestamp=datetime.now().isoformat(),
            agent="explainer",
            stage="start",
            message="Generando reporte ejecutivo forense",
            progress_pct=80
        ))

        partial_result = PipelineResult(
            document_id=audit_id, pdf_path=pdf_path, status="PARTIAL",
            vision=vision_out, compliance=compliance_result, reasoning=reasoning_out,
            validation=validator_out, total_processing_time_ms=int((time.time() - state.start_time) * 1000),
            timestamp=datetime.now(),
        )

        explainer_out = await explainer_agent.generate_report(partial_result)
        explainer_out.document_id = audit_id

        # Resultado final
        final_result = PipelineResult(
            document_id=audit_id, pdf_path=pdf_path, status="COMPLETE",
            vision=vision_out, compliance=compliance_result, reasoning=reasoning_out,
            validation=validator_out, explanation=explainer_out,
            total_processing_time_ms=int((time.time() - state.start_time) * 1000),
            timestamp=datetime.now(),
        )

        # ── 6. FINAL GATE (G4F) ────────────────────────────────────────────────
        db_client = get_client()
        g4f = await gate_4_final(final_result, db_client)
        if g4f.decision == GateDecision.ROLLBACK:
             return await _handle_atomic_failure(state, f"G4F Rollback: {g4f.reason}", vision_out, reasoning_out, validator_out)

        save_audit_result(final_result.model_dump(mode="json"))
        
        await event_bus.emit(AuditEvent(
            event_id=f"{audit_id}-complete",
            audit_id=audit_id,
            timestamp=datetime.now().isoformat(),
            agent="orchestrator",
            stage="complete",
            message="Auditoría v3.0 COMPLETADA",
            progress_pct=100
        ))
        
        return final_result

    except Exception as e:
        logger.error(f"Error fatal v3.0: {e}")
        return await _handle_atomic_failure(state, str(e))

async def _handle_atomic_failure(state: PipelineState, error: str, vision=None, reasoning=None, validator=None):
    total_time = int((time.time() - state.start_time) * 1000)
    result = PipelineResult(
        document_id=state.audit_id, pdf_path="", status="FAILED",
        vision=vision, reasoning=reasoning, validation=validator,
        error=error, total_processing_time_ms=total_time,
        timestamp=datetime.now()
    )
    save_audit_result(result.model_dump(mode="json"))
    
    await event_bus.emit(AuditEvent(
        event_id=f"{state.audit_id}-failed",
        audit_id=state.audit_id,
        timestamp=datetime.now().isoformat(),
        agent="orchestrator",
        stage="error",
        message=f"FALLO CRÍTICO: {error}",
        progress_pct=100
    ))
    return result
