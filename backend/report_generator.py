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
        if self.api_key:
            return self._generate_with_gemini(audit_result)
        return self._generate_fallback(audit_result)

    def _generate_with_gemini(self, result: dict[str, Any]) -> str:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            prompt = self._build_prompt(result)

            try:
                available_models = [
                    m.name for m in genai.list_models()
                    if "generateContent" in m.supported_generation_methods
                ]
                gemini_models = [m for m in available_models if "gemini" in m.lower()]
                priority = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro", "gemini-pro"]
                models_to_try = []
                for p in priority:
                    matches = [m for m in gemini_models if p in m]
                    if matches:
                        models_to_try.append(matches[0])
                for m in gemini_models:
                    if m not in models_to_try:
                        models_to_try.append(m)
                if not models_to_try:
                    models_to_try = ["gemini-1.5-flash", "gemini-pro"]
            except Exception:
                models_to_try = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]

            last_error = None
            for model_name in models_to_try:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt)
                    return response.text
                except Exception as e:
                    last_error = e
                    continue

            raise last_error or Exception("No models available")

        except Exception as e:
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
        score = result.get("fairness_score", 0)
        risk = result.get("risk_level", "unknown")
        context = result.get("dataset_context", {})
        base_rates = result.get("base_rates", {})
        domain = result.get("domain", "default")
        flags = result.get("flags", [])

        bias_verdict = context.get("bias_verdict", "unknown")
        bias_source = context.get("bias_source", "unknown")
        verdict_explanation = context.get("verdict_explanation", "")
        is_imbalanced = context.get("is_imbalanced_dataset", False)

        # Build base rate summary
        base_rate_lines = []
        for group, info in base_rates.items():
            base_rate_lines.append(
                f"  Group {group}: {info.get('representation', 0)*100:.1f}% of applicants | "
                f"Base rate={info.get('base_rate', 0)*100:.1f}% | "
                f"Predicted={info.get('predicted_rate', 0)*100:.1f}% | "
                f"Ratio={info.get('prediction_ratio', 1.0):.3f}"
            )
        base_rate_summary = "\n".join(base_rate_lines) if base_rate_lines else "  Not available"

        # FIXED: use json.dumps instead of raw Python repr
        flags_json = json.dumps(
            [{"severity": f.get("severity"), "metric": f.get("metric"), "message": f.get("message")}
             for f in flags],
            indent=2
        )

        domain_framing = {
            "hiring": "This is a hiring/employment AI system. EEOC guidelines apply.",
            "criminal_justice": "This is a criminal justice AI system. False positives (wrongful flagging) are especially harmful.",
            "healthcare": "This is a healthcare allocation AI system. False negatives (missed high-need patients) are life-or-death.",
            "financial": "This is a financial/lending AI system. ECOA and fair lending laws apply.",
            "default": "This AI system makes consequential decisions affecting people's lives.",
        }.get(domain, "This AI system makes consequential decisions.")

        return f"""You are a fairness auditing expert. Generate a professional, context-aware bias audit report.

DOMAIN CONTEXT: {domain_framing}

IMPORTANT — BIAS VERDICT: {bias_verdict.upper()}
This is the key finding. Before writing anything else, understand:
- "biased" = the MODEL is discriminating, intervention needed
- "proportional" = outcome gap exists but reflects dataset composition, NOT model bias
- "fair" = model passes all thresholds
- "inconsistent" = nuanced — model is inconsistent relative to base rates

Bias Source: {bias_source}
Explanation: {verdict_explanation}
Dataset Imbalanced: {is_imbalanced}

AUDIT SUMMARY:
Dataset: {result.get('dataset_id', 'Unknown')}
Sensitive Attributes: {result.get('sensitive_attrs', [])}
Fairness Score: {score}/100
Risk Level: {risk}

METRICS (raw = unadjusted, conditional = adjusted for base rates):
- Disparate Impact (raw):              {metrics.get('disparate_impact', 'N/A'):.3f} (threshold >= 0.80)
- Disparate Impact (conditional):      {metrics.get('conditional_disparate_impact', 'N/A'):.3f} (threshold >= 0.80)
- Demographic Parity Gap (raw):        {metrics.get('demographic_parity_diff', 'N/A'):.3f} (threshold <= 0.05)
- Demographic Parity Gap (conditional):{metrics.get('conditional_demographic_parity_diff', 'N/A'):.3f} (threshold <= 0.05)
- Equalized Odds Diff:                 {metrics.get('equalized_odds_diff', 'N/A'):.3f} (threshold <= 0.10)
- Individual Fairness (KNN):           {metrics.get('individual_fairness', 'N/A'):.3f} (threshold >= 0.85)
- Model Accuracy:                      {metrics.get('model_accuracy', 'N/A'):.3f}

GROUP BASE RATES:
{base_rate_summary}

FLAGS (JSON):
{flags_json}

Write a report with exactly these sections:
1. EXECUTIVE SUMMARY — State the bias_verdict plainly. One paragraph.
2. KEY FINDINGS — What each metric shows. Distinguish raw vs conditional metrics.
3. ROOT CAUSE ANALYSIS — Is this model bias or dataset composition? Be specific.
4. REAL-WORLD IMPACT — What harm could result if deployed? Tailor to the domain.
5. COMPLIANCE NOTES — Which regulations apply and whether thresholds are met.
6. RECOMMENDED ACTIONS — Separate:
   (a) Model-level fixes (if bias_verdict is "biased")
   (b) Upstream fixes (if bias_verdict is "proportional" — focus on applicant pool)
   (c) Monitoring recommendations (always)

Use plain English. Avoid jargon. Write for an executive or regulator, not a data scientist."""

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

KEY FINDINGS — FIVE METRICS
----------------------------
                                Raw       Conditional   Threshold   Status
Disparate Impact:               {di:.3f}     {cdi:.3f}         >= 0.80     {'PASS' if di >= 0.80 else 'FAIL'} / {'PASS' if cdi >= 0.80 else 'FAIL'}
Demographic Parity Gap:         {dp*100:.1f}%      {cdp*100:.1f}%          <= 5.0%     {'PASS' if dp <= 0.05 else 'FAIL'} / {'PASS' if cdp <= 0.05 else 'FAIL'}
Equalized Odds Diff:            {eo*100:.1f}%         —              <= 10.0%    {'PASS' if eo <= 0.10 else 'FAIL'}
Individual Fairness (KNN):      {if_score:.3f}        —              >= 0.85     {'PASS' if if_score >= 0.85 else 'FAIL'}
Model Accuracy:                 {acc*100:.1f}%         —              —           —

Note: Conditional metrics account for each group's actual qualification rate.
      When they diverge from raw metrics, the gap reflects dataset composition.
"""

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
