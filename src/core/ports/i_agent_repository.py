from abc import ABC, abstractmethod
from typing import List, Optional
from src.core.domain.entities import AgentConfig

class IAgentRepository(ABC):
    @abstractmethod
    async def save(self, agent_config: AgentConfig) -> None:
        pass

    @abstractmethod
    async def get(self, agent_id: str) -> Optional[AgentConfig]:
        pass

    @abstractmethod
    async def list_all(self) -> List[AgentConfig]:
        pass

    @abstractmethod
    async def delete(self, agent_id: str) -> bool:
        pass
