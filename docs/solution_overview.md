# FairSight — Solution Overview

## Hackathon: Solution Challenge 2026 India — Build with AI
## Theme: Unbiased AI Decision

---

## Solution Summary

**FairSight** is an end-to-end AI Bias Detection and Fairness Auditing Platform that enables
organizations to detect, measure, flag, and fix bias in their AI systems — before those systems
impact real people.

Built on **Google Cloud** with **Vertex AI**, **Firebase**, and **Flutter**, FairSight makes
fairness auditing accessible to both technical and non-technical users through a clean dashboard,
plain-English AI reports, and a REST API that integrates into existing ML pipelines.

---

## How It Solves the Problem

### Step 1 — Upload Data or Connect a Model
Organizations upload a CSV dataset (ground truth + model predictions + demographic columns) or
connect via API. FairSight supports four pre-loaded real-world datasets (COMPAS, Adult Income,
Loan Approval, Healthcare Allocation) for immediate demos.

### Step 2 — Automatic Bias Detection
FairSight's Bias Engine computes four industry-standard fairness metrics per demographic group:

| Metric | What It Measures | Legal Threshold |
|--------|-----------------|-----------------|
| Disparate Impact (DI) | Ratio of positive outcomes between groups | ≥ 0.80 (4/5ths rule) |
| Demographic Parity | Gap in outcome rates between groups | ≤ 5% |
| Equalized Odds | Gap in false positive/negative rates | ≤ 10% |
| Individual Fairness | Similar people treated similarly (KNN) | ≥ 0.85 |

### Step 3 — Severity Flagging
Issues are automatically classified as Critical, Warning, or Info with specific references to
which metric failed, which groups are affected, and what the legal implications are.

### Step 4 — AI-Powered Plain-English Reports
Using **Google Gemini** (via Vertex AI), FairSight generates audit reports that non-technical
executives, legal teams, and regulators can understand. Reports include executive summary,
key findings, risk level, compliance notes (EU AI Act, EEOC, ECOA), and recommended actions.

### Step 5 — Mitigation Strategies
FairSight recommends and applies bias mitigation strategies:
- **Pre-processing:** Dataset reweighting, SMOTE resampling
- **In-processing:** Fairness loss constraints, adversarial debiasing
- **Post-processing:** Threshold calibration per demographic group

Each strategy shows projected fairness improvement vs. accuracy trade-off before applying.

### Step 6 — Audit Trail
Every audit is stored with full results, enabling organizations to demonstrate fairness
compliance over time — essential for EU AI Act and EEOC reporting.

---

## Google Technologies Used

| Technology | How FairSight Uses It |
|-----------|----------------------|
| **Google Cloud Run** | Hosts the FastAPI backend (serverless, auto-scaling) |
| **Vertex AI (Gemini)** | Generates plain-English AI fairness reports |
| **Firebase Firestore** | Stores audit jobs, results, and reports in real-time |
| **Firebase Authentication** | User authentication and organization management |
| **Firebase Hosting** | Hosts the Flutter web frontend |
| **Google Cloud Storage** | Stores uploaded datasets securely |
| **Cloud Tasks** | Async bias computation job queue |
| **BigQuery** | Analytics on audit history and fairness trends |
| **Flutter** | Cross-platform frontend (web + mobile) |
| **Google Cloud Build** | CI/CD pipeline for automated deployment |

---

## Architecture

```
Flutter Web/Mobile
      │
      ▼
Firebase Hosting + Authentication
      │
      ▼
Cloud Run (FastAPI) ──► Cloud Tasks Queue ──► Cloud Run Workers
      │                                              │
      ▼                                              ▼
Firebase Firestore                            Bias Engine
(jobs, results,                          (DI, DP, EO, Individual
 reports, users)                          Fairness computation)
      │                                              │
      ▼                                              ▼
Google Cloud Storage                        Vertex AI / Gemini
(uploaded datasets)                      (AI report generation)
      │
      ▼
BigQuery (audit analytics)
```

---

## Key Differentiators

### vs. Manual Audits
Manual fairness audits take weeks, cost thousands, and require external consultants.
FairSight produces a full audit in seconds at zero marginal cost.

### vs. AIF360 / Fairlearn
These libraries require PhD-level ML expertise to use. FairSight wraps the same math in
a UI anyone can use — HR manager, compliance officer, or C-suite executive.

### vs. No Solution (Status Quo)
36% of companies report negative business impact from AI bias. FairSight turns a
liability into a competitive advantage: demonstrable fairness compliance.

---

## Innovation

1. **Multi-metric fairness scoring** — single 0-100 score combining 4 metrics with
   weighted legal relevance, making it easy to compare models and track improvement.

2. **Gemini-powered audit reports** — structured prompting of Gemini produces reports
   calibrated to the specific dataset, domain (hiring vs. healthcare vs. lending), and
   risk level — not generic templates.

3. **Projected mitigation** — before applying any mitigation strategy, FairSight shows
   the expected impact on all four fairness metrics AND accuracy, letting teams make
   informed trade-off decisions.

4. **Pluggable architecture** — the Bias Engine is a standalone Python module usable
   as a library in any existing ML pipeline, not just through the FairSight UI.

---

## Impact Metrics

| Metric | Value |
|--------|-------|
| Audit time | < 30 seconds (vs. weeks manually) |
| Datasets supported | Any CSV with demographic + prediction columns |
| Domains covered | Hiring, lending, healthcare, criminal justice, and any custom domain |
| Fairness metrics | 4 industry-standard metrics per demographic group |
| Report languages | English (Gemini can generate in any language) |
| Target users | 10,000+ organizations in India deploying AI in high-stakes decisions |

---

## Real-World Validation

FairSight was tested on three publicly available real-world datasets:

1. **COMPAS (ProPublica)** — Detected DI of 0.63 for Race attribute, confirming the
   documented discrimination in US criminal justice AI.

2. **Adult Income (UCI)** — Detected 22% Demographic Parity gap for Gender, consistent
   with documented gender pay gap in income prediction models.

3. **Healthcare Allocation (synthetic, based on Obermeyer et al. 2019)** — Detected
   critical racial bias when using healthcare cost as a proxy for medical need.

---

## Compliance Coverage

| Framework | Coverage |
|-----------|----------|
| EU AI Act (2024) | High-risk AI audit requirements |
| EEOC Guidelines | 4/5ths adverse impact rule |
| Equal Credit Opportunity Act (ECOA) | Fair lending bias detection |
| India IT Act / DPDP Act | Data privacy in audit process |
