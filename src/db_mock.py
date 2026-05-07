"""
ATLAS In-Memory Store — persiste audits durante la sesión del servidor.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

_audit_store: Dict[str, dict] = {}


def get_client():
    return None


def reset_client():
    pass


def save_audit_result(data: dict):
    doc_id = data.get("document_id")
    if not doc_id:
        logger.warning("[DB] save_audit_result called without document_id")
        return
    _audit_store[doc_id] = data
    logger.info(f"[DB] Guardado: {doc_id} status={data.get('status')}")


def get_audit_result(doc_id: str) -> Optional[dict]:
    return _audit_store.get(doc_id)


def get_all_audits(limit: int = 20, search: Optional[str] = None, severity: Optional[str] = None) -> List[dict]:
    results = list(reversed(list(_audit_store.values())))

    if severity:
        results = [
            r for r in results
            if (r.get("reasoning") or {}).get("trap_severity", "").upper() == severity.upper()
        ]
    if search:
        s = search.lower()
        results = [
            r for r in results
            if s in str(r.get("document_id", "")).lower()
            or s in str((r.get("vision") or {}).get("document_type", "")).lower()
        ]
    return results[:limit]


def get_stats() -> dict:
    if not _audit_store:
        return {
            "total_audits": 0,
            "fraud_detected": 0,
            "avg_confidence_pct": 0.0,
            "avg_processing_time_ms": 0.0,
            "distribution": {},
        }

    total = len(_audit_store)
    fraud = sum(
        1 for r in _audit_store.values()
        if (r.get("reasoning") or {}).get("trap_severity", "NONE") not in ("NONE", "LOW")
    )
    confidences = []
    times = []
    dist: Dict[str, int] = {}

    for r in _audit_store.values():
        expl = r.get("explanation") or {}
        cb = expl.get("confidence_breakdown") or {}
        if cb.get("overall_confidence"):
            confidences.append(float(cb["overall_confidence"]))
        if r.get("total_processing_time_ms"):
            times.append(float(r["total_processing_time_ms"]))
        sev = (r.get("reasoning") or {}).get("trap_severity", "UNKNOWN")
        dist[sev] = dist.get(sev, 0) + 1

    return {
        "total_audits": total,
        "fraud_detected": fraud,
        "avg_confidence_pct": round(sum(confidences) / len(confidences) * 100, 1) if confidences else 0.0,
        "avg_processing_time_ms": round(sum(times) / len(times), 0) if times else 0.0,
        "distribution": dist,
    }


def is_duplicate(doc_id, hash_val):
    return False


def is_blacklisted(name, rfc):
    return {"blacklisted": False}


def register_processed_doc(data):
    pass


def log_agent_action(**kwargs):
    pass
