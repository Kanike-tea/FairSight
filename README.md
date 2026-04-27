<p align="center">
  <img src="https://img.shields.io/badge/build-passing-brightgreen" alt="Build">
  <img src="https://img.shields.io/badge/tests-68%20passed-brightgreen" alt="Tests">
  <img src="https://img.shields.io/badge/Python-3.12-blue" alt="Python">
  <img src="https://img.shields.io/badge/Flutter-3.x-blue" alt="Flutter">
  <img src="https://img.shields.io/badge/Firebase-enabled-orange" alt="Firebase">
  <img src="https://img.shields.io/badge/Vertex%20AI-Gemini-blue" alt="Vertex AI">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
</p>

# FairSight

### AI Bias Detection & Fairness Auditing Platform

> **Solution Challenge 2026 India — Build with AI**
> Theme: **Unbiased AI Decision** | Built with Google Technologies

**Live Demo:** [https://fairsight-af293.web.app/](https://fairsight-af293.web.app/)

---

## Problem Statement

Computer programs now make life-changing decisions — who gets a job, a bank loan, or medical
care. When these systems learn from flawed historical data, they repeat and amplify
discriminatory mistakes at massive scale.

**FairSight** gives organizations a clear, accessible way to inspect datasets and AI models
for hidden bias, measure fairness using industry-standard metrics, flag violations, and fix
them — before they impact real people.

> **Full problem statement →** [`docs/problem_statement.md`](docs/problem_statement.md)

---

## Solution

```
Upload CSV  →  Detect Bias  →  Flag Issues  →  AI Report  →  Mitigate & Fix
```

1. **Upload** a dataset with demographic columns + model predictions
2. **Detect** bias using 5 industry-standard fairness metrics
3. **Flag** violations with severity levels and legal references
4. **Generate** plain-English audit reports powered by **Google Gemini**
5. **Apply** mitigation strategies and preview projected improvement

> **Full solution overview →** [`docs/solution_overview.md`](docs/solution_overview.md)

---

## Key Innovation: Context-Aware Bias Detection

FairSight goes beyond raw metric comparison. It distinguishes between two fundamentally
different situations that naive tools conflate:

| Situation | Example | Verdict | Action |
|-----------|---------|---------|--------|
| **Dataset composition** | 80% men applied, 80% men hired | `proportional` | Fix recruitment pipeline |
| **Model discrimination** | Equal applicants, model favours one group | `biased` | Fix the model |

Raw Disparate Impact cannot tell these apart. FairSight uses **Conditional Disparate Impact**
(adjusted for each group's actual qualification rate) to give the correct verdict.

---

## Google Technologies Used

| Technology | Role in FairSight |
|-----------|-------------------|
| **Vertex AI (Gemini)** | Context-aware plain-English fairness report generation |
| **Cloud Run** | Serverless auto-scaling API backend |
| **Firebase Firestore** | Real-time job and results storage |
| **Firebase Auth** | User authentication & org management |
| **Firebase Hosting** | Frontend deployment |
| **Cloud Storage** | Encrypted dataset storage |
| **Cloud Tasks** | Async bias computation queue |
| **BigQuery** | Audit analytics and fairness trends |
| **Flutter** | Cross-platform frontend (web + mobile) |
| **Cloud Build** | CI/CD pipeline |

---

## Fairness Metrics

| Metric | Formula | Threshold | Legal Basis |
|--------|---------|-----------|-------------|
| Disparate Impact | P(Y=1\|unprivileged) / P(Y=1\|privileged) | ≥ 0.80 | EEOC 4/5ths Rule |
| Conditional DI | Prediction ratio adjusted for base rates | ≥ 0.80 | Context-aware EEOC |
| Demographic Parity | \|P(Y=1\|A=0) − P(Y=1\|A=1)\| | ≤ 5% | EU AI Act |
| Equalized Odds | max(\|FPR diff\|, \|FNR diff\|) | ≤ 10% | Fair Lending |
| Individual Fairness | KNN consistency score | ≥ 0.85 | General Fairness |

Weights are **domain-aware** — the composite score uses different emphasis depending on context:

| Domain | DI | DP | EO | IF |
|--------|----|----|----|----|
| Hiring | 45% | 25% | 20% | 10% |
| Healthcare | 25% | 20% | 45% | 10% |
| Criminal Justice | 30% | 20% | 40% | 10% |
| Financial | 35% | 25% | 30% | 10% |

---

## Architecture

```
Flutter Web/Mobile App
        │
Firebase Hosting + Auth
        │
Cloud Run (FastAPI)  ──────►  Cloud Tasks Queue
        │                            │
        │                     Cloud Run Workers
        │                       (Bias Engine)
        │                            │
Firebase Firestore ◄─────────────────┘
Cloud Storage (datasets)
        │
Vertex AI / Gemini  (report generation)
BigQuery            (audit analytics)
```

---

## Project Structure

```
FairSight/
├── lib/                              ← Flutter application source
│   ├── main.dart                       Entry point, Firebase init, routing
│   ├── firebase_options.dart           Firebase configuration (generated)
│   ├── screens/
│   │   ├── home_screen.dart            Landing page + dataset browser
│   │   ├── audit_screen.dart           Configure & launch bias audit
│   │   ├── results_screen.dart         Metrics, charts, flags, mitigation
│   │   ├── report_screen.dart          Gemini AI-generated audit report
│   │   ├── auto_scan_screen.dart       Automatic bias detection
│   │   └── external_audit_screen.dart  Model file & API endpoint audit
│   └── services/
│       ├── audit_service.dart          API + Firestore integration
│       └── auth_service.dart           Firebase Auth wrapper
│
├── backend/                          ← Python FastAPI backend
│   ├── main.py                         REST API endpoints
│   ├── bias_engine.py                  Core fairness math (5 metrics, domain weights)
│   ├── dataset_loader.py               4 real-world datasets + smart CSV upload
│   ├── auto_scan.py                    Automatic column detection and bias scanning
│   ├── model_auditor.py                Secure model file + API endpoint auditing
│   ├── report_generator.py             Gemini API integration + template fallback
│   ├── gemma_analyzer.py               Gemini column classifier and bias interpreter
│   ├── tasks.py                        Async audit jobs
│   ├── models.py                       SQLAlchemy ORM (SQLite / Postgres)
│   ├── requirements.txt                Python dependencies
│   ├── Dockerfile                      Cloud Run container
│   └── tests/
│       ├── __init__.py
│       ├── test_bias_engine.py         68 unit tests (bias engine + dataset loader)
│       └── test_api.py                 14 integration tests (all API endpoints)
│
├── docs/
│   ├── problem_statement.md
│   ├── solution_overview.md
│   └── submission_checklist.md
│
├── scripts/
│   ├── deploy_backend.sh               Cloud Run deploy
│   └── deploy_frontend.sh              Firebase Hosting deploy
│
├── pubspec.yaml                      ← Flutter project config
├── docker-compose.yml                ← Local dev environment
├── .env.example                      ← Environment variable template
└── README.md
```

---

## Quick Start (Local — No Cloud Needed)

### Prerequisites

- Python 3.12+
- Flutter 3.10+ (`flutter doctor`)
- A Google API key (optional — fallback reports work without it)

### 1. Clone & configure

```bash
git clone https://github.com/Kanike-tea/FairSight
cd FairSight
cp .env.example .env
# Optional: add your GOOGLE_API_KEY to .env for Gemini-powered reports
```

### 2. Run the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
python main.py
```

Backend live at **http://localhost:8080/api/docs**

### 3. Run the Flutter app

```bash
# From project root
flutter pub get
flutter run -d chrome
```

App opens in Chrome. It will connect to your local backend automatically.

---

## Running the Tests

### Test file location

The main test file belongs at:

```
backend/tests/test_bias_engine.py
```

The secondary API integration test file is at:

```
backend/tests/test_api.py
```

Both files must live inside `backend/tests/` alongside the `__init__.py` file
so pytest can discover them as a package.

### Run all backend tests

```bash
cd backend
pytest tests/ -v
```

Expected output:

```
tests/test_bias_engine.py::TestOriginalMetrics::test_returns_full_audit_structure PASSED
tests/test_bias_engine.py::TestOriginalMetrics::test_detects_bias_in_biased_dataset PASSED
...
tests/test_bias_engine.py::TestDataQualityOutput::test_low_confidence_groups_flagged PASSED
tests/test_api.py::TestHealth::test_health_returns_200 PASSED
...
tests/test_api.py::TestMitigation::test_mitigate_after_audit PASSED

82 passed in 12.4s
```

### Run only bias engine unit tests

```bash
cd backend
pytest tests/test_bias_engine.py -v
# 68 passed
```

### Run only API integration tests

```bash
cd backend
pytest tests/test_api.py -v
# 14 passed
```

### Run a specific test class

```bash
# Test the teammate's dataset composition scenario specifically
pytest tests/test_bias_engine.py::TestBaseRateAndContext -v

# Test individual fairness (KNN)
pytest tests/test_bias_engine.py::TestIndividualFairness -v

# Test the mitigation engine
pytest tests/test_bias_engine.py::TestMitigationEngineFixed -v
```

### What the tests cover

| Test Class | Tests | What it validates |
|-----------|-------|-------------------|
| `TestOriginalMetrics` | 12 | Core DI, DP, EO, accuracy, flags, group metrics |
| `TestIndividualFairness` | 6 | KNN consistency score, flag generation, weight inclusion |
| `TestIntersectionalBias` | 4 | Multi-attribute intersection detection |
| `TestMinimumSampleSize` | 4 | n<10 blocks audit, n<30 warns, n≥30 runs normally |
| `TestDomainAwareScoring` | 5 | Hiring/healthcare/criminal justice weight differences |
| `TestBaseRateAndContext` | 13 | Dataset composition vs model bias (teammate's scenario) |
| `TestEOExtremeBaseRate` | 2 | EO info flag for extreme base rate distributions |
| `TestMitigationEngineFixed` | 8 | Regression-to-threshold, accuracy cost, strategy stacking |
| `TestDatasetLoader` | 13 | Dataset generation, column detection, CSV upload safety |
| `TestDataQualityOutput` | 3 | data_quality fields in audit result |

### Flutter tests

```bash
# From project root
flutter test
```

---

## Manual Testing Guide

Use these scenarios to manually verify the tool before the demo.

### Scenario 1 — Genuine bias (COMPAS)

1. Open the app → click **Manual Audit**
2. Select **COMPAS Recidivism** dataset
3. Select sensitive attribute: `race`
4. Click **Run Bias Audit**

**Expected result:**
- Fairness score: ~35–45/100
- Risk level: Critical
- Bias verdict: `BIASED`
- Disparate Impact ~0.63 (fails)
- Conditional DI also fails (genuine model discrimination)
- Flags: Critical disparate impact, equalized odds violation

### Scenario 2 — Dataset composition, fair model (Adult Income)

1. Open the app → click **Manual Audit**
2. Select **Adult Income (UCI)** dataset
3. Select sensitive attribute: `gender`
4. Click **Run Bias Audit**

**Expected result:**
- Bias verdict: `PROPORTIONAL`
- Raw DI fails (different outcome rates)
- Conditional DI passes (model is proportional to base rates)
- Flag severity: `info` (not critical) — explains this is dataset composition
- Recommendation: fix recruitment pipeline, not the model

### Scenario 3 — Auto-detect on your own CSV

1. Open the app → click **Auto-Detect**
2. Upload `biased_dataset.csv` (included in repo root)
3. FairSight auto-detects columns with no configuration

**Expected result:**
- Sensitive attributes detected: `race`, `gender`
- Per-attribute heatmap showing bias severity for each
- Binarization warning for any continuous attributes split at median

### Scenario 4 — Generate AI report

After any audit completes:
1. Click **Generate AI Report** on the results screen
2. With `GOOGLE_API_KEY` set: Gemini generates a context-aware report
3. Without key: Structured template report shows all 5 metrics

**Verify the report includes:**
- The `bias_verdict` prominently stated
- Distinction between raw DI and conditional DI
- Separate recommendations for model fixes vs upstream fixes

### Scenario 5 — Mitigation projection

After running the COMPAS audit:
1. On Results screen, select strategies: `reweight` + `threshold`
2. Click **Apply Strategies**

**Expected result:**
- Projected score increases toward (but not past) 100
- Disparate Impact shown improving toward 0.80 threshold
- Accuracy cost shown (reweight ~1%, threshold ~3%)

### Scenario 6 — Model file audit (security validated)

1. Go to **Audit Model** → **Upload Model** tab
2. Upload a `.pkl` model file + a test CSV
3. FairSight runs predictions and auto-scans for bias

**Security note for demo:** Only joblib-serialized sklearn models are accepted.
Try uploading a `.txt` file renamed to `.pkl` — it will be rejected with a clear error.

---

## Demo Video Script (≤ 3 minutes)

Use this script when recording your submission video.

### 0:00–0:20 — Hook (Problem)

> "AI is making life-changing decisions about who gets hired, who gets a loan, who gets
> healthcare. But these systems can discriminate — invisibly and at scale. The COMPAS
> algorithm falsely flagged Black defendants as future criminals at nearly twice the rate of
> white defendants. FairSight was built to catch this — before deployment."

**Show:** The FairSight home screen loading with the four dataset cards visible.

---

### 0:20–0:45 — The Insight (Context-aware detection)

> "Most fairness tools just compare outcome rates between groups. But that's not enough.
> If 80% of job applicants are men and 80% get hired — that's not bias, that's math.
> FairSight distinguishes between dataset composition and genuine model discrimination
> using Conditional Disparate Impact."

**Show:** The two-column comparison in the results screen — raw DI vs conditional DI.

---

### 0:45–1:30 — Live Demo Part 1 (Genuine bias)

> "Let's start with COMPAS. I'll select the dataset, choose race as the sensitive
> attribute, and run the audit."

**Do:** Run the COMPAS audit. Show the results loading.

> "Fairness score: 38 out of 100. Risk: Critical. Bias verdict: BIASED.
> The raw Disparate Impact is 0.63 — well below the EEOC threshold of 0.80.
> And crucially, even after adjusting for each group's actual recidivism rate,
> the Conditional DI still fails. This is genuine model discrimination."

**Show:** The score hero card and metrics grid. Point to the flags section.

---

### 1:30–1:50 — Live Demo Part 2 (Dataset composition)

> "Now let's look at Adult Income. Same tool, different story."

**Do:** Run the Adult Income audit with gender attribute.

> "Raw DI fails — but the Conditional DI passes. The model is actually fair.
> The outcome gap exists because women have different income rates in this dataset —
> a dataset composition effect, not model bias. FairSight tells you: fix your
> recruitment pipeline, not the model."

**Show:** The `PROPORTIONAL` verdict and the info-severity flag.

---

### 1:50–2:10 — Auto-scan

> "You don't need to know which columns are sensitive. FairSight's Auto-Detect
> scans the entire dataset automatically."

**Do:** Upload `biased_dataset.csv` via Auto-Detect.

**Show:** The bias heatmap appearing with per-attribute scores.

---

### 2:10–2:30 — Mitigation

> "Once bias is detected, FairSight shows you how to fix it — with projected
> improvement before you apply anything."

**Do:** On COMPAS results, select `reweight` + `threshold`, click Apply.

> "Score projected to improve from 38 to 61. Disparate Impact moves from 0.63
> toward the 0.80 threshold. Accuracy cost: 4%. You decide the trade-off."

**Show:** The mitigation result card with projected score and accuracy cost.

---

### 2:30–2:50 — AI Report + Google Stack

> "Finally, one click generates a plain-English audit report via Google Gemini.
> Not for data scientists — for executives, lawyers, and regulators."

**Do:** Click Generate AI Report. Show the report loading.

> "FairSight runs on Google Cloud Run, stores audit history in Firebase Firestore,
> and uses Vertex AI for report generation. Flutter gives us a single codebase
> for web and mobile."

**Show:** The report screen. Then briefly show the Google tech stack slide or mention logos.

---

### 2:50–3:00 — Close

> "FairSight. AI bias is not inevitable. It is measurable, flaggable, and fixable."

**Show:** Home screen with the tagline visible.

---

## Deployment to Google Cloud

### Deploy API to Cloud Run

```bash
# Option 1: Use the deployment script
./scripts/deploy_backend.sh

# Option 2: Manual
cd backend
gcloud builds submit --tag gcr.io/YOUR_PROJECT/fairsight-api
gcloud run deploy fairsight-api \
  --image gcr.io/YOUR_PROJECT/fairsight-api \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=your-key,ALLOWED_ORIGINS=https://fairsight-af293.web.app
```

### Deploy Flutter frontend to Firebase Hosting

```bash
# Option 1: Use the deployment script
API_URL=https://your-cloud-run-url ./scripts/deploy_frontend.sh

# Option 2: Manual
flutter build web --dart-define="API_URL=https://your-cloud-run-url"
firebase deploy --only hosting
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/datasets` | List demo datasets |
| `POST` | `/api/upload` | Upload custom CSV |
| `POST` | `/api/audit-sync` | Run a bias audit (recommended) |
| `POST` | `/api/audit` | Start audit async (background thread) |
| `GET` | `/api/audit/{id}/status` | Poll async job status |
| `GET` | `/api/audit/{id}/result` | Get async audit results |
| `GET` | `/api/strategies` | List mitigation strategies |
| `POST` | `/api/mitigate` | Apply mitigation and get projection |
| `POST` | `/api/report` | Generate Gemini AI report |
| `POST` | `/api/auto-scan` | Auto-detect bias in uploaded CSV |
| `POST` | `/api/auto-scan-dataset` | Auto-scan a built-in dataset |
| `POST` | `/api/audit-model` | Upload model + test data for bias audit |
| `POST` | `/api/audit-endpoint` | Audit external model API endpoint |

Full interactive docs: **http://localhost:8080/api/docs**

---

## Real-World Validation

| Dataset | Attribute | Finding | Verdict |
|---------|-----------|---------|---------|
| COMPAS Recidivism (ProPublica) | Race | DI: 0.63, Conditional DI: fails | `biased` |
| Adult Income (UCI) | Gender | Raw DI fails, Conditional DI passes | `proportional` |
| Healthcare Allocation | Race | DI: 0.66, model ignores higher need | `biased` |
| Loan Approval (synthetic) | Race | DI: 0.69, extra discrimination on top of gap | `biased` |

---

## Test Results

```
backend/tests/test_bias_engine.py  — 68 tests PASSED
backend/tests/test_api.py          — 14 tests PASSED
══════════════════════════════════════════════════
  82 passed in ~12s
```

### Test coverage by component

```
bias_engine.py     — 68 tests: DI, DP, EO, Individual Fairness, Intersectional,
                               domain weights, base rate context, sample size,
                               mitigation projection
dataset_loader.py  — 13 tests: all 4 datasets, CSV column detection, security
test_api.py        — 14 tests: health, datasets, audit, mitigation, strategies
```

---

## Compliance Coverage

| Framework | How FairSight Addresses It |
|-----------|---------------------------|
| **EU AI Act (2024)** | Fairness audit for high-risk AI systems; DP ≤ 5% threshold |
| **EEOC Guidelines** | 4/5ths adverse impact rule (DI ≥ 0.80); conditional variant |
| **Equal Credit Opportunity Act** | Fair lending bias detection (EO ≤ 10%) |
| **India DPDP Act** | Data privacy — datasets processed locally, not stored externally |

---

## Security

| Concern | Fix Applied |
|---------|-------------|
| `pickle.loads()` RCE | Removed entirely — joblib only, with sklearn namespace validation |
| CORS misconfiguration | `allow_origins` set to explicit domain list via `ALLOWED_ORIGINS` env var |
| Model file size | 50MB hard limit before deserialization |
| Untrusted file extensions | Whitelist: `.pkl`, `.joblib` only |
| Identifier columns as sensitive attrs | `name`, `id`, `email`, `phone` excluded from auto-detection |

---

## Challenges Overcome

| Challenge | How We Solved It |
|-----------|-----------------|
| **Dataset composition vs model bias** | Conditional Disparate Impact compares prediction rate to each group's actual qualification rate — not just to other groups |
| **Multiple conflicting fairness definitions** | 5 metrics with domain-aware weighted composite score; UI explains which metric applies in which legal context |
| **Making ML fairness accessible** | Gemini-powered plain-English reports replace statistical jargon with actionable recommendations |
| **Intersectional bias invisible to single-attribute audits** | `intersectional_bias()` method detects disparities at group intersections (e.g. Black women vs white men) |
| **Real-time audit performance** | Synchronous `/api/audit-sync` endpoint for reliable single-request audits in Cloud Run |
| **No single "right" mitigation** | Projected improvement uses regression-to-threshold logic with per-strategy accuracy cost |

---

## Team

**Team FairSight** — Solution Challenge 2026 India

| Member | Role |
|--------|------|
| Member A | ML/Backend — Bias Engine, FastAPI, Cloud Run |
| Member B | Frontend/UX — Flutter, Firebase |
| Member C | Data & Research — Datasets, Metrics, Documentation |

---

## License

MIT License — free to use, modify, and deploy.

IP remains with the team as per Solution Challenge 2026 terms.
