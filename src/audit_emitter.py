"""
ATLAS Audit Event Bus v3.0
Optimizado por Kimi-K2 Master Audit.
"""
import asyncio
import logging
from typing import Dict, List, Any, AsyncGenerator
from src.schemas import AuditEvent

logger = logging.getLogger(__name__)

class AuditEventBus:
    def __init__(self):
        # Mapeo de audit_id -> Cola de eventos
        self.streams: Dict[str, asyncio.Queue] = {}
        # Historial temporal para reconexiones
        self.history: Dict[str, List[str]] = {}

    def get_or_create_stream(self, audit_id: str) -> asyncio.Queue:
        if audit_id not in self.streams:
            self.streams[audit_id] = asyncio.Queue()
            self.history[audit_id] = []
        return self.streams[audit_id]

    async def emit(self, event: AuditEvent):
        """Emite un evento a la cola del audit_id correspondiente."""
        audit_id = event.audit_id
        queue = self.get_or_create_stream(audit_id)
        
        event_json = event.model_dump_json()
        self.history[audit_id].append(event_json)
        
        # Limitar historial a 100 eventos
        if len(self.history[audit_id]) > 100:
            self.history[audit_id].pop(0)
            
        await queue.put(event_json)
        logger.debug(f"Evento emitido: {event.event_id} para {audit_id}")

    async def get_events(self, audit_id: str) -> AsyncGenerator[str, None]:
        """Generador para SSE que consume eventos de la cola."""
        queue = self.get_or_create_stream(audit_id)
        
        # Primero enviar historial si existe para "catch up"
        for old_event in self.history.get(audit_id, []):
            yield old_event

        while True:
            try:
                event = await queue.get()
                yield event
            except asyncio.CancelledError:
                logger.info(f"Stream cancelado para {audit_id}")
                break

    def clear_stream(self, audit_id: str):
        self.streams.pop(audit_id, None)
        self.history.pop(audit_id, None)

# Instancia global
event_bus = AuditEventBus()

# Helpers para compatibilidad
async def emit_vision_start(audit_id: str):
    pass # Ya manejado en orchestrator v3

async def emit_pipeline_complete(audit_id: str, status: str, time_ms: int):
    pass # Ya manejado en orchestrator v3
