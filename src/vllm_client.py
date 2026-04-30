"""
Cliente vLLM unificado para ATLAS.
Compatible con OpenAI API — apunta al servidor AMD MI300X.
Usa peticiones HTTP puras sin depender de la librería openai.
"""
import requests
import logging
import time
from typing import List, Dict, Optional
from src.config import settings
from src.error_handling import handle_errors

logger = logging.getLogger(__name__)

class CircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_timeout=30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"

    def can_proceed(self):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        return True

    def record_success(self):
        self.failures = 0
        self.state = "CLOSED"

class VLLMClient:
    def __init__(self):
        self.base_url = settings.vllm_base_url
        self.model = settings.model_name
        self.timeout = settings.timeout_api
        self.breaker = CircuitBreaker()

    @handle_errors
    async def call_llm(
        self,
        prompt: str,
        system_prompt: str = "Eres un auditor forense experto en detección de fraude y errores contables.",
        max_tokens: int = 3072,
        temperature: float = 0.1,
        timeout: Optional[int] = None
    ) -> str:
        if not self.breaker.can_proceed():
            raise Exception("Circuit breaker is OPEN. Service unavailable.")
        
        url = f"{self.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=timeout or self.timeout)
            response.raise_for_status()
            data = response.json()
            self.breaker.record_success()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            self.breaker.record_failure()
            logger.error(f"Error en llamada LLM (vLLM): {type(e).__name__}")
            raise

    def verify_connection(self) -> bool:
        """Verifica que el servidor vLLM está disponible."""
        url = f"{self.base_url}/models"
        try:
            response = requests.get(url, timeout=self.timeout)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"No se puede conectar al servidor vLLM: {type(e).__name__}")
            return False

# Instancia global del cliente
vllm_client = VLLMClient()

# Alias para mantener compatibilidad con agentes existentes
call_llm = vllm_client.call_llm
verify_connection = vllm_client.verify_connection
