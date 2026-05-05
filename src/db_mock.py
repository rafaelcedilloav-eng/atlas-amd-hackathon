"""
MOCK Supabase Client for ATLAS Dry-Run
"""
import logging

logger = logging.getLogger(__name__)

def get_client():
    return None

def reset_client():
    pass

def save_audit_result(data):
    logger.info(f"[MOCK DB] Guardando resultado: {data.get('doc_id')}")

def is_duplicate(doc_id, hash_val):
    return False

def is_blacklisted(name, rfc):
    return {"blacklisted": False}

def register_processed_doc(data):
    pass

def log_agent_action(**kwargs):
    pass
