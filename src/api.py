"""
ATLAS FastAPI
Endpoints: /analyze, /upload, /result/{id}, /audits, /stats, /human_decision
"""
import logging
import tempfile
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from src.orchestrator import run_pipeline
from src.schemas import PipelineResult
from src.supabase_client import get_client

load_dotenv()
logger = logging.getLogger(__name__)

app = FastAPI(title="ATLAS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request models ─────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    pdf_path: str

class HumanDecisionRequest(BaseModel):
    document_id: str
    decision: str  # APPROVE | REJECT | REQUEST_MORE_INFO


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.post("/analyze", response_model=PipelineResult)
async def analyze_document(req: AnalyzeRequest):
    """Analiza un PDF por path del servidor."""
    return await run_pipeline(req.pdf_path)


@app.post("/upload", response_model=PipelineResult)
async def upload_document(file: UploadFile = File(...)):
    """Acepta un PDF como multipart/form-data, lo procesa y retorna el resultado."""
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF.")

    tmp_dir = Path(tempfile.gettempdir()) / "atlas_uploads"
    tmp_dir.mkdir(exist_ok=True)
    tmp_path = tmp_dir / (file.filename or "upload.pdf")

    content = await file.read()
    tmp_path.write_bytes(content)

    return await run_pipeline(str(tmp_path))


@app.get("/result/{document_id}")
async def get_result(document_id: str):
    """Retorna el resultado completo de una auditoría por doc_id."""
    try:
        sb = get_client()
        resp = (
            sb.table("audit_results")
            .select("*")
            .eq("doc_id", document_id)
            .limit(1)
            .execute()
        )
        if not resp.data:
            raise HTTPException(status_code=404, detail=f"Resultado no encontrado: {document_id}")
        row = resp.data[0]
        return {
            "document_id": row["doc_id"],
            "status": row["final_status"],
            "result_json": row.get("result_json"),
            "human_decision": row.get("human_decision"),
            "created_at": row["created_at"],
            "updated_at": row.get("created_at"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching result {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/audits")
async def list_audits(limit: int = 20):
    """Lista las últimas N auditorías con campos resumidos."""
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
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """Estadísticas agregadas del dashboard. Nunca lanza excepción — retorna ceros si falla."""
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


@app.post("/human_decision")
async def human_decision(req: HumanDecisionRequest):
    """Registra la decisión humana final sobre un documento auditado."""
    valid = ("APPROVE", "REJECT", "REQUEST_MORE_INFO")
    if req.decision not in valid:
        raise HTTPException(status_code=400, detail=f"decision debe ser uno de {valid}")
    try:
        sb = get_client()
        sb.table("audit_results").update(
            {"human_decision": req.decision}
        ).eq("doc_id", req.document_id).execute()
    except Exception as e:
        logger.warning(f"Supabase update human_decision failed: {e}")

    return {
        "status": "updated",
        "document_id": req.document_id,
        "decision": req.decision,
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
