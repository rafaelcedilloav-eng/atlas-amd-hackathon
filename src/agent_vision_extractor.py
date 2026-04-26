"""
Módulo de extracción robusta de documentos para Agente 1 (Vision).
Estrategia de extracción en capas:
1. PyMuPDF (texto nativo) — más rápido y limpio
2. pymupdf4llm (markdown estructurado) — para PDFs con tablas
3. Tesseract OCR — fallback para documentos escaneados/imágenes
"""
import os
import hashlib
from pathlib import Path
from typing import Optional
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Rutas de binarios configurables desde .env (crítico en Windows)
_TESSERACT_CMD = os.getenv("TESSERACT_CMD")   # ej: C:\Program Files\Tesseract-OCR\tesseract.exe
_POPPLER_PATH  = os.getenv("POPPLER_PATH")    # ej: C:\poppler-24.08.0\Library\bin

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logger.warning("PyMuPDF no disponible. Instala: pip install PyMuPDF")

try:
    import pymupdf4llm
    PYMUPDF4LLM_AVAILABLE = True
except ImportError:
    PYMUPDF4LLM_AVAILABLE = False
    logger.warning("pymupdf4llm no disponible. Instala: pip install pymupdf4llm")

try:
    import pytesseract
    from PIL import Image
    import pdf2image
    if _TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = _TESSERACT_CMD
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("Tesseract o pdf2image no disponible. Fallback de OCR desactivado.")


def extract_document_robust(file_path: str) -> dict:
    """
    Extracción robusta de documentos en capas.
    
    Args:
        file_path: Ruta al PDF o imagen

    Returns:
        {
            'raw_text': str,           # texto extraído completo
            'structured_text': str,    # texto con formato markdown
            'document_hash': str,      # SHA256 del archivo
            'page_count': int,
            'extraction_method': str,  # qué método funcionó
            'extraction_success': bool
        }
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Documento no encontrado: {file_path}")

    # Hash del documento para detección de duplicados (Agente 3)
    document_hash = _compute_hash(file_path)

    result = {
        'raw_text': '',
        'structured_text': '',
        'document_hash': document_hash,
        'page_count': 0,
        'extraction_method': 'none',
        'extraction_success': False
    }

    suffix = path.suffix.lower()

    try:
        if suffix == '.pdf':
            result = _extract_pdf(file_path, result)
        elif suffix in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            result = _extract_image(file_path, result)
        else:
            raise ValueError(f"Formato no soportado: {suffix}. Usa PDF o imagen.")

        if not result['raw_text'].strip():
            logger.error(f"Extracción fallida para {path.name} — texto vacío")
            result['extraction_success'] = False
        else:
            logger.info(
                f"✅ Extracción exitosa: {path.name} | "
                f"Método: {result['extraction_method']} | "
                f"Chars: {len(result['raw_text'])} | "
                f"Páginas: {result['page_count']}"
            )
            result['extraction_success'] = True
    except Exception as e:
        logger.error(f"Error crítico en extracción de {path.name}: {e}")
        result['extraction_success'] = False

    return result


def _extract_pdf(file_path: str, result: dict) -> dict:
    """Extracción PDF en capas: pymupdf4llm → PyMuPDF nativo → Tesseract."""

    # Capa 1: pymupdf4llm — mejor para PDFs con tablas financieras
    if PYMUPDF4LLM_AVAILABLE:
        try:
            md_text = pymupdf4llm.to_markdown(file_path)
            if md_text and len(md_text.strip()) > 50:
                result['structured_text'] = md_text
                result['raw_text'] = md_text
                result['extraction_method'] = 'pymupdf4llm'
                # Contar páginas
                if PYMUPDF_AVAILABLE:
                    with fitz.open(file_path) as doc:
                        result['page_count'] = len(doc)
                return result
        except Exception as e:
            logger.warning(f"pymupdf4llm falló: {e} — intentando PyMuPDF nativo")

    # Capa 2: PyMuPDF nativo
    if PYMUPDF_AVAILABLE:
        try:
            with fitz.open(file_path) as doc:
                result['page_count'] = len(doc)
                pages_text = []
                for page_num, page in enumerate(doc):
                    text = page.get_text("text")
                    if text.strip():
                        pages_text.append(f"--- Página {page_num + 1} ---\n{text}")
                full_text = "\n".join(pages_text)
                if full_text.strip() and len(full_text.strip()) > 50:
                    result['raw_text'] = full_text
                    result['structured_text'] = full_text
                    result['extraction_method'] = 'pymupdf_native'
                    return result
        except Exception as e:
            logger.warning(f"PyMuPDF nativo falló: {e} — intentando Tesseract OCR")

    # Capa 3: Tesseract OCR — para PDFs escaneados
    if TESSERACT_AVAILABLE:
        try:
            # Note: poppler must be installed for this to work
            images = pdf2image.convert_from_path(
                file_path, dpi=300,
                poppler_path=_POPPLER_PATH or None,
            )
            result['page_count'] = len(images)
            pages_text = []
            for i, img in enumerate(images):
                text = pytesseract.image_to_string(img, lang='spa+eng')
                if text.strip():
                    pages_text.append(f"--- Página {i + 1} ---\n{text}")
            full_text = "\n".join(pages_text)
            result['raw_text'] = full_text
            result['structured_text'] = full_text
            result['extraction_method'] = 'tesseract_ocr'
            return result
        except Exception as e:
            logger.error(f"Tesseract OCR falló: {e}")

    return result


def _extract_image(file_path: str, result: dict) -> dict:
    """Extracción de imágenes via Tesseract."""
    result['page_count'] = 1

    if TESSERACT_AVAILABLE:
        try:
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img, lang='spa+eng')
            result['raw_text'] = text
            result['structured_text'] = text
            result['extraction_method'] = 'tesseract_image'
            return result
        except Exception as e:
            logger.error(f"Error extrayendo imagen: {e}")
    else:
        logger.error("Tesseract no disponible para procesar imagen")

    return result


def _compute_hash(file_path: str) -> str:
    """SHA256 del archivo — usado por Agente 3 para detección de duplicados exactos."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()
