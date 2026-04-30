from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List
import logging

from src.schemas import VisionOutput, ReasoningOutput, ValidatorOutput

class GateDecision(str, Enum):
    PASS = "PASS"
    RETRY = "RETRY"
    ESCALATE = "ESCALATE"

@dataclass
class GateResult:
    gate_id: str              # "gate_1_2", "gate_2_3", "gate_3_4"
    decision: GateDecision
    anomalies: List[str]      # lista de lo que encontró raro
    retry_hint: Optional[str] # contexto para el reintento si decision == RETRY
    document_id: str
    timestamp: str

def gate_1_2(vision: VisionOutput) -> GateResult:
    """Valida Vision antes de pasar a Reasoning."""
    anomalies = []
    decision = GateDecision.PASS
    
    if vision.confidence < 0.3:
        anomalies.append(f"Confianza muy baja en visión: {vision.confidence}")
        decision = GateDecision.RETRY
        
    if vision.document_type == "unknown" and vision.confidence > 0.5:
        anomalies.append("Documento no clasificado a pesar de alta confianza")
        
    return GateResult(
        gate_id="gate_1_2",
        decision=decision,
        anomalies=anomalies,
        retry_hint="Reintentar extracción con mayor temperatura o prompt reforzado" if decision == GateDecision.RETRY else None,
        document_id=vision.document_id,
        timestamp=datetime.now().isoformat()
    )

def gate_2_3(vision: VisionOutput, reasoning: ReasoningOutput) -> GateResult:
    """Valida Reasoning contra Vision."""
    anomalies = []
    decision = GateDecision.PASS
    
    # Consistencia de trampa
    has_math_issue = any("Math Error" in issue for issue in vision.detected_issues)
    if has_math_issue and reasoning.trap_detected == "No Trap":
        anomalies.append("CONTRADICCIÓN: Vision detectó error matemático pero Reasoning no encontró trampa")
        decision = GateDecision.ESCALATE

    if len(reasoning.reasoning_chain) < 3:
        anomalies.append(f"Cadena de razonamiento demasiado corta: {len(reasoning.reasoning_chain)} pasos")
        if decision != GateDecision.ESCALATE: decision = GateDecision.RETRY

    return GateResult(
        gate_id="gate_2_3",
        decision=decision,
        anomalies=anomalies,
        retry_hint="Solicitar al razonador profundizar en las evidencias de Vision" if decision == GateDecision.RETRY else None,
        document_id=vision.document_id,
        timestamp=datetime.now().isoformat()
    )

def gate_3_4(reasoning: ReasoningOutput, validator: ValidatorOutput) -> GateResult:
    """Valida Validator contra Reasoning."""
    anomalies = []
    decision = GateDecision.PASS
    
    # Contradicción: Si se verificó un error matemático (math_verified es False)
    # pero trap_is_real es False, es una anomalía crítica.
    if validator.validation_result.math_verified is False and not validator.validation_result.trap_is_real:
        anomalies.append("CONTRADICCIÓN: Error matemático confirmado pero se reporta como documento sin trampa")
        decision = GateDecision.ESCALATE
        
    if validator.recommendation == "APPROVE" and validator.validation_result.trap_is_real:
        anomalies.append("RIESGO SEMÁNTICO: Recomendación de aprobación para documento con trampa confirmada")
        decision = GateDecision.ESCALATE

    return GateResult(
        gate_id="gate_3_4",
        decision=decision,
        anomalies=anomalies,
        retry_hint=None,
        document_id=reasoning.document_id,
        timestamp=datetime.now().isoformat()
    )
