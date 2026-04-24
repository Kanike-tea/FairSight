"""
Gemma Analyzer — Gemma 4 powered bias intelligence.

Uses Google's Gemma 4 model (via Google AI / Gemini API) to:
    1. Intelligently classify dataset columns by role
    2. Interpret bias findings in plain English
    3. Generate targeted mitigation recommendations
    4. Assess real-world harm potential
"""

import os
import json
from typing import Any

from google import genai


# ── Gemma 4 model configuration ──────────────────────────────────

_API_KEY = os.getenv("GOOGLE_API_KEY")
_MODEL_NAME = "gemma-4-27b-it"  # Gemma 4 27B Instruct (via Gemini API)

# Fallback chain: try Gemma 4 → Gemini 2.5 Flash
_FALLBACK_MODELS = ["gemma-4-4b-it", "gemini-2.5-flash"]


def _generate_content(prompt: str) -> Any:
    """Generate content using Gemma 4 model with fallback."""
    if not _API_KEY:
        raise RuntimeError("GOOGLE_API_KEY not set")
    client = genai.Client(api_key=_API_KEY)

    # Try primary model first, then fallbacks
    last_error = None
    for model_name in [_MODEL_NAME] + _FALLBACK_MODELS:
        try:
            return client.models.generate_content(
                model=model_name,
                contents=prompt
            )
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"No Gemma/Gemini model available. Last error: {last_error}")


class GemmaColumnClassifier:
    """
    Uses Gemma 4 to intelligently classify dataset columns.

    Much smarter than regex heuristics — understands context,
    domain-specific terminology, and ambiguous column names.
    """

    def classify(self, column_names: list[str], sample_values: dict[str, list]) -> dict[str, Any]:
        """
        Ask Gemma 4 to classify columns by their likely role.

        Args:
            column_names: List of column names from the dataset.
            sample_values: Dict mapping column name → list of sample values.

        Returns:
            Classification result with sensitive, target, prediction, feature lists.
        """
        # Build a concise representation of the data
        col_info = []
        for col in column_names:
            samples = sample_values.get(col, [])
            sample_str = str(samples[:5]) if samples else "[]"
            col_info.append(f"  - {col}: {sample_str}")

        prompt = f"""You are a fairness auditing AI. Analyze these dataset columns and classify each one.

COLUMNS AND SAMPLE VALUES:
{chr(10).join(col_info)}

Classify EACH column into exactly ONE of these roles:
- "sensitive": Protected/demographic attributes (race, gender, age, religion, disability, etc.)
- "target": Ground-truth label or outcome variable (what is being predicted)
- "prediction": Model prediction or score column
- "feature": Regular feature used for prediction

IMPORTANT: Look at both the column NAME and the SAMPLE VALUES to make your determination.
- Low-cardinality columns with demographic-sounding names → sensitive
- Binary columns named like "approved", "hired", "label" → target
- Columns named like "predicted", "score", "prob" → prediction

Respond ONLY with valid JSON in this exact format:
{{
  "sensitive": ["col1", "col2"],
  "target": ["col3"],
  "prediction": ["col4"],
  "feature": ["col5", "col6"],
  "reasoning": "Brief explanation of why each sensitive attribute was chosen"
}}"""

        try:
            response = _generate_content(prompt)
            text = response.text.strip()

            # Extract JSON from response
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            result = json.loads(text)

            # Validate structure
            for key in ["sensitive", "target", "prediction", "feature"]:
                if key not in result:
                    result[key] = []

            result["source"] = "gemma4"
            return result

        except Exception as e:
            return {
                "sensitive": [],
                "target": [],
                "prediction": [],
                "feature": column_names,
                "source": "fallback",
                "error": str(e),
            }


class GemmaBiasInterpreter:
    """
    Uses Gemma 4 to interpret bias findings in plain English.

    Transforms raw metrics into actionable, human-readable insights
    with real-world harm assessment and regulatory context.
    """

    def interpret(self, scan_result: dict[str, Any]) -> dict[str, Any]:
        """
        Generate Gemma 4 powered interpretation of auto-scan results.

        Args:
            scan_result: Full output from AutoBiasScanner.scan()

        Returns:
            Enhanced result with AI-powered interpretation.
        """
        summary = scan_result.get("summary", {})
        attributes = scan_result.get("attribute_results", [])

        # Build a concise metrics summary for Gemma
        attr_summaries = []
        for attr in attributes[:5]:  # Limit to top 5
            if attr.get("error"):
                continue
            metrics = attr.get("metrics", {})
            attr_summaries.append(
                f"- {attr['attribute']}: "
                f"DI={metrics.get('disparate_impact', 0):.3f}, "
                f"DP={metrics.get('demographic_parity_diff', 0):.3f}, "
                f"EO={metrics.get('equalized_odds_diff', 0):.3f}, "
                f"Score={attr.get('fairness_score', 0)}/100, "
                f"Risk={attr.get('risk_level', 'unknown')}"
            )

        prompt = f"""You are a fairness auditing AI expert. Analyze these bias detection results and provide actionable insights.

OVERALL: Fairness Score = {summary.get('overall_fairness_score', 0)}/100, Risk = {summary.get('overall_risk_level', 'unknown')}
Biased attributes: {summary.get('biased_attributes_found', 0)} of {summary.get('total_attributes_scanned', 0)}

PER-ATTRIBUTE METRICS:
{chr(10).join(attr_summaries) if attr_summaries else "No attributes analyzed"}

Metric thresholds:
- Disparate Impact (DI): >= 0.80 is fair (EEOC 4/5ths rule)
- Demographic Parity Diff (DP): <= 0.05 is fair (EU AI Act)
- Equalized Odds Diff (EO): <= 0.10 is fair (Fair Lending)

Respond ONLY with valid JSON:
{{
  "overall_interpretation": "2-3 sentence plain-English summary of the bias findings",
  "harm_assessment": "What real-world harm could this bias cause?",
  "regulatory_risk": "Which regulations might be violated? (EU AI Act, EEOC, ECOA, etc.)",
  "attribute_insights": [
    {{
      "attribute": "column_name",
      "finding": "What the bias means for this attribute",
      "severity": "critical/warning/low",
      "action": "Specific recommended action"
    }}
  ],
  "top_recommendation": "The single most important thing to fix first"
}}"""

        try:
            response = _generate_content(prompt)
            text = response.text.strip()

            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            interpretation = json.loads(text)
            interpretation["source"] = "gemma4"
            return interpretation

        except Exception as e:
            return self._fallback_interpretation(scan_result, str(e))

    def _fallback_interpretation(self, scan_result: dict, error: str) -> dict:
        """Template-based fallback when Gemma is unavailable."""
        summary = scan_result.get("summary", {})
        score = summary.get("overall_fairness_score", 0)
        risk = summary.get("overall_risk_level", "unknown")
        biased = summary.get("biased_attributes_found", 0)

        return {
            "overall_interpretation": (
                f"The dataset shows {'significant' if score < 40 else 'moderate' if score < 65 else 'minimal'} "
                f"bias with a fairness score of {score}/100. "
                f"{biased} attribute(s) were flagged as biased."
            ),
            "harm_assessment": (
                "Biased outcomes may disproportionately affect protected groups, "
                "leading to unfair denial of services or opportunities."
            ),
            "regulatory_risk": (
                f"{'HIGH — Likely violates EEOC 4/5ths rule and EU AI Act high-risk thresholds.' if score < 40 else 'MODERATE — Review recommended for compliance.' if score < 65 else 'LOW — Within acceptable thresholds.'}"
            ),
            "attribute_insights": [],
            "top_recommendation": (
                "Apply data reweighting and threshold calibration to the most biased attribute."
            ),
            "source": "fallback",
            "error": error,
        }
