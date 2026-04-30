"""
ATLAS Audit Event Emitter — SSE event bus for the X-Ray Panel.
Emits events in real time at each pipeline stage.
"""
import json
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class AuditEvent:
    event_id: str
    audit_id: str
    timestamp: str
    agent: str    # vision | compliance | reasoning | validator | explainer | orchestrator
    stage: str    # start | processing | complete | error
    message: str
    detail: Optional[Dict] = None
    progress_pct: int = 0
    severity: str = "info"  # info | warning | error | success


class AuditEventBus:
    """In-memory SSE bus. Each audit_id has its own queue + history."""

    def __init__(self):
        self._queues:   Dict[str, asyncio.Queue] = {}
        self._history:  Dict[str, List[Dict]]    = {}

    def create_audit_stream(self, audit_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._queues[audit_id]  = q
        self._history[audit_id] = []
        return q

    async def emit(self, event: AuditEvent):
        d = asdict(event)
        if event.audit_id in self._history:
            self._history[event.audit_id].append(d)
        if event.audit_id in self._queues:
            await self._queues[event.audit_id].put(d)

    async def get_events(self, audit_id: str):
        """Async generator for SSE. Yields history first, then live events."""
        if audit_id not in self._queues:
            self.create_audit_stream(audit_id)

        history = list(self._history.get(audit_id, []))

        # Replay history
        for evt in history:
            yield f"data: {json.dumps(evt)}\n\n"

        # If pipeline is already complete in history, close immediately
        if any(e.get("agent") == "orchestrator" and e.get("stage") == "complete"
               for e in history):
            return

        # Otherwise wait for live events
        q = self._queues[audit_id]
        try:
            while True:
                evt = await asyncio.wait_for(q.get(), timeout=90.0)
                yield f"data: {json.dumps(evt)}\n\n"
                # Only close when the orchestrator signals pipeline complete
                if evt.get("agent") == "orchestrator" and evt.get("stage") == "complete":
                    break
        except asyncio.TimeoutError:
            yield f"data: {json.dumps({'type': 'timeout', 'message': 'No events for 90s'})}\n\n"

    def get_history(self, audit_id: str) -> List[Dict]:
        return list(self._history.get(audit_id, []))

    def cleanup(self, audit_id: str):
        self._queues.pop(audit_id, None)


# ── Singleton ─────────────────────────────────────────────────────────────────
event_bus = AuditEventBus()


# ── Helper functions used by the orchestrator ─────────────────────────────────

async def emit_vision_start(audit_id: str):
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-v-start", audit_id=audit_id,
        timestamp=datetime.now().isoformat(), agent="vision", stage="start",
        message="Iniciando extracción OCR + campos del documento...",
        progress_pct=5, severity="info",
    ))


async def emit_vision_complete(audit_id: str, confidence: float, fields_count: int):
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-v-done", audit_id=audit_id,
        timestamp=datetime.now().isoformat(), agent="vision", stage="complete",
        message=f"Extracción completada — {fields_count} campos (confianza: {confidence:.0%})",
        detail={"fields_count": fields_count, "confidence": confidence},
        progress_pct=20, severity="success",
    ))


async def emit_compliance_start(audit_id: str, country: str):
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-c-start", audit_id=audit_id,
        timestamp=datetime.now().isoformat(), agent="compliance", stage="start",
        message=f"Detectando jurisdicción fiscal: {country}...",
        detail={"country": country}, progress_pct=25, severity="info",
    ))


async def emit_compliance_findings(audit_id: str, findings_count: int, score: float, country: str):
    sev = "success" if score > 0.8 else "warning" if score > 0.5 else "error"
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-c-done", audit_id=audit_id,
        timestamp=datetime.now().isoformat(), agent="compliance", stage="complete",
        message=f"Compliance [{country}]: {findings_count} hallazgo(s) — Score {score:.0%}",
        detail={"findings_count": findings_count, "compliance_score": score, "country": country},
        progress_pct=38, severity=sev,
    ))


async def emit_reasoning_start(audit_id: str):
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-r-start", audit_id=audit_id,
        timestamp=datetime.now().isoformat(), agent="reasoning", stage="start",
        message="DeepSeek-R1 en AMD MI300X — analizando patrones de fraude...",
        progress_pct=42, severity="info",
    ))


async def emit_reasoning_step(audit_id: str, step_num: int, conclusion: str):
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-r-step{step_num}", audit_id=audit_id,
        timestamp=datetime.now().isoformat(), agent="reasoning", stage="processing",
        message=f"Paso {step_num}: {conclusion}",
        detail={"step": step_num}, progress_pct=42 + step_num * 5, severity="info",
    ))


async def emit_reasoning_complete(audit_id: str, trap_detected: str, severity: str):
    sev = "error" if severity in ("CRITICAL", "HIGH") else "warning" if severity == "MEDIUM" else "info"
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-r-done", audit_id=audit_id,
        timestamp=datetime.now().isoformat(), agent="reasoning", stage="complete",
        message=f"Análisis forense — Trampa: {trap_detected} [{severity}]",
        detail={"trap": trap_detected, "severity": severity},
        progress_pct=58, severity=sev,
    ))


async def emit_validator_start(audit_id: str):
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-val-start", audit_id=audit_id,
        timestamp=datetime.now().isoformat(), agent="validator", stage="start",
        message="Validando integridad: matemáticas · duplicados · blacklist...",
        progress_pct=62, severity="info",
    ))


async def emit_validator_gate(audit_id: str, gate_name: str, passed: bool, detail: str):
    pct = {"math": 68, "duplicate": 74, "blacklist": 80}.get(gate_name, 70)
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-val-{gate_name}", audit_id=audit_id,
        timestamp=datetime.now().isoformat(), agent="validator", stage="processing",
        message=f"Gate [{gate_name.upper()}]: {'PASS' if passed else 'FAIL'} — {detail}",
        detail={"gate": gate_name, "passed": passed},
        progress_pct=pct, severity="success" if passed else "error",
    ))


async def emit_validator_complete(audit_id: str, recommendation: str):
    sev = "success" if recommendation == "APPROVE" else "error" if recommendation == "FLAG" else "warning"
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-val-done", audit_id=audit_id,
        timestamp=datetime.now().isoformat(), agent="validator", stage="complete",
        message=f"Validación completa — Recomendación: {recommendation}",
        detail={"recommendation": recommendation},
        progress_pct=85, severity=sev,
    ))


async def emit_explainer_start(audit_id: str):
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-e-start", audit_id=audit_id,
        timestamp=datetime.now().isoformat(), agent="explainer", stage="start",
        message="Generando reporte ejecutivo forense (es-MX)...",
        progress_pct=88, severity="info",
    ))


async def emit_explainer_complete(audit_id: str, next_action: str):
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-e-done", audit_id=audit_id,
        timestamp=datetime.now().isoformat(), agent="explainer", stage="complete",
        message=f"Reporte generado — Acción: {next_action}",
        detail={"next_action": next_action},
        progress_pct=95, severity="success",
    ))


async def emit_pipeline_complete(audit_id: str, status: str, processing_time_ms: int):
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-done", audit_id=audit_id,
        timestamp=datetime.now().isoformat(), agent="orchestrator", stage="complete",
        message=f"Pipeline ATLAS completado en {processing_time_ms}ms — {status}",
        detail={"status": status, "processing_time_ms": processing_time_ms},
        progress_pct=100, severity="success",
    ))


async def emit_error(audit_id: str, agent: str, error_msg: str):
    await event_bus.emit(AuditEvent(
        event_id=f"{audit_id}-err-{agent}", audit_id=audit_id,
        timestamp=datetime.now().isoformat(), agent=agent, stage="error",
        message=f"ERROR en {agent}: {error_msg[:200]}",
        detail={"error": error_msg[:500]},
        progress_pct=0, severity="error",
    ))
