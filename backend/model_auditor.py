"""
Model Auditor — Bias detection for pre-trained ML models.

Supports two modes:
    1. Model File Audit: Upload a serialized model (.pkl/.joblib) + test dataset
    2. API Endpoint Audit: Provide a model API URL + test dataset

Both modes generate predictions, then feed them through the AutoBiasScanner.
"""

import io
import numpy as np
import pandas as pd
from typing import Any

from auto_scan import AutoBiasScanner


class ModelFileAuditor:
    """
    Audits a serialized sklearn-compatible model for bias.

    Loads the model, runs predictions on the test dataset,
    then passes the augmented dataset through AutoBiasScanner.
    """

    SUPPORTED_EXTENSIONS = {".pkl", ".joblib", ".pickle"}

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
            model_bytes: Raw bytes of the serialized model file.
            model_filename: Original filename (used to determine format).
            test_data: DataFrame to run predictions on.
            target_col: Optional ground-truth column name.

        Returns:
            Complete bias audit results.
        """
        # Step 1: Load the model
        model = self._load_model(model_bytes, model_filename)

        # Step 2: Identify feature columns (exclude target if known)
        feature_cols = [c for c in test_data.columns if c != target_col]

        # Only use numeric columns for prediction
        numeric_features = test_data[feature_cols].select_dtypes(
            include=[np.number]
        ).columns.tolist()

        if not numeric_features:
            return {
                "status": "error",
                "message": "No numeric feature columns found in test dataset.",
            }

        # Step 3: Generate predictions
        try:
            X = test_data[numeric_features].fillna(0).values
            predictions = model.predict(X)

            # Binarize predictions if needed
            if hasattr(predictions, 'dtype') and np.issubdtype(predictions.dtype, np.floating):
                predictions = (predictions > 0.5).astype(int)
            else:
                predictions = np.array(predictions).astype(int)

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to generate predictions: {e}",
            }

        # Step 4: Add predictions to dataframe
        augmented_df = test_data.copy()
        augmented_df["_model_prediction"] = predictions

        # Step 5: Run auto-scan
        scan_result = self.scanner.scan(
            augmented_df,
            target_col=target_col,
            prediction_col="_model_prediction",
        )

        # Enrich with model metadata
        scan_result["audit_type"] = "model_file"
        scan_result["model_filename"] = model_filename
        scan_result["test_samples"] = len(test_data)
        scan_result["features_used"] = numeric_features

        return scan_result

    def _load_model(self, model_bytes: bytes, filename: str) -> Any:
        """Deserialize a model from bytes."""
        import joblib
        import pickle

        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext in (".joblib",):
            return joblib.load(io.BytesIO(model_bytes))
        elif ext in (".pkl", ".pickle"):
            return pickle.loads(model_bytes)
        else:
            # Try joblib first, then pickle
            try:
                return joblib.load(io.BytesIO(model_bytes))
            except Exception:
                return pickle.loads(model_bytes)


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
        """
        Audit an external API endpoint for bias.

        Args:
            endpoint_url: The model API URL.
            test_data: DataFrame with test records.
            target_col: Optional ground-truth column.
            request_format: "json_rows" (one row per request) or
                            "json_batch" (batch of rows).
            response_key: JSON key in the response containing the prediction.
            headers: Optional HTTP headers (e.g., auth tokens).
            batch_size: Number of rows per batch request.

        Returns:
            Complete bias audit results.
        """
        import httpx

        predictions = []
        errors = []
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)

        async with httpx.AsyncClient(timeout=30.0) as client:
            if request_format == "json_batch":
                # Send data in batches
                for i in range(0, len(test_data), batch_size):
                    batch = test_data.iloc[i:i + batch_size]
                    payload = batch.to_dict(orient="records")

                    try:
                        resp = await client.post(
                            endpoint_url,
                            headers=req_headers,
                            json=payload,
                        )
                        if resp.status_code == 200:
                            body = resp.json()
                            if isinstance(body, list):
                                predictions.extend(body)
                            elif isinstance(body, dict) and response_key in body:
                                preds = body[response_key]
                                if isinstance(preds, list):
                                    predictions.extend(preds)
                                else:
                                    predictions.append(preds)
                            else:
                                predictions.extend([None] * len(batch))
                                errors.append(f"Batch {i}: unexpected response format")
                        else:
                            predictions.extend([None] * len(batch))
                            errors.append(
                                f"Batch {i}: HTTP {resp.status_code}"
                            )
                    except Exception as e:
                        predictions.extend([None] * len(batch))
                        errors.append(f"Batch {i}: {str(e)}")

            else:
                # Send one row at a time
                for idx, row in test_data.iterrows():
                    payload = row.to_dict()
                    # Convert numpy types to Python types
                    payload = {
                        k: (v.item() if hasattr(v, 'item') else v)
                        for k, v in payload.items()
                    }

                    try:
                        resp = await client.post(
                            endpoint_url,
                            headers=req_headers,
                            json=payload,
                        )
                        if resp.status_code == 200:
                            body = resp.json()
                            if isinstance(body, dict) and response_key in body:
                                predictions.append(body[response_key])
                            elif isinstance(body, (int, float)):
                                predictions.append(body)
                            else:
                                predictions.append(None)
                                errors.append(
                                    f"Row {idx}: unexpected response"
                                )
                        else:
                            predictions.append(None)
                            errors.append(
                                f"Row {idx}: HTTP {resp.status_code}"
                            )
                    except Exception as e:
                        predictions.append(None)
                        errors.append(f"Row {idx}: {str(e)}")

        # Check if we got enough valid predictions
        valid_preds = [p for p in predictions if p is not None]
        if len(valid_preds) < 10:
            return {
                "status": "error",
                "message": f"Only {len(valid_preds)} valid predictions received "
                           f"out of {len(test_data)} requests.",
                "errors": errors[:20],
            }

        # Add predictions to dataframe
        augmented_df = test_data.copy()
        pred_series = pd.Series(predictions, index=test_data.index)

        # Binarize if numeric
        if pd.api.types.is_numeric_dtype(pred_series.dropna()):
            pred_series = pred_series.fillna(0)
            if pred_series.nunique() > 2:
                pred_series = (pred_series > pred_series.median()).astype(int)
            else:
                pred_series = pred_series.astype(int)
        else:
            pred_series = pred_series.astype("category").cat.codes

        augmented_df["_api_prediction"] = pred_series

        # Run auto-scan
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
