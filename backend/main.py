"""
FairSight API — FastAPI backend for AI bias detection and fairness auditing.

Endpoints:
    GET  /api/health           Health check
    GET  /api/datasets         List available demo datasets
    POST /api/upload           Upload custom CSV dataset
    POST /api/audit            Start a bias audit (async)
    GET  /api/audit/{id}/status   Poll audit job status
    GET  /api/audit/{id}/result   Retrieve completed audit results
    POST /api/mitigate         Apply mitigation strategies
    GET  /api/strategies       List available mitigation strategies
    POST /api/report           Generate Gemini AI report
    GET  /api/reports/{id}     Retrieve a stored report
"""

import os
import uuid
import threading
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from bias_engine import BiasEngine, MitigationEngine
from dataset_loader import DatasetLoader
from report_generator import ReportGenerator
from tasks import run_audit_async

app = FastAPI(
    title="FairSight API",
    description="AI Bias Detection & Fairness Auditing Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── CORS ────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory job store (swap for Firestore/Redis in production) ─
jobs: dict = {}
loader = DatasetLoader()
report_gen = ReportGenerator()


# ── Request / Response models ──────────────────────────────────
class AuditRequest(BaseModel):
    dataset_id: str
    sensitive_attributes: list[str]
    target_column: str
    prediction_column: Optional[str] = None


class MitigateRequest(BaseModel):
    audit_id: str
    strategies: list[str]


class ReportRequest(BaseModel):
    audit_id: str


# ── Health ─────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "service": "fairsight-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ── Datasets ───────────────────────────────────────────────────
@app.get("/api/datasets")
def list_datasets():
    return {"datasets": loader.list_datasets()}


# ── Upload CSV ─────────────────────────────────────────────────
@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(400, "Only CSV files are accepted")
    content = await file.read()
    dataset_id = f"custom_{uuid.uuid4().hex[:8]}"
    loader.store_upload(dataset_id, content, file.filename)
    return {"dataset_id": dataset_id, "filename": file.filename}


# ── Start audit ────────────────────────────────────────────────
@app.post("/api/audit", status_code=202)
def start_audit(req: AuditRequest):
    if not loader.dataset_exists(req.dataset_id):
        raise HTTPException(404, f"Dataset '{req.dataset_id}' not found")

    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "dataset_id": req.dataset_id,
        "sensitive_attrs": req.sensitive_attributes,
        "target_column": req.target_column,
        "prediction_column": req.prediction_column,
        "result": None,
        "created_at": datetime.utcnow().isoformat(),
    }

    # Run in background thread (swap for Cloud Tasks in production)
    threading.Thread(
        target=run_audit_async,
        args=(job_id, jobs, loader, req),
        daemon=True,
    ).start()

    return {"job_id": job_id, "status": "queued"}


# ── Poll status ────────────────────────────────────────────────
@app.get("/api/audit/{job_id}/status")
def audit_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    j = jobs[job_id]
    return {"status": j["status"], "progress": j["progress"]}


# ── Get result ─────────────────────────────────────────────────
@app.get("/api/audit/{job_id}/result")
def audit_result(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    j = jobs[job_id]
    if j["status"] != "complete":
        raise HTTPException(409, "Audit not yet complete")
    return j["result"]


# ── Mitigation ─────────────────────────────────────────────────
@app.post("/api/mitigate")
def mitigate(req: MitigateRequest):
    if req.audit_id not in jobs:
        raise HTTPException(404, "Audit not found")
    j = jobs[req.audit_id]
    if j["status"] != "complete" or not j["result"]:
        raise HTTPException(409, "Audit not complete")

    engine = MitigationEngine()
    projection = engine.project(j["result"], req.strategies)
    return {"strategies": req.strategies, "projected": projection}


# ── Available strategies ───────────────────────────────────────
@app.get("/api/strategies")
def list_strategies():
    return {
        "strategies": [
            {"id": "reweight", "name": "Data Reweighting", "type": "pre-processing"},
            {"id": "resample", "name": "SMOTE Resampling", "type": "pre-processing"},
            {"id": "threshold", "name": "Threshold Calibration", "type": "post-processing"},
            {"id": "adversarial", "name": "Adversarial Debiasing", "type": "in-processing"},
            {"id": "fairloss", "name": "Fairness Loss Constraint", "type": "in-processing"},
        ]
    }


# ── Report generation ─────────────────────────────────────────
@app.post("/api/report")
def generate_report(req: ReportRequest):
    if req.audit_id not in jobs:
        raise HTTPException(404, "Audit not found")
    j = jobs[req.audit_id]
    if j["status"] != "complete" or not j["result"]:
        raise HTTPException(409, "Audit not complete")

    content = report_gen.generate(j["result"])
    return {"audit_id": req.audit_id, "content": content}


# ── Entry point ────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
