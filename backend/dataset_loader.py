"""
Dataset Loader — Generates synthetic versions of real-world bias datasets.

Supports: COMPAS Recidivism, Adult Income, Fair Lending, Healthcare Allocation.
Also handles user-uploaded CSV datasets.
"""

import io
import csv
import pandas as pd
import numpy as np
from typing import Any


class DatasetLoader:
    """Loads built-in synthetic datasets and user-uploaded CSV files."""

    _DATASETS: dict[str, dict[str, Any]] = {
        "compas": {
            "id": "compas",
            "name": "COMPAS Recidivism",
            "domain": "criminal_justice",
            "description": "Recidivism prediction — modelled on ProPublica COMPAS analysis",
            "risk": "high",
            "rows": 5000,
            "sensitive_attrs": ["race", "sex"],
            "target": "two_year_recid",
        },
        "adult_income": {
            "id": "adult_income",
            "name": "Adult Income (UCI)",
            "domain": "employment",
            "description": "Income prediction — modelled on UCI Adult dataset",
            "risk": "high",
            "rows": 8000,
            "sensitive_attrs": ["gender", "race"],
            "target": "income",
        },
        "lending": {
            "id": "lending",
            "name": "Loan Approval",
            "domain": "financial_services",
            "description": "Synthetic loan approval data with demographic features",
            "risk": "high",
            "rows": 4000,
            "sensitive_attrs": ["race", "gender"],
            "target": "approved",
        },
        "healthcare": {
            "id": "healthcare",
            "name": "Healthcare Allocation",
            "domain": "healthcare",
            "description": "Health resource allocation — based on Obermeyer et al. 2019",
            "risk": "medium",
            "rows": 3000,
            "sensitive_attrs": ["race", "socioeconomic_status"],
            "target": "high_need",
        },
    }

    _uploads: dict[str, bytes] = {}

    def list_datasets(self) -> list[dict[str, Any]]:
        return list(self._DATASETS.values())

    def dataset_exists(self, dataset_id: str) -> bool:
        return dataset_id in self._DATASETS or dataset_id in self._uploads

    def store_upload(self, dataset_id: str, content: bytes, filename: str) -> None:
        self._uploads[dataset_id] = content

    def get_dataset(
        self, dataset_id: str, sensitive_attr: str = "race"
    ) -> tuple[pd.DataFrame, str, str, str]:
        """
        Returns (data, sensitive_col, target_col, prediction_col).

        For built-in datasets, generates synthetic biased data to demonstrate
        metric computation. For uploads, parses the CSV.
        """
        if dataset_id in self._uploads:
            return self._parse_csv(self._uploads[dataset_id])

        if dataset_id not in self._DATASETS:
            raise ValueError(f"Dataset '{dataset_id}' not found")

        meta = self._DATASETS[dataset_id]
        rng = np.random.default_rng(42)
        n = meta["rows"]

        # Synthetic data: [sensitive, target, prediction]
        sensitive = rng.integers(0, 2, size=n)
        target = rng.integers(0, 2, size=n)

        # Inject bias: privileged group gets more positive predictions
        prediction = target.copy()
        flip_mask = (sensitive == 0) & (rng.random(n) < 0.30)
        prediction[flip_mask] = 0  # Reduce positive predictions for group 0

        df = pd.DataFrame({
            sensitive_attr: sensitive,
            meta["target"]: target,
            "prediction": prediction
        })
        
        # Add some random continuous columns for bias scanning demo
        for col_name in meta.get("sensitive_attrs", []) + ["age", "income", "credit_score"]:
            if col_name not in df.columns:
                df[col_name] = rng.normal(size=n)
                
        # Make one column heavily biased against the target to demonstrate scanning
        if "income" in df.columns and "income" != meta["target"]:
            df["income"] = df[meta["target"]] * 50000 + rng.normal(size=n) * 10000

        return df, sensitive_attr, meta["target"], "prediction"

    def _parse_csv(self, content: bytes) -> tuple[pd.DataFrame, str, str, str]:
        try:
            df = pd.read_csv(io.BytesIO(content))
        except Exception as e:
            raise ValueError(f"Could not parse CSV: {e}")
            
        if len(df) < 1:
            raise ValueError("CSV must have a header and at least one data row")
            
        cols = df.columns.tolist()
        if len(cols) < 3:
            raise ValueError("CSV must have at least 3 columns")
            
        # Default: first col = sensitive, second to last = target, last = prediction
        return df, cols[0], cols[-2], cols[-1]

    def get_most_biased_columns(self, dataset_id: str) -> list[str]:
        """Automatically scans the dataset and returns a list of the most heavily biased columns."""
        if not self.dataset_exists(dataset_id):
            return []
            
        try:
            df, _, target_col, _ = self.get_dataset(dataset_id)
        except Exception:
            return []

        if target_col not in df.columns:
            return []
            
        correlations = {}
        for col in df.columns:
            if col in [target_col, "prediction"] or not pd.api.types.is_numeric_dtype(df[col]):
                continue
            corr = df[col].corr(df[target_col])
            if pd.notna(corr):
                correlations[col] = abs(corr)
                
        # Sort by absolute correlation
        sorted_cols = sorted(correlations.items(), key=lambda x: x[1], reverse=True)
        return [col for col, _ in sorted_cols[:3]]
