"""
Cliente vLLM unificado para ATLAS.
Compatible con OpenAI API — apunta al servidor AMD MI300X.
"""
import os
from openai import OpenAI
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://165.245.138.52:8000/v1")
VLLM_MODEL    = os.getenv("VLLM_MODEL", "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B")
VLLM_TIMEOUT  = int(os.getenv("VLLM_TIMEOUT", "30"))

# vLLM no requiere API key real si es una instancia privada
client = OpenAI(
    base_url=VLLM_BASE_URL,
    api_key=os.getenv("VLLM_API_KEY", "not-needed"),
    timeout=VLLM_TIMEOUT
)

def call_llm(
    prompt: str,
    system_prompt: str = "Eres un auditor forense experto en detección de fraude y errores contables.",
    max_tokens: int = 1024,
    temperature: float = 0.1
) -> str:
    """
    Llamada unificada al LLM en AMD.
    Todos los agentes usan esta función — nunca llaman a OpenAI directamente.
    """
    try:
        response = client.chat.completions.create(
            model=VLLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        result = response.choices[0].message.content
        logger.debug(f"LLM response received: {len(result)} chars")
        return result
    except Exception as e:
        logger.error(f"Error en llamada LLM (vLLM): {e}")
        raise


def verify_connection() -> bool:
    """Verifica que el servidor vLLM está disponible y tiene el modelo cargado."""
    try:
        models = client.models.list()
        available = [m.id for m in models.data]
        logger.info(f"vLLM conectado. Modelos disponibles: {available}")
        return VLLM_MODEL in available
    except Exception as e:
        logger.error(f"No se puede conectar a vLLM en {VLLM_BASE_URL}: {e}")
        return False
