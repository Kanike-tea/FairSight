"""
Auto-Scan Engine — Automatic bias detection without user-specified filters.

Given a raw dataset, this module:
    1. Classifies columns by role (sensitive, target, prediction, feature)
    2. Runs BiasEngine across every valid combination
    3. Produces a ranked "bias heatmap" showing where bias lives
"""

import re
import numpy as np
import os
import pandas as pd
from typing import Any
from bias_engine import BiasEngine
from gemma_analyzer import GemmaColumnClassifier, GemmaBiasInterpreter


# ── Heuristic patterns for column role detection ──────────────────

# Column names that strongly suggest sensitive/protected attributes
_SENSITIVE_PATTERNS = [
    r"race", r"ethnicit", r"gender", r"sex", r"religion",
    r"disabilit", r"national", r"marital", r"orienta",
    r"socioeconomic", r"ses\b", r"caste", r"tribe",
    r"citizen", r"immigra", r"refugee", r"language",
    r"veteran", r"pregnan",
]

# Column names that suggest a ground-truth target / label
_TARGET_PATTERNS = [
    r"target", r"label", r"outcome", r"result",
    r"approved", r"accepted", r"admitted", r"hired",
    r"recid", r"default", r"churn", r"fraud",
    r"diagnosis", r"high_need", r"eligible",
    r"income\b", r"salary", r"class\b",
]

# Column names that suggest model predictions
_PREDICTION_PATTERNS = [
    r"predict", r"score", r"prob", r"decision",
    r"classified", r"output", r"y_hat", r"y_pred",
    r"forecast",
]


class ColumnClassifier:
    """Heuristically classifies DataFrame columns by their likely role."""

    def classify(self, df: pd.DataFrame) -> dict[str, list[str]]:
        """
        Returns {
            "sensitive": [...],
            "target": [...],
            "prediction": [...],
            "feature": [...]
        }
        """
        roles: dict[str, list[str]] = {
            "sensitive": [],
            "target": [],
            "prediction": [],
            "feature": [],
        }

        for col in df.columns:
            col_lower = col.lower().strip()
            nunique = df[col].nunique()
            is_numeric = pd.api.types.is_numeric_dtype(df[col])
            is_binary = nunique == 2

            # ── Check prediction patterns first (most specific) ───
            if _matches_any(col_lower, _PREDICTION_PATTERNS):
                roles["prediction"].append(col)
                continue

            # ── Check target patterns ─────────────────────────────
            if _matches_any(col_lower, _TARGET_PATTERNS):
                roles["target"].append(col)
                continue

            # ── Check sensitive attribute patterns ────────────────
            if _matches_any(col_lower, _SENSITIVE_PATTERNS):
                roles["sensitive"].append(col)
                continue

            # ── Heuristic: low-cardinality categorical → sensitive
            if not is_numeric and 2 <= nunique <= 20:
                roles["sensitive"].append(col)
                continue

            # ── Heuristic: binary numeric columns could be target/prediction
            if is_binary and is_numeric:
                # Ambiguous — could be target or prediction
                # We'll add to target; auto-scanner resolves ambiguity
                roles["target"].append(col)
                continue

            # ── Heuristic: numeric columns with 2-10 unique values
            #    and name hints at demographics → sensitive
            if is_numeric and 2 <= nunique <= 10:
                # Likely encoded categorical → potential sensitive attr
                roles["sensitive"].append(col)
                continue

            # ── Everything else is a feature ──────────────────────
            roles["feature"].append(col)

        return roles


class AutoBiasScanner:
    """
    Scans a dataset for bias across all detected sensitive attributes.

    Produces a ranked list of biased attributes with per-attribute
    metric breakdowns and an overall bias heatmap.
    """

    def __init__(self):
        self.heuristic_classifier = ColumnClassifier()
        self.gemma_classifier = GemmaColumnClassifier()
        self.gemma_interpreter = GemmaBiasInterpreter()
        self.use_ai = bool(os.getenv("GOOGLE_API_KEY"))

    def scan(
        self,
        df: pd.DataFrame,
        target_col: str | None = None,
        prediction_col: str | None = None,
    ) -> dict[str, Any]:
        """
        Full auto-scan pipeline.

        Args:
            df: The dataset to scan.
            target_col: Override auto-detected target column.
            prediction_col: Override auto-detected prediction column.

        Returns:
            Comprehensive bias scan report with heatmap and rankings.
        """
        # Step 1: Classify columns
        if self.use_ai:
            # Build sample values for Gemma
            sample_values = {col: df[col].dropna().head(5).tolist() for col in df.columns}
            roles = self.gemma_classifier.classify(df.columns.tolist(), sample_values)
        else:
            roles = self.heuristic_classifier.classify(df)

        # Step 2: Resolve target and prediction columns
        resolved_target = target_col or self._pick_best(
            roles["target"], df, prefer_name=True
        )
        resolved_prediction = prediction_col or self._pick_best(
            roles["prediction"], df, prefer_name=True
        )

        # If no prediction column found, use target as proxy
        # (dataset-only bias: comparing subgroup distributions)
        if resolved_prediction is None and resolved_target is not None:
            resolved_prediction = resolved_target

        if resolved_target is None:
            # Last resort: pick the last binary column
            binary_cols = [
                c for c in df.columns if df[c].nunique() == 2 and pd.api.types.is_numeric_dtype(df[c])
            ]
            if binary_cols:
                resolved_target = binary_cols[-1]
                if len(binary_cols) >= 2:
                    resolved_prediction = binary_cols[-1]
                    resolved_target = binary_cols[-2]
                else:
                    resolved_prediction = resolved_target

        if resolved_target is None or resolved_prediction is None:
            return {
                "status": "error",
                "message": "Could not auto-detect target/prediction columns. "
                           "Please specify them manually.",
                "detected_roles": {k: v for k, v in roles.items()},
            }

        # Step 3: Determine sensitive attributes to scan
        sensitive_candidates = roles["sensitive"]

        # Also consider target candidates that aren't the chosen target
        for col in roles["target"]:
            if col not in (resolved_target, resolved_prediction) and col not in sensitive_candidates:
                sensitive_candidates.append(col)

        # Remove target/prediction from sensitive list
        sensitive_candidates = [
            c for c in sensitive_candidates
            if c not in (resolved_target, resolved_prediction)
        ]

        if not sensitive_candidates:
            return {
                "status": "warning",
                "message": "No potential sensitive attributes detected in dataset.",
                "detected_roles": {k: v for k, v in roles.items()},
                "resolved_target": resolved_target,
                "resolved_prediction": resolved_prediction,
            }

        # Step 4: Run bias analysis for each sensitive attribute
        attribute_results = []
        for sens_col in sensitive_candidates:
            result = self._analyze_attribute(
                df, sens_col, resolved_target, resolved_prediction
            )
            if result is not None:
                attribute_results.append(result)

        # Step 5: Sort by bias severity (lowest fairness_score = most biased)
        attribute_results.sort(key=lambda x: x["fairness_score"])

        # Step 6: Build overall summary
        overall_score = (
            int(np.mean([r["fairness_score"] for r in attribute_results]))
            if attribute_results
            else 100
        )

        most_biased = attribute_results[0] if attribute_results else None
        critical_count = sum(
            1 for r in attribute_results if r["risk_level"] == "critical"
        )

        result = {
            "status": "success",
            "summary": {
                "total_attributes_scanned": len(sensitive_candidates),
                "biased_attributes_found": sum(
                    1 for r in attribute_results if r["fairness_score"] < 65
                ),
                "critical_attributes": critical_count,
                "overall_fairness_score": overall_score,
                "overall_risk_level": _risk_from_score(overall_score),
                "most_biased_attribute": (
                    most_biased["attribute"] if most_biased else None
                ),
            },
            "resolved_columns": {
                "target": resolved_target,
                "prediction": resolved_prediction,
                "sensitive_attributes": sensitive_candidates,
            },
            "detected_roles": {k: v for k, v in roles.items()},
            "attribute_results": attribute_results,
            "bias_heatmap": self._build_heatmap(attribute_results),
        }

        # Step 7: Interpret bias with AI
        if self.use_ai:
            result["ai_interpretation"] = self.gemma_interpreter.interpret(result)

        return result

    def _analyze_attribute(
        self,
        df: pd.DataFrame,
        sens_col: str,
        target_col: str,
        prediction_col: str,
    ) -> dict[str, Any] | None:
        """Run full bias analysis for a single sensitive attribute."""
        try:
            # Ensure columns are numeric for BiasEngine
            work_df = df[[sens_col, target_col, prediction_col]].copy()

            # Encode non-numeric sensitive column
            if not pd.api.types.is_numeric_dtype(work_df[sens_col]):
                work_df[sens_col] = work_df[sens_col].astype("category").cat.codes

            # Ensure target and prediction are numeric
            for col in [target_col, prediction_col]:
                if not pd.api.types.is_numeric_dtype(work_df[col]):
                    work_df[col] = work_df[col].astype("category").cat.codes

            # Binarize if needed (BiasEngine expects 0/1)
            for col in [sens_col, target_col, prediction_col]:
                if work_df[col].nunique() > 2:
                    median_val = work_df[col].median()
                    work_df[col] = (work_df[col] > median_val).astype(int)

            work_df = work_df.dropna()
            if len(work_df) < 10:
                return None

            engine = BiasEngine(work_df, sens_col, target_col, prediction_col)
            audit = engine.run_full_audit()

            # Get group labels from original data
            original_groups = df[sens_col].value_counts().to_dict()
            group_labels = {
                str(k): v for k, v in original_groups.items()
            }

            return {
                "attribute": sens_col,
                "fairness_score": audit["fairness_score"],
                "risk_level": audit["risk_level"],
                "metrics": audit["metrics"],
                "flags": audit["flags"],
                "group_metrics": audit["group_metrics"],
                "group_labels": group_labels,
                "num_groups": df[sens_col].nunique(),
                "is_biased": audit["fairness_score"] < 65,
            }
        except Exception as e:
            return {
                "attribute": sens_col,
                "fairness_score": -1,
                "risk_level": "error",
                "error": str(e),
                "is_biased": False,
            }

    def _build_heatmap(
        self, attribute_results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Build a condensed bias heatmap for visualization."""
        heatmap = []
        for r in attribute_results:
            if r.get("error"):
                continue
            metrics = r.get("metrics", {})
            heatmap.append({
                "attribute": r["attribute"],
                "fairness_score": r["fairness_score"],
                "risk_level": r["risk_level"],
                "disparate_impact": metrics.get("disparate_impact", 0),
                "demographic_parity_diff": metrics.get("demographic_parity_diff", 0),
                "equalized_odds_diff": metrics.get("equalized_odds_diff", 0),
                "is_biased": r.get("is_biased", False),
            })
        return heatmap

    def _pick_best(
        self,
        candidates: list[str],
        df: pd.DataFrame,
        prefer_name: bool = True,
    ) -> str | None:
        """Pick the best column from a list of candidates."""
        if not candidates:
            return None
        if len(candidates) == 1:
            return candidates[0]
        # Prefer binary columns
        binary = [c for c in candidates if df[c].nunique() == 2]
        if binary:
            return binary[0]
        return candidates[0]


def _matches_any(text: str, patterns: list[str]) -> bool:
    """Check if text matches any of the regex patterns."""
    return any(re.search(p, text) for p in patterns)


def _risk_from_score(score: int) -> str:
    if score >= 65:
        return "low"
    if score >= 40:
        return "medium"
    return "critical"
