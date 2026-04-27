"""
Dataset Loader — Generates realistic synthetic versions of real-world bias datasets.

Each dataset is generated with realistic base rates so the bias engine can
distinguish between model bias and dataset composition effects.

Datasets:
    compas       — Genuine model bias, similar actual recidivism rates
    adult_income — Fair model, different base rates (teammate's scenario)
    lending      — Genuine bias on top of some real qualification gap
    healthcare   — Critical bias via proxy variable (Obermeyer et al. 2019)
"""

import io
import json
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
            "expected_verdict": "biased",
        },
        "adult_income": {
            "id": "adult_income",
            "name": "Adult Income (UCI)",
            "domain": "employment",
            "description": "Income prediction — demonstrates dataset composition vs model bias",
            "risk": "high",
            "rows": 8000,
            "sensitive_attrs": ["gender", "race"],
            "target": "income",
            "expected_verdict": "proportional",
        },
        "lending": {
            "id": "lending",
            "name": "Loan Approval",
            "domain": "financial_services",
            "description": "Synthetic loan approval with genuine model bias on top of qualification gap",
            "risk": "high",
            "rows": 4000,
            "sensitive_attrs": ["race", "gender"],
            "target": "approved",
            "expected_verdict": "biased",
        },
        "healthcare": {
            "id": "healthcare",
            "name": "Healthcare Allocation",
            "domain": "healthcare",
            "description": "Health resource allocation — based on Obermeyer et al. 2019",
            "risk": "high",
            "rows": 3000,
            "sensitive_attrs": ["race", "socioeconomic_status"],
            "target": "high_need",
            "expected_verdict": "biased",
        },
    }

    _uploads: dict[str, bytes] = {}

    def list_datasets(self) -> list[dict[str, Any]]:
        # Return without internal fields
        public_fields = {"id", "name", "domain", "description", "risk", "rows", "sensitive_attrs", "target"}
        return [{k: v for k, v in ds.items() if k in public_fields} for ds in self._DATASETS.values()]

    def dataset_exists(self, dataset_id: str) -> bool:
        return dataset_id in self._DATASETS or dataset_id in self._uploads

    def store_upload(self, dataset_id: str, content: bytes, filename: str) -> None:
        self._uploads[dataset_id] = content

    def get_dataset(
        self, dataset_id: str, sensitive_attr: str = "race"
    ) -> tuple[pd.DataFrame, str, str, str]:
        """Returns (data, sensitive_col, target_col, prediction_col)."""
        if dataset_id in self._uploads:
            return self._parse_csv(self._uploads[dataset_id])

        if dataset_id not in self._DATASETS:
            raise ValueError(f"Dataset '{dataset_id}' not found")

        generators = {
            "compas": self._generate_compas,
            "adult_income": self._generate_adult_income,
            "lending": self._generate_lending,
            "healthcare": self._generate_healthcare,
        }
        return generators[dataset_id](sensitive_attr)

    def _generate_compas(self, sensitive_attr: str = "race") -> tuple:
        """
        Genuine model bias scenario.
        Both groups have similar actual recidivism (~45%), but the model
        flags minority defendants at a higher rate regardless.
        Expected: bias_verdict = 'biased'
        """
        rng = np.random.default_rng(42)
        n = 5000
        race = rng.choice([0, 1], size=n, p=[0.60, 0.40])
        base_prob = np.where(race == 0, 0.46, 0.44)
        two_year_recid = (rng.random(n) < base_prob).astype(int)
        prediction = two_year_recid.copy()

        # Model bias: extra false positives for minority, extra false negatives for majority
        minority_mask = race == 0
        flip_to_1 = minority_mask & (two_year_recid == 0) & (rng.random(n) < 0.30)
        flip_to_0 = (~minority_mask) & (two_year_recid == 1) & (rng.random(n) < 0.25)
        prediction[flip_to_1] = 1
        prediction[flip_to_0] = 0

        df = pd.DataFrame({
            sensitive_attr: race,
            "two_year_recid": two_year_recid,
            "prediction": prediction,
            "age": rng.integers(18, 65, n),
            "priors_count": rng.integers(0, 15, n),
        })
        return df, sensitive_attr, "two_year_recid", "prediction"

    def _generate_adult_income(self, sensitive_attr: str = "gender") -> tuple:
        """
        Demonstrates your teammate's insight: different outcome rates that are
        PROPORTIONAL to actual base rates — dataset composition, not model bias.
        Expected: bias_verdict = 'proportional'
        """
        rng = np.random.default_rng(42)
        n = 8000
        gender = rng.choice([0, 1], size=n, p=[0.33, 0.67])
        base_prob = np.where(gender == 0, 0.28, 0.45)
        income = (rng.random(n) < base_prob).astype(int)
        prediction = income.copy()
        noise_mask = rng.random(n) < 0.08
        prediction[noise_mask] = 1 - prediction[noise_mask]
        df = pd.DataFrame({
            sensitive_attr: gender,
            "income": income,
            "prediction": prediction,
            "age": rng.integers(18, 65, n),
            "education_years": rng.integers(8, 20, n),
            "hours_per_week": rng.integers(20, 60, n),
        })
        return df, sensitive_attr, "income", "prediction"

    def _generate_lending(self, sensitive_attr: str = "race") -> tuple:
        """
        Some real qualification gap exists, AND model adds discrimination on top.
        Expected: bias_verdict = 'biased'
        """
        rng = np.random.default_rng(42)
        n = 4000
        race = rng.choice([0, 1], size=n, p=[0.45, 0.55])
        base_prob = np.where(race == 0, 0.42, 0.55)
        approved = (rng.random(n) < base_prob).astype(int)
        prediction = approved.copy()
        minority_qualified = (race == 0) & (approved == 1)
        majority_unqualified = (race == 1) & (approved == 0)
        prediction[minority_qualified & (rng.random(n) < 0.28)] = 0
        prediction[majority_unqualified & (rng.random(n) < 0.15)] = 1
        df = pd.DataFrame({
            sensitive_attr: race,
            "approved": approved,
            "prediction": prediction,
            "credit_score": rng.integers(300, 850, n),
            "income": rng.integers(20000, 150000, n),
            "debt_to_income": rng.uniform(0.1, 0.6, n).round(2),
        })
        return df, sensitive_attr, "approved", "prediction"

    def _generate_healthcare(self, sensitive_attr: str = "race") -> tuple:
        """
        Based on Obermeyer et al. 2019 cost-as-proxy bias.
        Black patients have HIGHER actual need but model rates them lower.
        Expected: bias_verdict = 'biased'
        """
        rng = np.random.default_rng(42)
        n = 3000
        race = rng.choice([0, 1], size=n, p=[0.40, 0.60])
        base_prob = np.where(race == 0, 0.52, 0.48)
        high_need = (rng.random(n) < base_prob).astype(int)
        prediction = high_need.copy()
        black_high_need = (race == 0) & (high_need == 1)
        white_low_need = (race == 1) & (high_need == 0)
        prediction[black_high_need & (rng.random(n) < 0.38)] = 0
        prediction[white_low_need & (rng.random(n) < 0.12)] = 1
        df = pd.DataFrame({
            sensitive_attr: race,
            "high_need": high_need,
            "prediction": prediction,
            "historical_cost": rng.integers(1000, 50000, n),
            "age": rng.integers(18, 90, n),
            "chronic_conditions": rng.integers(0, 8, n),
        })
        return df, sensitive_attr, "high_need", "prediction"

    def _parse_csv(self, content: bytes) -> tuple[pd.DataFrame, str, str, str]:
        """
        Parse a user-uploaded CSV.

        FIXED: No longer blindly uses positional column defaults (cols[0], cols[-1]).
        Instead uses pattern matching to identify column roles, with a clear
        error when ambiguous columns cannot be resolved.
        """
        try:
            df = pd.read_csv(io.BytesIO(content))
        except Exception as e:
            raise ValueError(f"Could not parse CSV: {e}")

        if len(df) < 2:
            raise ValueError("CSV must have at least 2 data rows")

        cols = df.columns.tolist()
        if len(cols) < 3:
            raise ValueError("CSV must have at least 3 columns (sensitive, target, prediction)")

        sensitive_col, target_col, pred_col = self._detect_columns(df)

        if target_col is None or pred_col is None:
            raise ValueError(
                "Could not auto-detect target and prediction columns. "
                "Please ensure your CSV has columns named like: "
                "'hired', 'approved', 'label' (target) and "
                "'prediction', 'score', 'predicted' (prediction). "
                f"Columns found: {cols}"
            )

        return df, sensitive_col, target_col, pred_col

    def _detect_columns(self, df: pd.DataFrame) -> tuple[str | None, str | None, str | None]:
        """
        Detect column roles using name patterns and dtype heuristics.
        Returns (sensitive_col, target_col, prediction_col).
        """
        import re

        PREDICTION_PATTERNS = [r"predict", r"\bscore\b", r"prob\b", r"y_hat", r"y_pred", r"output", r"decision"]
        TARGET_PATTERNS = [r"\btarget\b", r"\blabel\b", r"outcome", r"hired\b", r"approved\b",
                           r"admitted\b", r"recid", r"default\b", r"fraud\b", r"high_need", r"eligible"]
        SENSITIVE_PATTERNS = [r"race", r"ethnicit", r"gender", r"\bsex\b", r"religion",
                              r"disabilit", r"national", r"marital", r"caste", r"age\b",
                              r"socioeconomic", r"\bses\b", r"veteran"]
        # Columns to explicitly EXCLUDE from sensitive (identifiers, names, IDs)
        IDENTIFIER_PATTERNS = [r"\bname\b", r"\bid\b", r"_id$", r"^id_", r"uuid", r"email", r"phone"]

        def matches(col, patterns):
            return any(re.search(p, col.lower()) for p in patterns)

        pred_col = next((c for c in df.columns if matches(c, PREDICTION_PATTERNS)), None)
        target_col = next((c for c in df.columns
                           if matches(c, TARGET_PATTERNS) and c != pred_col), None)

        # Sensitive: name-matched first, then low-cardinality categorical,
        # but never identifiers, target, or prediction columns
        exclude = {pred_col, target_col}
        sensitive_col = None
        for c in df.columns:
            if c in exclude:
                continue
            if matches(c, IDENTIFIER_PATTERNS):
                continue
            if matches(c, SENSITIVE_PATTERNS):
                sensitive_col = c
                break

        # Fallback: first low-cardinality non-identifier non-excluded column
        if sensitive_col is None:
            for c in df.columns:
                if c in exclude or matches(c, IDENTIFIER_PATTERNS):
                    continue
                if 2 <= df[c].nunique() <= 10:
                    sensitive_col = c
                    break

        # Final fallback: positional (with warning — only if nothing else worked)
        if sensitive_col is None and len(df.columns) >= 3:
            candidates = [c for c in df.columns if c not in exclude and not matches(c, IDENTIFIER_PATTERNS)]
            sensitive_col = candidates[0] if candidates else None

        return sensitive_col, target_col, pred_col

    def get_most_biased_columns(self, dataset_id: str) -> list[str]:
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
        return [col for col, _ in sorted(correlations.items(), key=lambda x: x[1], reverse=True)[:3]]
