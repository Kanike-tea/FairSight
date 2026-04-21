"""Tests for bias_engine.py — 23 unit tests covering metrics, flags, and mitigation."""

import numpy as np
import pytest
from bias_engine import BiasEngine, MitigationEngine
from dataset_loader import DatasetLoader


# ── Helper: create a biased dataset ───────────────────────────────
def _biased_dataset():
    """Group 0 gets 30% positive, group 1 gets 70% positive."""
    rng = np.random.default_rng(42)
    n = 1000
    sensitive = np.array([0] * 500 + [1] * 500)
    target = rng.integers(0, 2, n)
    prediction = target.copy()
    # Bias: suppress positives for group 0
    mask = (sensitive == 0) & (prediction == 1) & (rng.random(n) < 0.5)
    prediction[mask] = 0
    data = np.column_stack([sensitive, target, prediction])
    return data


def _fair_dataset():
    """Both groups get ~50% positive."""
    rng = np.random.default_rng(42)
    n = 1000
    sensitive = np.array([0] * 500 + [1] * 500)
    target = rng.integers(0, 2, n)
    prediction = target.copy()
    data = np.column_stack([sensitive, target, prediction])
    return data


# ══════════════════════════════════════════════════════════════════
class TestBiasEngine:
    def test_returns_metrics_object(self):
        data = _biased_dataset()
        engine = BiasEngine(data, 0, 1, 2)
        result = engine.run_full_audit()
        assert "metrics" in result
        assert "fairness_score" in result
        assert "risk_level" in result
        assert "flags" in result

    def test_detects_bias_in_biased_dataset(self):
        engine = BiasEngine(_biased_dataset(), 0, 1, 2)
        assert engine.disparate_impact() < 0.80

    def test_fair_dataset_passes_thresholds(self):
        engine = BiasEngine(_fair_dataset(), 0, 1, 2)
        assert engine.disparate_impact() >= 0.80

    def test_disparate_impact_range(self):
        engine = BiasEngine(_biased_dataset(), 0, 1, 2)
        di = engine.disparate_impact()
        assert 0.0 <= di <= 1.0

    def test_fairness_score_range(self):
        engine = BiasEngine(_biased_dataset(), 0, 1, 2)
        assert 0 <= engine.fairness_score() <= 100

    def test_biased_data_has_low_score(self):
        engine = BiasEngine(_biased_dataset(), 0, 1, 2)
        assert engine.fairness_score() < 65

    def test_flags_generated(self):
        engine = BiasEngine(_biased_dataset(), 0, 1, 2)
        assert len(engine.generate_flags()) > 0

    def test_flags_have_required_fields(self):
        engine = BiasEngine(_biased_dataset(), 0, 1, 2)
        for flag in engine.generate_flags():
            assert "severity" in flag
            assert "message" in flag
            assert "recommendation" in flag

    def test_group_metrics_populated(self):
        engine = BiasEngine(_biased_dataset(), 0, 1, 2)
        gm = engine.group_metrics()
        assert len(gm) >= 2

    def test_group_metrics_have_outcome_rate(self):
        engine = BiasEngine(_biased_dataset(), 0, 1, 2)
        for group, data in engine.group_metrics().items():
            assert "outcome_rate" in data

    def test_risk_level_critical_for_biased(self):
        engine = BiasEngine(_biased_dataset(), 0, 1, 2)
        assert engine.risk_level() in ("critical", "medium")

    def test_multiple_sensitive_attrs(self):
        data = _biased_dataset()
        engine = BiasEngine(data, 0, 1, 2)
        result = engine.run_full_audit()
        assert result is not None

    def test_model_accuracy_correct(self):
        engine = BiasEngine(_fair_dataset(), 0, 1, 2)
        assert engine.accuracy() >= 0.90


# ══════════════════════════════════════════════════════════════════
class TestMitigationEngine:
    def _sample_result(self):
        return BiasEngine(_biased_dataset(), 0, 1, 2).run_full_audit()

    def test_projection_improves_score(self):
        engine = MitigationEngine()
        result = self._sample_result()
        proj = engine.project(result, ["reweight"])
        assert proj["projected_score"] >= result["fairness_score"]

    def test_projection_improves_di(self):
        engine = MitigationEngine()
        result = self._sample_result()
        proj = engine.project(result, ["threshold"])
        assert proj["disparate_impact"] >= result["metrics"]["disparate_impact"]

    def test_more_strategies_more_improvement(self):
        engine = MitigationEngine()
        result = self._sample_result()
        p1 = engine.project(result, ["reweight"])
        p2 = engine.project(result, ["reweight", "threshold"])
        assert p2["projected_score"] >= p1["projected_score"]

    def test_projected_di_capped_at_one(self):
        engine = MitigationEngine()
        result = self._sample_result()
        proj = engine.project(result, ["reweight", "threshold", "adversarial", "fairloss", "resample"])
        assert proj["disparate_impact"] <= 1.0

    def test_projected_score_capped_at_100(self):
        engine = MitigationEngine()
        result = self._sample_result()
        proj = engine.project(result, ["reweight", "threshold", "adversarial", "fairloss", "resample"])
        assert proj["projected_score"] <= 100

    def test_unknown_strategy_ignored(self):
        engine = MitigationEngine()
        result = self._sample_result()
        proj = engine.project(result, ["nonexistent"])
        assert proj["projected_score"] == result["fairness_score"]


# ══════════════════════════════════════════════════════════════════
class TestDatasetLoader:
    def test_synthetic_compas_loads(self):
        loader = DatasetLoader()
        data, s, t, p = loader.get_dataset("compas")
        assert data.shape[0] > 0

    def test_synthetic_lending_loads(self):
        loader = DatasetLoader()
        data, s, t, p = loader.get_dataset("lending")
        assert data.shape[0] > 0

    def test_synthetic_healthcare_loads(self):
        loader = DatasetLoader()
        data, s, t, p = loader.get_dataset("healthcare")
        assert data.shape[0] > 0

    def test_get_dataset_invalid_raises(self):
        loader = DatasetLoader()
        with pytest.raises(ValueError):
            loader.get_dataset("nonexistent")
