"""
Cliente Supabase singleton para ATLAS.
Todos los módulos importan desde aquí — nunca instancian su propio cliente.
"""
import os
import logging
from supabase import create_client, Client
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
        _client = create_client(url, key)
        logger.info(f"Supabase client inicializado → {url}")
    return _client
