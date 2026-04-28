"""
Auto-Scan Engine — Automatic bias detection without user-specified filters.

Given a raw dataset, this module:
    1. Classifies columns by role (sensitive, target, prediction, feature)
    2. Runs BiasEngine across every valid sensitive attribute
    3. Produces a ranked "bias heatmap" showing where bias lives
    4. Detects domain context for appropriate metric weighting

FIXES applied:
    - Outcome/target columns are NO LONGER added to sensitive_candidates
      (previously caused 'hired' to be audited as a demographic attribute)
    - Domain is detected from dataset metadata and passed to BiasEngine
    - Binarization of continuous sensitive attrs now warns the user
    - Minimum sample size enforced per group before running BiasEngine
"""

import re
import numpy as np
import os
import pandas as pd
from typing import Any
from bias_engine import BiasEngine
from gemma_analyzer import GemmaColumnClassifier, GemmaBiasInterpreter

# ── Column role patterns ───────────────────────────────────────────

_SENSITIVE_PATTERNS = [
    r"race", r"ethnicit", r"gender", r"\bsex\b", r"religion",
    r"disabilit", r"national", r"marital", r"orienta",
    r"socioeconomic", r"\bses\b", r"caste", r"tribe",
    r"citizen", r"immigra", r"refugee", r"language",
    r"veteran", r"pregnan", r"\bage\b",
]

_TARGET_PATTERNS = [
    r"\btarget\b", r"\blabel\b", r"outcome", r"\bresult\b",
    r"approved\b", r"accepted\b", r"admitted\b", r"\bhired\b",
    r"recid", r"default\b", r"churn\b", r"fraud\b",
    r"diagnosis", r"high_need", r"eligible\b",
    r"\bincome\b", r"\bsalary\b", r"\bclass\b",
]

_PREDICTION_PATTERNS = [
    r"predict", r"\bscore\b", r"\bprob\b", r"decision\b",
    r"classified", r"\boutput\b", r"y_hat", r"y_pred",
    r"forecast",
]

# Columns that should NEVER be treated as sensitive attributes
_IDENTIFIER_PATTERNS = [
    r"\bname\b", r"\bid\b", r"_id$", r"^id_", r"uuid",
    r"email", r"phone", r"address", r"zip\b", r"ssn",
]

# Domain detection patterns from column names
_DOMAIN_PATTERNS = {
    "criminal_justice": [r"recid", r"arrest", r"crime", r"offend", r"jail", r"prison", r"compas"],
    "healthcare":       [r"diagnos", r"medical", r"health", r"patient", r"clinical", r"high_need", r"treatment"],
    "financial":        [r"loan", r"credit", r"approv", r"lend", r"mortgage", r"debt", r"financ"],
    "hiring":           [r"hired\b", r"employ", r"job\b", r"applicant", r"recruit", r"salary", r"income\b"],
}


class ColumnClassifier:
    """Heuristically classifies DataFrame columns by their likely role."""

    def classify(self, df: pd.DataFrame) -> dict[str, list[str]]:
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

            # Skip identifier columns — never sensitive or target
            if _matches_any(col_lower, _IDENTIFIER_PATTERNS):
                roles["feature"].append(col)
                continue

            if _matches_any(col_lower, _PREDICTION_PATTERNS):
                roles["prediction"].append(col)
                continue

            if _matches_any(col_lower, _TARGET_PATTERNS):
                roles["target"].append(col)
                continue

            if _matches_any(col_lower, _SENSITIVE_PATTERNS):
                roles["sensitive"].append(col)
                continue

            # Low-cardinality categorical → sensitive (but not binary numeric — could be target)
            if not is_numeric and 2 <= nunique <= 20:
                roles["sensitive"].append(col)
                continue

            # Binary numeric → target (most likely label)
            if is_numeric and nunique == 2:
                roles["target"].append(col)
                continue

            # Low-cardinality numeric (3–10 values) → sensitive (encoded categorical)
            if is_numeric and 3 <= nunique <= 10:
                roles["sensitive"].append(col)
                continue

            roles["feature"].append(col)

        return roles


def _detect_domain(df: pd.DataFrame) -> str:
    """Detect dataset domain from column names."""
    all_cols = " ".join(df.columns.str.lower())
    for domain, patterns in _DOMAIN_PATTERNS.items():
        if _matches_any(all_cols, patterns):
            return domain
    return "default"


class AutoBiasScanner:
    """
    Scans a dataset for bias across all detected sensitive attributes.
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
        domain: str | None = None,
        sensitive_cols: str | None = None,
    ) -> dict[str, Any]:
        """
        Full auto-scan pipeline.

        Args:
            df:             Dataset to scan.
            target_col:     Override auto-detected target column.
            prediction_col: Override auto-detected prediction column.
            domain:         Domain context for score weighting. If None, auto-detected.

        Returns:
            Comprehensive bias scan report with heatmap and rankings.
        """
        # Step 1: Classify columns
        if self.use_ai:
            sample_values = {col: df[col].dropna().head(5).tolist() for col in df.columns}
            roles = self.gemma_classifier.classify(df.columns.tolist(), sample_values)
        else:
            roles = self.heuristic_classifier.classify(df)

        # Step 2: Resolve target and prediction columns
        resolved_target = target_col or self._pick_best(roles["target"], df)
        resolved_prediction = prediction_col or self._pick_best(roles["prediction"], df)

        if resolved_prediction is None and resolved_target is not None:
            resolved_prediction = resolved_target

        if resolved_target is None:
            binary_cols = [
                c for c in df.columns
                if df[c].nunique() == 2 and pd.api.types.is_numeric_dtype(df[c])
            ]
            if binary_cols:
                resolved_target = binary_cols[-1]
                resolved_prediction = binary_cols[-2] if len(binary_cols) >= 2 else resolved_target

        if resolved_target is None or resolved_prediction is None:
            return {
                "status": "error",
                "message": (
                    "Could not auto-detect target/prediction columns. "
                    "Please specify them manually."
                ),
                "detected_roles": {k: v for k, v in roles.items()},
            }

        # Step 3: Build sensitive candidates.
        # FIXED: Do NOT add target-role columns to sensitive_candidates.
        # Previously, leftover target columns (not chosen as the primary target)
        # were added here, causing outcome variables like 'hired' to be audited
        # as if they were demographic attributes.
        if sensitive_cols:
            # User explicitly specified sensitive columns — use them directly
            sensitive_candidates = [
                c.strip() for c in sensitive_cols.split(",")
                if c.strip() in df.columns
            ]
        else:
            # Fallback to auto-detect
            sensitive_candidates = [
                c for c in roles["sensitive"]
                if c not in (resolved_target, resolved_prediction)
            ]

        if not sensitive_candidates:
            return {
                "status": "warning",
                "message": f"No potential sensitive attributes detected in dataset. Roles: {roles}. Target: {resolved_target}",
                "detected_roles": {k: v for k, v in roles.items()},
                "resolved_target": resolved_target,
                "resolved_prediction": resolved_prediction,
            }

        # Step 4: Detect domain if not provided
        detected_domain = domain or _detect_domain(df)

        # Step 5: Run bias analysis per sensitive attribute
        attribute_results = []
        for sens_col in sensitive_candidates:
            result = self._analyze_attribute(
                df, sens_col, resolved_target, resolved_prediction, detected_domain
            )
            if result is not None:
                attribute_results.append(result)

        attribute_results.sort(key=lambda x: x["fairness_score"])

        overall_score = (
            int(np.mean([r["fairness_score"] for r in attribute_results]))
            if attribute_results else 100
        )

        most_biased = attribute_results[0] if attribute_results else None
        critical_count = sum(1 for r in attribute_results if r["risk_level"] == "critical")

        result = {
            "status": "success",
            "summary": {
                "total_attributes_scanned": len(sensitive_candidates),
                "biased_attributes_found": sum(
                    1 for r in attribute_results
                    if r["fairness_score"] < 65
                    or r.get("metrics", {}).get("disparate_impact", 1.0) < 0.80
                ),
                "critical_attributes": critical_count,
                "overall_fairness_score": overall_score,
                "overall_risk_level": _risk_from_score(overall_score),
                "most_biased_attribute": most_biased["attribute"] if most_biased else None,
            },
            "resolved_columns": {
                "target": resolved_target,
                "prediction": resolved_prediction,
                "sensitive_attributes": sensitive_candidates,
            },
            "detected_roles": {k: v for k, v in roles.items()},
            "detected_domain": detected_domain,
            "attribute_results": attribute_results,
            "bias_heatmap": self._build_heatmap(attribute_results),
        }

        if self.use_ai:
            result["ai_interpretation"] = self.gemma_interpreter.interpret(result)

        return result

    def _analyze_attribute(
        self,
        df: pd.DataFrame,
        sens_col: str,
        target_col: str,
        prediction_col: str,
        domain: str = "default",
    ) -> dict[str, Any] | None:
        """Run full bias analysis for a single sensitive attribute."""
        try:
            # Deduplicate columns (target == prediction in dataset-only mode)
            needed_cols = list(dict.fromkeys([sens_col, target_col, prediction_col]))
            work_df = df[needed_cols].copy()
            # If target == prediction, create a separate prediction column
            if target_col == prediction_col:
                work_df = work_df.rename(columns={}, copy=True)
                # Ensure we have distinct columns for the engine
                work_df['_prediction'] = work_df[target_col]
                prediction_col = '_prediction'

            binarized_note = None

            # Encode non-numeric sensitive column
            if not pd.api.types.is_numeric_dtype(work_df[sens_col]):
                work_df[sens_col] = work_df[sens_col].astype("category").cat.codes

            # Ensure target and prediction are numeric
            for col in [target_col, prediction_col]:
                if not pd.api.types.is_numeric_dtype(work_df[col]):
                    work_df[col] = work_df[col].astype("category").cat.codes

            # Binarize sensitive attr if needed — WARN the user
            if work_df[sens_col].nunique() > 2:
                original_nunique = work_df[sens_col].nunique()
                median_val = work_df[sens_col].median()
                work_df[sens_col] = (work_df[sens_col] > median_val).astype(int)
                binarized_note = (
                    f"'{sens_col}' had {original_nunique} unique values and was binarized "
                    f"at the median ({median_val:.1f}). Results reflect groups "
                    f"below vs. above the median — not individual value distinctions."
                )

            # Binarize target and prediction if needed
            for col in [target_col, prediction_col]:
                if work_df[col].nunique() > 2:
                    median_val = work_df[col].median()
                    work_df[col] = (work_df[col] > median_val).astype(int)

            work_df = work_df.dropna()
            if len(work_df) < 10:
                return None

            # Pass feature columns from original df for Individual Fairness
            feature_cols = [
                c for c in df.columns
                if c not in (sens_col, target_col, prediction_col)
                and pd.api.types.is_numeric_dtype(df[c])
            ]
            # Merge features back into work_df
            full_work_df = work_df.copy()
            for fc in feature_cols:
                if fc in df.columns:
                    full_work_df[fc] = df.loc[work_df.index, fc].values

            engine = BiasEngine(
                full_work_df,
                sens_col,
                target_col,
                prediction_col,
                domain=domain,
                feature_cols=feature_cols if feature_cols else None,
            )
            audit = engine.run_full_audit()

            # Handle insufficient data result
            if audit.get("status") == "insufficient_data":
                return None

            original_groups = df[sens_col].value_counts().to_dict()

            result = {
                "attribute": sens_col,
                "fairness_score": audit["fairness_score"],
                "risk_level": audit["risk_level"],
                "metrics": audit["metrics"],
                "flags": audit["flags"],
                "group_metrics": audit["group_metrics"],
                "base_rates": audit.get("base_rates", {}),
                "dataset_context": audit.get("dataset_context", {}),
                "group_labels": {str(k): v for k, v in original_groups.items()},
                "num_groups": df[sens_col].nunique(),
                "is_biased": (
                    audit["fairness_score"] < 65
                    or audit.get("metrics", {}).get("disparate_impact", 1.0) < 0.80
                ),
                "domain": domain,
            }

            if binarized_note:
                result["binarization_warning"] = binarized_note

            return result

        except Exception as e:
            return {
                "attribute": sens_col,
                "fairness_score": -1,
                "risk_level": "error",
                "error": str(e),
                "is_biased": False,
            }

    def _build_heatmap(self, attribute_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        heatmap = []
        for r in attribute_results:
            if r.get("error"):
                continue
            metrics = r.get("metrics", {})
            entry = {
                "attribute": r["attribute"],
                "fairness_score": r["fairness_score"],
                "risk_level": r["risk_level"],
                "disparate_impact": metrics.get("disparate_impact", 0),
                "conditional_disparate_impact": metrics.get("conditional_disparate_impact", 0),
                "demographic_parity_diff": metrics.get("demographic_parity_diff", 0),
                "equalized_odds_diff": metrics.get("equalized_odds_diff", 0),
                "individual_fairness": metrics.get("individual_fairness", 1.0),
                "is_biased": r.get("is_biased", False),
                "bias_verdict": r.get("dataset_context", {}).get("bias_verdict", "unknown"),
            }
            if "binarization_warning" in r:
                entry["binarization_warning"] = r["binarization_warning"]
            heatmap.append(entry)
        return heatmap

    def _pick_best(self, candidates: list[str], df: pd.DataFrame) -> str | None:
        if not candidates:
            return None
        if len(candidates) == 1:
            return candidates[0]
        binary = [c for c in candidates if df[c].nunique() == 2]
        return binary[0] if binary else candidates[0]


def _matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text) for p in patterns)


def _risk_from_score(score: int) -> str:
    if score >= 85:
        return "low"
    if score >= 60:
        return "medium"
    if score >= 40:
        return "high"
    return "critical"
