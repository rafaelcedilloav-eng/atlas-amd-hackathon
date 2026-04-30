"""
ATLAS Agent 4: Explainer — Executive Reporter
Gemini 2.5 Pro (Vertex AI) con Google Search grounding.
Genera el reporte ejecutivo en es-MX y enriquece el market_intelligence
con datos reales buscados en tiempo real.
"""
import re
import json
import logging
import time
from datetime import datetime

from src.schemas import (
    ExplainerOutput, PipelineResult, ConfidenceBreakdown,
    ExplanationContent, MarketData,
)
from src.supabase_persistence import log_agent_action

logger = logging.getLogger(__name__)

_EXPLAINER_MODEL = "gemini-2.5-pro"


class ExplainerAgent:
    def __init__(self):
        self.model_name = _EXPLAINER_MODEL

    async def generate_report(self, pipeline_result: PipelineResult) -> ExplainerOutput:
        start_time = time.time()
        logger.info(f"Explainer Agent (Gemini 2.5 Pro + Search): {pipeline_result.document_id}")

        context = {
            "vision":      pipeline_result.vision.model_dump(mode="json")     if pipeline_result.vision      else {},
            "compliance":  pipeline_result.compliance.model_dump(mode="json") if pipeline_result.compliance  else {},
            "reasoning":   pipeline_result.reasoning.model_dump(mode="json")  if pipeline_result.reasoning   else {},
            "validation":  pipeline_result.validation.model_dump(mode="json") if pipeline_result.validation  else {},
            "status":      pipeline_result.status,
        }

        # Extraer nombre de empresa para que Search tenga contexto
        vendor = ""
        buyer  = ""
        if pipeline_result.vision and pipeline_result.vision.extracted_fields:
            vendor_f = pipeline_result.vision.extracted_fields.get("vendor") or \
                       pipeline_result.vision.extracted_fields.get("proveedor") or \
                       pipeline_result.vision.extracted_fields.get("emisor")
            buyer_f  = pipeline_result.vision.extracted_fields.get("buyer") or \
                       pipeline_result.vision.extracted_fields.get("comprador") or \
                       pipeline_result.vision.extracted_fields.get("receptor")
            vendor = str(vendor_f.value) if vendor_f else ""
            buyer  = str(buyer_f.value)  if buyer_f  else ""

        company_hint = vendor or buyer or "la empresa del documento"

        prompt = f"""GENERA UN REPORTE DE AUDITORÍA EJECUTIVO COMPLETO.

EMPRESA PRINCIPAL DEL DOCUMENTO: "{company_hint}"
PAÍS DETECTADO: {pipeline_result.compliance.country_detected if pipeline_result.compliance else "UNKNOWN"}

CONTEXTO TÉCNICO DEL PIPELINE:
{json.dumps(context, indent=2, ensure_ascii=False)}

INSTRUCCIÓN:
Actúa como Socio de Auditoría Senior y Analista de Inteligencia Global.
1. Usa Google Search para buscar información real sobre "{company_hint}":
   presencia geográfica, sector, noticias recientes, listas de sanciones.
2. Redacta el reporte COMPLETO en ESPAÑOL (es-MX), profesional y ejecutivo.
3. Genera el market_intelligence con datos REALES encontrados en búsqueda.

RESPONDE ÚNICAMENTE CON JSON válido (sin markdown, sin backticks):
{{
  "explanation": {{
    "title": "Título ejecutivo del hallazgo",
    "summary": "Resumen de 2-3 oraciones para el CFO",
    "detailed_explanation": "Análisis técnico detallado",
    "why_its_a_trap": "Por qué este documento es sospechoso o fraudulento",
    "what_to_do": ["Acción concreta 1", "Acción concreta 2"],
    "financial_impact": "Estimación del impacto económico"
  }},
  "market_intelligence": [
    {{
      "country_code": "MX",
      "participation_pct": 35.0,
      "status": "Established",
      "influence_score": 8,
      "audits_completed": 0,
      "alerts_forenses": 0,
      "risk_level": "medium"
    }}
  ],
  "human_review_required": true,
  "next_action": "AWAIT_HUMAN_DECISION",
  "markdown_report": "# Reporte completo en Markdown"
}}

Reglas:
- market_intelligence: mínimo 3 países reales donde opera "{company_hint}".
  Si no encuentras datos reales, usa tu conocimiento del sector para estimar.
  risk_level debe reflejar hallazgos de la auditoría: si hay fraude en un país, sube su risk.
- next_action debe ser uno de: AWAIT_HUMAN_DECISION | AUTO_APPROVE | ESCALATE
- El markdown_report debe incluir secciones: Resumen Ejecutivo, Hallazgos, Evidencia, Recomendaciones."""

        v_conf   = pipeline_result.vision.confidence     if pipeline_result.vision     else 0.0
        r_conf   = pipeline_result.reasoning.confidence  if pipeline_result.reasoning  else 0.0
        val_conf = float(pipeline_result.validation.validation_confidence) if pipeline_result.validation else 0.0
        overall  = round((v_conf + r_conf + val_conf) / 3, 3)
        confidence_breakdown = ConfidenceBreakdown(
            vision_confidence=v_conf,
            reasoning_confidence=r_conf,
            validation_confidence=val_conf,
            overall_confidence=overall,
        )

        try:
            from src.vertex_client import call_gemini

            response_text = call_gemini(
                prompt=prompt,
                model=_EXPLAINER_MODEL,
                system=(
                    "Eres un Socio de Auditoría Forense Senior. Combinas datos técnicos "
                    "del pipeline con investigación en tiempo real para producir reportes "
                    "ejecutivos que protejan a la organización de fraudes financieros."
                ),
                with_search=True,
                temperature=0.2,
            )

            # Gemini no genera <think> tags, solo limpiar posibles backticks
            cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", response_text).strip()
            start = cleaned.find("{")
            end   = cleaned.rfind("}") + 1
            data  = json.loads(cleaned[start:end])

            explanation = ExplanationContent(**data.get("explanation", {}))

            market_intel_raw = data.get("market_intelligence", [])
            market_intel = []
            for m in market_intel_raw:
                try:
                    market_intel.append(MarketData(**m))
                except Exception:
                    pass

            human_review_required = data.get("human_review_required", True)
            if pipeline_result.reasoning:
                human_review_required = pipeline_result.reasoning.trap_severity != "NONE"

            output = ExplainerOutput(
                document_id=pipeline_result.document_id,
                document_type=pipeline_result.vision.document_type if pipeline_result.vision else "unknown",
                trap_type=pipeline_result.reasoning.trap_detected   if pipeline_result.reasoning else "Unknown",
                trap_severity=pipeline_result.reasoning.trap_severity if pipeline_result.reasoning else "NONE",
                explanation=explanation,
                confidence_breakdown=confidence_breakdown,
                human_review_required=human_review_required,
                next_action=data.get("next_action", "AWAIT_HUMAN_DECISION"),
                markdown_report=data.get("markdown_report", ""),
                market_intelligence=market_intel or None,
                timestamp=datetime.now(),
            )

            try:
                log_agent_action(
                    document_id=pipeline_result.document_id,
                    agent_name="explainer",
                    model_used=_EXPLAINER_MODEL,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    output_data=output.model_dump(mode="json"),
                )
            except Exception:
                pass

            return output

        except Exception as e:
            logger.error(f"Explainer Agent falló: {e} — reporte de emergencia")
            return ExplainerOutput(
                document_id=pipeline_result.document_id,
                document_type="unknown",
                trap_type="Unknown",
                trap_severity="MEDIUM",
                explanation=ExplanationContent(
                    title="Error en generación de reporte",
                    summary="El agente Explainer encontró un error interno.",
                    detailed_explanation=str(e),
                    why_its_a_trap="No determinado",
                    what_to_do=["Revisar logs del sistema", "Escalar a revisión manual"],
                    financial_impact="No determinado",
                ),
                confidence_breakdown=confidence_breakdown,
                human_review_required=True,
                next_action="AWAIT_HUMAN_DECISION",
                markdown_report="# Error\nEl agente Explainer requiere revisión manual.",
                timestamp=datetime.now(),
            )
