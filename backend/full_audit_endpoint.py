"""
Standalone FastAPI router for a basic end-to-end audit.

Adds:
  POST /api/full-audit

This module is intentionally self-contained and does not modify any existing
app wiring. To enable it, include the router from your FastAPI app:

    from full_audit_endpoint import router as full_audit_router
    app.include_router(full_audit_router)
"""

from __future__ import annotations

import io
from typing import Any

import numpy as np
import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

router = APIRouter()


def _to_py(v: Any) -> Any:
    """Convert numpy/pandas scalars into JSON-serializable Python types."""
    if isinstance(v, (np.generic,)):
        return v.item()
    return v


def _parse_sensitive_columns(raw: str | None) -> list[str]:
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p]


def _detect_sensitive_columns(df: pd.DataFrame) -> list[str]:
    needles = ("gender", "sex", "race", "age")
    cols = []
    for c in df.columns:
        cl = str(c).lower()
        if any(n in cl for n in needles):
            cols.append(str(c))
    return cols


def _detect_binary_target(df: pd.DataFrame) -> str | None:
    # Prefer numeric binary columns (0/1, -1/1, etc.) by nunique==2.
    for c in df.columns:
        s = df[c]
        if pd.api.types.is_numeric_dtype(s) and s.dropna().nunique() == 2:
            return str(c)
    return None


def _pick_numeric_baseline_column(df: pd.DataFrame, exclude: set[str]) -> str | None:
    for c in df.columns:
        if str(c) in exclude:
            continue
        s = df[c]
        if pd.api.types.is_numeric_dtype(s) and s.dropna().size > 0:
            return str(c)
    return None


@router.post("/full-audit")
async def full_audit(
    dataset: UploadFile = File(...),
    model_file: UploadFile | None = File(None),
    target_column: str | None = Form(None),
    sensitive_columns: str | None = Form(None),
):
    # STEP 1: LOAD DATA
    if not dataset.filename or not dataset.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="dataset must be a .csv file")

    try:
        content = await dataset.read()
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")

    if df.empty or df.shape[1] == 0:
        raise HTTPException(status_code=400, detail="CSV must have at least 1 column and 1 row")

    # STEP 2: COLUMN HANDLING
    requested_sensitive = _parse_sensitive_columns(sensitive_columns)
    if requested_sensitive:
        sens_cols = [c for c in requested_sensitive if c in df.columns]
        missing = [c for c in requested_sensitive if c not in df.columns]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"sensitive_columns not found in CSV: {missing}",
            )
    else:
        sens_cols = _detect_sensitive_columns(df)

    if not sens_cols:
        raise HTTPException(
            status_code=400,
            detail="No sensitive columns provided/detected. Provide sensitive_columns or include columns like gender/sex/race/age.",
        )

    resolved_target = target_column if (target_column and target_column in df.columns) else None
    if resolved_target is None:
        resolved_target = _detect_binary_target(df)

    # STEP 3: CONTEXT LAYER (BASIC)
    representation: dict[str, dict[str, float]] = {}
    for s in sens_cols:
        vc = df[s].fillna("NA").astype(str).value_counts(normalize=True, dropna=False)
        representation[s] = {str(k): float(_to_py(v)) for k, v in vc.to_dict().items()}

    # Qualification baseline
    qualification: dict[str, Any] = {
        "method": None,
        "target_column": resolved_target,
        "baseline_column": None,
    }

    qualified: pd.Series
    if resolved_target is not None:
        # "qualified = target == 1" (coerce to numeric where possible)
        tgt = pd.to_numeric(df[resolved_target], errors="coerce").fillna(0)
        qualified = (tgt == 1)
        qualification["method"] = "target_equals_1"
    else:
        baseline_col = _pick_numeric_baseline_column(df, exclude=set(sens_cols))
        if baseline_col is None:
            raise HTTPException(
                status_code=400,
                detail="No target_column detected and no numeric column available for top-50% baseline.",
            )
        x = pd.to_numeric(df[baseline_col], errors="coerce")
        thr = float(_to_py(x.median(skipna=True))) if x.notna().any() else 0.0
        qualified = x.fillna(-np.inf) >= thr
        qualification["method"] = "top_50_percent_numeric"
        qualification["baseline_column"] = baseline_col
        qualification["threshold_median"] = thr


    # Qualification distribution per group
    qualification_by_group: dict[str, dict[str, float]] = {}
    for s in sens_cols:
        grp = (
            pd.DataFrame({"s": df[s].fillna("NA").astype(str), "q": qualified.astype(int)})
            .groupby("s")["q"]
            .mean()
        )
        qualification_by_group[s] = {str(k): float(_to_py(v)) for k, v in grp.to_dict().items()}

    context = {
        "representation": representation,
        "qualification": {
            **qualification,
            "qualification_rate_by_group": qualification_by_group,
        },
    }

    # STEP 4: BASIC ANALYSIS
    analysis: dict[str, Any] = {}
    if resolved_target is not None:
        actual = (pd.to_numeric(df[resolved_target], errors="coerce") > 0).astype(int)
       # actual = pd.to_numeric(df[resolved_target], errors="coerce").fillna(0).astype(int)
    else:
        actual = qualified.astype(int)
    for s in sens_cols:
        # Selection rate per group
        grp_rates = (
            pd.DataFrame({"s": df[s].fillna("NA").astype(str), "sel": actual})
            .groupby("s")["sel"]
            .mean()
        )
        rates = {str(k): float(_to_py(v)) for k, v in grp_rates.to_dict().items()}
        vals = list(rates.values())
        diff = float(max(vals) - min(vals)) if len(vals) >= 2 else 0.0

        analysis[s] = {
            "selection_rate_by_group": rates,
            "selection_rate_diff": diff,
        }

    # STEP 5: MODEL HANDLING (SAFE)
    model_info = None
    if model_file is not None and model_file.filename:
        try:
            model_bytes = await model_file.read()
            model_info = {
                "received": True,
                "filename": model_file.filename,
                "size_bytes": len(model_bytes),
                "note": "Model received; prediction logic intentionally not executed in this endpoint.",
            }
        except Exception as e:
            model_info = {
                "received": False,
                "filename": model_file.filename,
                "error": str(e),
            }

    if model_info is not None:
        context["model"] = model_info

    # STEP 6: RESPONSE
    return {
        "summary": "Basic audit completed successfully",
        "details": {
            "context": context,
            "analysis": analysis,
        },
    }

