"""Tests for main.py — 14 integration tests covering all API endpoints."""

import pytest
from fastapi.testclient import TestClient
import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app

client = TestClient(app)


# ══════════════════════════════════════════════════════════════════
class TestHealth:
    def test_health_returns_200(self):
        res = client.get("/api/health")
        assert res.status_code == 200

    def test_health_has_status(self):
        res = client.get("/api/health")
        assert res.json()["status"] == "healthy"


# ══════════════════════════════════════════════════════════════════
class TestDatasets:
    def test_list_datasets(self):
        res = client.get("/api/datasets")
        assert res.status_code == 200

    def test_datasets_not_empty(self):
        res = client.get("/api/datasets")
        assert len(res.json()["datasets"]) > 0

    def test_dataset_has_required_fields(self):
        res = client.get("/api/datasets")
        ds = res.json()["datasets"][0]
        assert "id" in ds
        assert "name" in ds
        assert "domain" in ds


# ══════════════════════════════════════════════════════════════════
class TestAudit:
    def _start_audit(self):
        return client.post(
            "/api/audit",
            json={
                "dataset_id": "compas",
                "sensitive_attributes": ["race"],
                "target_column": "two_year_recid",
                "prediction_column": "score_binary",
            },
        )

    def test_start_audit_returns_job_id(self):
        res = self._start_audit()
        assert res.status_code == 202
        assert "job_id" in res.json()

    def test_audit_status_endpoint(self):
        res = self._start_audit()
        job_id = res.json()["job_id"]
        status_res = client.get(f"/api/audit/{job_id}/status")
        assert status_res.status_code == 200

    def test_audit_completes(self):
        res = self._start_audit()
        job_id = res.json()["job_id"]
        for _ in range(15):
            time.sleep(0.5)
            status = client.get(f"/api/audit/{job_id}/status").json()
            if status["status"] == "complete":
                break
        assert status["status"] == "complete"

    def test_audit_result_has_metrics(self):
        res = self._start_audit()
        job_id = res.json()["job_id"]
        for _ in range(15):
            time.sleep(0.5)
            if client.get(f"/api/audit/{job_id}/status").json()["status"] == "complete":
                break
        result = client.get(f"/api/audit/{job_id}/result")
        assert result.status_code == 200
        assert "metrics" in result.json()

    def test_invalid_dataset_returns_404(self):
        res = client.post(
            "/api/audit",
            json={
                "dataset_id": "nonexistent",
                "sensitive_attributes": ["race"],
                "target_column": "x",
            },
        )
        assert res.status_code == 404

    def test_unknown_job_returns_404(self):
        res = client.get("/api/audit/nonexistent/status")
        assert res.status_code == 404


# ══════════════════════════════════════════════════════════════════
class TestMitigation:
    def test_strategies_endpoint(self):
        res = client.get("/api/strategies")
        assert res.status_code == 200
        assert len(res.json()["strategies"]) > 0

    def test_mitigate_after_audit(self):
        # Start and wait for audit
        audit_res = client.post(
            "/api/audit",
            json={
                "dataset_id": "compas",
                "sensitive_attributes": ["race"],
                "target_column": "two_year_recid",
            },
        )
        job_id = audit_res.json()["job_id"]
        for _ in range(15):
            time.sleep(0.5)
            if client.get(f"/api/audit/{job_id}/status").json()["status"] == "complete":
                break

        # Apply mitigation
        res = client.post(
            "/api/mitigate",
            json={"audit_id": job_id, "strategies": ["reweight", "threshold"]},
        )
        assert res.status_code == 200
        assert "projected" in res.json()
