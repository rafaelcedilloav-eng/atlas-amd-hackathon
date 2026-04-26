"""
ATLAS Agent 2: Reasoning (DeepSeek-R1)
Analiza los datos extraídos para detectar trampas y fraudes usando Chain-of-Thought.
"""
import os
import re
import json
import logging
import time
from datetime import datetime
from typing import List

from src.vllm_client import call_llm
from src.schemas import ReasoningOutput, ReasoningStep, VisionOutput
from src.supabase_persistence import log_agent_action

logger = logging.getLogger(__name__)

class ReasoningAgent:
    def __init__(self):
        self.model_name = os.getenv("VLLM_MODEL", "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B")

    async def reason_about_document(self, vision_output: VisionOutput) -> ReasoningOutput:
        """
        Analiza los campos extraídos por el Agente 1 para detectar inconsistencias lógicas o fraude.
        """
        start_time = time.time()
        logger.info(f"Iniciando razonamiento forense para: {vision_output.document_id}")

        # Preparar contexto para el LLM
        fields_json = json.dumps(
            {k: v.model_dump() for k, v in vision_output.extracted_fields.items()}, 
            indent=2
        )
        
        prompt = f"""AUDITORÍA FORENSE REQUERIDA.
DOCUMENTO: {vision_output.document_type}
CAMPOS EXTRAÍDOS:
{fields_json}

INSTRUCCIÓN:
Como auditor forense, analiza estos datos buscando "trampas" o fraudes comunes:
1. Errores matemáticos (Subtotal + IVA != Total).
2. RFCs inválidos o sospechosos.
3. Fechas inconsistentes o términos de pago inusuales.
4. Montos inflados o conceptos vagos.

DEBES RESPONDER EN FORMATO JSON SIGUIENDO ESTA ESTRUCTURA:
{{
  "trap_detected": "Math Error" | "Missing Field" | "Inconsistency" | "Unclear Value" | "No Trap",
  "trap_id": "T-00X",
  "trap_severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "NONE",
  "reasoning_chain": [
    {{
      "step": 1,
      "description": "descripción del paso",
      "evidence": "evidencia encontrada",
      "conclusion": "conclusión del paso"
    }},
    ... (mínimo 3 pasos)
  ],
  "confidence": 0.0 a 1.0,
  "reasoning_valid": true,
  "assumptions": ["lista de asunciones hechas"]
}}

IMPORTANTE: Si detectas un error matemático, detállalo paso a paso. Responde SOLO el JSON."""

        try:
            response = call_llm(prompt, system_prompt="Eres un Auditor Forense Senior de ATLAS. Tu especialidad es detectar anomalías en documentos financieros usando razonamiento deductivo profundo.")

            # Limpieza de respuesta para DeepSeek-R1 (<think>...</think> o <thinking>...</thinking>)
            json_content = re.sub(
                r'<think(?:ing)?>(.*?)</think(?:ing)?>',
                '', response, flags=re.DOTALL
            ).strip()

            # Parsear JSON
            start = json_content.find('{')
            end = json_content.rfind('}') + 1
            data = json.loads(json_content[start:end])

            # Mapeo a ReasoningStep — asegurar mínimo 3 pasos
            raw_steps = data.get("reasoning_chain", [])
            while len(raw_steps) < 3:
                raw_steps.append({
                    "step": len(raw_steps) + 1,
                    "description": "Verificación adicional requerida",
                    "evidence": "Paso requerido por política de auditoría",
                    "conclusion": "Confirmar hallazgos anteriores",
                })
            steps = [ReasoningStep(**s) for s in raw_steps]

            processing_time_ms = int((time.time() - start_time) * 1000)

            output = ReasoningOutput(
                document_id=vision_output.document_id,
                trap_detected=data.get("trap_detected", "Unclear Value"),
                trap_id=data.get("trap_id", f"T-{vision_output.document_id[:8]}-001"),
                reasoning_chain=steps,
                trap_severity=data.get("trap_severity", "MEDIUM"),
                confidence=float(data.get("confidence", 0.8)),
                reasoning_valid=data.get("reasoning_valid", True),
                assumptions=data.get("assumptions", []),
                model_used=self.model_name,
                processing_time_ms=processing_time_ms,
                timestamp=datetime.now(),
                used_fallback=False,
            )

            log_agent_action(
                doc_id=output.document_id,
                agent="reasoning",
                action="forensic_analysis",
                input_data={"vision_confidence": vision_output.confidence},
                output_data=output.model_dump(mode="json"),
                duration_ms=processing_time_ms,
                success=True,
            )

            return output

        except Exception as e:
            logger.error(f"Error en Agente de Razonamiento: {e} — activando fallback determinista")
            processing_time_ms = int((time.time() - start_time) * 1000)
            first_issue = vision_output.detected_issues[0] if vision_output.detected_issues else "Anomalía detectada"
            fallback = ReasoningOutput(
                document_id=vision_output.document_id,
                trap_detected="Unclear Value",
                trap_id=f"T-{vision_output.document_id[:8]}-FALLBACK",
                reasoning_chain=[
                    ReasoningStep(step=1, description="LLM no disponible", evidence=str(e)[:200], conclusion="Análisis incompleto — fallback activado"),
                    ReasoningStep(step=2, description="Revisión de issues detectados", evidence=first_issue, conclusion="Se detectaron posibles anomalías en el documento"),
                    ReasoningStep(step=3, description="Escalamiento preventivo", evidence="Error de sistema", conclusion="Revisión humana obligatoria"),
                ],
                trap_severity="MEDIUM",
                confidence=0.3,
                reasoning_valid=False,
                assumptions=["Análisis basado en fallback — resultado del LLM no disponible"],
                model_used="rule-based-fallback",
                processing_time_ms=processing_time_ms,
                timestamp=datetime.now(),
                used_fallback=True,
            )
            log_agent_action(
                doc_id=fallback.document_id,
                agent="reasoning",
                action="forensic_analysis_fallback",
                input_data={"vision_confidence": vision_output.confidence},
                output_data={"error": str(e), "used_fallback": True},
                duration_ms=processing_time_ms,
                success=False,
                error_message=str(e),
            )
            return fallback
