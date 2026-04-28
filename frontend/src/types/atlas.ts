export type DocumentType = "invoice" | "contract" | "unknown";
export type TrapType = "Math Error" | "Missing Field" | "Inconsistency" | "Unclear Value" | "No Trap";
export type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "NONE";
export type Recommendation = "APPROVE" | "FLAG" | "UNCERTAIN";
export type HumanDecision = "APPROVE" | "REJECT" | "REQUEST_MORE_INFO" | null;

export interface ExtractedField {
  value: string | number | null;
  confidence: number;
}

export interface VisionOutput {
  document_id: string;
  document_type: DocumentType;
  pdf_path: string;
  extracted_fields: Record<string, ExtractedField>;
  detected_issues: string[];
  confidence: number;
  model_used: string;
  processing_time_ms: number;
  timestamp: string;
}

export interface ReasoningStep {
  step: number;
  description: string;
  evidence: string;
  conclusion: string;
}

export interface ReasoningOutput {
  document_id: string;
  trap_detected: TrapType;
  trap_id: string;
  reasoning_chain: ReasoningStep[];
  trap_severity: Severity;
  confidence: number;
  reasoning_valid: boolean;
  assumptions: string[];
  model_used: string;
  processing_time_ms: number;
  timestamp: string;
  used_fallback?: boolean;
}

export interface ValidationResult {
  logically_sound: boolean;
  trap_is_real: boolean;
  severity_confirmed: Severity;
  math_verified?: boolean;
  math_verification_detail?: string;
}

export interface ValidatorOutput {
  document_id: string;
  trap_id: string;
  validation_result: ValidationResult;
  validation_confidence: number;
  issues_found: string[];
  adjustments: string[];
  recommendation: Recommendation;
  recommendation_detail: string;
  model_used: string;
  timestamp: string;
}

export interface ConfidenceBreakdown {
  vision_confidence: number;
  reasoning_confidence: number;
  validation_confidence: number;
  overall_confidence: number;
}

export interface ExplanationContent {
  title: string;
  summary: string;
  detailed_explanation: string;
  why_its_a_trap: string;
  what_to_do: string[];
  financial_impact: string;
}

export interface ExplainerOutput {
  document_id: string;
  document_type: string;
  trap_type: string;
  trap_severity: Severity;
  explanation: ExplanationContent;
  confidence_breakdown: ConfidenceBreakdown;
  human_review_required: boolean;
  next_action: "AWAIT_HUMAN_DECISION" | "AUTO_APPROVE" | "ESCALATE";
  language: string;
  markdown_report: string;
  timestamp: string;
}

export interface PipelineResult {
  document_id: string;
  pdf_path: string;
  status: "COMPLETE" | "PARTIAL" | "FAILED";
  vision?: VisionOutput;
  reasoning?: ReasoningOutput;
  validation?: ValidatorOutput;
  explanation?: ExplainerOutput;
  total_processing_time_ms: number;
  error?: string;
  timestamp: string;
}

export interface AtlasAuditRow {
  document_id: string;
  status: string;
  result_json: PipelineResult;
  human_decision: HumanDecision;
  created_at: string;
  updated_at?: string;
}

export interface StatsResponse {
  total_audits: number;
  fraud_detected: number;
  avg_confidence_pct: number;
  avg_processing_time_ms: number;
  distribution: Record<string, number>;
}

export interface AuditListItem {
  doc_id: string;
  fraud_type: string | null;
  fraud_classification: string | null;
  severity: string | null;
  confidence_score: number | null;
  final_status: string;
  recommended_action: string | null;
  is_duplicate: boolean;
  is_blacklisted: boolean;
  created_at: string;
}
