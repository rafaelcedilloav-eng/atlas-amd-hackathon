import sys
from pathlib import Path
from typing import Dict, Any
from src.core.ports.i_agent import IAgent

class AgentAdapter(IAgent):
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "executed", "task_id": task.get("id")}

    async def health_check(self) -> bool:
        return True
