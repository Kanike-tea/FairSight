"""
Report Generator — Produces plain-English fairness audit reports.

FIXES applied:
    - Gemini prompt now uses json.dumps() for flags (not raw Python repr)
    - Prompt includes all five metrics including individual_fairness
    - Prompt includes bias_verdict and dataset_context for context-aware reports
    - Template fallback includes individual fairness and conditional metrics
    - Domain context included in prompt for appropriate framing
"""

import os
import json
from typing import Any


class ReportGenerator:
    """Generates audit reports using Gemini or a structured fallback template."""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")

    def generate(self, audit_result: dict[str, Any]) -> str:
        normalized = self._normalize_result(audit_result)
        if self.api_key:
            return self._generate_with_gemini(normalized)
        return self._generate_fallback(normalized)

    def _normalize_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize auto-scan / model-audit results into the flat structure
        that the report template and Gemini prompt expect.

        Manual audit results already have flat keys (metrics, fairness_score, etc.)
        and pass through unchanged.

        Auto-scan / model-audit results nest data under 'summary' and
        'attribute_results' — this method extracts the most-biased attribute's
        data and promotes it to top-level keys.
        """
        # If result already has flat 'metrics' key, it's a manual audit — pass through
        if "metrics" in result and "attribute_results" not in result:
            return result

        # Auto-scan / model-audit structure detected
        summary = result.get("summary", {})
        attr_results = result.get("attribute_results", [])
        resolved = result.get("resolved_columns", {})

        if not attr_results:
            return result

        # Pick the most biased attribute (first in list — already sorted by score)
        primary = attr_results[0]

        normalized = dict(result)  # shallow copy — preserves all original keys
        normalized["fairness_score"] = summary.get("overall_fairness_score", 0)
        normalized["risk_level"] = summary.get("overall_risk_level", "unknown")
        normalized["metrics"] = primary.get("metrics", {})
        normalized["flags"] = primary.get("flags", [])
        normalized["dataset_context"] = primary.get("dataset_context", {})
        normalized["base_rates"] = primary.get("base_rates", {})
        normalized["domain"] = primary.get("domain", result.get("detected_domain", "default"))
        normalized["sensitive_attrs"] = resolved.get("sensitive_attributes", [])

        # Include a per-attribute summary for multi-attribute reports
        normalized["all_attributes"] = [
            {
                "attribute": a.get("attribute"),
                "fairness_score": a.get("fairness_score"),
                "risk_level": a.get("risk_level"),
                "is_biased": a.get("is_biased", False),
            }
            for a in attr_results
        ]

        return normalized

    def _generate_with_gemini(self, result: dict[str, Any]) -> str:
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            prompt = self._build_prompt(result)

            try:
                # Dynamic discovery with the new SDK
                available_models = [
                    m.name for m in client.models.list()
                    if 'generateContent' in (getattr(m, 'supported_actions', []) or getattr(m, 'supported_generation_methods', []))
                ]
                gemini_models = [m for m in available_models if "gemini" in m.lower()]
                priority = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro", "gemini-pro"]
                models_to_try = []
                for p in priority:
                    matches = [m for m in gemini_models if p in m]
                    if matches:
                        models_to_try.append(matches[0])
                for m in gemini_models:
                    if m not in models_to_try:
                        models_to_try.append(m)
                if not models_to_try:
                    models_to_try = ["gemini-1.5-flash", "gemini-1.0-pro"]
            except Exception:
                models_to_try = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"]

            last_error = None
            for model_name in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    return response.text
                except Exception as e:
                    print(f"Gemini Error ({model_name}): {e}")
                    last_error = e
                    continue

            raise last_error or Exception("No Gemini models available for this API key.")

        except Exception as e:
            print(f"Gemini Error (all models): {e}")
            error_msg = str(e)
            if "503" in error_msg:
                error_msg = "Gemini service overloaded. Using template report."
            elif "404" in error_msg:
                error_msg = "Gemini model not found."
            elif "401" in error_msg or "403" in error_msg:
                error_msg = "Invalid Google API key."
            return self._generate_fallback(result) + f"\n\n[Status: {error_msg}]"

    def _build_prompt(self, result: dict[str, Any]) -> str:
        metrics = result.get("metrics", {})
        overall_score = result.get("fairness_score", 0)
        overall_risk = result.get("risk_level", "unknown")
        primary_attr = result.get("primary_attribute", "Unknown")
        primary_score = result.get("primary_score", 0)
        flags = result.get("flags", [])
        context = result.get("dataset_context", {})
        base_rates = result.get("base_rates", {})
        domain = result.get("domain", "default")

        di = metrics.get("disparate_impact", 0)
        cdi = metrics.get("conditional_disparate_impact", di)
        dp = metrics.get("demographic_parity_diff", 0)
        eo = metrics.get("equalized_odds_diff", 0)
        if_score = metrics.get("individual_fairness", 1.0)
        acc = metrics.get("model_accuracy", 0)

        bias_verdict = context.get("bias_verdict", "unknown")
        bias_source = context.get("bias_source", "unknown")

        # Prepare context summaries for prompt
        base_rate_lines = []
        for group, info in base_rates.items():
            base_rate_lines.append(
                f"  Group {group}: {info.get('representation', 0)*100:.1f}% of applicants | "
                f"Base rate={info.get('base_rate', 0)*100:.1f}% | "
                f"Predicted={info.get('predicted_rate', 0)*100:.1f}% | "
                f"Ratio={info.get('prediction_ratio', 1.0):.3f}"
            )
        base_rate_summary = "\n".join(base_rate_lines) if base_rate_lines else "  Not available"
        
        flags_json = json.dumps(
            [{"severity": f.get("severity"), "metric": f.get("metric"), "message": f.get("message")}
             for f in flags],
            indent=2
        )

        domain_framing = {
            "hiring": "This AI system is used for recruitment. EEOC 4/5ths rule applies.",
            "criminal_justice": "This is a high-stakes legal AI system. Procedural justice is critical.",
            "healthcare": "This system allocates medical resources. Health equity is the priority.",
            "financial": "This is a financial/lending AI system. ECOA and fair lending laws apply.",
            "default": "This AI system makes consequential decisions affecting people's lives.",
        }.get(domain, "This AI system makes consequential decisions.")

        # Detect dataset-only mode
        is_dataset_only = (acc >= 0.999 and eo <= 0.001)
        dataset_only_note = ""
        if is_dataset_only:
            dataset_only_note = """
CRITICAL NOTE: This is a DATASET-ONLY analysis (no model was involved).
Model Accuracy = 100% and Equalized Odds = 0% confirm that target == prediction.
All findings reflect inherent dataset composition bias, NOT model behavior.
Do NOT use language like "the model discriminates" — instead say "the dataset contains disparities."
Any model trained on this data will likely inherit or amplify these disparities.
"""

        return f"""You are a fairness auditing expert. Generate a professional, context-aware bias audit report.

DOMAIN CONTEXT: {domain_framing}
{dataset_only_note}

DATA POINTS:
- Overall Audit Score: {overall_score}/100
- Overall Risk Level: {overall_risk.upper()}
- Primary Finding Attribute: {primary_attr}
- Primary Attribute Score: {primary_score}/100
- Disparate Impact: {di:.3f} (Conditional: {cdi:.3f})
- Demographic Parity Gap: {dp*100:.1f}%
- Equalized Odds Diff: {eo*100:.1f}%
- Individual Fairness: {if_score:.3f}
- Model Accuracy: {acc*100:.1f}%

IMPORTANT — BIAS VERDICT: {bias_verdict.upper()}
Root Cause: {bias_source}

GROUP BASE RATES:
{base_rate_summary}

FLAGS:
{flags_json}

INSTRUCTIONS:
1. Use the "Overall Audit Score" ({overall_score}) and "Overall Risk Level" ({overall_risk.upper()}) for the EXECUTIVE SUMMARY.
2. Clearly state that specific metrics (DI, DP) refer to the most-affected attribute ({primary_attr}).
3. Use these section headers: EXECUTIVE SUMMARY, KEY FINDINGS, ROOT CAUSE ANALYSIS, COMPLIANCE STATUS, RECOMMENDED ACTIONS.
4. Format findings into a clear table where possible.
5. Be objective and professional.
"""

    def _generate_fallback(self, result: dict[str, Any]) -> str:
        """Structured template report — context-aware and includes all five metrics."""
        metrics = result.get("metrics", {})
        score = result.get("fairness_score", 0)
        risk = result.get("risk_level", "unknown")
        flags = result.get("flags", [])
        context = result.get("dataset_context", {})
        base_rates = result.get("base_rates", {})
        domain = result.get("domain", "default")

        di = metrics.get("disparate_impact", 0)
        cdi = metrics.get("conditional_disparate_impact", di)
        dp = metrics.get("demographic_parity_diff", 0)
        cdp = metrics.get("conditional_demographic_parity_diff", dp)
        eo = metrics.get("equalized_odds_diff", 0)
        if_score = metrics.get("individual_fairness", 1.0)
        acc = metrics.get("model_accuracy", 0)

        bias_verdict = context.get("bias_verdict", "unknown")
        bias_source = context.get("bias_source", "unknown")
        verdict_explanation = context.get("verdict_explanation", "")
        is_imbalanced = context.get("is_imbalanced_dataset", False)
        violations = [f for f in flags if f.get("severity") == "critical"]

        verdict_icons = {
            "fair":          "FAIR",
            "proportional":  "PROPORTIONAL — Dataset Composition, Not Model Bias",
            "biased":        "BIASED — Genuine Model Discrimination Detected",
            "inconsistent":  "INCONSISTENT — Requires Investigation",
            "unknown":       "UNKNOWN",
        }
        verdict_label = verdict_icons.get(bias_verdict, "UNKNOWN")

        domain_labels = {
            "hiring": "Employment / Hiring",
            "criminal_justice": "Criminal Justice",
            "healthcare": "Healthcare Allocation",
            "financial": "Financial Services / Lending",
            "default": "General",
        }

        # Detect dataset-only mode (auto-detect with no model)
        is_dataset_only = (acc >= 0.999 and eo <= 0.001)

        report = f"""================================================================================
  FAIRSIGHT AI FAIRNESS AUDIT REPORT
================================================================================

EXECUTIVE SUMMARY
-----------------
Dataset:             {result.get('dataset_id', 'Unknown')}
Sensitive Attributes:{', '.join(result.get('sensitive_attrs', []))}
Domain:              {domain_labels.get(domain, domain)}
Fairness Score:      {score}/100
Risk Level:          {risk.upper()}
Critical Violations: {len(violations)}

BIAS VERDICT: {verdict_label}

{verdict_explanation}

KEY FINDINGS — {result.get('primary_attribute', 'Most Biased Attribute').upper()}
----------------------------
(Attribute Score: {result.get('primary_score', 0)}/100)

                                Raw       Cond.         Threshold   Status
"""
        if is_dataset_only:
            report += f"Disparate Impact:               {di:.3f}     N/A           >= 0.80       {'PASS' if di >= 0.80 else 'FAIL'}\n"
            report += f"Demographic Parity Gap:         {dp*100:.1f}%      N/A           <= 5.0%       {'PASS' if dp <= 0.05 else 'FAIL'}\n"
            report += f"Individual Fairness (KNN):      {if_score:.3f}        N/A           >= 0.85       {'PASS' if if_score >= 0.85 else 'FAIL'}\n"
        else:

            report += f"Disparate Impact:               {di:.3f}     {cdi:.3f}         >= 0.80     {'PASS' if di >= 0.80 else 'FAIL'} / {'PASS' if cdi >= 0.80 else 'FAIL'}\n"
            report += f"Demographic Parity Gap:         {dp*100:.1f}%      {cdp*100:.1f}%          <= 5.0%     {'PASS' if dp <= 0.05 else 'FAIL'} / {'PASS' if cdp <= 0.05 else 'FAIL'}\n"
            report += f"Equalized Odds Diff:            {eo*100:.1f}%         —              <= 10.0%    {'PASS' if eo <= 0.10 else 'FAIL'}\n"
            report += f"Individual Fairness (KNN):      {if_score:.3f}        —              >= 0.85     {'PASS' if if_score >= 0.85 else 'FAIL'}\n"
            report += f"Model Accuracy:                 {acc*100:.1f}%         —              —           —\n"

        if not is_dataset_only:
            report += "\nNote: Conditional metrics account for each group's actual qualification rate.\n"
            report += "      When they diverge from raw metrics, the gap reflects dataset composition.\n"
        else:
            report += "\nNote: This is a dataset-only scan. Conditional and model metrics are not applicable.\n"


        if base_rates:
            report += "\nGROUP BASE RATES\n"
            report += "-" * 16 + "\n"
            for group, info in base_rates.items():
                ratio = info.get("prediction_ratio", 1.0)
                ratio_ok = 0.85 <= ratio <= 1.15
                report += (
                    f"  Group {group}: {info.get('representation',0)*100:.0f}% of applicants | "
                    f"Qualified: {info.get('base_rate',0)*100:.1f}% | "
                    f"Predicted: {info.get('predicted_rate',0)*100:.1f}% | "
                    f"Ratio: {ratio:.2f} ({'Fair' if ratio_ok else 'Skewed'})\n"
                )

        report += "\nROOT CAUSE ANALYSIS\n"
        report += "-" * 20 + "\n"
        if bias_source == "dataset_composition":
            report += (
                "The disparity originates from the APPLICANT POOL, not the model.\n"
                "The model predicts proportionally to each group's actual qualification rate.\n"
                "This requires upstream intervention — not model-level fixes.\n"
            )
        elif bias_source == "model_discrimination":
            report += (
                "The model introduces bias BEYOND what dataset composition explains.\n"
                "Even accounting for each group's qualification rate, the model\n"
                "systematically under-predicts for disadvantaged groups.\n"
                "Direct model intervention is required.\n"
            )
        elif bias_verdict == "inconsistent" or (di < 0.80 or cdi < 0.80 or dp > 0.05 or eo > 0.10):
            report += (
                "INCONSISTENCY DETECTED between raw and conditional metrics.\n"
                f"Raw Disparate Impact ({di:.3f}) vs Conditional DI ({cdi:.3f}) diverge,\n"
                "indicating the model treats groups differently relative to their\n"
                "actual qualification rates. Further investigation is required to\n"
                "determine whether this stems from data imbalance or model bias.\n"
            )
        else:
            report += "No significant bias detected from dataset or model.\n"

        report += "\nCOMPLIANCE STATUS\n"
        report += "-" * 18 + "\n"
        eeoc_compliant = di >= 0.80 or (is_imbalanced and cdi >= 0.80)
        report += f"  EEOC 4/5ths Rule:    {'COMPLIANT' if eeoc_compliant else 'NON-COMPLIANT'}\n"
        report += f"  EU AI Act (DP):      {'COMPLIANT' if dp <= 0.05 else 'NON-COMPLIANT'}\n"
        report += f"  ECOA Fair Lending:   {'COMPLIANT' if di >= 0.80 else 'REVIEW REQUIRED'}\n"
        report += f"  Individual Fairness: {'COMPLIANT' if if_score >= 0.85 else 'NON-COMPLIANT'}\n"

        report += "\nRECOMMENDED ACTIONS\n"
        report += "-" * 20 + "\n"

        critical_flags = [f for f in flags if f.get("severity") == "critical"]
        warning_flags = [f for f in flags if f.get("severity") == "warning"]
        info_flags = [f for f in flags if f.get("severity") == "info"]

        for flag in critical_flags:
            report += f"  [CRITICAL] {flag.get('recommendation', '')}\n"
        for flag in warning_flags:
            report += f"  [WARNING]  {flag.get('recommendation', '')}\n"
        for flag in info_flags:
            report += f"  [INFO]     {flag.get('recommendation', '')}\n"

        if not flags:
            report += "  No critical issues detected. Continue monitoring.\n"

        if is_imbalanced and bias_source == "dataset_composition":
            report += "\n  UPSTREAM (Applicant Pool):\n"
            report += "  - Expand recruitment to reach underrepresented groups\n"
            report += "  - Audit application-stage barriers that may reduce representation\n"
            report += "  - Track applicant pool composition alongside model audit metrics\n"

        report += "\n  MONITORING (Always):\n"
        report += "  - Re-audit after any model update or retraining\n"
        report += "  - Set up automated fairness monitoring in production\n"
        report += "  - Track fairness metrics alongside accuracy in dashboards\n"

        report += "\n================================================================================\n"
        report += "  Generated by FairSight"
        if not self.api_key:
            report += " (Gemini unavailable — structured template report)"
        report += "\n================================================================================\n"

        return report
