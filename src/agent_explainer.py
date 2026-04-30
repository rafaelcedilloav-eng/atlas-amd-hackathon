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
from src.config import settings

logger = logging.getLogger(__name__)

def extract_json_from_response(response: str) -> dict:
    """Extrae un objeto JSON válido de una respuesta de LLM, incluso si contiene texto adicional."""
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        pass

    start = response.find('{')
    end = response.rfind('}') + 1
    if start != -1 and end > start:
        json_str = response[start:end]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    cleaned = re.sub(r'<think(?:ing)?>(.*?)</think(?:ing)?>', '', response, flags=re.DOTALL)
    start = cleaned.find('{')
    end = cleaned.rfind('}') + 1
    if start != -1 and end > start:
        json_str = cleaned[start:end]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    raise ValueError("No se pudo extraer un JSON válido de la respuesta del LLM.")

class ExplainerAgent:
    def __init__(self):
        self.model_name = settings.model_name

    async def generate_report(self, pipeline_result: PipelineResult) -> ExplainerOutput:
        start_time = time.time()
        logger.info(f"Generando reporte ejecutivo para: {pipeline_result.document_id}")

        context = {
            "vision":     pipeline_result.vision.model_dump(mode="json")     if pipeline_result.vision     else {},
            "reasoning":  pipeline_result.reasoning.model_dump(mode="json")  if pipeline_result.reasoning  else {},
            "validation": pipeline_result.validation.model_dump(mode="json") if pipeline_result.validation else {},
            "status":     pipeline_result.status
        }

        prompt = f"""ERES UN PROCESO AUTOMÁTICO DE AUDITORÍA FORENSE Y ANÁLISIS ESTRATÉGICO GLOBAL.
CONTEXTO DE AUDITORÍA:
{json.dumps(context, indent=2)}

INSTRUCCIÓN:
1. Genera un reporte ejecutivo en formato JSON válido, sin texto adicional, sin razonamiento visible, sin etiquetas <think>.
2. Basa tu análisis en los datos técnicos proporcionados.
3. Si la empresa tiene presencia global, estima al menos 3 mercados relevantes con datos de inteligencia de mercado.

RESPUESTA ESPERADA:
{{"explanation":{{"title":"Título","summary":"Resumen","detailed_explanation":"Detalle","why_its_a_trap":"Por qué es trampa","what_to_do":["acción"],"financial_impact":"Impacto"}},"market_intelligence":[{{"country_code":"ISO-2","participation_pct":0.0,"status":"Market Entry"|"Expanding"|"Established","influence_score":1-10,"audits_completed":0,"alerts_forenses":0,"risk_level":"low"|"medium"|"high"|"critical"}}],"human_review_required":true,"next_action":"AWAIT_HUMAN_DECISION","markdown_report":"Markdown"}}

REGLAS:
- NO INCLUYAS TEXTO INTRODUCTORIO.
- NO INCLUYAS ETIQUETAS DE RAZONAMIENTO (<think>, <reasoning>, etc.).
- NO INCLUYAS COMENTARIOS O EXPLICACIONES FUERA DEL JSON.
- RESPONDE ÚNICAMENTE CON UN OBJETO JSON VÁLIDO, SIN MARCAS DE CÓDIGO (sin ```json).
- Market Intelligence: Genera al menos 3 países relevantes para esta empresa (ej. si es Amazon: US, MX, DE).
- Si hubo fallos críticos, el risk_level en los mercados clave debe elevarse."""

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
            response = call_llm(
                prompt,
                system_prompt="Eres un Experto en Auditoría Forense y Estrategia de Mercados Globales. Tu misión es transformar datos técnicos en visión estratégica.",
                timeout=settings.timeout_explainer
            )

            data = extract_json_from_response(response)

            explanation      = ExplanationContent(**data.get("explanation", {}))
            market_intel_raw = data.get("market_intelligence", [])
            from src.schemas import MarketData
            market_intel = [MarketData(**m) for m in market_intel_raw]

            processing_time_ms = int((time.time() - start_time) * 1000)

            human_review_required = data.get("human_review_required", True)
            if pipeline_result.reasoning and hasattr(pipeline_result.reasoning, 'trap_severity'):
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
                timestamp=datetime.now(),
            )
            output.market_intelligence = market_intel

            log_agent_action(
                doc_id=output.document_id,
                agent="explainer",
                action="generate_market_report",
                input_data={"status": pipeline_result.status},
                output_data=output.model_dump(mode="json"),
                duration_ms=processing_time_ms,
                success=True,
            )
            return output

        except Exception as e:
            logger.error(f"Error en Agente Explainer: fallo durante la generación del reporte. Error: {type(e).__name__}")
            processing_time_ms = int((time.time() - start_time) * 1000)
            trap     = pipeline_result.reasoning.trap_detected  if pipeline_result.reasoning else "Unknown"
            severity = pipeline_result.reasoning.trap_severity  if pipeline_result.reasoning else "MEDIUM"

            emergency = ExplainerOutput(
                document_id=pipeline_result.document_id,
                document_type=pipeline_result.vision.document_type if pipeline_result.vision else "unknown",
                trap_type=trap,
                trap_severity=severity,
                explanation=ExplanationContent(
                    title="Error en generación de reporte — Revisión manual requerida",
                    summary="El sistema encontró un error al generar el reporte ejecutivo.",
                    detailed_explanation="Error del sistema detectado durante la generación del reporte.",
                    why_its_a_trap="No disponible — revisar resultados de los Agentes 2 y 3.",
                    what_to_do=["Revisar manualmente el documento", "Consultar audit_trail en Supabase", "Escalar al equipo de auditoría"],
                    financial_impact="Por determinar manualmente.",
                ),
                confidence_breakdown=confidence_breakdown,
                human_review_required=True,
                next_action="AWAIT_HUMAN_DECISION",
                markdown_report=f"# Error en Agente Explainer\n\n**Documento:** {pipeline_result.document_id}\n\n**Error:** Se produjo un fallo interno. Requiere revisión manual.\n\nRevisión humana mandatoria.",
                timestamp=datetime.now(),
            )
            log_agent_action(
                doc_id=emergency.document_id,
                agent="explainer",
                action="generate_executive_report_emergency",
                input_data={"status": pipeline_result.status},
                output_data={"error": "Fallo durante la generación del reporte."},
                duration_ms=processing_time_ms,
                success=False,
                error_message="Fallo durante la generación del reporte.",
            )
            return emergency
