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
from fastapi.responses import StreamingResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from dotenv import load_dotenv

from src.orchestrator import run_pipeline
from src.schemas import PipelineResult
from src.supabase_client import get_client, reset_client
from src.audit_emitter import event_bus

load_dotenv()
logger = logging.getLogger(__name__)

# ── Security configuration ────────────────────────────────────────────────────

_API_KEY = os.getenv("ATLAS_API_KEY", "")
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Root directory allowed for /analyze (only files inside this path)
_ALLOWED_ANALYZE_DIR = Path(os.getenv("ATLAS_DOCS_DIR", "test_documents")).resolve()

# Upload size limit: 20 MB
_MAX_UPLOAD_BYTES = 20 * 1024 * 1024

# Allowed CORS origins (adjust for production)
_ALLOWED_ORIGINS = os.getenv(
    "ATLAS_CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173"
).split(",")


def _require_api_key(key: str = Depends(_api_key_header)):
    """Validates X-API-Key if ATLAS_API_KEY is configured in .env."""
    if not _API_KEY:
        return  # No key configured — dev mode, no auth (localhost only)
    if key != _API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")


def _safe_path(raw_path: str) -> Path:
    """
    Resolves the path and verifies it is within the allowed directory.
    Mitigates path traversal attacks (../../etc/passwd, etc.).
    """
    try:
        resolved = Path(raw_path).resolve()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid file path.")

    if not resolved.is_relative_to(_ALLOWED_ANALYZE_DIR):
        raise HTTPException(
            status_code=400,
            detail=f"Path outside allowed directory. Only files in: {_ALLOWED_ANALYZE_DIR} are permitted."
        )
    if not resolved.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    if resolved.suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files accepted.")
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
    # 1. Validate file extension
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files accepted.")

    # 2. Read content with size limit
    content = await file.read(_MAX_UPLOAD_BYTES + 1)
    if len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed: {_MAX_UPLOAD_BYTES // 1024 // 1024} MB."
        )

    # 3. Validate PDF magic bytes
    if not _validate_pdf_magic(content):
        raise HTTPException(status_code=400, detail="Not a valid PDF file.")

    # 4. Sanitize filename before writing to disk
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
    """Returns the audit result for a given doc_id."""
    # Validar que document_id sea un hash SHA256 válido (64 hex chars)
    if not re.fullmatch(r"[a-f0-9]{64}", document_id):
        raise HTTPException(status_code=400, detail="Invalid document_id.")
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
            raise HTTPException(status_code=404, detail="Result not found.")
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
        raise HTTPException(status_code=500, detail="Error fetching result.")


@app.get("/audit-list", dependencies=[Depends(_require_api_key)])
async def list_audits(
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=100),
    severity: str | None = Query(default=None),
):
    """Lists the last N audits (max 100). Supports full-text search and severity filter."""
    try:
        sb = get_client()
        # Pull a larger pool when searching so client-side filter can find enough results
        fetch_limit = 300 if search else limit

        query = (
            sb.table("audit_results")
            .select(
                "doc_id, fraud_type, fraud_classification, severity, "
                "confidence_score, final_status, recommended_action, "
                "is_duplicate, is_blacklisted, created_at, result_json"
            )
            .order("created_at", desc=True)
            .limit(fetch_limit)
        )

        if severity:
            sev = severity.upper()
            if sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE"):
                query = query.eq("severity", sev)

        resp = query.execute()

        processed = []
        for row in resp.data:
            # Extract vendor_name safely from nested JSONB
            vendor_name: str | None = None
            try:
                rj = row.get("result_json") or {}
                ef = (rj.get("vision") or {}).get("extracted_fields") or {}
                vn = ef.get("vendor_name") or {}
                vendor_name = str(vn["value"]) if isinstance(vn, dict) and vn.get("value") else None
            except Exception:
                pass

            record = {k: v for k, v in row.items() if k != "result_json"}
            record["vendor_name"] = vendor_name

            if search:
                needle = search.strip().lower()
                haystack = " ".join(
                    s for s in (
                        vendor_name or "",
                        record.get("fraud_type") or "",
                        record.get("fraud_classification") or "",
                        record.get("doc_id") or "",
                    )
                    if s
                ).lower()
                if needle not in haystack:
                    continue

            processed.append(record)
            if len(processed) >= limit:
                break

        return {"audits": processed, "total": len(processed)}
    except Exception as e:
        logger.error(f"Error listing audits: {e}")
        raise HTTPException(status_code=500, detail="Error listing audits.")


@app.get("/stats")
async def get_stats():
    """Aggregated dashboard statistics. Public endpoint (read-only aggregates)."""
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
        reset_client()  # fuerza nueva conexión en el próximo request
        return {
            "total_audits": 0,
            "fraud_detected": 0,
            "avg_confidence_pct": 0.0,
            "avg_processing_time_ms": 0,
            "distribution": {},
        }


@app.post("/human_decision", dependencies=[Depends(_require_api_key)])
async def human_decision(req: HumanDecisionRequest):
    """Records the final human decision for an audited document."""
    valid = ("APPROVE", "REJECT", "REQUEST_MORE_INFO")
    if req.decision not in valid:
        raise HTTPException(status_code=400, detail=f"decision must be one of {valid}")
    if not re.fullmatch(r"[a-f0-9]{64}", req.document_id):
        raise HTTPException(status_code=400, detail="Invalid document_id.")
    try:
        sb = get_client()
        sb.table("audit_results").update(
            {"human_decision": req.decision}
        ).eq("doc_id", req.document_id).execute()
    except Exception as e:
        logger.error(f"Error saving human_decision: {e}")
        raise HTTPException(status_code=500, detail="Error saving decision.")

    return {
        "status": "updated",
        "document_id": req.document_id,
        "decision": req.decision,
        "timestamp": datetime.now().isoformat(),
    }


# ── X-Ray SSE endpoints ───────────────────────────────────────────────────────

@app.get("/stream/{audit_id}")
async def stream_audit_events(audit_id: str):
    """
    Server-Sent Events for the X-Ray Panel.
    Replays history if pipeline is done; streams live if still running.
    No API key required (read-only event stream).
    """
    if not re.fullmatch(r"[a-f0-9]{64}", audit_id):
        raise HTTPException(status_code=400, detail="Invalid audit_id.")

    async def generator():
        async for chunk in event_bus.get_events(audit_id):
            yield chunk

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/stream/history/{audit_id}")
async def get_audit_history(audit_id: str):
    """Returns the full event history for an audit (for reconnection / debugging)."""
    if not re.fullmatch(r"[a-f0-9]{64}", audit_id):
        raise HTTPException(status_code=400, detail="Invalid audit_id.")
    history = event_bus.get_history(audit_id)
    return {"audit_id": audit_id, "events": history, "total": len(history)}


@app.get("/compliance/{document_id}", dependencies=[Depends(_require_api_key)])
async def get_compliance_result(document_id: str):
    """Returns the compliance check result for a document (11-country analysis)."""
    if not re.fullmatch(r"[a-f0-9]{64}", document_id):
        raise HTTPException(status_code=400, detail="Invalid document_id.")
    try:
        sb = get_client()
        resp = (
            sb.table("audit_results")
            .select("result_json")
            .eq("doc_id", document_id)
            .limit(1)
            .execute()
        )
        if not resp.data:
            raise HTTPException(status_code=404, detail="Result not found.")
        result_json  = resp.data[0].get("result_json") or {}
        compliance   = result_json.get("compliance") or {}
        return {
            "document_id":       document_id,
            "country_detected":  compliance.get("country_detected", "UNKNOWN"),
            "country_confidence": compliance.get("country_confidence", 0),
            "compliance_score":  compliance.get("compliance_score", 0),
            "findings_count":    len(compliance.get("findings", [])),
            "findings":          compliance.get("findings", []),
            "cross_border_flags": compliance.get("cross_border_flags", []),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching compliance {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching compliance data.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
