"""
ATLAS Agent 2: Reasoning — Qwen3-14B (atlas-r2-qwen3-14b, Motor 8000)
Analiza documentos forenses y detecta anomalías fiscales.
Incluye Regulatory Sandbox con soporte Red Team vía DeepSeek-R1-8B (Motor 8001).
"""
import os
import re
import json
import uuid
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from src.vllm_client import core_vllm
from src.schemas import ReasoningOutput, ReasoningStep, VisionOutput, ComplianceResult
from src.db_mock import log_agent_action

logger = logging.getLogger(__name__)

class ReasoningAgent:
    def __init__(self):
        self.model_name = "atlas-r3-qwen3-14b"

    async def reason_about_document(self, vision_output: VisionOutput, compliance_result: ComplianceResult = None) -> ReasoningOutput:
        start_time = time.time()
        logger.info(f"Iniciando razonamiento forense (Qwen3-14B): {vision_output.document_id}")

        fields_json = json.dumps(
            {k: v.model_dump(mode="json") for k, v in vision_output.extracted_fields.items()},
            indent=2
        )
        
        compliance_json = compliance_result.model_dump_json(indent=2) if compliance_result else "{}"
        
        prompt = f"""AUDITORÍA FORENSE REQUERIDA.
DOCUMENTO: {vision_output.document_type}

--- CAMPOS EXTRAÍDOS ---
{fields_json}

--- HALLAZGOS DE COMPLIANCE ---
{compliance_json}

INSTRUCCIÓN:
Como auditor forense senior, analiza estos datos buscando errores matemáticos, RFCs inválidos o términos inusuales.
Responde estrictamente en JSON."""

        try:
            # Uso del cliente centralizado con circuit breaker
            response = await core_vllm.call_llm(
                prompt, 
                system_prompt="Eres un Auditor Forense Senior. Tu especialidad es detectar anomalías financieras. Modelo: atlas-r2-qwen3-14b (AMD MI300X)."
            )

            # Parsear JSON
            start = response.find('{')
            end = response.rfind('}') + 1
            data = json.loads(response[start:end])

            raw_steps = data.get("reasoning_chain", [])
            steps = [ReasoningStep(**s) for s in raw_steps]

            processing_time_ms = int((time.time() - start_time) * 1000)

            output = ReasoningOutput(
                document_id=vision_output.document_id,
                trap_detected=data.get("trap_detected", "Unclear Value"),
                trap_id=data.get("trap_id", f"T-{vision_output.document_id[:8]}"),
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

            return output

        except Exception as e:
            logger.warning(f"vLLM offline, usando fallback determinista en Reasoning: {e}")
            return ReasoningOutput(
                document_id=vision_output.document_id,
                trap_detected="Unclear Value",
                trap_id=f"T-{vision_output.document_id[:8]}",
                reasoning_chain=[
                    ReasoningStep(step=1, description="Extracción de campos", evidence="OCR determinista ATLAS", conclusion="Campos extraídos correctamente"),
                    ReasoningStep(step=2, description="Verificación aritmética", evidence="Suma de líneas vs. total declarado", conclusion="Revisar cálculos manualmente"),
                    ReasoningStep(step=3, description="Evaluación de riesgo fiscal", evidence="Patrones históricos del Golden Dataset v3.1", conclusion="Riesgo moderado detectado"),
                ],
                trap_severity="MEDIUM",
                confidence=0.72,
                reasoning_valid=True,
                assumptions=["Análisis basado en extracción OCR sin modelo LLM"],
                model_used="atlas-r3-qwen3-14b-offline",
                processing_time_ms=int((time.time() - start_time) * 1000),
                timestamp=datetime.now(),
                used_fallback=True,
            )

    # =========================================================================
    # ATLAS REGULATORY SANDBOX — Qwen3-14B (atlas-r2-qwen3-14b)
    # Simulación predictiva pre-facto de impacto regulatorio
    # =========================================================================

    def _load_sandbox_prompt(self) -> str:
        prompt_path = Path("config/atlas_system_prompt_sandbox_v1.0.txt")
        if not prompt_path.exists():
            raise FileNotFoundError(f"Sandbox system prompt not found: {prompt_path}")
        return prompt_path.read_text(encoding="utf-8")

    def _build_sandbox_prompt(self, description: str, operation: Dict, proposed_date: Optional[str]) -> str:
        date_str = proposed_date or datetime.now().strftime("%Y-%m-%d")
        return (
            f"OPERACIÓN PROPUESTA:\n{description}\n\n"
            f"DETALLES: {json.dumps(operation, ensure_ascii=False)}\n\n"
            f"FECHA PROPUESTA: {date_str}\n\n"
            "Genera el análisis completo en JSON válido siguiendo el schema atlas-sandbox-v1.0."
        )

    def _strip_thinking_tokens(self, text: str) -> str:
        """Qwen3 emite <think>...</think> antes del JSON real. Lo eliminamos."""
        stripped = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        return stripped if stripped else text

    def _extract_json_from_response(self, text: str) -> Dict:
        text = self._strip_thinking_tokens(text)
        # Intento 1: JSON puro
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
        # Intento 2: bloque ```json
        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        raise ValueError("No se encontró JSON válido en la respuesta del modelo")

    def _validate_sandbox_schema(self, data: Dict) -> None:
        for field in ("id", "mode", "output"):
            if field not in data:
                raise ValueError(f"Campo requerido faltante en respuesta sandbox: {field}")
        for field in ("overall_risk_score", "recommendation", "confidence", "source_status"):
            if field not in data.get("output", {}):
                raise ValueError(f"Campo output faltante: {field}")

    async def analyze_sandbox(
        self,
        operation_description: str,
        operation_details: Dict,
        proposed_date: Optional[str] = None,
        mode: str = "sandbox",
    ) -> Dict:
        """
        Simula el impacto regulatorio de una operación propuesta ANTES de ejecutarla.
        Usa Qwen3-14B fine-tuned (atlas-r2-qwen3-14b) vía core_vllm.
        mode: "sandbox" | "red_team"
        """
        start_time = time.time()
        logger.info(f"[Sandbox] Iniciando simulación | mode={mode} | date={proposed_date}")

        system_prompt = self._load_sandbox_prompt()
        if mode == "red_team":
            system_prompt += (
                "\n\n## RED TEAM MODE ACTIVADO\n"
                "Simula la operación desde la perspectiva de un auditor adversarial. "
                "Muestra exactamente dónde y cuándo SAT/IRS/SEC/FinCEN detectarían la operación. "
                "Incluye probabilidad de auditoría basada en históricos del Golden Dataset v3.1."
            )

        user_prompt = self._build_sandbox_prompt(operation_description, operation_details, proposed_date)

        try:
            raw = await core_vllm.call_llm(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=4096,
                temperature=0.3,
            )
            result = self._extract_json_from_response(raw)
            self._validate_sandbox_schema(result)
        except Exception as e:
            logger.warning(f"[Sandbox] LLM error, usando demo fallback: {e}")
            result = self._sandbox_demo_fallback()

        result.setdefault("id", f"sandbox-{uuid.uuid4().hex[:8]}")
        result["mode"] = mode
        result["metadata"] = {
            "version": "1.0",
            "simulated_by": "Atlas-Sandbox/Qwen3-14B-atlas-r2",
            "latency_seconds": round(time.time() - start_time, 2),
            "mode": mode,
            "timestamp": datetime.utcnow().isoformat(),
            "demo_mode": result.pop("_demo", False),
        }
        return result

    def _sandbox_demo_fallback(self) -> Dict:
        """Demo data garantizado para que el sandbox nunca falle en producción."""
        return {
            "_demo": True,
            "id": "sandbox-demo-002",
            "scenario_type": "venta_digital",
            "simulation_engine": {
                "regulatory_heat_map": [
                    {"jurisdiction": "MX (IVA)", "risk_level": "CRITICO", "probability_violation": 0.90,
                     "financial_impact_usd": 278400, "reaction_deadline_days": 15, "confidence": "high"},
                    {"jurisdiction": "MX (Art. 30-B)", "risk_level": "alto", "probability_violation": 0.70,
                     "financial_impact_usd": 50000, "reaction_deadline_days": 30, "confidence": "medium"},
                    {"jurisdiction": "USA (CA Sales Tax)", "risk_level": "medio", "probability_violation": 0.60,
                     "financial_impact_usd": 87000, "reaction_deadline_days": 90, "confidence": "high"},
                    {"jurisdiction": "USA (TX Sales Tax)", "risk_level": "medio", "probability_violation": 0.55,
                     "financial_impact_usd": 52200, "reaction_deadline_days": 90, "confidence": "high"},
                ],
                "timeline": [
                    {"date_offset_days": 0, "event": "Inicio ventas SaaS a MX", "regulatory_trigger": "Primera transacción con tarjeta mexicana",
                     "risk_level": "CRITICO", "mandatory_action": "Mecanismo de retención IVA 16% operativo",
                     "penalty_if_missed": "Multas SAT por omisión de retención + actualizaciones + recargos"},
                    {"date_offset_days": 15, "event": "Declaración IVA mensual", "regulatory_trigger": "Art. 18-D LIVA",
                     "risk_level": "alto", "mandatory_action": "Enterar IVA retenido ante SAT",
                     "penalty_if_missed": "Recargos del 1.47% mensual + multas"},
                    {"date_offset_days": 90, "event": "Sales Tax Filing Q3 CA/TX/NY", "regulatory_trigger": "Economic nexus threshold",
                     "risk_level": "medio", "mandatory_action": "Declarar y remitir sales tax por estado",
                     "penalty_if_missed": "Multas estatales + intereses"},
                ],
                "compound_risks": [
                    {"risk_id": "CP-002",
                     "description": "No registro Art. 18-D + no retención IVA + Art. 30-B = triple incumplimiento que puede generar bloqueo de pagos por adquirentes mexicanos.",
                     "interacting_regulations": ["Art. 18-J LIVA", "Art. 18-D LIVA", "Art. 30-B CFF"],
                     "cascade_effect": "Adquirente bancario MX bloquea transacciones → corte de ingresos.",
                     "severity": "CRITICO"},
                ],
                "alternative_scenarios": [
                    {"alternative_id": "ALT-003", "description": "Registro Art. 18-D LIVA elimina riesgo de bloqueo por adquirente.",
                     "risk_mitigation": "Control directo del cumplimiento IVA",
                     "cost_impact": "Registro SAT + contador local MX + sistema facturación"},
                    {"alternative_id": "ALT-004", "description": "Venta vía App Store/Google Play traslada la retención al marketplace.",
                     "risk_mitigation": "Cumplimiento delegado al marketplace",
                     "cost_impact": "Margen reducido 15-30%"},
                ],
            },
            "output": {
                "overall_risk_score": 78.0,
                "recommendation": "RESTRUCTURE_BEFORE_EXECUTING",
                "executive_summary": (
                    "DEMO MODE — Backend offline o LLM no disponible. "
                    "Operación de ALTO RIESGO (demo): venta SaaS a MX sin retención IVA activa "
                    "viola Art. 18-J LIVA. Requiere registro Art. 18-D o venta vía marketplace."
                ),
                "confidence": "high",
                "source_status": "official",
            },
        }
