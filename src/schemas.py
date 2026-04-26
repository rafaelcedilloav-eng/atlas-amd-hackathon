"""
Pydantic schemas — contratos de datos entre agentes ATLAS.
"""
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Literal, Annotated
from datetime import datetime


class ExtractedField(BaseModel):
    value: Decimal | str | None
    confidence: float = Field(ge=0.0, le=1.0)


class VisionOutput(BaseModel):
    document_id: str
    document_type: Literal["invoice", "contract", "unknown"]
    pdf_path: str
    extracted_fields: dict[str, ExtractedField]
    detected_issues: List[str]
    confidence: float = Field(ge=0.0, le=1.0)
    model_used: str
    processing_time_ms: int
    timestamp: datetime


class ReasoningStep(BaseModel):
    step: int
    description: str
    evidence: str
    conclusion: str


class ReasoningOutput(BaseModel):
    document_id: str
    trap_detected: Literal["Math Error", "Missing Field", "Inconsistency", "Unclear Value", "No Trap"]
    trap_id: str
    reasoning_chain: Annotated[List[ReasoningStep], Field(min_length=3)]
    trap_severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning_valid: bool
    assumptions: List[str]
    model_used: str
    processing_time_ms: int
    timestamp: datetime
    used_fallback: bool = False


class ValidationResult(BaseModel):
    logically_sound: bool
    trap_is_real: bool
    severity_confirmed: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE"]
    math_verified: Optional[bool] = None
    math_verification_detail: Optional[str] = None


class ValidatorOutput(BaseModel):
    model_config = ConfigDict(json_encoders={Decimal: str})

    document_id: str
    trap_id: str
    validation_result: ValidationResult
    validation_confidence: Decimal = Field(ge=Decimal("0.0"), le=Decimal("1.0"))
    issues_found: List[str]
    adjustments: List[str]
    recommendation: Literal["APPROVE", "FLAG", "UNCERTAIN"]
    recommendation_detail: str
    model_used: str
    timestamp: datetime


class ConfidenceBreakdown(BaseModel):
    vision_confidence: float
    reasoning_confidence: float
    validation_confidence: float
    overall_confidence: float


class ExplanationContent(BaseModel):
    title: str
    summary: str
    detailed_explanation: str
    why_its_a_trap: str
    what_to_do: List[str]
    financial_impact: str


class ExplainerOutput(BaseModel):
    document_id: str
    document_type: str
    trap_type: str
    trap_severity: str
    explanation: ExplanationContent
    confidence_breakdown: ConfidenceBreakdown
    human_review_required: bool
    next_action: Literal["AWAIT_HUMAN_DECISION", "AUTO_APPROVE", "ESCALATE"]
    language: str = "es-MX"
    markdown_report: str
    timestamp: datetime


class PipelineResult(BaseModel):
    document_id: str
    pdf_path: str
    status: Literal["COMPLETE", "PARTIAL", "FAILED"]
    vision: Optional[VisionOutput] = None
    reasoning: Optional[ReasoningOutput] = None
    validation: Optional[ValidatorOutput] = None
    explanation: Optional[ExplainerOutput] = None
    total_processing_time_ms: int
    error: Optional[str] = None
    timestamp: datetime
