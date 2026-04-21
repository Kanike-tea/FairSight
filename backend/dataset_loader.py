"""
Dataset Loader — Generates synthetic versions of real-world bias datasets.

Supports: COMPAS Recidivism, Adult Income, Fair Lending, Healthcare Allocation.
Also handles user-uploaded CSV datasets.
"""

import io
import csv
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
    ) -> tuple[np.ndarray, int, int, int]:
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

        data = np.column_stack([sensitive, target, prediction])
        return data, 0, 1, 2

    def _parse_csv(self, content: bytes) -> tuple[np.ndarray, int, int, int]:
        reader = csv.reader(io.StringIO(content.decode("utf-8")))
        rows = list(reader)
        if len(rows) < 2:
            raise ValueError("CSV must have a header and at least one data row")
        header = rows[0]
        data = np.array(rows[1:], dtype=float)
        # Default: col 0 = sensitive, col -2 = target, col -1 = prediction
        return data, 0, len(header) - 2, len(header) - 1
