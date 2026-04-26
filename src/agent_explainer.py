"""
ATLAS Agent 4: Explainer (Executive Reporter)
Transforma los hallazgos técnicos en reportes ejecutivos profesionales es-MX.
"""
import os
import re
import json
import logging
import time
from datetime import datetime

from src.vllm_client import call_llm
from src.schemas import ExplainerOutput, PipelineResult, ConfidenceBreakdown, ExplanationContent
from src.supabase_persistence import log_agent_action

logger = logging.getLogger(__name__)

class ExplainerAgent:
    def __init__(self):
        self.model_name = os.getenv("VLLM_MODEL", "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B")

    async def generate_report(self, pipeline_result: PipelineResult) -> ExplainerOutput:
        """
        Genera el reporte final basado en los resultados de todo el pipeline.
        """
        start_time = time.time()
        logger.info(f"Generando reporte ejecutivo para: {pipeline_result.document_id}")

        # Recopilar contexto para el LLM
        context = {
            "vision": pipeline_result.vision.model_dump(mode="json") if pipeline_result.vision else {},
            "reasoning": pipeline_result.reasoning.model_dump(mode="json") if pipeline_result.reasoning else {},
            "validation": pipeline_result.validation.model_dump(mode="json") if pipeline_result.validation else {},
            "status": pipeline_result.status
        }

        prompt = f"""GENERA UN REPORTE DE AUDITORÍA EJECUTIVO PROFESIONAL.
CONTEXTO DE AUDITORÍA:
{json.dumps(context, indent=2)}

INSTRUCCIÓN:
Como socio de auditoría senior, redacta un reporte en ESPAÑOL (es-MX) que sea claro, directo y profesional.
El reporte debe ser un JSON que siga esta estructura exacta:
{{
  "explanation": {{
    "title": "Título impactante del reporte",
    "summary": "Resumen ejecutivo de 2 párrafos",
    "detailed_explanation": "Explicación técnica de los hallazgos",
    "why_its_a_trap": "Explicación clara de por qué esto se considera una anomalía o fraude",
    "what_to_do": ["acción 1", "acción 2"],
    "financial_impact": "Descripción del impacto económico"
  }},
  "human_review_required": true/false,
  "next_action": "AWAIT_HUMAN_DECISION" | "AUTO_APPROVE" | "ESCALATE",
  "markdown_report": "Versión completa del reporte en formato Markdown elegante"
}}

Reglas:
1. Sé extremadamente profesional.
2. Si hubo un error matemático o blacklist, resáltalo como crítico.
3. Responde SOLO el JSON."""

        v_conf = pipeline_result.vision.confidence if pipeline_result.vision else 0.0
        r_conf = pipeline_result.reasoning.confidence if pipeline_result.reasoning else 0.0
        val_conf = float(pipeline_result.validation.validation_confidence) if pipeline_result.validation else 0.0
        overall = round((v_conf + r_conf + val_conf) / 3, 3)
        confidence_breakdown = ConfidenceBreakdown(
            vision_confidence=v_conf,
            reasoning_confidence=r_conf,
            validation_confidence=val_conf,
            overall_confidence=overall,
        )

        try:
            response = call_llm(
                prompt,
                system_prompt="Eres un Socio de Auditoría en una Big Four. Tu especialidad es la comunicación ejecutiva de hallazgos forenses complejos.",
            )

            # Limpieza DeepSeek-R1: strips <think>...</think> y <thinking>...</thinking>
            json_content = re.sub(
                r'<think(?:ing)?>(.*?)</think(?:ing)?>',
                '', response, flags=re.DOTALL,
            ).strip()

            start = json_content.find('{')
            end = json_content.rfind('}') + 1
            data = json.loads(json_content[start:end])

            explanation = ExplanationContent(**data.get("explanation", {}))
            processing_time_ms = int((time.time() - start_time) * 1000)

            output = ExplainerOutput(
                document_id=pipeline_result.document_id,
                document_type=pipeline_result.vision.document_type if pipeline_result.vision else "unknown",
                trap_type=pipeline_result.reasoning.trap_detected if pipeline_result.reasoning else "Unknown",
                trap_severity=pipeline_result.reasoning.trap_severity if pipeline_result.reasoning else "NONE",
                explanation=explanation,
                confidence_breakdown=confidence_breakdown,
                human_review_required=data.get("human_review_required", True),
                next_action=data.get("next_action", "AWAIT_HUMAN_DECISION"),
                markdown_report=data.get("markdown_report", ""),
                timestamp=datetime.now(),
            )

            log_agent_action(
                doc_id=output.document_id,
                agent="explainer",
                action="generate_executive_report",
                input_data={"status": pipeline_result.status},
                output_data=output.model_dump(mode="json"),
                duration_ms=processing_time_ms,
                success=True,
            )
            return output

        except Exception as e:
            logger.error(f"Error en Agente Explainer: {e} — generando reporte de emergencia")
            processing_time_ms = int((time.time() - start_time) * 1000)
            trap = pipeline_result.reasoning.trap_detected if pipeline_result.reasoning else "Unknown"
            severity = pipeline_result.reasoning.trap_severity if pipeline_result.reasoning else "MEDIUM"

            emergency = ExplainerOutput(
                document_id=pipeline_result.document_id,
                document_type=pipeline_result.vision.document_type if pipeline_result.vision else "unknown",
                trap_type=trap,
                trap_severity=severity,
                explanation=ExplanationContent(
                    title="Error en generación de reporte — Revisión manual requerida",
                    summary="El sistema encontró un error al generar el reporte ejecutivo. Los hallazgos técnicos están disponibles en los logs.",
                    detailed_explanation=f"Error del sistema: {str(e)[:300]}",
                    why_its_a_trap="No disponible — revisar resultados de los Agentes 2 y 3.",
                    what_to_do=["Revisar manualmente el documento", "Consultar audit_trail en Supabase", "Escalar al equipo de auditoría"],
                    financial_impact="Por determinar manualmente.",
                ),
                confidence_breakdown=confidence_breakdown,
                human_review_required=True,
                next_action="AWAIT_HUMAN_DECISION",
                markdown_report=f"# Error en Agente Explainer\n\n**Documento:** {pipeline_result.document_id}\n\n**Error:** {str(e)[:200]}\n\nRevisión humana mandatoria.",
                timestamp=datetime.now(),
            )
            log_agent_action(
                doc_id=emergency.document_id,
                agent="explainer",
                action="generate_executive_report_emergency",
                input_data={"status": pipeline_result.status},
                output_data={"error": str(e)},
                duration_ms=processing_time_ms,
                success=False,
                error_message=str(e),
            )
            return emergency
