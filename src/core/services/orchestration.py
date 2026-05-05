from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import uuid4
from src.core.domain.entities import Task, TaskStatus, Message, Conversation, AgentConfig, MessageType
from src.core.ports.i_agent_repository import IAgentRepository
from src.core.ports.i_task_repository import ITaskRepository

class OrchestrationService:
    def __init__(
        self,
        agent_repository: IAgentRepository,
        task_repository: ITaskRepository,
    ):
        self._agent_repository = agent_repository
        self._task_repository = task_repository

    async def submit_task(self, agent_id: str, input_data: Dict[str, Any]) -> Task:        
        agent_config = await self._agent_repository.get(agent_id)
        if not agent_config:
            raise ValueError(f"Agent {agent_id} not found")

        task = Task(agent_id=agent_id, input_data=input_data)
        return await self._task_repository.create(task)

    async def get_task_status(self, task_id: str) -> Optional[Task]:
        return await self._task_repository.get(task_id)

    async def list_agent_tasks(self, agent_id: str, limit: int = 100) -> List[Task]:       
        return await self._task_repository.list_by_agent(agent_id, limit)

    async def update_task_status(self, task: Task, status: TaskStatus,
                                   error_message: Optional[str] = None) -> Task:
        updated_task = task.model_copy(
            update={
                "status": status,
                "started_at": datetime.utcnow() if status == TaskStatus.RUNNING else task.started_at,
                "completed_at": datetime.utcnow() if status in [TaskStatus.COMPLETED, TaskStatus.FAILED] else task.completed_at,
                "error_message": error_message,
            }
        )
        return await self._task_repository.update(updated_task)
