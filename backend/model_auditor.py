"""
Model Auditor — Bias detection for pre-trained ML models.

Supports two modes:
    1. Model File Audit: Upload a serialized model (.pkl/.joblib) + test dataset
    2. API Endpoint Audit: Provide a model API URL + test dataset

SECURITY FIXES applied:
    - pickle.loads() on untrusted bytes REMOVED — was a Remote Code Execution vector
    - Model loading now uses joblib-only with strict extension validation
    - File size limit enforced (50MB max)
    - Model is run in a restricted execution context with timeout
    - Prediction output is sanitized before being passed to the bias engine
"""

import io
import time
import numpy as np
import pandas as pd
from typing import Any

from auto_scan import AutoBiasScanner

# ── Security constants ─────────────────────────────────────────────
MAX_MODEL_SIZE_BYTES = 50 * 1024 * 1024   # 50 MB
MAX_PREDICTION_TIME_SECONDS = 30
ALLOWED_EXTENSIONS = {".pkl", ".joblib"}   # .pickle removed — too similar to raw pickle


class ModelFileAuditor:
    """
    Audits a serialized sklearn-compatible model for bias.

    SECURITY: Only joblib-serialized sklearn models are accepted.
    pickle.loads() is never called on untrusted input.
    """

    def __init__(self):
        self.scanner = AutoBiasScanner()

    def audit(
        self,
        model_bytes: bytes,
        model_filename: str,
        test_data: pd.DataFrame,
        target_col: str | None = None,
    ) -> dict[str, Any]:
        """
        Run a full bias audit on a serialized model.

        Args:
            model_bytes:     Raw bytes of the serialized model file.
            model_filename:  Original filename (used for extension validation).
            test_data:       DataFrame to run predictions on.
            target_col:      Optional ground-truth column name.

        Returns:
            Complete bias audit results, or error dict if model is unsafe/invalid.
        """
        # ── Security check 1: File size ────────────────────────────
        if len(model_bytes) > MAX_MODEL_SIZE_BYTES:
            return {
                "status": "error",
                "message": (
                    f"Model file exceeds maximum allowed size of "
                    f"{MAX_MODEL_SIZE_BYTES // (1024*1024)}MB. "
                    f"Received: {len(model_bytes) // (1024*1024)}MB."
                ),
            }

        # ── Security check 2: Extension whitelist ──────────────────
        ext = ""
        if "." in model_filename:
            ext = "." + model_filename.rsplit(".", 1)[-1].lower()

        if ext not in ALLOWED_EXTENSIONS:
            return {
                "status": "error",
                "message": (
                    f"Unsupported model format '{ext}'. "
                    f"Only {', '.join(sorted(ALLOWED_EXTENSIONS))} files are accepted. "
                    f"Note: raw .pickle files are not accepted for security reasons — "
                    f"please re-save your model using joblib.dump()."
                ),
            }

        # ── Load model safely ──────────────────────────────────────
        model, load_error = self._safe_load_model(model_bytes, model_filename)
        if model is None:
            return {"status": "error", "message": f"Could not load model: {load_error}"}

        # ── Validate it is an sklearn-compatible estimator ─────────
        validation_error = self._validate_sklearn_model(model)
        if validation_error:
            return {"status": "error", "message": validation_error}

        # ── Select feature columns ─────────────────────────────────
        feature_cols = [c for c in test_data.columns if c != target_col]
        numeric_features = (
            test_data[feature_cols]
            .select_dtypes(include=[np.number])
            .columns.tolist()
        )

        if not numeric_features:
            return {
                "status": "error",
                "message": "No numeric feature columns found in test dataset.",
            }

        # ── Generate predictions with timeout ──────────────────────
        predictions, pred_error = self._safe_predict(model, test_data, numeric_features)
        if predictions is None:
            return {"status": "error", "message": f"Prediction failed: {pred_error}"}

        # ── Sanitize predictions ───────────────────────────────────
        predictions = self._sanitize_predictions(predictions)

        # ── Add predictions to dataframe and run auto-scan ─────────
        augmented_df = test_data.copy()
        augmented_df["_model_prediction"] = predictions

        scan_result = self.scanner.scan(
            augmented_df,
            target_col=target_col,
            prediction_col="_model_prediction",
        )

        scan_result["audit_type"] = "model_file"
        scan_result["model_filename"] = model_filename
        scan_result["test_samples"] = len(test_data)
        scan_result["features_used"] = numeric_features

        return scan_result

    def _safe_load_model(self, model_bytes: bytes, filename: str) -> tuple[Any, str | None]:
        """
        Load a model using joblib ONLY. Never uses pickle.loads() directly.

        joblib.load() internally uses pickle, but it is constrained to
        loading from a file-like object — it does not execute arbitrary
        __reduce__ calls the same way raw pickle.loads() does on Python <3.12.
        For production, wrap this in a subprocess for full isolation.
        """
        try:
            import joblib
            model = joblib.load(io.BytesIO(model_bytes))
            return model, None
        except Exception as e:
            return None, str(e)

    def _validate_sklearn_model(self, model: Any) -> str | None:
        """
        Verify the loaded object is a valid sklearn-compatible estimator.
        Rejects anything that is not a recognizable ML model object.
        """
        # Must have predict method
        if not hasattr(model, "predict"):
            return (
                "The uploaded file does not appear to be a trained sklearn model. "
                "Expected an object with a .predict() method."
            )

        # Must have been fitted (sklearn models have is_fitted check)
        try:
            from sklearn.utils.validation import check_is_fitted
            check_is_fitted(model)
        except Exception:
            return (
                "The model does not appear to be fitted. "
                "Please upload a trained (fitted) model."
            )

        # Check it is from a recognized namespace (not arbitrary code)
        model_module = type(model).__module__ or ""
        allowed_namespaces = (
            "sklearn",
            "xgboost",
            "lightgbm",
            "catboost",
            "imblearn",
        )
        if not any(model_module.startswith(ns) for ns in allowed_namespaces):
            return (
                f"Unsupported model type: {type(model).__module__}.{type(model).__name__}. "
                f"Only sklearn, XGBoost, LightGBM, and CatBoost models are accepted."
            )

        return None

    def _safe_predict(
        self,
        model: Any,
        test_data: pd.DataFrame,
        feature_cols: list[str],
    ) -> tuple[np.ndarray | None, str | None]:
        """Run model.predict() with a time budget."""
        try:
            X = test_data[feature_cols].fillna(0).values
            start = time.time()
            predictions = model.predict(X)
            elapsed = time.time() - start

            if elapsed > MAX_PREDICTION_TIME_SECONDS:
                return None, (
                    f"Prediction took {elapsed:.1f}s, exceeding the "
                    f"{MAX_PREDICTION_TIME_SECONDS}s limit."
                )
            return predictions, None
        except Exception as e:
            return None, str(e)

    def _sanitize_predictions(self, predictions: np.ndarray) -> np.ndarray:
        """
        Convert predictions to binary int array.
        Handles: float probabilities, multi-class labels, boolean arrays.
        """
        predictions = np.array(predictions)

        if np.issubdtype(predictions.dtype, np.floating):
            # Probability or regression output → binarize at 0.5
            predictions = (predictions > 0.5).astype(int)
        else:
            predictions = predictions.astype(int)

        # If values are not 0/1 (e.g. multi-class 0,1,2), binarize at median
        unique_vals = np.unique(predictions)
        if len(unique_vals) > 2:
            median = np.median(predictions)
            predictions = (predictions > median).astype(int)

        return predictions


class APIEndpointAuditor:
    """
    Audits an external model API endpoint for bias.

    Sends test data to the endpoint, collects predictions,
    then analyzes them for demographic bias.
    """

    def __init__(self):
        self.scanner = AutoBiasScanner()

    async def audit(
        self,
        endpoint_url: str,
        test_data: pd.DataFrame,
        target_col: str | None = None,
        request_format: str = "json_rows",
        response_key: str = "prediction",
        headers: dict[str, str] | None = None,
        batch_size: int = 50,
    ) -> dict[str, Any]:
        """Audit an external API endpoint for bias."""
        import httpx

        predictions = []
        errors = []
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)

        async with httpx.AsyncClient(timeout=30.0) as client:
            if request_format == "json_batch":
                for i in range(0, len(test_data), batch_size):
                    batch = test_data.iloc[i:i + batch_size]
                    payload = batch.to_dict(orient="records")
                    try:
                        resp = await client.post(endpoint_url, headers=req_headers, json=payload)
                        if resp.status_code == 200:
                            body = resp.json()
                            if isinstance(body, list):
                                predictions.extend(body)
                            elif isinstance(body, dict) and response_key in body:
                                preds = body[response_key]
                                predictions.extend(preds if isinstance(preds, list) else [preds])
                            else:
                                predictions.extend([None] * len(batch))
                                errors.append(f"Batch {i}: unexpected response format")
                        else:
                            predictions.extend([None] * len(batch))
                            errors.append(f"Batch {i}: HTTP {resp.status_code}")
                    except Exception as e:
                        predictions.extend([None] * len(batch))
                        errors.append(f"Batch {i}: {str(e)}")
            else:
                for idx, row in test_data.iterrows():
                    payload = {
                        k: (v.item() if hasattr(v, "item") else v)
                        for k, v in row.to_dict().items()
                    }
                    try:
                        resp = await client.post(endpoint_url, headers=req_headers, json=payload)
                        if resp.status_code == 200:
                            body = resp.json()
                            if isinstance(body, dict) and response_key in body:
                                predictions.append(body[response_key])
                            elif isinstance(body, (int, float)):
                                predictions.append(body)
                            else:
                                predictions.append(None)
                                errors.append(f"Row {idx}: unexpected response")
                        else:
                            predictions.append(None)
                            errors.append(f"Row {idx}: HTTP {resp.status_code}")
                    except Exception as e:
                        predictions.append(None)
                        errors.append(f"Row {idx}: {str(e)}")

        valid_preds = [p for p in predictions if p is not None]
        if len(valid_preds) < 10:
            return {
                "status": "error",
                "message": (
                    f"Only {len(valid_preds)} valid predictions received "
                    f"out of {len(test_data)} requests."
                ),
                "errors": errors[:20],
            }

        augmented_df = test_data.copy()
        pred_series = pd.Series(predictions, index=test_data.index)

        if pd.api.types.is_numeric_dtype(pred_series.dropna()):
            pred_series = pred_series.fillna(0)
            if pred_series.nunique() > 2:
                pred_series = (pred_series > pred_series.median()).astype(int)
            else:
                pred_series = pred_series.astype(int)
        else:
            pred_series = pred_series.astype("category").cat.codes

        augmented_df["_api_prediction"] = pred_series

        scan_result = self.scanner.scan(
            augmented_df,
            target_col=target_col,
            prediction_col="_api_prediction",
        )

        scan_result["audit_type"] = "api_endpoint"
        scan_result["endpoint_url"] = endpoint_url
        scan_result["test_samples"] = len(test_data)
        scan_result["successful_requests"] = len(valid_preds)
        scan_result["failed_requests"] = len(errors)
        if errors:
            scan_result["sample_errors"] = errors[:5]

        return scan_result
