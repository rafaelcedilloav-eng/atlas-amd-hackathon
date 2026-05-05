from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Protocol, runtime_checkable
from dataclasses import dataclass

@dataclass
class ExecutionContext:
    """Contexto de ejecución para agents."""
    request_id: str
    metadata: Dict[str, Any]
    timestamp: float

@runtime_checkable
class IAsyncPipeline(Protocol):
    """Protocolo para pipeline asíncrono (puerto secundario)."""
    async def register_agent(self, agent: "IAgent") -> None: ...
    async def execute_pipeline(self, context: ExecutionContext) -> Dict[str, Any]: ...
    async def shutdown(self) -> None: ...

class IAgent(ABC):
    """Interfaz base para todos los agents de ATLAS (puerto primario)."""
    @property
    @abstractmethod
    def agent_id(self) -> str: ...
    @property
    @abstractmethod
    def version(self) -> str: ...
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None: ...
    @abstractmethod
    async def execute(self, input_data: Any, context: ExecutionContext) -> Any: ...
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]: ...
    @abstractmethod
    async def shutdown(self) -> None: ...

class IEventPublisher(ABC):
    """Interfaz para publicación de eventos (puerto secundario)."""
    @abstractmethod
    async def publish(self, event_name: str, payload: Dict[str, Any]) -> None: ...

class IRepository(ABC):
    """Interfaz para persistencia de datos (puerto secundario)."""
    @abstractmethod
    async def save(self, key: str, data: Any) -> None: ...
    @abstractmethod
    async def retrieve(self, key: str) -> Optional[Any]: ...
