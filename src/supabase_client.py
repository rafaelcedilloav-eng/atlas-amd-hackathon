"""
Cliente Supabase singleton para ATLAS.
Todos los módulos importan desde aquí — nunca instancian su propio cliente.
"""
import os
import logging
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_PUBLISHABLE_KEY")
        if not url or not key:
            raise EnvironmentError(
                "SUPABASE_URL y SUPABASE_SERVICE_KEY son requeridas en .env"
            )
        # headers fuerzan HTTP/1.1 — evita StreamReset en entornos cloud (DO, Render)
        _client = create_client(
            url,
            key,
            options=ClientOptions(headers={"Connection": "keep-alive"}),
        )
        logger.info(f"Supabase client inicializado → {url}")
    return _client


def reset_client() -> None:
    """Fuerza re-creación del cliente en el próximo get_client()."""
    global _client
    _client = None
