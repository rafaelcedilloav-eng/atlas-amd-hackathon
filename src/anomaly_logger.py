import json
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import asdict
from typing import Dict

from src.pipeline_gates import GateResult

logger = logging.getLogger(__name__)

def log_anomaly(gate_result: GateResult) -> None:
    """Append gate result to anomaly_log.jsonl if there are anomalies."""
    if not gate_result.anomalies and gate_result.decision == "PASS":
        return

    try:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "anomaly_log.jsonl"
        
        entry = {
            **asdict(gate_result),
            "logged_at": datetime.now().isoformat()
        }
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
            
        logger.warning(f"Anomalía registrada en {gate_result.gate_id} para doc {gate_result.document_id}")
    except Exception as e:
        logger.error(f"Error escribiendo en anomaly_log: {e}")

def get_anomaly_patterns(last_n: int = 100) -> Dict[str, int]:
    """
    Lee las últimas N entradas del log y agrupa anomalías por tipo.
    """
    patterns = {}
    try:
        log_file = Path("logs/anomaly_log.jsonl")
        if not log_file.exists():
            return {}
            
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()[-last_n:]
            
        for line in lines:
            entry = json.loads(line)
            for anomaly in entry.get("anomalies", []):
                patterns[anomaly] = patterns.get(anomaly, 0) + 1
    except Exception as e:
        logger.error(f"Error leyendo patrones de anomalías: {e}")
        
    return dict(sorted(patterns.items(), key=lambda item: item[1], reverse=True))
