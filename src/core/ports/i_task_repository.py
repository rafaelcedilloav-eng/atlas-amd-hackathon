from abc import ABC, abstractmethod
from typing import List, Optional
from src.core.domain.entities import Task

class ITaskRepository(ABC):
    @abstractmethod
    async def create(self, task: Task) -> Task:
        pass

    @abstractmethod
    async def get(self, task_id: str) -> Optional[Task]:
        pass

    @abstractmethod
    async def update(self, task: Task) -> Task:
        pass

    @abstractmethod
    async def list_by_agent(self, agent_id: str, limit: int = 100) -> List[Task]:
        pass

    @abstractmethod
    async def list_pending(self, agent_id: Optional[str] = None) -> List[Task]:
        pass
