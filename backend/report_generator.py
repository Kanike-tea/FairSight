"""
Report Generator — Produces plain-English fairness audit reports.

Uses Google Gemini (Vertex AI) when available, falls back to a
structured template-based report when API key is not configured.
"""

import os
from typing import Any


class ReportGenerator:
    """Generates audit reports using Gemini or a fallback template."""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")

    def generate(self, audit_result: dict[str, Any]) -> str:
        """Generate a human-readable fairness audit report."""
        if self.api_key:
            return self._generate_with_gemini(audit_result)
        return self._generate_fallback(audit_result)

    def _generate_with_gemini(self, result: dict[str, Any]) -> str:
        """Call Google Gemini API for AI-powered report."""
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            prompt = self._build_prompt(result)
            
            # Dynamically discover available models that support content generation
            try:
                available_models = [
                    m.name for m in genai.list_models() 
                    if 'generateContent' in m.supported_generation_methods
                ]
                # Filter for Gemini models and sort (prefer 1.5-flash then 1.5-pro then others)
                gemini_models = [m for m in available_models if "gemini" in m.lower()]
                
                # Manual priority sorting
                priority = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro", "gemini-pro"]
                models_to_try = []
                
                for p in priority:
                    matches = [m for m in gemini_models if p in m]
                    if matches:
                        models_to_try.append(matches[0])
                
                # Add any others we found just in case
                for m in gemini_models:
                    if m not in models_to_try:
                        models_to_try.append(m)
                
                if not models_to_try:
                    models_to_try = ["gemini-1.5-flash", "gemini-pro"] # Absolute fallbacks
            except Exception:
                # If listing fails (e.g. permission issues), use a safe hardcoded list
                models_to_try = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]

            last_error = None
            for model_name in models_to_try:
                try:
                    # Some models come back as 'models/gemini-...' from list_models()
                    # GenerativeModel handles both prefixed and non-prefixed names
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt)
                    return response.text
                except Exception as e:
                    last_error = e
                    continue

            if last_error:
                raise last_error
            return "No response from any available Gemini models."
        except Exception as e:
            error_msg = str(e)
            if "503" in error_msg:
                error_msg = "Gemini service is currently overloaded. Using template report."
            elif "404" in error_msg:
                error_msg = "Requested Gemini model not found. Check project availability."
            elif "401" in error_msg or "403" in error_msg:
                error_msg = "Invalid Google API key. Please check your configuration."
            
            return self._generate_fallback(result) + f"\n\n[Status: {error_msg}]"

    def _build_prompt(self, result: dict[str, Any]) -> str:
        metrics = result.get("metrics", {})
        score = result.get("fairness_score", 0)
        risk = result.get("risk_level", "unknown")

        return f"""You are a fairness auditor. Generate a professional bias audit report.

Dataset: {result.get('dataset_id', 'Unknown')}
Sensitive Attributes: {result.get('sensitive_attrs', [])}
Fairness Score: {score}/100
Risk Level: {risk}

Metrics:
- Disparate Impact: {metrics.get('disparate_impact', 'N/A')} (threshold: ≥ 0.80)
- Demographic Parity Gap: {metrics.get('demographic_parity_diff', 'N/A')} (threshold: ≤ 0.05)
- Equalized Odds Diff: {metrics.get('equalized_odds_diff', 'N/A')} (threshold: ≤ 0.10)
- Model Accuracy: {metrics.get('model_accuracy', 'N/A')}

Flags: {result.get('flags', [])}

Write sections: Executive Summary, Key Findings, Risk Assessment,
Compliance Notes (EU AI Act, EEOC, ECOA), and Recommended Actions.
Use clear, non-technical language suitable for executives and regulators."""

    def _generate_fallback(self, result: dict[str, Any]) -> str:
        """Template-based report when Gemini is unavailable."""
        metrics = result.get("metrics", {})
        score = result.get("fairness_score", 0)
        risk = result.get("risk_level", "unknown")
        flags = result.get("flags", [])
        di = metrics.get("disparate_impact", 0)
        dp = metrics.get("demographic_parity_diff", 0)
        eo = metrics.get("equalized_odds_diff", 0)
        acc = metrics.get("model_accuracy", 0)

        violations = [f for f in flags if f.get("severity") == "critical"]

        report = f"""═══════════════════════════════════════════════
  FAIRSIGHT — AI FAIRNESS AUDIT REPORT
═══════════════════════════════════════════════

EXECUTIVE SUMMARY
─────────────────
Dataset: {result.get('dataset_id', 'Unknown')}
Sensitive Attributes: {', '.join(result.get('sensitive_attrs', []))}
Fairness Score: {score}/100
Risk Level: {risk.upper()}
Critical Violations: {len(violations)}

KEY FINDINGS
────────────
1. Disparate Impact: {di:.3f} {'✅ PASS' if di >= 0.80 else '❌ FAIL (< 0.80)'}
2. Demographic Parity Gap: {dp*100:.1f}% {'✅ PASS' if dp <= 0.05 else '❌ FAIL (> 5%)'}
3. Equalized Odds Diff: {eo*100:.1f}% {'✅ PASS' if eo <= 0.10 else '❌ FAIL (> 10%)'}
4. Model Accuracy: {acc*100:.1f}%

COMPLIANCE STATUS
─────────────────
• EEOC 4/5ths Rule: {'COMPLIANT' if di >= 0.80 else 'NON-COMPLIANT'}
• EU AI Act: {'Review recommended' if risk != 'low' else 'Low risk'}
• ECOA Fair Lending: {'Requires attention' if di < 0.80 else 'Acceptable'}

RECOMMENDED ACTIONS
───────────────────"""

        for flag in flags:
            report += f"\n• [{flag.get('severity', 'info').upper()}] {flag.get('recommendation', '')}"

        if not flags:
            report += "\n• No critical issues detected. Continue monitoring."

        report += "\n\n═══════════════════════════════════════════════"
        report += "\n  Generated by FairSight (Gemini unavailable — template report)"
        report += "\n═══════════════════════════════════════════════"

        return report
