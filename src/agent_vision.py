"""
ATLAS Agent 1: Vision Analyzer (Deterministic Wrapper)
Extrae campos clave de documentos financieros usando pdf_reader.
"""
import logging
import time
from datetime import datetime
from src.pdf_reader import analyze_pdf
from src.schemas import VisionOutput, ExtractedField

logger = logging.getLogger(__name__)

class VisionAnalyzerAgent:
    def __init__(self):
        self.model_name = "ATLAS-Deterministic-OCR-v2"

    async def analyze_document(self, pdf_path: str) -> VisionOutput:
        """
        Extrae texto y campos clave del PDF de forma determinista.
        """
        start_time = time.time()
        logger.info(f"Analizando documento con OCR determinista: {pdf_path}")
        
        doc_type, fields, issues, confidence = analyze_pdf(pdf_path)
        
        # Mapeo a ExtractedField schemas
        extracted_fields = {
            k: ExtractedField(value=v["value"], confidence=v["confidence"])
            for k, v in fields.items()
        }
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # document_id es el SHA256 del path en esta versión (o contenido)
        import hashlib
        with open(pdf_path, "rb") as f:
            doc_id = hashlib.sha256(f.read()).hexdigest()

        # Obtener raw_text para el Compliance Router
        from src.pdf_reader import extract_text
        raw_text = extract_text(pdf_path)

        return VisionOutput(
            document_id=doc_id,
            document_type=doc_type,
            pdf_path=pdf_path,
            extracted_fields=extracted_fields,
            detected_issues=issues,
            confidence=confidence,
            model_used=self.model_name,
            processing_time_ms=processing_time_ms,
            timestamp=datetime.now(),
            raw_text=raw_text
        )
