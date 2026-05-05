from uuid import UUID, uuid4
from typing import Optional, Dict, Any
from datetime import datetime

from src.core.ports.i_agent_repository import IAgentRepository
from src.core.ports.i_task_repository import ITaskRepository
from src.core.ports.i_agent import IAgent
# NOTA: ILLMService debe ser definido en ports/i_llm.py si es necesario independizarlo
from src.core.domain.entities import Task, TaskStatus

class AuditService:
    """Coordina los casos de uso de auditoría de documentos."""

    def __init__(
        self,
        agent_repository: IAgentRepository,
        task_repository: ITaskRepository,
        agent: IAgent
    ) -> None:
        self._agent_repository = agent_repository
        self._task_repository = task_repository
        self._agent = agent

    async def audit_document(self, pdf_path: str, country: str) -> UUID:
        """
        Coordina la auditoría de un documento PDF.
        """
        audit_id = uuid4()

        task = Task(
            task_id=str(audit_id),
            input_data={"pdf_path": pdf_path, "country": country},
            status=TaskStatus.PENDING
        )
        await self._task_repository.create(task)

        try:
            # Ejecución via puerto de agente
            audit_result = await self._agent.execute_task(task)

            # Actualizar tarea a COMPLETED
            task.status = TaskStatus.COMPLETED
            task.output_data = audit_result.output_data
            task.completed_at = datetime.utcnow()
            await self._task_repository.update(task)

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            await self._task_repository.update(task)
            raise

        return audit_id

    async def get_audit_report(self, audit_id: UUID) -> Optional[Dict[str, Any]]:
        """Recupera el reporte de una auditoría realizada."""
        task = await self._task_repository.get(str(audit_id))

        if not task:
            return None

        return {
            "audit_id": task.task_id,
            "status": task.status.value,
            "result": task.output_data if task.status == TaskStatus.COMPLETED else None,
            "error": task.error_message if task.status == TaskStatus.FAILED else None
        }
