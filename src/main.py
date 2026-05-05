import asyncio
import sys
from pathlib import Path
from src.adapters.outgoing.agent_adapter import AgentAdapter
from src.core.ports.i_agent import IAgent

async def bootstrap():
    config = {'agent_name': 'ATLAS-K2', 'version': '3.0'}
    agent: IAgent = AgentAdapter(config)
    if await agent.health_check():
        print('✅ ATLAS Core: [ONLINE]')
    result = await agent.execute({'id': 'test_001', 'action': 'scan'})
    print(f'📊 Resultado: {result}')
    return agent

if __name__ == '__main__':
    asyncio.run(bootstrap())
