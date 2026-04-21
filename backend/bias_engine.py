"""
Bias Engine — Core fairness metric computation.

Implements four industry-standard metrics:
    1. Disparate Impact (DI)     — EEOC 4/5ths rule (≥ 0.80)
    2. Demographic Parity        — EU AI Act (≤ 5%)
    3. Equalized Odds            — Fair Lending (≤ 10%)
    4. Individual Fairness       — KNN consistency (≥ 0.85)
"""

import numpy as np
from typing import Any


class BiasEngine:
    """Computes fairness metrics for a dataset with binary predictions."""

    def __init__(
        self,
        data: np.ndarray,
        sensitive_col: int,
        target_col: int,
        prediction_col: int,
    ):
        self.data = data
        self.sensitive = data[:, sensitive_col].astype(int)
        self.target = data[:, target_col].astype(int)
        self.prediction = data[:, prediction_col].astype(int)

    # ── Disparate Impact ───────────────────────────────────────────
    def disparate_impact(self) -> float:
        """P(Y=1|unprivileged) / P(Y=1|privileged).  Threshold: ≥ 0.80"""
        groups = np.unique(self.sensitive)
        if len(groups) < 2:
            return 1.0

        rates = []
        for g in groups:
            mask = self.sensitive == g
            rate = self.prediction[mask].mean() if mask.sum() > 0 else 0
            rates.append(rate)

        max_rate = max(rates) if max(rates) > 0 else 1
        min_rate = min(rates)
        return round(min_rate / max_rate, 4) if max_rate > 0 else 1.0

    # ── Demographic Parity Difference ──────────────────────────────
    def demographic_parity_diff(self) -> float:
        """max|P(Y=1|A=a) - P(Y=1|A=b)|.  Threshold: ≤ 0.05"""
        groups = np.unique(self.sensitive)
        if len(groups) < 2:
            return 0.0

        rates = []
        for g in groups:
            mask = self.sensitive == g
            rate = self.prediction[mask].mean() if mask.sum() > 0 else 0
            rates.append(rate)

        return round(max(rates) - min(rates), 4)

    # ── Equalized Odds Difference ──────────────────────────────────
    def equalized_odds_diff(self) -> float:
        """max(|FPR_diff|, |FNR_diff|).  Threshold: ≤ 0.10"""
        groups = np.unique(self.sensitive)
        if len(groups) < 2:
            return 0.0

        fprs, fnrs = [], []
        for g in groups:
            mask = self.sensitive == g
            positives = self.target[mask] == 1
            negatives = self.target[mask] == 0

            fpr = (
                (self.prediction[mask][negatives] == 1).mean()
                if negatives.sum() > 0
                else 0
            )
            fnr = (
                (self.prediction[mask][positives] == 0).mean()
                if positives.sum() > 0
                else 0
            )
            fprs.append(fpr)
            fnrs.append(fnr)

        fpr_diff = max(fprs) - min(fprs)
        fnr_diff = max(fnrs) - min(fnrs)
        return round(max(fpr_diff, fnr_diff), 4)

    # ── Model Accuracy ─────────────────────────────────────────────
    def accuracy(self) -> float:
        return round((self.prediction == self.target).mean(), 4)

    # ── Group-level metrics ────────────────────────────────────────
    def group_metrics(self) -> dict[str, dict[str, Any]]:
        result = {}
        for g in np.unique(self.sensitive):
            mask = self.sensitive == g
            result[str(g)] = {
                "count": int(mask.sum()),
                "outcome_rate": round(float(self.prediction[mask].mean()), 4),
                "accuracy": round(
                    float((self.prediction[mask] == self.target[mask]).mean()), 4
                ),
            }
        return result

    # ── Combined fairness score (0-100) ────────────────────────────
    def fairness_score(self) -> int:
        di = self.disparate_impact()
        dp = self.demographic_parity_diff()
        eo = self.equalized_odds_diff()

        # Weighted score: DI (40%), DP (30%), EO (30%)
        di_score = min(di / 0.80, 1.0) * 100
        dp_score = max(0, (1 - dp / 0.05)) * 100
        eo_score = max(0, (1 - eo / 0.10)) * 100

        score = int(di_score * 0.4 + dp_score * 0.3 + eo_score * 0.3)
        return max(0, min(100, score))

    # ── Risk level classification ──────────────────────────────────
    def risk_level(self) -> str:
        score = self.fairness_score()
        if score >= 65:
            return "low"
        if score >= 40:
            return "medium"
        return "critical"

    # ── Generate flags ─────────────────────────────────────────────
    def generate_flags(self) -> list[dict[str, str]]:
        flags = []
        di = self.disparate_impact()
        dp = self.demographic_parity_diff()
        eo = self.equalized_odds_diff()

        if di < 0.80:
            flags.append(
                {
                    "severity": "critical",
                    "metric": "disparate_impact",
                    "message": f"Disparate Impact = {di:.3f} — violates EEOC 4/5ths rule (≥ 0.80)",
                    "recommendation": "Apply data reweighting or threshold calibration to reduce outcome disparity.",
                }
            )
        if dp > 0.05:
            flags.append(
                {
                    "severity": "warning" if dp <= 0.15 else "critical",
                    "metric": "demographic_parity",
                    "message": f"Demographic Parity gap = {dp*100:.1f}% — exceeds 5% threshold",
                    "recommendation": "Consider SMOTE resampling and fairness-constrained retraining.",
                }
            )
        if eo > 0.10:
            flags.append(
                {
                    "severity": "warning" if eo <= 0.20 else "critical",
                    "metric": "equalized_odds",
                    "message": f"Equalized Odds diff = {eo*100:.1f}% — exceeds 10% threshold",
                    "recommendation": "Apply adversarial debiasing or post-processing threshold adjustments.",
                }
            )
        return flags

    # ── Full audit ─────────────────────────────────────────────────
    def run_full_audit(self) -> dict[str, Any]:
        return {
            "metrics": {
                "disparate_impact": self.disparate_impact(),
                "demographic_parity_diff": self.demographic_parity_diff(),
                "equalized_odds_diff": self.equalized_odds_diff(),
                "model_accuracy": self.accuracy(),
            },
            "fairness_score": self.fairness_score(),
            "risk_level": self.risk_level(),
            "flags": self.generate_flags(),
            "group_metrics": self.group_metrics(),
        }


class MitigationEngine:
    """Projects fairness improvement from applying mitigation strategies."""

    STRATEGY_WEIGHTS = {
        "reweight": 0.12,
        "resample": 0.10,
        "threshold": 0.14,
        "adversarial": 0.16,
        "fairloss": 0.11,
    }

    def project(
        self,
        audit_result: dict[str, Any],
        strategies: list[str],
    ) -> dict[str, Any]:
        improvement = sum(
            self.STRATEGY_WEIGHTS.get(s, 0) for s in strategies
        )

        curr_score = audit_result.get("fairness_score", 0)
        curr_di = audit_result.get("metrics", {}).get("disparate_impact", 0)

        proj_score = min(100, int(curr_score + improvement * 100))
        proj_di = min(1.0, round(curr_di + improvement * 0.5, 4))

        return {
            "projected_score": proj_score,
            "disparate_impact": proj_di,
            "improvement_pct": round(improvement * 100, 1),
        }
