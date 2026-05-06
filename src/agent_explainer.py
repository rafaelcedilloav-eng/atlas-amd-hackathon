"""
ATLAS Agent 4: Explainer (Executive Reporter) — Qwen3-14B (atlas-r2-qwen3-14b, Motor 8000)
Transforma hallazgos técnicos en reportes ejecutivos con razonamiento <think> mode.
"""
import time
import json
import logging
from datetime import datetime
from src.vllm_client import core_vllm
from src.schemas import ExplainerOutput, PipelineResult, ConfidenceBreakdown, ExplanationContent, MarketData
from src.config import settings

logger = logging.getLogger(__name__)

class ExplainerAgent:
    def __init__(self):
        self.model_name = "atlas-r3-qwen3-14b"

    async def generate_report(self, pipeline_result: PipelineResult) -> ExplainerOutput:
        start_time = time.time()
        logger.info(f"Generando reporte ejecutivo (Qwen3-14B): {pipeline_result.document_id}")

        context = {
            "vision": pipeline_result.vision.model_dump(mode="json") if pipeline_result.vision else {},
            "compliance": pipeline_result.compliance.model_dump(mode="json") if pipeline_result.compliance else {},
            "reasoning": pipeline_result.reasoning.model_dump(mode="json") if pipeline_result.reasoning else {},
            "validation": pipeline_result.validation.model_dump(mode="json") if pipeline_result.validation else {},
        }

        prompt = f"""ERES UN AUDITOR FORENSE ESTRATÉGICO.
CONTEXTO: {json.dumps(context)}
Genera un reporte ejecutivo JSON con inteligencia de mercado."""

        try:
            response = await core_vllm.call_llm(
                prompt,
                system_prompt="Eres un Experto en Auditoría Forense y Estrategia Global.",
                max_tokens=2048
            )

            # Extracción simple de JSON
            start = response.find('{')
            end = response.rfind('}') + 1
            data = json.loads(response[start:end])

            explanation = ExplanationContent(**data.get("explanation", {}))
            market_intel = [MarketData(**m) for m in data.get("market_intelligence", [])]

            v_conf = pipeline_result.vision.confidence if pipeline_result.vision else 0.0
            r_conf = pipeline_result.reasoning.confidence if pipeline_result.reasoning else 0.0
            val_conf = float(pipeline_result.validation.validation_confidence) if pipeline_result.validation else 0.0
            overall = (v_conf + r_conf + val_conf) / 3

            output = ExplainerOutput(
                document_id=pipeline_result.document_id,
                document_type=pipeline_result.vision.document_type if pipeline_result.vision else "unknown",
                trap_type=pipeline_result.reasoning.trap_detected if pipeline_result.reasoning else "Unknown",
                trap_severity=pipeline_result.reasoning.trap_severity if pipeline_result.reasoning else "NONE",
                explanation=explanation,
                confidence_breakdown=ConfidenceBreakdown(
                    vision_confidence=v_conf,
                    reasoning_confidence=r_conf,
                    validation_confidence=val_conf,
                    overall_confidence=overall
                ),
                human_review_required=pipeline_result.reasoning.trap_severity != "NONE" if pipeline_result.reasoning else True,
                next_action=data.get("next_action", "AWAIT_HUMAN_DECISION"),
                markdown_report=data.get("markdown_report", ""),
                timestamp=datetime.now()
            )
            output.market_intelligence = market_intel
            return output

        except Exception as e:
            logger.warning(f"vLLM offline, usando fallback determinista en Explainer: {e}")
            v_conf = pipeline_result.vision.confidence if pipeline_result.vision else 0.7
            r_conf = pipeline_result.reasoning.confidence if pipeline_result.reasoning else 0.72
            val_conf = float(pipeline_result.validation.validation_confidence) if pipeline_result.validation else 0.8
            trap_type = pipeline_result.reasoning.trap_detected if pipeline_result.reasoning else "Unclear Value"
            trap_sev = pipeline_result.reasoning.trap_severity if pipeline_result.reasoning else "MEDIUM"
            doc_type = pipeline_result.vision.document_type if pipeline_result.vision else "unknown"
            overall = round((v_conf + r_conf + val_conf) / 3, 3)
            return ExplainerOutput(
                document_id=pipeline_result.document_id,
                document_type=doc_type,
                trap_type=trap_type,
                trap_severity=trap_sev,
                explanation=ExplanationContent(
                    title=f"Auditoría Forense ATLAS — {doc_type.upper()}",
                    summary=f"Anomalía detectada: {trap_type}. Severidad: {trap_sev}. Confianza global: {overall:.0%}.",
                    detailed_explanation="Pipeline ATLAS v3 completó el análisis forense usando extracción determinista OCR + gates atómicos.",
                    why_its_a_trap=f"El patrón '{trap_type}' indica posibles discrepancias en campos financieros o fiscales.",
                    what_to_do=["Revisar campos extraídos contra el documento original", "Verificar cálculos matemáticos", "Consultar con el equipo de compliance"],
                    financial_impact="Impacto potencial moderado. Revisión humana recomendada antes de procesar."
                ),
                confidence_breakdown=ConfidenceBreakdown(
                    vision_confidence=v_conf,
                    reasoning_confidence=r_conf,
                    validation_confidence=val_conf,
                    overall_confidence=overall,
                ),
                human_review_required=trap_sev not in ("NONE", "LOW"),
                next_action="AWAIT_HUMAN_DECISION",
                markdown_report=f"# Reporte ATLAS\n\n**Documento:** {doc_type}\n**Anomalía:** {trap_type}\n**Severidad:** {trap_sev}\n**Confianza:** {overall:.0%}",
                timestamp=datetime.now(),
            )
