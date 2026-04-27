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
    POST /api/auto-scan        Auto-detect bias in uploaded CSV
    POST /api/upload-model     Upload a trained model file
    POST /api/audit-model      Audit uploaded model for bias
    POST /api/audit-endpoint   Audit external API endpoint for bias
"""

######## edit 1 start
# from full_audit_endpoint import router as full_audit_router
# app.include_router(full_audit_router)

######### edit 1 end


import io
import os
import uuid
import threading
from datetime import datetime
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from bias_engine import BiasEngine, MitigationEngine
from dataset_loader import DatasetLoader
from report_generator import ReportGenerator
from auto_scan import AutoBiasScanner
from model_auditor import ModelFileAuditor, APIEndpointAuditor
from tasks import run_audit_async

from full_audit_endpoint import router as full_audit_router

app = FastAPI(
    title="FairSight API",
    description="AI Bias Detection & Fairness Auditing Platform",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)


app.include_router(full_audit_router, prefix="/api")
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
scanner = AutoBiasScanner()
model_auditor = ModelFileAuditor()
api_auditor = APIEndpointAuditor()

# ── Store for uploaded model files ───────────────────────────────
uploaded_models: dict[str, dict] = {}
uploaded_scan_data: dict[str, bytes] = {}


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


class AutoScanRequest(BaseModel):
    dataset_id: str
    target_column: Optional[str] = None
    prediction_column: Optional[str] = None


class AuditModelRequest(BaseModel):
    model_id: str
    dataset_id: str
    target_column: Optional[str] = None


class AuditEndpointRequest(BaseModel):
    endpoint_url: str
    dataset_id: str
    target_column: Optional[str] = None
    response_key: str = "prediction"
    request_format: str = "json_rows"
    headers: Optional[dict[str, str]] = None


# ── Health ─────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "service": "fairsight-api",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "bias_audit",
            "auto_scan",
            "model_audit",
            "endpoint_audit",
            "mitigation",
            "gemini_reports",
        ],
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
    # Also store for auto-scan
    uploaded_scan_data[dataset_id] = content

    # Auto-detect columns for the response
    try:
        df = pd.read_csv(io.BytesIO(content))
        col_info = {
            "columns": df.columns.tolist(),
            "rows": len(df),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "sample": df.head(3).to_dict(orient="records"),
        }
    except Exception:
        col_info = {}

    return {
        "dataset_id": dataset_id,
        "filename": file.filename,
        "column_info": col_info,
    }


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


# ── Synchronous audit (single request-response) ───────────────
@app.post("/api/audit-sync")
def audit_sync(req: AuditRequest):
    """Run a bias audit synchronously and return results immediately."""
    if not loader.dataset_exists(req.dataset_id):
        raise HTTPException(404, f"Dataset '{req.dataset_id}' not found")

    try:
        data, sens_col, tgt_col, pred_col = loader.get_dataset(
            req.dataset_id,
            req.sensitive_attributes[0] if req.sensitive_attributes else "race",
        )

        engine = BiasEngine(data, sens_col, tgt_col, pred_col)
        result = engine.run_full_audit()
        result["dataset_id"] = req.dataset_id
        result["sensitive_attrs"] = req.sensitive_attributes

        # Store as a job so report generation still works
        job_id = str(uuid.uuid4())
        jobs[job_id] = {
            "status": "complete",
            "progress": 100,
            "dataset_id": req.dataset_id,
            "result": result,
            "created_at": datetime.utcnow().isoformat(),
            "audit_type": "manual",
        }
        result["job_id"] = job_id

        return result
    except Exception as e:
        raise HTTPException(500, f"Audit failed: {e}")


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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  NEW FEATURE: Auto-Scan — Automatic Bias Detection
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.post("/api/auto-scan")
async def auto_scan_csv(file: UploadFile = File(...)):
    """
    Upload a CSV file and automatically detect bias across ALL columns.

    No need to specify sensitive attributes, target, or prediction columns.
    The engine auto-detects everything and returns a comprehensive bias report.
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(400, "Only CSV files are accepted")

    content = await file.read()

    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(400, f"Could not parse CSV: {e}")

    if len(df) < 2:
        raise HTTPException(400, "CSV must have at least 2 data rows")

    # Store for future use (e.g., model audit)
    dataset_id = f"scan_{uuid.uuid4().hex[:8]}"
    uploaded_scan_data[dataset_id] = content
    loader.store_upload(dataset_id, content, file.filename)

    # Run auto-scan
    result = scanner.scan(df)
    result["dataset_id"] = dataset_id
    result["filename"] = file.filename
    result["dataset_info"] = {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": df.columns.tolist(),
    }

    # Store as a job for report generation
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "complete",
        "progress": 100,
        "dataset_id": dataset_id,
        "result": result,
        "created_at": datetime.utcnow().isoformat(),
        "audit_type": "auto_scan",
    }
    result["job_id"] = job_id

    return result


@app.post("/api/auto-scan-dataset")
def auto_scan_existing(req: AutoScanRequest):
    """
    Run auto-scan on an already-uploaded or built-in dataset.
    """
    if not loader.dataset_exists(req.dataset_id):
        raise HTTPException(404, f"Dataset '{req.dataset_id}' not found")

    try:
        df, _, tgt, pred = loader.get_dataset(req.dataset_id)
    except Exception as e:
        raise HTTPException(500, f"Failed to load dataset: {e}")

    result = scanner.scan(
        df,
        target_col=req.target_column or tgt,
        prediction_col=req.prediction_column or pred,
    )
    result["dataset_id"] = req.dataset_id

    # Store as job
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "complete",
        "progress": 100,
        "dataset_id": req.dataset_id,
        "result": result,
        "created_at": datetime.utcnow().isoformat(),
        "audit_type": "auto_scan",
    }
    result["job_id"] = job_id

    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  NEW FEATURE: Model Bias Audit
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.post("/api/upload-model")
async def upload_model(file: UploadFile = File(...)):
    """Upload a trained model file (.pkl or .joblib)."""
    if not file.filename:
        raise HTTPException(400, "Filename is required")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("pkl", "joblib", "pickle"):
        raise HTTPException(
            400,
            "Supported formats: .pkl, .joblib, .pickle"
        )

    content = await file.read()
    model_id = f"model_{uuid.uuid4().hex[:8]}"
    uploaded_models[model_id] = {
        "content": content,
        "filename": file.filename,
        "uploaded_at": datetime.utcnow().isoformat(),
    }

    return {
        "model_id": model_id,
        "filename": file.filename,
        "size_bytes": len(content),
    }


@app.post("/api/audit-model")
async def audit_model(
    model_file: UploadFile = File(...),
    test_data_file: UploadFile = File(...),
    target_column: Optional[str] = Form(None),
):
    """
    Upload a model file AND test dataset simultaneously.
    Runs predictions through the model and auto-scans for bias.
    """
    # Validate model file
    if not model_file.filename:
        raise HTTPException(400, "Model filename is required")

    ext = model_file.filename.rsplit(".", 1)[-1].lower() if "." in model_file.filename else ""
    if ext not in ("pkl", "joblib", "pickle"):
        raise HTTPException(400, "Supported model formats: .pkl, .joblib, .pickle")

    # Validate test data
    if not test_data_file.filename or not test_data_file.filename.endswith(".csv"):
        raise HTTPException(400, "Test data must be a CSV file")

    model_bytes = await model_file.read()
    test_bytes = await test_data_file.read()

    try:
        test_df = pd.read_csv(io.BytesIO(test_bytes))
    except Exception as e:
        raise HTTPException(400, f"Could not parse test CSV: {e}")

    if len(test_df) < 10:
        raise HTTPException(400, "Test dataset must have at least 10 rows")

    # Run model audit
    result = model_auditor.audit(
        model_bytes=model_bytes,
        model_filename=model_file.filename,
        test_data=test_df,
        target_col=target_column,
    )

    # Store as job
    job_id = str(uuid.uuid4())
    dataset_id = f"model_test_{uuid.uuid4().hex[:8]}"
    jobs[job_id] = {
        "status": "complete",
        "progress": 100,
        "dataset_id": dataset_id,
        "result": result,
        "created_at": datetime.utcnow().isoformat(),
        "audit_type": "model_file",
    }
    result["job_id"] = job_id

    return result


@app.post("/api/audit-endpoint")
async def audit_endpoint(req: AuditEndpointRequest):
    """
    Audit an external model API endpoint for bias.

    Sends test data to the endpoint, collects predictions,
    and runs auto-scan on the results.
    """
    if not loader.dataset_exists(req.dataset_id):
        raise HTTPException(404, f"Dataset '{req.dataset_id}' not found")

    try:
        df, _, tgt, _ = loader.get_dataset(req.dataset_id)
    except Exception as e:
        raise HTTPException(500, f"Failed to load dataset: {e}")

    # Limit to 200 rows for API probing
    if len(df) > 200:
        df = df.sample(200, random_state=42)

    result = await api_auditor.audit(
        endpoint_url=req.endpoint_url,
        test_data=df,
        target_col=req.target_column or tgt,
        response_key=req.response_key,
        request_format=req.request_format,
        headers=req.headers,
    )

    # Store as job
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "complete",
        "progress": 100,
        "dataset_id": req.dataset_id,
        "result": result,
        "created_at": datetime.utcnow().isoformat(),
        "audit_type": "api_endpoint",
    }
    result["job_id"] = job_id

    return result


# ── Entry point ────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
