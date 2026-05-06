"""
ATLAS v3.0 - UUIDv7 generator utility
"""
import time
import uuid

def generate_audit_id() -> str:
    """Generate timestamp-prefixed UUID for temporal sorting and traceability."""
    timestamp_ms = int(time.time() * 1000)
    rand = uuid.uuid4().int & 0x3FFFFFFFFFFF
    uuid7_int = (timestamp_ms << 74) | rand
    raw = uuid7_int.to_bytes(16, "big")
    # Set version nibble = 7 and variant bits manually (Python 3.11 rejects version=7)
    raw = raw[:6] + bytes([(raw[6] & 0x0F) | 0x70]) + raw[7:]
    raw = raw[:8] + bytes([(raw[8] & 0x3F) | 0x80]) + raw[9:]
    return str(uuid.UUID(bytes=raw))
