"""
ATLAS FastAPI
Endpoints: /analyze, /upload, /result/{id}, /audits, /stats, /human_decision
"""
import logging
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from dotenv import load_dotenv

from src.orchestrator import run_pipeline
from src.schemas import PipelineResult
from src.supabase_client import get_client

load_dotenv()
logger = logging.getLogger(__name__)

# ── Configuración de seguridad ─────────────────────────────────────────────────

_API_KEY = os.getenv("ATLAS_API_KEY", "")
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Directorio raíz permitido para /analyze (solo archivos dentro de aquí)
_ALLOWED_ANALYZE_DIR = Path(os.getenv("ATLAS_DOCS_DIR", "test_documents")).resolve()

# Límite de tamaño para uploads: 20 MB
_MAX_UPLOAD_BYTES = 20 * 1024 * 1024

# Origins permitidos (ajustar en producción)
_ALLOWED_ORIGINS = os.getenv(
    "ATLAS_CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173"
).split(",")


def _require_api_key(key: str = Depends(_api_key_header)):
    """Valida X-API-Key si ATLAS_API_KEY está configurada en .env."""
    if not _API_KEY:
        return  # Sin key configurada — modo dev, sin auth (solo para localhost)
    if key != _API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida o ausente.")


def _safe_path(raw_path: str) -> Path:
    """
    Resuelve la ruta y verifica que esté dentro del directorio permitido.
    Mitiga path traversal (../../etc/passwd, etc.).
    """
    try:
        resolved = Path(raw_path).resolve()
    except Exception:
        raise HTTPException(status_code=400, detail="Ruta de archivo inválida.")

    if not resolved.is_relative_to(_ALLOWED_ANALYZE_DIR):
        raise HTTPException(
            status_code=400,
            detail=f"Ruta fuera del directorio permitido. Solo se permiten archivos en: {_ALLOWED_ANALYZE_DIR}"
        )
    if not resolved.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")
    if resolved.suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF.")
    return resolved


def _safe_filename(filename: str) -> str:
    """Sanitiza el nombre de archivo para evitar path traversal via filename."""
    name = Path(filename).name  # Elimina cualquier componente de directorio
    name = re.sub(r"[^\w\-.]", "_", name)  # Solo alfanumérico, guión, punto
    if not name.lower().endswith(".pdf"):
        name = name + ".pdf"
    return name[:100]  # Truncar para evitar nombres muy largos


def _validate_pdf_magic(content: bytes) -> bool:
    """Verifica que el contenido comience con el magic byte de PDF (%PDF-)."""
    return content[:5] == b"%PDF-"


# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(title="ATLAS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=False,  # False cuando origins incluye wildcard o son múltiples
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Key", "Content-Type"],
)


# ── Request models ─────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    pdf_path: str

class HumanDecisionRequest(BaseModel):
    document_id: str
    decision: str


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.post("/analyze", response_model=PipelineResult, dependencies=[Depends(_require_api_key)])
async def analyze_document(req: AnalyzeRequest):
    """
    Analiza un PDF por path del servidor.
    El path debe estar dentro del directorio ATLAS_DOCS_DIR (.env).
    """
    safe = _safe_path(req.pdf_path)
    return await run_pipeline(str(safe))


@app.post("/upload", response_model=PipelineResult, dependencies=[Depends(_require_api_key)])
async def upload_document(file: UploadFile = File(...)):
    """Acepta un PDF como multipart/form-data, lo procesa y retorna el resultado."""
    # 1. Validar extensión del filename
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF.")

    # 2. Leer contenido con límite de tamaño
    content = await file.read(_MAX_UPLOAD_BYTES + 1)
    if len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Archivo demasiado grande. Máximo permitido: {_MAX_UPLOAD_BYTES // 1024 // 1024} MB."
        )

    # 3. Validar magic bytes (contenido real de PDF)
    if not _validate_pdf_magic(content):
        raise HTTPException(status_code=400, detail="El archivo no es un PDF válido.")

    # 4. Sanitizar filename antes de escribir al disco
    safe_name = _safe_filename(file.filename or "upload.pdf")
    tmp_dir = Path(tempfile.gettempdir()) / "atlas_uploads"
    tmp_dir.mkdir(exist_ok=True)
    tmp_path = tmp_dir / safe_name

    tmp_path.write_bytes(content)

    try:
        return await run_pipeline(str(tmp_path))
    finally:
        # Eliminar el archivo temporal después de procesar
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass


@app.get("/result/{document_id}", dependencies=[Depends(_require_api_key)])
async def get_result(document_id: str):
    """Retorna el resultado de una auditoría por doc_id."""
    # Validar que document_id sea un hash SHA256 válido (64 hex chars)
    if not re.fullmatch(r"[a-f0-9]{64}", document_id):
        raise HTTPException(status_code=400, detail="document_id inválido.")
    try:
        sb = get_client()
        resp = (
            sb.table("audit_results")
            .select("doc_id, final_status, result_json, human_decision, created_at, fraud_classification, severity")
            .eq("doc_id", document_id)
            .limit(1)
            .execute()
        )
        if not resp.data:
            raise HTTPException(status_code=404, detail="Resultado no encontrado.")
        row = resp.data[0]
        return {
            "document_id": row["doc_id"],
            "status": row["final_status"],
            "fraud_classification": row.get("fraud_classification"),
            "severity": row.get("severity"),
            "result_json": row.get("result_json"),
            "human_decision": row.get("human_decision"),
            "created_at": row["created_at"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching result {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Error interno al obtener el resultado.")


@app.get("/audits", dependencies=[Depends(_require_api_key)])
async def list_audits(limit: int = Query(default=20, ge=1, le=100)):
    """Lista las últimas N auditorías (máximo 100)."""
    try:
        sb = get_client()
        resp = (
            sb.table("audit_results")
            .select(
                "doc_id, fraud_type, fraud_classification, severity, "
                "confidence_score, final_status, recommended_action, "
                "is_duplicate, is_blacklisted, created_at"
            )
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return {"audits": resp.data, "total": len(resp.data)}
    except Exception as e:
        logger.error(f"Error listing audits: {e}")
        raise HTTPException(status_code=500, detail="Error interno al listar auditorías.")


@app.get("/stats")
async def get_stats():
    """Estadísticas agregadas del dashboard. Endpoint público (solo lectura agregada)."""
    try:
        sb = get_client()

        total_resp = sb.table("audit_results").select("id", count="exact").execute()
        total = total_resp.count or 0

        fraud_resp = (
            sb.table("audit_results")
            .select("id", count="exact")
            .neq("fraud_classification", "LIMPIO")
            .execute()
        )
        fraud_count = fraud_resp.count or 0

        rows_resp = sb.table("audit_results").select("confidence_score, processing_time_ms").execute()
        rows = rows_resp.data or []

        scores = [r["confidence_score"] for r in rows if r.get("confidence_score") is not None]
        avg_confidence = round(sum(scores) / len(scores) * 100, 1) if scores else 0.0

        times = [r["processing_time_ms"] for r in rows if r.get("processing_time_ms") is not None]
        avg_time = round(sum(times) / len(times)) if times else 0

        dist_resp = sb.table("audit_results").select("fraud_classification").execute()
        dist: dict[str, int] = {}
        for r in dist_resp.data or []:
            key = r.get("fraud_classification") or "UNKNOWN"
            dist[key] = dist.get(key, 0) + 1

        return {
            "total_audits": total,
            "fraud_detected": fraud_count,
            "avg_confidence_pct": avg_confidence,
            "avg_processing_time_ms": avg_time,
            "distribution": dist,
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {
            "total_audits": 0,
            "fraud_detected": 0,
            "avg_confidence_pct": 0.0,
            "avg_processing_time_ms": 0,
            "distribution": {},
        }


@app.post("/human_decision", dependencies=[Depends(_require_api_key)])
async def human_decision(req: HumanDecisionRequest):
    """Registra la decisión humana final sobre un documento auditado."""
    valid = ("APPROVE", "REJECT", "REQUEST_MORE_INFO")
    if req.decision not in valid:
        raise HTTPException(status_code=400, detail=f"decision debe ser uno de {valid}")
    # Validar que document_id tenga formato SHA256
    if not re.fullmatch(r"[a-f0-9]{64}", req.document_id):
        raise HTTPException(status_code=400, detail="document_id inválido.")
    try:
        sb = get_client()
        sb.table("audit_results").update(
            {"human_decision": req.decision}
        ).eq("doc_id", req.document_id).execute()
    except Exception as e:
        logger.error(f"Error registrando human_decision: {e}")
        raise HTTPException(status_code=500, detail="Error al registrar la decisión.")

    return {
        "status": "updated",
        "document_id": req.document_id,
        "decision": req.decision,
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
