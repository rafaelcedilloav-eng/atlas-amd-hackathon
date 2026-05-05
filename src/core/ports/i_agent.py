from abc import ABC, abstractmethod
from typing import Dict, Any

class IAgent(ABC):
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass
