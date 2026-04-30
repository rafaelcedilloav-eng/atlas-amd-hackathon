"""
ATLAS Audit Event Emitter
Emite eventos en tiempo real para el X-Ray Panel via Server-Sent Events (SSE).
Se integra con el orchestrator para emitir logs en cada etapa del pipeline.
"""
import json
import asyncio
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class AuditEvent:
    event_id: str
    audit_id: str
    timestamp: str
    agent: str  # vision, reasoning, validator, explainer, compliance, orchestrator
    stage: str  # start, processing, complete, error
    message: str
    detail: Optional[Dict] = None
    progress_pct: int = 0
    severity: str = "info"  # info, warning, error, success


class AuditEventBus:
    """
    Bus de eventos en memoria para SSE.
    Cada auditoría tiene su propia cola de eventos.
    """
    
    def __init__(self):
        self._queues: Dict[str, asyncio.Queue] = {}
        self._history: Dict[str, List[Dict]] = {}
        self._subscribers: List[Callable] = []
    
    def get_or_create_stream(self, audit_id: str) -> asyncio.Queue:
        """Crea una nueva cola de eventos para una auditoría si no existe."""
        if audit_id not in self._queues:
            self._queues[audit_id] = asyncio.Queue()
            self._history[audit_id] = []
        return self._queues[audit_id]
    
    async def emit(self, event: AuditEvent):
        """Emite un evento a todos los suscriptores y guarda en historia."""
        event_dict = asdict(event)
        
        # Guardar en historia
        if event.audit_id not in self._history:
            self._history[event.audit_id] = []
        self._history[event.audit_id].append(event_dict)
        
        # Enviar a cola si existe
        if event.audit_id in self._queues:
            await self._queues[event.audit_id].put(event_dict)
        
        # Notificar suscriptores
        for sub in self._subscribers:
            try:
                await sub(event_dict)
            except Exception:
                pass
    
    async def get_events(self, audit_id: str):
        """Generador async para SSE. Yields eventos hasta timeout o completion."""
        queue = self.get_or_create_stream(audit_id)

        # Replay history so late-connecting clients see all prior events
        for event in list(self._history.get(audit_id, [])):
            yield json.dumps(event)
            if event.get("agent") == "orchestrator" and event.get("stage") == "complete":
                return
            if event.get("stage") == "error":
                return

        # Listen for new events
        try:
            while True:
                event = await asyncio.wait_for(queue.get(), timeout=60.0)
                yield json.dumps(event)

                if event.get("agent") == "orchestrator" and event.get("stage") == "complete":
                    break
                if event.get("stage") == "error":
                    break
        except asyncio.TimeoutError:
            yield json.dumps({"type": "timeout", "message": "No events received for 60s"})
    
    def get_history(self, audit_id: str) -> List[Dict]:
        """Retorna el historial de eventos de una auditoría."""
        return self._history.get(audit_id, [])
    
    def cleanup(self, audit_id: str):
        """Limpia recursos de una auditoría completada."""
        self._queues.pop(audit_id, None)
        # Programar limpieza del historial en 10 minutos
        asyncio.create_task(self._delayed_history_cleanup(audit_id))

    async def _delayed_history_cleanup(self, audit_id: str, delay: int = 600):
        """Elimina el historial después de un retraso para evitar fugas de memoria."""
        await asyncio.sleep(delay)
        self._history.pop(audit_id, None)
        logger.debug(f"Historial de SSE purgado para {audit_id}")


# Singleton global
event_bus = AuditEventBus()


# ── Helper functions para el orchestrator ────────────────────────────────────

async def emit_vision_start(audit_id: str):
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-v-start",
        audit_id=audit_id,
        timestamp=datetime.now().isoformat(),
        agent="vision",
        stage="start",
        message="Iniciando extracción de texto y campos del documento...",
        progress_pct=5,
        severity="info"
    ))

async def emit_vision_complete(audit_id: str, confidence: float, fields_count: int):
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-v-done",
        audit_id=audit_id,
        timestamp=datetime.now().isoformat(),
        agent="vision",
        stage="complete",
        message=f"Extracción completada. {fields_count} campos detectados (confianza: {confidence:.0%}).",
        detail={"fields_count": fields_count, "confidence": confidence},
        progress_pct=25,
        severity="success"
    ))

async def emit_compliance_start(audit_id: str, message: str = "detectando..."):
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-c-start",
        audit_id=audit_id,
        timestamp=datetime.now().isoformat(),
        agent="compliance",
        stage="start",
        message=f"Compliance check: {message}",
        progress_pct=30,
        severity="info"
    ))

async def emit_compliance_findings(audit_id: str, findings_count: int, score: float, country: str):
    severity = "success" if score > 0.8 else "warning" if score > 0.5 else "error"
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-c-done",
        audit_id=audit_id,
        timestamp=datetime.now().isoformat(),
        agent="compliance",
        stage="complete",
        message=f"Jurisdicción detectada: {country}. {findings_count} hallazgos (Score: {score:.0%})",
        detail={"findings_count": findings_count, "compliance_score": score, "country": country},
        progress_pct=40,
        severity=severity
    ))

async def emit_reasoning_start(audit_id: str):
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-r-start",
        audit_id=audit_id,
        timestamp=datetime.now().isoformat(),
        agent="reasoning",
        stage="start",
        message="DeepSeek-R1 analizando patrones de fraude e inconsistencias lógicas...",
        progress_pct=45,
        severity="info"
    ))

async def emit_reasoning_step(audit_id: str, step_num: int, conclusion: str):
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-r-step{step_num}",
        audit_id=audit_id,
        timestamp=datetime.now().isoformat(),
        agent="reasoning",
        stage="processing",
        message=f"Paso {step_num}: {conclusion}",
        detail={"step": step_num},
        progress_pct=45 + step_num * 5,
        severity="info"
    ))

async def emit_reasoning_complete(audit_id: str, trap_detected: str, severity: str):
    sev = "error" if severity in ["CRITICAL", "HIGH"] else "warning" if severity == "MEDIUM" else "info"
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-r-done",
        audit_id=audit_id,
        timestamp=datetime.now().isoformat(),
        agent="reasoning",
        stage="complete",
        message=f"Análisis forense completo. Trampa detectada: {trap_detected} ({severity})",
        detail={"trap": trap_detected, "severity": severity},
        progress_pct=60,
        severity=sev
    ))

async def emit_validator_start(audit_id: str):
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-val-start",
        audit_id=audit_id,
        timestamp=datetime.now().isoformat(),
        agent="validator",
        stage="start",
        message="Validando integridad: matemáticas, duplicados, blacklist...",
        progress_pct=65,
        severity="info"
    ))

async def emit_validator_gate(audit_id: str, gate_name: str, passed: bool, detail: str):
    sev = "success" if passed else "error"
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-val-{gate_name}",
        audit_id=audit_id,
        timestamp=datetime.now().isoformat(),
        agent="validator",
        stage="processing",
        message=f"Gate {gate_name}: {'PASS' if passed else 'FAIL'} — {detail}",
        detail={"gate": gate_name, "passed": passed},
        progress_pct=70 if gate_name == "math" else 75 if gate_name == "duplicate" else 80,
        severity=sev
    ))

async def emit_validator_complete(audit_id: str, recommendation: str):
    sev = "success" if recommendation == "APPROVE" else "error" if recommendation == "FLAG" else "warning"
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-val-done",
        audit_id=audit_id,
        timestamp=datetime.now().isoformat(),
        agent="validator",
        stage="complete",
        message=f"Validación completa. Recomendación: {recommendation}",
        detail={"recommendation": recommendation},
        progress_pct=85,
        severity=sev
    ))

async def emit_explainer_start(audit_id: str):
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-e-start",
        audit_id=audit_id,
        timestamp=datetime.now().isoformat(),
        agent="explainer",
        stage="start",
        message="Generando reporte ejecutivo en español (es-MX)...",
        progress_pct=90,
        severity="info"
    ))

async def emit_explainer_complete(audit_id: str, next_action: str):
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-e-done",
        audit_id=audit_id,
        timestamp=datetime.now().isoformat(),
        agent="explainer",
        stage="complete",
        message=f"Reporte generado. Acción recomendada: {next_action}",
        detail={"next_action": next_action},
        progress_pct=95,
        severity="success"
    ))

async def emit_pipeline_complete(audit_id: str, status: str, processing_time_ms: int):
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-done",
        audit_id=audit_id,
        timestamp=datetime.now().isoformat(),
        agent="orchestrator",
        stage="complete",
        message=f"Pipeline ATLAS completado en {processing_time_ms}ms. Estado: {status}",
        detail={"status": status, "processing_time_ms": processing_time_ms},
        progress_pct=100,
        severity="success"
    ))

async def emit_error(audit_id: str, agent: str, error_msg: str):
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-err",
        audit_id=audit_id,
        timestamp=datetime.now().isoformat(),
        agent=agent,
        stage="error",
        message=f"ERROR en {agent}: {error_msg[:150]}",
        detail={"error": error_msg},
        progress_pct=0,
        severity="error"
    ))
