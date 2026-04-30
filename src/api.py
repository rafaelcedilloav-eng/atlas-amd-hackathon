"""
ATLAS FastAPI v2.0
Endpoints: /analyze, /upload, /result/{id}, /audits, /stats, /human_decision
Nuevos: /stream/{audit_id} (SSE), /compliance/{document_id}
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
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from src.orchestrator import run_pipeline
from src.schemas import PipelineResult
from src.supabase_client import get_client, reset_client
from src.audit_emitter import event_bus

load_dotenv()
logger = logging.getLogger(__name__)

# ── Configuración de seguridad ─────────────────────────────────────────────────

_API_KEY = os.getenv("ATLAS_API_KEY", "")
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

_ALLOWED_ANALYZE_DIR = Path(os.getenv("ATLAS_DOCS_DIR", "test_documents")).resolve()
_MAX_UPLOAD_BYTES = 20 * 1024 * 1024

_ALLOWED_ORIGINS = os.getenv(
    "ATLAS_CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,https://atlas-amd-qs5g4.ondigitalocean.app"
).split(",")

def _require_api_key(key: str = Depends(_api_key_header)):
    if not _API_KEY:
        return
    if key != _API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida o ausente.")

def _safe_path(raw_path: str) -> Path:
    try:
        resolved = Path(raw_path).resolve()
    except Exception:
        raise HTTPException(status_code=400, detail="Ruta de archivo inválida.")
    if not resolved.is_relative_to(_ALLOWED_ANALYZE_DIR):
        raise HTTPException(
            status_code=400,
            detail=f"Ruta fuera del directorio permitido."
        )
    if not resolved.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")
    if resolved.suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF.")
    return resolved

def _safe_filename(filename: str) -> str:
    name = Path(filename).name
    name = re.sub(r"[^\w\-.]", "_", name)
    if not name.lower().endswith(".pdf"):
        name = name + ".pdf"
    return name[:100]

def _validate_pdf_magic(content: bytes) -> bool:
    return content[:5] == b"%PDF-"

# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(title="ATLAS API v2.0", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Key", "Content-Type"],
)

# ── Request models ─────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    pdf_path: str

class HumanDecisionRequest(BaseModel):
    document_id: str
    decision: str

# ── Endpoints existentes ───────────────────────────────────────────────────────

@app.post("/analyze", response_model=PipelineResult, dependencies=[Depends(_require_api_key)])
async def analyze_document(req: AnalyzeRequest):
    safe = _safe_path(req.pdf_path)
    return await run_pipeline(str(safe))

@app.post("/upload", response_model=PipelineResult, dependencies=[Depends(_require_api_key)])
async def upload_document(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF.")
    content = await file.read(_MAX_UPLOAD_BYTES + 1)
    if len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Archivo demasiado grande.")
    if not _validate_pdf_magic(content):
        raise HTTPException(status_code=400, detail="El archivo no es un PDF válido.")
    
    safe_name = _safe_filename(file.filename or "upload.pdf")
    tmp_dir = Path(tempfile.gettempdir()) / "atlas_uploads"
    tmp_dir.mkdir(exist_ok=True)
    tmp_path = tmp_dir / safe_name
    tmp_path.write_bytes(content)
    
    try:
        return await run_pipeline(str(tmp_path))
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass

@app.get("/result/{document_id}", dependencies=[Depends(_require_api_key)])
async def get_result(document_id: str):
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

@app.get("/audit-list", dependencies=[Depends(_require_api_key)])
async def list_audits(limit: int = Query(default=20, ge=1, le=100)):
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
    try:
        sb = get_client()
        total_resp = sb.table("audit_results").select("id", count="exact").execute()
        total = total_resp.count or 0
        fraud_resp = sb.table("audit_results").select("id", count="exact").neq("fraud_classification", "LIMPIO").execute()
        fraud_count = fraud_resp.count or 0
        rows_resp = sb.table("audit_results").select("confidence_score, processing_time_ms").execute()
        rows = rows_resp.data or []
        scores = [r["confidence_score"] for r in rows if r.get("confidence_score") is not None]
        avg_confidence = round(sum(scores) / len(scores) * 100, 1) if scores else 0.0
        times = [r["processing_time_ms"] for r in rows if r.get("processing_time_ms") is not None]
        avg_time = round(sum(times) / len(times)) if times else 0
        dist_resp = sb.table("audit_results").select("fraud_classification").execute()
        dist = {}
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
        reset_client()
        return {"total_audits": 0, "fraud_detected": 0, "avg_confidence_pct": 0.0, "avg_processing_time_ms": 0, "distribution": {}}

@app.post("/human_decision", dependencies=[Depends(_require_api_key)])
async def human_decision(req: HumanDecisionRequest):
    valid = ("APPROVE", "REJECT", "REQUEST_MORE_INFO")
    if req.decision not in valid:
        raise HTTPException(status_code=400, detail=f"decision debe ser uno de {valid}")
    try:
        sb = get_client()
        sb.table("audit_results").update({"human_decision": req.decision}).eq("doc_id", req.document_id).execute()
    except Exception as e:
        logger.error(f"Error registrando human_decision: {e}")
        raise HTTPException(status_code=500, detail="Error al registrar la decisión.")
    return {"status": "updated", "document_id": req.document_id, "decision": req.decision, "timestamp": datetime.now().isoformat()}

# ── NUEVOS ENDPOINTS v2.0 ─────────────────────────────────────────────────────

@app.get("/stream/{audit_id}")
async def stream_audit_events(audit_id: str):
    """
    Server-Sent Events (SSE) para el X-Ray Panel.
    Emite logs en tiempo real del pipeline de auditoría.
    """
    async def event_generator():
        async for event in event_bus.get_events(audit_id):
            yield f"data: {event}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

@app.get("/compliance/{document_id}", dependencies=[Depends(_require_api_key)])
async def get_compliance_result(document_id: str):
    """
    Retorna el resultado del compliance check para un documento.
    """
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
            raise HTTPException(status_code=404, detail="Resultado no encontrado.")
        
        result_json = resp.data[0].get("result_json", {})
        compliance_data = result_json.get("compliance", {})
        
        return {
            "document_id": document_id,
            "country_detected": compliance_data.get("country_detected", "UNKNOWN"),
            "country_confidence": compliance_data.get("country_confidence", 0),
            "compliance_score": compliance_data.get("compliance_score", 0),
            "findings_count": len(compliance_data.get("findings", [])),
            "findings": compliance_data.get("findings", []),
            "cross_border_flags": compliance_data.get("cross_border_flags", []),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching compliance {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Error interno al obtener compliance.")

@app.get("/stream/history/{audit_id}")
async def get_audit_history(audit_id: str):
    """Retorna el historial completo de eventos de una auditoría."""
    history = event_bus.get_history(audit_id)
    return {"audit_id": audit_id, "events": history, "total": len(history)}

@app.get("/market-intelligence/{company_name}")
async def get_market_intelligence(company_name: str):
    """
    Retorna datos de inteligencia de mercado para una empresa específica.
    """
    # En producción esto vendría de una tabla 'market_intelligence' en Supabase
    # Aquí simulamos la respuesta para el demo del hackathon
    from src.schemas import MarketData
    
    # Mock data mapper
    demo_companies = {
        "nexus": [
            MarketData(country_code="MX", participation_pct=35.5, status="Established", influence_score=8, audits_completed=128, alerts_forenses=23, risk_level="medium"),
            MarketData(country_code="US", participation_pct=28.0, status="Established", influence_score=9, audits_completed=245, alerts_forenses=18, risk_level="low"),
            MarketData(country_code="CN", participation_pct=15.0, status="Expanding", influence_score=7, audits_completed=89, alerts_forenses=45, risk_level="high"),
        ],
        "aerotech": [
            MarketData(country_code="US", participation_pct=45.0, status="Established", influence_score=10, audits_completed=312, alerts_forenses=8, risk_level="low"),
            MarketData(country_code="DE", participation_pct=20.0, status="Established", influence_score=8, audits_completed=96, alerts_forenses=11, risk_level="low"),
        ]
    }
    
    key = company_name.lower().split()[0]
    data = demo_companies.get(key, demo_companies["nexus"])
    return {"company": company_name, "market_footprint": data}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
