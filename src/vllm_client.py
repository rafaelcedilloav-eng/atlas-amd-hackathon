"""
ATLAS v3.0 - Cliente VLLM ultra-resiliente para modelos 40B+ en MI300X
Re-escrito para cumplir con el contrato de Chat Completions de InternVL2 e Internos Llama.
Optimizado por Kimi-K2 + Qwen Joint Audit.
"""

import asyncio
import json
import logging
import base64
from typing import AsyncGenerator, Dict, Any, Optional, List
import aiohttp

from src.config import settings
from src.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

# Circuit breakers globales con recovery_timeout optimizado (60s)
circuit_core = CircuitBreaker(name="CORE-LLM", failure_threshold=5, recovery_timeout=60)
circuit_vision = CircuitBreaker(name="VISION-QWEN-FP8-FINANCE", failure_threshold=5, recovery_timeout=60)
circuit_router = CircuitBreaker(name="ROUTER-OLLAMA", failure_threshold=5, recovery_timeout=60)

class VLLMClient:
    """Cliente VLLM optimizado para AMD MI300X Clusters"""
    
    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: float = 25.0,
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_val = timeout
        self.circuit_breaker = circuit_breaker
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Headers MI300X-specific
        self.headers = {
            "User-Agent": "ATLAS-VLLM-Client/3.0",
            "X-MI300X-Optimized": "true",
            "Content-Type": "application/json"
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout_val, connect=3.0, sock_read=self.timeout_val)
            connector = aiohttp.TCPConnector(limit=100, keepalive_timeout=60)
            self.session = aiohttp.ClientSession(connector=connector, timeout=timeout, headers=self.headers)
        return self.session

    async def call_llm(self, prompt: str, system_prompt: str = "", max_tokens: int = 2048, temperature: float = 0.1) -> str:
        """Llamada con Fallback Inteligente entre modelos"""
        try:
            return await self._execute_call(self.model, prompt, system_prompt, max_tokens, temperature)
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                logger.warning(f"Cuota agotada en {self.model}, pivotando a {settings.fallback_model}")
                return await self._execute_call(settings.fallback_model, prompt, system_prompt, max_tokens, temperature)
            raise e

    async def _execute_call(self, model: str, prompt: str, system_prompt: str, max_tokens: int, temperature: float) -> str:
        """Endpoint: /v1/chat/completions (Chat format para todos los modelos v3)"""
        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }
        
        async def _request():
            session = await self._get_session()
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    err = await response.text()
                    raise Exception(f"VLLM Error {response.status}: {err}")
                data = await response.json()
                return data["choices"][0]["message"]["content"].strip()

        return await self.circuit_breaker.call(_request)

    async def generate_vision(self, prompt: str, image_path: str, max_tokens: int = 1024) -> str:
        """Endpoint: /v1/chat/completions (Específico para InternVL2-40B)"""
        url = f"{self.base_url}/v1/chat/completions"
        
        # Codificar imagen
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode()

        # InternVL2 Vision-Language Payload
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                        }
                    ]
                }
            ],
            "max_tokens": max_tokens,
            "temperature": 0.2,
            "stream": False
        }

        async def _request():
            session = await self._get_session()
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    err = await response.text()
                    raise Exception(f"Vision Engine Error {response.status}: {err}")
                data = await response.json()
                return data["choices"][0]["message"]["content"].strip()

        return await self.circuit_breaker.call(_request)

    async def generate_embedding(self, text: str) -> List[float]:
        """Endpoint Ollama: /api/embeddings"""
        url = f"{self.base_url}/api/embeddings"
        payload = {"model": self.model, "prompt": text}
        
        async def _request():
            session = await self._get_session()
            async with session.post(url, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("embedding", [])

        return await self.circuit_breaker.call(_request)

    async def close(self):
        if self.session:
            await self.session.close()

# Instancias Globales
core_vllm = VLLMClient(base_url=settings.core_url, model=settings.core_model, circuit_breaker=circuit_core)
vision_vllm = VLLMClient(base_url=settings.vision_url, model=settings.vision_model, circuit_breaker=circuit_vision)
router_vllm = VLLMClient(base_url=settings.router_url, model=settings.router_model, circuit_breaker=circuit_router)
