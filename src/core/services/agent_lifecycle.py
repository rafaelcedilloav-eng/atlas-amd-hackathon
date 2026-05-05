from typing import Dict, Any, List, Optional
from uuid import uuid4
from src.core.domain.entities import AgentConfig, AgentStatus, AgentMetrics, Message, Conversation, MessageType
from src.core.ports.i_agent import IAgent
from src.core.ports.i_agent_repository import IAgentRepository

class AgentLifecycleService:
    def __init__(
        self,
        agent_repository: IAgentRepository,
        agent_adapter: IAgent,
    ):
        self._agent_repository = agent_repository
        self._agent_adapter = agent_adapter

    async def register_agent(self, config: AgentConfig) -> AgentConfig:
        await self._agent_repository.save(config)
        await self._agent_adapter.initialize(config.agent_id, config.model_dump())
        return config

    async def unregister_agent(self, agent_id: str) -> bool:
        await self._agent_adapter.shutdown(agent_id)
        return await self._agent_repository.delete(agent_id)

    async def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        agent_config = await self._agent_repository.get(agent_id)
        if not agent_config:
            raise ValueError(f"Agent {agent_id} not found")

        status = await self._agent_adapter.get_status()
        metrics = await self._agent_adapter.get_metrics()
        capabilities = await self._agent_adapter.get_capabilities()

        return {
            "agent_id": agent_id,
            "name": agent_config.name,
            "status": status.value,
            "metrics": metrics.model_dump(),
            "capabilities": capabilities,
        }

    async def process_message(
        self,
        agent_id: str,
        content: str,
        conversation_id: Optional[str] = None,
    ) -> Message:
        agent_config = await self._agent_repository.get(agent_id)
        if not agent_config:
            raise ValueError(f"Agent {agent_id} not found")

        conversation = Conversation(
            conversation_id=conversation_id or str(uuid4()),
            agent_id=agent_id
        )
        message = Message(
            conversation_id=conversation.conversation_id,
            content=content,
            message_type=MessageType.HUMAN,
            sender="user",
        )

        return await self._agent_adapter.process_message(message, conversation)
