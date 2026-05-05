"""
ATLAS v3.0 - UUIDv7 generator utility
"""
import time
import uuid

def generate_audit_id() -> str:
    """Generate UUIDv7 for temporal sorting and traceability"""
    timestamp_ms = int(time.time() * 1000)
    rand = uuid.uuid4().int & 0x3FFFFFFFFFFF  # 74 bits random
    uuid7_int = (timestamp_ms << 74) | rand
    return str(uuid.UUID(int=uuid7_int, version=7))
