"""
ATLAS Agent 1: Vision Analyzer (Robust Version)
Extrae texto de documentos usando una estrategia de 3 capas y estructura la información.
"""
import os
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.agent_vision_extractor import extract_document_robust
from src.vllm_client import call_llm
from src.schemas import VisionOutput, ExtractedField
from src.supabase_persistence import save_document, log_agent_action

logger = logging.getLogger(__name__)

class VisionAnalyzerAgent:
    def __init__(self):
        self.model_name = os.getenv("VLLM_MODEL", "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B")
        logger.info(f"VisionAnalyzerAgent inicializado con modelo: {self.model_name}")

    async def analyze_document(self, file_path: str) -> VisionOutput:
        """
        Proceso completo del Agente 1:
        1. Extracción robusta (OCR/PDF)
        2. Clasificación y extracción estructurada vía vLLM (DeepSeek-R1)
        3. Persistencia inicial en Supabase
        """
        start_time = time.time()
        logger.info(f"Iniciando análisis visual de: {file_path}")

        # 1. Extracción robusta
        extraction = extract_document_robust(file_path)
        if not extraction["extraction_success"]:
            logger.error(f"Fallo crítico en extracción de texto para {file_path}")
            return self._generate_error_output(file_path, "Error de extracción de texto")

        raw_text = extraction["raw_text"]
        structured_text = extraction["structured_text"]
        doc_hash = extraction["document_hash"]

        # 2. Extracción de datos vía LLM
        try:
            extraction_result = self._call_llm_for_extraction(structured_text)
            doc_type = extraction_result.get("document_type", "unknown")
            fields_raw = extraction_result.get("extracted_fields", {})
            issues = extraction_result.get("detected_issues", [])
            confidence = extraction_result.get("confidence", 0.5)
        except Exception as e:
            logger.error(f"Error llamando al LLM para extracción: {e}")
            return self._generate_error_output(file_path, f"Error de inferencia: {e}")

        # Mapeo a objetos ExtractedField
        extracted_fields = {
            k: ExtractedField(value=v.get("value"), confidence=v.get("confidence", 0.7))
            for k, v in fields_raw.items()
        }

        processing_time_ms = int((time.time() - start_time) * 1000)
        
        output = VisionOutput(
            document_id=doc_hash,
            document_type=doc_type,
            pdf_path=file_path,
            extracted_fields=extracted_fields,
            detected_issues=issues,
            confidence=confidence,
            model_used=self.model_name,
            processing_time_ms=processing_time_ms,
            timestamp=datetime.now()
        )

        # 3. Persistencia y Audit Trail
        self._persist_results(output, raw_text)

        return output

    def _call_llm_for_extraction(self, text: str) -> dict:
        """Llamada al LLM para convertir texto plano en JSON estructurado."""
        prompt = f"""Analiza el siguiente texto extraído de un documento financiero y extrae la información en formato JSON.

TEXTO DEL DOCUMENTO:
\"\"\"
{text[:8000]}
\"\"\"

Debes responder ÚNICAMENTE con un objeto JSON que siga esta estructura:
{{
  "document_type": "invoice" | "contract" | "unknown",
  "confidence": 0.0 a 1.0,
  "extracted_fields": {{
    "vendor_name": {{"value": "nombre", "confidence": 0.9}},
    "total_amount": {{"value": 1234.56, "confidence": 0.9}},
    "date": {{"value": "YYYY-MM-DD", "confidence": 0.9}},
    "currency": {{"value": "MXN", "confidence": 0.9}},
    "vendor_rfc": {{"value": "RFC", "confidence": 0.9}}
  }},
  "detected_issues": ["lista de problemas visuales detectados como texto borroso, campos faltantes, etc"]
}}

Reglas:
1. Si es factura, busca vendor_name, total_amount, date, rfc.
2. Si es contrato, busca partes, montos, vigencia.
3. Responde SOLO el JSON, sin explicaciones."""

        response = call_llm(prompt, system_prompt="Eres el Agente de Visión de ATLAS. Tu especialidad es el OCR inteligente y extracción de campos financieros.")
        
        # Limpieza de la respuesta por si el modelo incluye razonamiento (DeepSeek-R1)
        json_content = response
        if "</thought>" in response:
            json_content = response.split("</thought>")[-1].strip()
        
        # Intentar parsear JSON
        try:
            # Buscar el primer { y el último }
            start = json_content.find('{')
            end = json_content.rfind('}') + 1
            if start != -1 and end != 0:
                json_content = json_content[start:end]
            return json.loads(json_content)
        except Exception as e:
            logger.error(f"Error parseando JSON del LLM: {e}. Raw: {json_content[:200]}")
            raise

    @staticmethod
    def _safe_float(field: Optional[ExtractedField]) -> Optional[float]:
        """Convierte cualquier valor numérico de ExtractedField a float para Supabase."""
        if field is None or field.value is None:
            return None
        try:
            return float(str(field.value).replace(",", "").replace("$", "").strip())
        except (ValueError, TypeError):
            return None

    def _persist_results(self, output: VisionOutput, raw_text: str):
        """Guarda en Supabase."""
        try:
            fields = output.extracted_fields
            vendor_field = fields.get("vendor_name")
            # Mapeo a tabla 'documents'
            doc_data = {
                "doc_id": output.document_id,
                "filename": Path(output.pdf_path).name,
                "file_type": output.document_type,
                "vendor_name": str(vendor_field.value) if isinstance(vendor_field, ExtractedField) and vendor_field.value is not None else None,
                "total_amount": self._safe_float(fields.get("total_amount")),
                "raw_text": raw_text,
                "extracted_fields": {k: v.model_dump(mode="json") for k, v in output.extracted_fields.items()}
            }
            save_document(doc_data)
            
            # Audit Trail
            log_agent_action(
                doc_id=output.document_id,
                agent="vision",
                action="extract_and_structure",
                input_data={"pdf_path": output.pdf_path},
                output_data=output.model_dump(mode="json"),
                duration_ms=output.processing_time_ms,
                success=True
            )
        except Exception as e:
            logger.warning(f"Error persistiendo datos del Agente 1: {e}")

    def _generate_error_output(self, file_path: str, error_msg: str) -> VisionOutput:
        return VisionOutput(
            document_id=f"ERR-{int(time.time())}",
            document_type="unknown",
            pdf_path=file_path,
            extracted_fields={},
            detected_issues=[error_msg],
            confidence=0.0,
            model_used=self.model_name,
            processing_time_ms=0,
            timestamp=datetime.now()
        )
