# ATLAS — Master Prompt para Claude Code
## Sistema de Auditoría Forense con Pipeline de 4 Agentes + Supabase + AMD MI300X

---

## 🎯 MISIÓN

Eres el arquitecto e implementador del sistema **ATLAS** — un pipeline de auditoría forense de documentos financieros (facturas y contratos) que corre sobre una GPU AMD Instinct MI300X VF con vLLM.

Tu trabajo es:
1. Leer y entender **todo** el código existente en `D:\Proyectos\atlas-amd-hackathon\src` antes de modificar cualquier cosa
2. Diseñar e implementar el schema completo de Supabase
3. Reforzar el Agente 1 (Vision) con extracción robusta de documentos
4. Validar la integración y lógica de los 4 agentes
5. Conectar todo el pipeline al servidor vLLM en AMD
6. Verificar que el sistema completo funciona end-to-end

**No inventes nada. Lee primero, implementa después.**

---

## 🏗️ ARQUITECTURA DEL SISTEMA

### Pipeline Secuencial (los 4 agentes en orden)

```
[Documento PDF/Imagen]
        ↓
[Agente 1 — Vision]      → Extracción OCR + datos estructurados
        ↓
[Agente 2 — Reasoning]   → DeepSeek-R1 clasifica trampa + Chain-of-Thought
        ↓
[Agente 3 — Validator]   → Verificación matemática Decimal + Gate de Integridad
        ↓
[Agente 4 — Explainer]   → Reporte ejecutivo profesional en es-MX
        ↓
[Supabase]               → Persistencia de resultados + Audit Trail
```

### Infraestructura

| Componente | Valor |
|------------|-------|
| GPU Server IP | `165.245.141.216` |
| vLLM API | `http://165.245.141.216:8000/v1` |
| Modelo LLM | `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B` |
| Supabase URL | `https://fkjwaubqwvcereilllow.supabase.co` |
| Supabase API | `https://fkjwaubqwvcereilllow.supabase.co/rest/v1/` |
| Supabase Project | `atlas-hackathon` |
| Supabase Project ID | `fkjwaubqwvcereilllow` |

---

## PASO 0 — LEE EL PROYECTO COMPLETO PRIMERO

```
Lee todos los archivos en D:\Proyectos\atlas-amd-hackathon\src en este orden:
1. schemas.py          — contratos de datos Pydantic
2. agent_vision.py     — Agente 1 (Vision)
3. agent_reasoning.py  — Agente 2 (Reasoning)
4. agent_validator.py  — Agente 3 (Validator)
5. agent_explainer.py  — Agente 4 (Explainer)
6. orchestrator.py     — orquestador del pipeline (si existe)
7. requirements.txt    — dependencias actuales
8. .env o config.py    — configuración actual

Después de leer cada archivo, declara:
- Qué hace
- Qué inputs recibe y qué outputs produce
- Qué dependencias externas usa
- Qué problemas o fragilidades identificas

NO hagas ningún cambio hasta haber leído y analizado todos los archivos.
```

---

## PASO 1 — ANÁLISIS Y DIAGNÓSTICO

Después de leer el proyecto, produce este reporte antes de continuar:

```
### Diagnóstico ATLAS

**Estado actual del pipeline:**
- Agente 1 (Vision):    [FUNCIONAL / FRÁGIL / ROTO] — [razón]
- Agente 2 (Reasoning): [FUNCIONAL / FRÁGIL / ROTO] — [razón]
- Agente 3 (Validator): [FUNCIONAL / FRÁGIL / ROTO] — [razón]
- Agente 4 (Explainer): [FUNCIONAL / FRÁGIL / ROTO] — [razón]
- Orquestador:          [EXISTE / NO EXISTE]

**Schemas Pydantic detectados:** [lista de modelos]
**Dependencias actuales:** [lista de requirements.txt]
**Problemas críticos identificados:** [lista numerada]
**Archivos que necesitan modificación:** [lista]
**Archivos que NO se deben tocar:** [lista]
```

---

## PASO 2 — CONFIGURACIÓN DE VARIABLES DE ENTORNO

Crea o actualiza el archivo `.env` en la raíz del proyecto:

```bash
# .env
# AMD vLLM Server
VLLM_BASE_URL=http://165.245.141.216:8000/v1
VLLM_MODEL=deepseek-ai/DeepSeek-R1-Distill-Qwen-32B
VLLM_TIMEOUT=120
VLLM_MAX_TOKENS=4096
VLLM_TEMPERATURE=0.1

# Supabase
SUPABASE_URL=https://fkjwaubqwvcereilllow.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_-x4BgGcPYsaSmdWlYUhhwA_b-cVFC0c
SUPABASE_REST_API=https://fkjwaubqwvcereilllow.supabase.co/rest/v1/

# Pipeline Config
ATLAS_ENV=production
LOG_LEVEL=INFO
OCR_ENGINE=pymupdf
```

Crea también `.env.example` con los mismos campos pero sin valores reales.

---

## PASO 3 — DEPENDENCIAS

Actualiza `requirements.txt` asegurando que incluya:

```txt
# LLM Client
openai>=1.0.0

# Supabase
supabase>=2.0.0

# OCR y procesamiento de documentos
PyMuPDF>=1.23.0
pymupdf4llm>=0.0.5
pytesseract>=0.3.10
Pillow>=10.0.0
pdf2image>=1.16.3

# Validación y esquemas
pydantic>=2.0.0
python-dotenv>=1.0.0

# Matemática contable
# (Decimal está en stdlib — no requiere instalación)

# Utilidades
httpx>=0.25.0
python-multipart>=0.0.6
loguru>=0.7.0
```

Instala las dependencias del sistema operativo primero (requerido en el servidor Linux):
```bash
sudo apt-get update && sudo apt-get install -y tesseract-ocr poppler-utils
```

> **Por qué es obligatorio:** `pytesseract` es solo un wrapper de Python — el binario `tesseract` debe existir en el sistema para que funcione. `pdf2image` usa `pdftoppm` de `poppler-utils` para convertir páginas PDF a imágenes. Sin estos dos paquetes, el fallback OCR del Agente 1 fallará con `FileNotFoundError` o `TesseractNotFoundError` aunque `pip install` haya completado sin errores.

Luego instala las dependencias de Python:
```bash
pip install -r requirements.txt
```

---

## PASO 4 — SCHEMA DE SUPABASE

### 4.1 — Conéctate a Supabase y ejecuta el SQL completo

Ve al **SQL Editor** de Supabase en:
`https://supabase.com/dashboard/project/fkjwaubqwvcereilllow/sql`

Ejecuta este script completo:

```sql
-- ============================================================
-- ATLAS — Schema completo de Supabase
-- Compatible con schemas Pydantic del proyecto
-- ============================================================

-- Habilitar extensión para UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- TABLA 1: documents
-- Almacena metadatos de cada documento procesado
-- Compatible con: DocumentMetadata (Pydantic)
-- ============================================================
CREATE TABLE IF NOT EXISTS documents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doc_id          TEXT UNIQUE NOT NULL,   -- ID único del documento (hash o referencia)
    filename        TEXT NOT NULL,
    file_type       TEXT NOT NULL,          -- 'invoice' | 'contract'
    vendor_name     TEXT,
    vendor_rfc      TEXT,
    total_amount    NUMERIC(15, 2),
    currency        TEXT DEFAULT 'MXN',
    document_date   DATE,
    raw_text        TEXT,                   -- texto extraído por Vision
    extracted_fields JSONB,                 -- campos estructurados del Agente 1
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TABLA 2: audit_results
-- Almacena el resultado completo del pipeline por documento
-- Compatible con: AuditResult (Pydantic)
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_results (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id         UUID REFERENCES documents(id) ON DELETE CASCADE,
    doc_id              TEXT NOT NULL,

    -- Salida Agente 2 (Reasoning)
    fraud_type          TEXT,               -- tipo de fraude detectado
    fraud_classification TEXT,              -- 'FRAUDE_CONFIRMADO' | 'SOSPECHOSO' | 'LIMPIO'
    severity            TEXT,               -- 'CRÍTICO' | 'ALTO' | 'MEDIO' | 'BAJO'
    reasoning_chain     TEXT,               -- Chain-of-Thought de DeepSeek-R1
    confidence_score    NUMERIC(5, 4),      -- 0.0000 a 1.0000

    -- Salida Agente 3 (Validator)
    math_validation     BOOLEAN,            -- ¿pasa verificación matemática?
    math_discrepancy    NUMERIC(15, 2),     -- diferencia detectada
    is_duplicate        BOOLEAN DEFAULT FALSE,
    is_blacklisted      BOOLEAN DEFAULT FALSE,
    integrity_passed    BOOLEAN,            -- Gate de Integridad completo

    -- Salida Agente 4 (Explainer)
    final_status        TEXT NOT NULL,      -- 'APPROVE' | 'FLAG' | 'ESCALATE'
    executive_report    TEXT,               -- reporte en español profesional
    financial_impact    NUMERIC(15, 2),     -- impacto financiero calculado
    recommended_action  TEXT,               -- acción recomendada al auditor

    -- Metadata
    pipeline_version    TEXT DEFAULT '1.0.0',
    processing_time_ms  INTEGER,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TABLA 3: processed_doc_ids
-- Control de duplicados — Agente 3 consulta esta tabla
-- Compatible con: ProcessedDocument (Pydantic)
-- ============================================================
CREATE TABLE IF NOT EXISTS processed_doc_ids (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doc_id          TEXT UNIQUE NOT NULL,   -- ID del documento procesado
    document_hash   TEXT,                   -- hash del contenido para detección exacta
    filename        TEXT,
    vendor_name     TEXT,
    total_amount    NUMERIC(15, 2),
    processed_at    TIMESTAMPTZ DEFAULT NOW(),
    audit_result_id UUID REFERENCES audit_results(id)
);

-- ============================================================
-- TABLA 4: blacklist_vendors
-- Lista negra de proveedores fraudulentos
-- Compatible con: BlacklistVendor (Pydantic)
-- ============================================================
CREATE TABLE IF NOT EXISTS blacklist_vendors (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vendor_name     TEXT NOT NULL,
    vendor_rfc      TEXT,                   -- RFC del proveedor (MX)
    reason          TEXT NOT NULL,          -- razón de inclusión en blacklist
    severity        TEXT DEFAULT 'ALTO',    -- 'CRÍTICO' | 'ALTO' | 'MEDIO'
    reported_by     TEXT,                   -- quién lo reportó
    evidence_doc_id TEXT,                   -- documento que originó el registro
    is_active       BOOLEAN DEFAULT TRUE,
    added_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TABLA 5: audit_trail
-- Log inmutable de todas las acciones del pipeline
-- Para trazabilidad y auditoría humana
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_trail (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doc_id          TEXT NOT NULL,
    agent           TEXT NOT NULL,          -- 'vision' | 'reasoning' | 'validator' | 'explainer'
    action          TEXT NOT NULL,          -- descripción de la acción
    input_data      JSONB,                  -- input recibido por el agente
    output_data     JSONB,                  -- output producido por el agente
    duration_ms     INTEGER,
    success         BOOLEAN NOT NULL,
    error_message   TEXT,                   -- null si success=true
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- ÍNDICES para performance
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_documents_doc_id ON documents(doc_id);
CREATE INDEX IF NOT EXISTS idx_documents_vendor ON documents(vendor_name);
CREATE INDEX IF NOT EXISTS idx_audit_results_doc_id ON audit_results(doc_id);
CREATE INDEX IF NOT EXISTS idx_audit_results_status ON audit_results(final_status);
CREATE INDEX IF NOT EXISTS idx_processed_doc_ids_hash ON processed_doc_ids(document_hash);
CREATE INDEX IF NOT EXISTS idx_blacklist_vendors_rfc ON blacklist_vendors(vendor_rfc);
CREATE INDEX IF NOT EXISTS idx_blacklist_vendors_name ON blacklist_vendors(vendor_name);
CREATE INDEX IF NOT EXISTS idx_audit_trail_doc_id ON audit_trail(doc_id);
CREATE INDEX IF NOT EXISTS idx_audit_trail_agent ON audit_trail(agent);

-- ============================================================
-- ROW LEVEL SECURITY (básico — ajustar según auth requerida)
-- ============================================================
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE processed_doc_ids ENABLE ROW LEVEL SECURITY;
ALTER TABLE blacklist_vendors ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_trail ENABLE ROW LEVEL SECURITY;

-- Política permisiva para service role (backend)
CREATE POLICY "service_role_all" ON documents FOR ALL USING (true);
CREATE POLICY "service_role_all" ON audit_results FOR ALL USING (true);
CREATE POLICY "service_role_all" ON processed_doc_ids FOR ALL USING (true);
CREATE POLICY "service_role_all" ON blacklist_vendors FOR ALL USING (true);
CREATE POLICY "service_role_all" ON audit_trail FOR ALL USING (true);

-- ============================================================
-- DATOS INICIALES — Blacklist de ejemplo
-- ============================================================
INSERT INTO blacklist_vendors (vendor_name, vendor_rfc, reason, severity) VALUES
('Proveedora Fantasma SA de CV', 'PFA123456789', 'Empresa sin existencia fiscal verificable', 'CRÍTICO'),
('Servicios Duplicados MX', 'SDM987654321', 'Historial de double billing confirmado', 'ALTO')
ON CONFLICT DO NOTHING;

-- ============================================================
-- VERIFICACIÓN FINAL
-- ============================================================
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns 
     WHERE table_name = t.table_name 
     AND table_schema = 'public') as column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
AND table_name IN ('documents', 'audit_results', 'processed_doc_ids', 'blacklist_vendors', 'audit_trail')
ORDER BY table_name;
```

### 4.2 — Obtén el Service Role Key de Supabase

Ve a: `https://supabase.com/dashboard/project/fkjwaubqwvcereilllow/settings/api`

Copia el **service_role key** (no el anon key) y agrégalo al `.env`:
```bash
SUPABASE_SERVICE_KEY=<pega aquí el service_role key>
```

---

## PASO 5 — CLIENTE SUPABASE

Crea el archivo `src/supabase_client.py`:

```python
"""
Cliente Supabase centralizado para ATLAS.
Todos los agentes importan desde aquí — nunca instancian su propio cliente.
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_PUBLISHABLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError(
        "SUPABASE_URL y SUPABASE_SERVICE_KEY son requeridas. Verifica tu .env"
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
logger.info(f"Supabase client inicializado → {SUPABASE_URL}")


def get_client() -> Client:
    """Retorna el cliente Supabase singleton."""
    return supabase
```

---

## PASO 6 — REFUERZO DEL AGENTE 1 (VISION)

Lee `agent_vision.py` existente. Identifica el método `_read_document` o equivalente.

Refuerza la extracción con esta lógica robusta. **Preserva toda la lógica existente** — solo reemplaza el método de lectura del documento:

```python
"""
Módulo de extracción robusta de documentos para Agente 1 (Vision).
Reemplaza el método _read_document del agent_vision.py existente.

Estrategia de extracción en capas:
1. PyMuPDF (texto nativo) — más rápido y limpio
2. pymupdf4llm (markdown estructurado) — para PDFs con tablas
3. Tesseract OCR — fallback para documentos escaneados/imágenes
"""
import os
import hashlib
from pathlib import Path
from decimal import Decimal
from typing import Optional
from loguru import logger

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

try:
    import pytesseract
    from PIL import Image
    import pdf2image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("Tesseract no disponible. Fallback de OCR desactivado.")


def extract_document_robust(file_path: str) -> dict:
    """
    Extracción robusta de documentos en capas.
    Retorna dict compatible con los schemas Pydantic del proyecto.

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
            images = pdf2image.convert_from_path(file_path, dpi=300)
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
```

**Instrucción para Claude Code:** Integra estas funciones en el `agent_vision.py` existente. Reemplaza el método `_read_document` con una llamada a `extract_document_robust()`. Preserva toda la lógica de extracción de campos y llamada al modelo de visión.

---

## PASO 7 — CLIENTE vLLM

Crea `src/vllm_client.py` — cliente unificado que todos los agentes usan:

```python
"""
Cliente vLLM unificado para ATLAS.
Compatible con OpenAI API — apunta al servidor AMD MI300X.
"""
import os
from openai import OpenAI
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://165.245.141.216:8000/v1")
VLLM_MODEL    = os.getenv("VLLM_MODEL", "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B")
VLLM_TIMEOUT  = int(os.getenv("VLLM_TIMEOUT", "120"))

client = OpenAI(
    base_url=VLLM_BASE_URL,
    api_key="not-needed",  # vLLM no requiere API key
    timeout=VLLM_TIMEOUT
)

def call_llm(
    prompt: str,
    system_prompt: str = "Eres un auditor forense experto.",
    max_tokens: int = 4096,
    temperature: float = 0.1
) -> str:
    """
    Llamada unificada al LLM en AMD.
    Todos los agentes usan esta función — nunca llaman a OpenAI directamente.
    """
    try:
        response = client.chat.completions.create(
            model=VLLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        result = response.choices[0].message.content
        logger.debug(f"LLM response: {len(result)} chars")
        return result
    except Exception as e:
        logger.error(f"Error en llamada LLM: {e}")
        raise


def verify_connection() -> bool:
    """Verifica que el servidor vLLM está disponible."""
    try:
        models = client.models.list()
        available = [m.id for m in models.data]
        logger.info(f"vLLM conectado. Modelos disponibles: {available}")
        return VLLM_MODEL in available
    except Exception as e:
        logger.error(f"No se puede conectar a vLLM en {VLLM_BASE_URL}: {e}")
        return False
```

---

## PASO 8 — CAPA DE PERSISTENCIA SUPABASE

Crea `src/supabase_persistence.py`:

```python
"""
Capa de persistencia para ATLAS.
Centraliza todas las operaciones de lectura/escritura a Supabase.
"""
import hashlib
from datetime import datetime
from decimal import Decimal
from typing import Optional
from loguru import logger
from supabase_client import get_client


class AtlasPersistence:

    def __init__(self):
        self.db = get_client()

    # ─────────────────────────────────────────────
    # DOCUMENTOS
    # ─────────────────────────────────────────────

    def save_document(self, document_data: dict) -> str:
        """Guarda metadatos del documento. Retorna el UUID generado."""
        try:
            result = self.db.table("documents").insert(document_data).execute()
            doc_uuid = result.data[0]['id']
            logger.info(f"Documento guardado: {doc_uuid}")
            return doc_uuid
        except Exception as e:
            logger.error(f"Error guardando documento: {e}")
            raise

    # ─────────────────────────────────────────────
    # CONTROL DE DUPLICADOS (Agente 3)
    # ─────────────────────────────────────────────

    def is_duplicate(self, doc_id: str, document_hash: str) -> bool:
        """
        Verifica si el documento ya fue procesado.
        Usa doc_id Y hash para máxima precisión.
        """
        try:
            # Verificar por ID
            by_id = self.db.table("processed_doc_ids")\
                .select("id")\
                .eq("doc_id", doc_id)\
                .execute()
            if by_id.data:
                logger.warning(f"Duplicado detectado por doc_id: {doc_id}")
                return True

            # Verificar por hash de contenido
            by_hash = self.db.table("processed_doc_ids")\
                .select("id")\
                .eq("document_hash", document_hash)\
                .execute()
            if by_hash.data:
                logger.warning(f"Duplicado detectado por hash: {document_hash[:16]}...")
                return True

            return False
        except Exception as e:
            logger.error(f"Error verificando duplicado: {e}")
            return False  # fail-safe: no bloquear si hay error de DB

    def register_processed_doc(self, doc_data: dict) -> None:
        """Registra documento como procesado para futuras verificaciones."""
        try:
            self.db.table("processed_doc_ids").insert(doc_data).execute()
            logger.info(f"Documento registrado como procesado: {doc_data.get('doc_id')}")
        except Exception as e:
            logger.error(f"Error registrando documento procesado: {e}")

    # ─────────────────────────────────────────────
    # BLACKLIST (Agente 3)
    # ─────────────────────────────────────────────

    def is_blacklisted(self, vendor_name: str, vendor_rfc: Optional[str] = None) -> dict:
        """
        Verifica si el proveedor está en la lista negra.
        Retorna {'blacklisted': bool, 'reason': str, 'severity': str}
        """
        try:
            query = self.db.table("blacklist_vendors")\
                .select("*")\
                .eq("is_active", True)

            # Búsqueda por nombre (case-insensitive)
            by_name = query.ilike("vendor_name", f"%{vendor_name}%").execute()
            if by_name.data:
                entry = by_name.data[0]
                return {
                    'blacklisted': True,
                    'reason': entry['reason'],
                    'severity': entry['severity']
                }

            # Búsqueda por RFC si está disponible
            if vendor_rfc:
                by_rfc = self.db.table("blacklist_vendors")\
                    .select("*")\
                    .eq("is_active", True)\
                    .eq("vendor_rfc", vendor_rfc)\
                    .execute()
                if by_rfc.data:
                    entry = by_rfc.data[0]
                    return {
                        'blacklisted': True,
                        'reason': entry['reason'],
                        'severity': entry['severity']
                    }

            return {'blacklisted': False, 'reason': None, 'severity': None}
        except Exception as e:
            logger.error(f"Error consultando blacklist: {e}")
            return {'blacklisted': False, 'reason': None, 'severity': None}

    # ─────────────────────────────────────────────
    # RESULTADOS DE AUDITORÍA
    # ─────────────────────────────────────────────

    def save_audit_result(self, result_data: dict) -> str:
        """Guarda el resultado completo del pipeline."""
        try:
            result = self.db.table("audit_results").insert(result_data).execute()
            result_uuid = result.data[0]['id']
            logger.info(f"Resultado de auditoría guardado: {result_uuid} | Status: {result_data.get('final_status')}")
            return result_uuid
        except Exception as e:
            logger.error(f"Error guardando resultado de auditoría: {e}")
            raise

    # ─────────────────────────────────────────────
    # AUDIT TRAIL (trazabilidad por agente)
    # ─────────────────────────────────────────────

    def log_agent_action(
        self,
        doc_id: str,
        agent: str,
        action: str,
        input_data: dict,
        output_data: dict,
        duration_ms: int,
        success: bool,
        error_message: Optional[str] = None
    ) -> None:
        """Registra la acción de cada agente en el audit trail."""
        try:
            self.db.table("audit_trail").insert({
                "doc_id":        doc_id,
                "agent":         agent,
                "action":        action,
                "input_data":    input_data,
                "output_data":   output_data,
                "duration_ms":   duration_ms,
                "success":       success,
                "error_message": error_message
            }).execute()
        except Exception as e:
            logger.error(f"Error en audit trail: {e}")
            # No re-raise — el audit trail no debe romper el pipeline


# Singleton
persistence = AtlasPersistence()
```

---

## PASO 9 — VALIDACIÓN DE CONEXIONES

Crea `src/validate_connections.py` y ejecútalo:

```python
"""
Script de validación de todas las conexiones de ATLAS.
Ejecutar antes de correr el pipeline: python validate_connections.py
"""
import sys
from loguru import logger

def validate_all():
    results = {}

    # 1. vLLM / AMD
    logger.info("Validando conexión vLLM (AMD MI300X)...")
    try:
        from vllm_client import verify_connection
        results['vllm'] = verify_connection()
    except Exception as e:
        logger.error(f"vLLM: FALLO — {e}")
        results['vllm'] = False

    # 2. Supabase
    logger.info("Validando conexión Supabase...")
    try:
        from supabase_client import get_client
        db = get_client()
        test = db.table("blacklist_vendors").select("id").limit(1).execute()
        results['supabase'] = True
        logger.success(f"Supabase: OK — blacklist_vendors accesible")
    except Exception as e:
        logger.error(f"Supabase: FALLO — {e}")
        results['supabase'] = False

    # 3. Tablas de Supabase
    logger.info("Validando schema de Supabase...")
    required_tables = ['documents', 'audit_results', 'processed_doc_ids', 'blacklist_vendors', 'audit_trail']
    try:
        from supabase_client import get_client
        db = get_client()
        for table in required_tables:
            db.table(table).select("id").limit(1).execute()
            logger.success(f"  ✅ Tabla '{table}' accesible")
        results['schema'] = True
    except Exception as e:
        logger.error(f"Schema: FALLO — {e}")
        results['schema'] = False

    # 4. OCR / Extracción
    logger.info("Validando motores de extracción...")
    try:
        import fitz
        logger.success("  ✅ PyMuPDF disponible")
        results['ocr'] = True
    except ImportError:
        logger.warning("  ⚠️ PyMuPDF no disponible")
        results['ocr'] = False

    # Reporte final
    print("\n" + "="*50)
    print("ATLAS — REPORTE DE VALIDACIÓN")
    print("="*50)
    all_ok = True
    for component, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {component.upper()}: {'OK' if status else 'FALLO'}")
        if not status:
            all_ok = False

    print("="*50)
    if all_ok:
        print("🚀 ATLAS listo para procesar documentos")
    else:
        print("⚠️  Resuelve los fallos antes de ejecutar el pipeline")
        sys.exit(1)

if __name__ == "__main__":
    validate_all()
```

Ejecútalo:
```bash
cd D:\Proyectos\atlas-amd-hackathon\src
python validate_connections.py
```

---

## PASO 10 — INTEGRACIÓN DE SUPABASE EN LOS AGENTES

**Instrucción para Claude Code:**

Lee cada agente existente y agrega la integración con Supabase siguiendo estas reglas:

### Agente 1 (Vision) — agregar al final del procesamiento:
```python
from supabase_persistence import persistence
from agent_vision_extractor import extract_document_robust

# Después de extraer el documento:
doc_extraction = extract_document_robust(file_path)
# Guardar en Supabase
persistence.save_document({
    "doc_id": doc_id,
    "filename": filename,
    "file_type": file_type,
    "raw_text": doc_extraction['raw_text'],
    "extracted_fields": extracted_fields_dict
})
persistence.log_agent_action(doc_id, "vision", "extract_document", {}, doc_extraction, duration_ms, True)
```

### Agente 3 (Validator) — agregar verificaciones de integridad:
```python
from supabase_persistence import persistence

# Gate 1: Verificar duplicado
is_dup = persistence.is_duplicate(doc_id, document_hash)

# Gate 2: Verificar blacklist
blacklist_result = persistence.is_blacklisted(vendor_name, vendor_rfc)

# Si pasa ambos gates, registrar como procesado
if not is_dup and not blacklist_result['blacklisted']:
    persistence.register_processed_doc({
        "doc_id": doc_id,
        "document_hash": document_hash,
        "filename": filename,
        "vendor_name": vendor_name,
        "total_amount": float(total_amount)
    })
```

### Agente 4 (Explainer) — guardar resultado final:
```python
from supabase_persistence import persistence

# Al final del pipeline — guardar resultado completo
persistence.save_audit_result({
    "doc_id": doc_id,
    "fraud_classification": fraud_classification,
    "severity": severity,
    "reasoning_chain": reasoning_chain,
    "math_validation": math_ok,
    "is_duplicate": is_duplicate,
    "is_blacklisted": is_blacklisted,
    "integrity_passed": integrity_passed,
    "final_status": final_status,  # 'APPROVE' | 'FLAG' | 'ESCALATE'
    "executive_report": executive_report,
    "financial_impact": float(financial_impact),
    "recommended_action": recommended_action,
    "processing_time_ms": total_time_ms
})
```

---

## PASO 11 — VERIFICACIÓN END-TO-END

Crea `src/test_pipeline.py`:

```python
"""
Test end-to-end del pipeline ATLAS.
Usa un documento de prueba para verificar los 4 agentes + Supabase.
"""
import time
from loguru import logger

def test_full_pipeline():
    logger.info("="*60)
    logger.info("ATLAS — TEST END-TO-END")
    logger.info("="*60)

    # 1. Verificar conexiones
    logger.info("\n[1/5] Verificando conexiones...")
    from vllm_client import verify_connection
    assert verify_connection(), "vLLM no disponible"
    logger.success("vLLM: OK")

    from supabase_client import get_client
    db = get_client()
    db.table("blacklist_vendors").select("id").limit(1).execute()
    logger.success("Supabase: OK")

    # 2. Crear documento de prueba sintético
    logger.info("\n[2/5] Preparando documento de prueba...")
    test_doc = {
        "doc_id": f"TEST-{int(time.time())}",
        "filename": "test_invoice.pdf",
        "file_type": "invoice",
        "vendor_name": "Proveedor Test SA de CV",
        "vendor_rfc": "PTS123456789",
        "total_amount": 150000.00,
        "raw_text": """
        FACTURA ELECTRÓNICA
        Proveedor: Proveedor Test SA de CV
        RFC: PTS123456789
        Fecha: 2026-04-26
        Concepto: Servicios de consultoría
        Subtotal: 129,310.34
        IVA 16%: 20,689.66
        Total: 150,000.00 MXN
        """
    }
    logger.success(f"Documento de prueba: {test_doc['doc_id']}")

    # 3. Ejecutar pipeline completo
    logger.info("\n[3/5] Ejecutando pipeline de 4 agentes...")
    # Aquí Claude Code debe importar el orquestador existente
    # y ejecutar el pipeline con el documento de prueba
    # Ejemplo:
    # from orchestrator import run_pipeline
    # result = run_pipeline(test_doc)

    # 4. Verificar persistencia en Supabase
    logger.info("\n[4/5] Verificando persistencia en Supabase...")
    docs = db.table("documents")\
        .select("*")\
        .eq("doc_id", test_doc['doc_id'])\
        .execute()

    if docs.data:
        logger.success(f"Documento persistido en Supabase: {docs.data[0]['id']}")
    else:
        logger.warning("Documento no encontrado en Supabase — verificar integración")

    # 5. Verificar audit trail
    logger.info("\n[5/5] Verificando audit trail...")
    trail = db.table("audit_trail")\
        .select("agent, action, success")\
        .eq("doc_id", test_doc['doc_id'])\
        .execute()

    for entry in trail.data:
        icon = "✅" if entry['success'] else "❌"
        logger.info(f"  {icon} [{entry['agent']}] {entry['action']}")

    logger.info("\n" + "="*60)
    logger.success("TEST COMPLETADO — Revisa los resultados arriba")
    logger.info("="*60)

if __name__ == "__main__":
    test_full_pipeline()
```

Ejecútalo:
```bash
python test_pipeline.py
```

---

## PASO 12 — CHECKLIST FINAL

Antes de declarar ATLAS como production-ready, verifica:

```
□ .env creado con todas las variables
□ requirements.txt actualizado e instalado
□ SQL ejecutado en Supabase — 5 tablas creadas
□ python validate_connections.py → todos en ✅
□ agent_vision.py usa extract_document_robust()
□ Agente 3 consulta is_duplicate() e is_blacklisted() antes de procesar
□ Agente 4 llama save_audit_result() al finalizar
□ audit_trail registra cada agente
□ python test_pipeline.py → sin errores críticos
□ curl http://165.245.141.216:8000/v1/models → DeepSeek visible
```

---

## 🚨 REGLAS PARA CLAUDE CODE

1. **Lee antes de modificar** — nunca sobreescribas lógica existente sin entenderla primero
2. **Preserva los schemas Pydantic** — son el contrato del sistema, no los cambies
3. **Un archivo nuevo por responsabilidad** — no metas todo en un solo archivo
4. **Si algo falla, logea con contexto** — usa `logger.error(f"Contexto: {variable} — Error: {e}")`
5. **El pipeline no debe romperse por un error de DB** — el audit_trail falla silencioso, el resto propaga
6. **Reporta qué encontraste en el código existente** antes de hacer cualquier cambio

---

*Generado el 26 de Abril 2026 — ATLAS v1.0 — AMD MI300X + DeepSeek-R1-Distill-Qwen-32B + Supabase*
