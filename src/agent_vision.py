"""
ATLAS Agent 1: Vision Analyzer
Gemini 2.5 Flash (Vertex AI) para extracción multimodal de PDFs.
Fallback automático al parser determinista si Vertex no está disponible.
"""
import re
import json
import logging
import time
import hashlib
from datetime import datetime

from src.schemas import VisionOutput, ExtractedField

logger = logging.getLogger(__name__)

_VISION_MODEL = "gemini-2.5-flash"

_SYSTEM = (
    "Eres un Auditor Forense Senior especializado en documentos financieros. "
    "Extraes campos con precisión absoluta y detectas anomalías sutiles que "
    "pasarían inadvertidas para un revisor humano."
)

_PROMPT = """Analiza este documento financiero en detalle.

RESPONDE ÚNICAMENTE CON JSON válido (sin markdown, sin backticks, sin texto extra):
{
  "document_type": "invoice|contract|unknown",
  "confidence": 0.95,
  "extracted_fields": {
    "nombre_campo": {"value": "valor_extraido", "confidence": 0.9}
  },
  "detected_issues": ["descripción de anomalía o inconsistencia"]
}

Campos a extraer (todos los que encuentres en el documento):
invoice_number, date, due_date, vendor, buyer, total_amount, subtotal,
tax, currency, payment_terms, description, quantity, unit_price,
po_number, rfc_emisor, rfc_receptor, bank_account, swift, iban,
contract_number, parties, effective_date, expiry_date

En detected_issues reporta CUALQUIER anomalía visible:
- Montos que no cuadran matemáticamente
- Fechas incoherentes, imposibles o inconsistentes
- Campos obligatorios ausentes para el tipo de documento
- Texto alterado, sobreescrito, borrado o ilegible
- Discrepancias entre campos relacionados (ej. total ≠ subtotal + tax)
- Firmas o sellos ausentes o sospechosos"""


class VisionAnalyzerAgent:
    def __init__(self):
        self.model_name = _VISION_MODEL

    async def analyze_document(self, pdf_path: str) -> VisionOutput:
        start_time = time.time()
        logger.info(f"Vision Agent (Gemini 2.5 Flash): {pdf_path}")

        with open(pdf_path, "rb") as f:
            raw_bytes = f.read()
        doc_id = hashlib.sha256(raw_bytes).hexdigest()

        # raw_text via pdfplumber — necesario para el Compliance Router (regex)
        from src.pdf_reader import extract_text
        raw_text = extract_text(pdf_path)

        try:
            return await _gemini_extraction(pdf_path, doc_id, raw_text, start_time)
        except Exception as e:
            logger.warning(f"Gemini Vision falló, usando OCR determinista: {e}")
            return await _deterministic_fallback(pdf_path, doc_id, raw_text, start_time)


async def _gemini_extraction(
    pdf_path: str, doc_id: str, raw_text: str, start_time: float
) -> VisionOutput:
    from src.vertex_client import call_gemini

    response_text = call_gemini(
        prompt=_PROMPT,
        model=_VISION_MODEL,
        pdf_path=pdf_path,
        system=_SYSTEM,
        temperature=0.1,
    )

    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", response_text).strip()
    start = cleaned.find("{")
    end   = cleaned.rfind("}") + 1
    data  = json.loads(cleaned[start:end])

    raw_fields = data.get("extracted_fields", {})
    extracted_fields = {
        k: ExtractedField(
            value=v.get("value"),
            confidence=float(v.get("confidence", 0.8)),
        )
        for k, v in raw_fields.items()
    }

    doc_type = data.get("document_type", "unknown")
    if doc_type not in ("invoice", "contract", "unknown"):
        doc_type = "unknown"

    return VisionOutput(
        document_id=doc_id,
        document_type=doc_type,
        pdf_path=pdf_path,
        extracted_fields=extracted_fields,
        detected_issues=data.get("detected_issues", []),
        confidence=float(data.get("confidence", 0.85)),
        model_used=_VISION_MODEL,
        processing_time_ms=int((time.time() - start_time) * 1000),
        timestamp=datetime.now(),
        raw_text=raw_text,
    )


async def _deterministic_fallback(
    pdf_path: str, doc_id: str, raw_text: str, start_time: float
) -> VisionOutput:
    from src.pdf_reader import analyze_pdf

    doc_type, fields, issues, confidence = analyze_pdf(pdf_path)
    extracted_fields = {
        k: ExtractedField(value=v["value"], confidence=v["confidence"])
        for k, v in fields.items()
    }

    return VisionOutput(
        document_id=doc_id,
        document_type=doc_type,
        pdf_path=pdf_path,
        extracted_fields=extracted_fields,
        detected_issues=issues,
        confidence=confidence,
        model_used="ATLAS-Deterministic-OCR-v2-fallback",
        processing_time_ms=int((time.time() - start_time) * 1000),
        timestamp=datetime.now(),
        raw_text=raw_text,
    )
