"""
Tasks — Async audit job execution.

Runs bias engine computation in a background thread.
In production, swap threading for Cloud Tasks / Celery.
"""

import time
from typing import Any
from bias_engine import BiasEngine


def run_audit_async(
    job_id: str,
    jobs: dict[str, Any],
    loader: Any,
    request: Any,
) -> None:
    """Execute a bias audit asynchronously and update the job store."""
    try:
        jobs[job_id]["status"] = "running"
        jobs[job_id]["progress"] = 10

        # Load dataset
        data, sens_col, tgt_col, pred_col = loader.get_dataset(
            request.dataset_id,
            request.sensitive_attributes[0] if request.sensitive_attributes else "race",
        )
        jobs[job_id]["progress"] = 30

        # Compute metrics
        engine = BiasEngine(data, sens_col, tgt_col, pred_col)
        jobs[job_id]["progress"] = 60

        result = engine.run_full_audit()
        result["dataset_id"] = request.dataset_id
        result["sensitive_attrs"] = request.sensitive_attributes

        jobs[job_id]["progress"] = 90

        # Simulate processing time for realistic UX
        time.sleep(1)

        jobs[job_id]["result"] = result
        jobs[job_id]["status"] = "complete"
        jobs[job_id]["progress"] = 100

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
