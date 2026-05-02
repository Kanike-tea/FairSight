<p align="center">
  <img src="https://img.shields.io/badge/build-passing-brightgreen?style=flat-square" alt="Build">
  <img src="https://img.shields.io/badge/tests-82%20passed-brightgreen?style=flat-square" alt="Tests">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flutter-3.x-02569B?style=flat-square&logo=flutter&logoColor=white" alt="Flutter">
  <img src="https://img.shields.io/badge/Firebase-enabled-FFCA28?style=flat-square&logo=firebase&logoColor=black" alt="Firebase">
  <img src="https://img.shields.io/badge/Gemini-Vertex%20AI-4285F4?style=flat-square&logo=google&logoColor=white" alt="Vertex AI">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License">
</p>

<h1 align="center">⚖️ FairSight</h1>
<h3 align="center">AI Bias Detection & Fairness Auditing Platform</h3>

<p align="center">
  <strong>Solution Challenge 2026 India — Build with AI</strong><br>
  Theme: <em>Unbiased AI Decision</em> &nbsp;|&nbsp; Built with Google Technologies
</p>

<p align="center">
  <a href="https://fairsight-af293.web.app/"><strong>🌐 Live Demo → fairsight-af293.web.app</strong></a>
</p>

---

## The Problem

Computer programs now make life-changing decisions — who gets a job, a bank loan, or medical care. When these systems learn from flawed historical data, they repeat and amplify discriminatory mistakes at massive scale.

The COMPAS recidivism algorithm falsely flagged Black defendants as future criminals at **nearly twice the rate** of white defendants. Hiring models trained on historical data routinely disadvantage women and minorities. Healthcare allocation systems underserve high-need populations.

**There is no accessible, end-to-end tool that lets non-experts audit these systems, understand *why* they are biased, and know exactly what to fix.**

> Full problem statement → [`docs/problem_statement.md`](docs/problem_statement.md)

---

## The Solution

```
Upload CSV  →  Detect Bias  →  Flag Issues  →  AI Report  →  Mitigate & Fix
```

1. **Upload** a dataset with demographic columns + model predictions (or pick one of 4 included real-world datasets)
2. **Detect** bias using 5 industry-standard fairness metrics with domain-aware scoring
3. **Flag** violations with severity levels, legal references, and clear explanations
4. **Generate** plain-English audit reports powered by **Google Gemini** — written for executives and regulators, not data scientists
5. **Apply** mitigation strategies and preview projected improvement *before* committing

> Full solution overview → [`docs/solution_overview.md`](docs/solution_overview.md)

---

## Key Innovation: Context-Aware Bias Detection

FairSight goes beyond raw metric comparison. It distinguishes between two fundamentally different situations that naive fairness tools conflate:

| Situation | Example | Verdict | Correct Action |
|-----------|---------|---------|----------------|
| **Dataset composition** | 80% men applied, 80% hired | `proportional` | Fix the recruitment pipeline |
| **Model discrimination** | Equal applicants, model favours one group | `biased` | Fix the model |

Raw Disparate Impact cannot tell these apart. FairSight uses **Conditional Disparate Impact** — adjusting each group's prediction rate by its actual qualification rate — to give the correct verdict and the correct recommendation.

---

## Google Technologies

| Technology | Role in FairSight |
|---|---|
| **Vertex AI (Gemini)** | Context-aware plain-English fairness report generation |
| **Cloud Run** | Serverless auto-scaling API backend |
| **Firebase Firestore** | Real-time audit job and results storage |
| **Firebase Auth** | User authentication & organisation management |
| **Firebase Hosting** | Flutter web frontend deployment |
| **Cloud Storage** | Encrypted dataset storage |
| **Cloud Tasks** | Async bias computation queue |
| **BigQuery** | Audit analytics and fairness trend tracking |
| **Flutter** | Cross-platform frontend (web + mobile, single codebase) |
| **Cloud Build** | CI/CD pipeline |

---

## Fairness Metrics

| Metric | Formula | Threshold | Legal Basis |
|--------|---------|-----------|-------------|
| Disparate Impact | P(Y=1\|unprivileged) / P(Y=1\|privileged) | ≥ 0.80 | EEOC 4/5ths Rule |
| Conditional DI | Prediction ratio adjusted for base rates | ≥ 0.80 | Context-aware EEOC |
| Demographic Parity | \|P(Y=1\|A=0) − P(Y=1\|A=1)\| | ≤ 5% | EU AI Act |
| Equalized Odds | max(\|FPR diff\|, \|FNR diff\|) | ≤ 10% | Fair Lending Act |
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
Flutter Web / Mobile App (Firebase Hosting)
          │
    Firebase Auth
          │
  Cloud Run (FastAPI)  ──────►  Cloud Tasks Queue
          │                            │
          │                     Cloud Run Workers
          │                       (Bias Engine)
          │                            │
  Firebase Firestore ◄─────────────────┘
  Cloud Storage (datasets)
          │
  Vertex AI / Gemini  ──  Report generation
  BigQuery            ──  Audit analytics
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
│   │   ├── auto_scan_screen.dart       Automatic bias detection + heatmap
│   │   └── external_audit_screen.dart  Model file & API endpoint audit
│   └── services/
│       ├── audit_service.dart          API + Firestore integration
│       └── auth_service.dart           Firebase Auth wrapper
│
├── backend/                          ← Python FastAPI backend
│   ├── main.py                         REST API (14 endpoints)
│   ├── bias_engine.py                  Core fairness math (5 metrics, domain weights)
│   ├── dataset_loader.py               4 real-world datasets + smart CSV upload
│   ├── auto_scan.py                    Automatic column detection & bias scanning
│   ├── model_auditor.py                Secure model file + API endpoint auditing
│   ├── report_generator.py             Gemini API integration + template fallback
│   ├── gemma_analyzer.py               Gemini column classifier & bias interpreter
│   ├── tasks.py                        Async audit jobs
│   ├── models.py                       SQLAlchemy ORM (SQLite / Postgres)
│   ├── requirements.txt                Python dependencies
│   ├── Dockerfile                      Cloud Run container definition
│   └── tests/
│       ├── test_bias_engine.py         68 unit tests (bias engine + dataset loader)
│       └── test_api.py                 14 integration tests (all API endpoints)
│
├── docs/
│   ├── problem_statement.md
│   ├── solution_overview.md
│   └── submission_checklist.md
│
├── scripts/
│   ├── deploy_backend.sh               Cloud Run deploy script
│   └── deploy_frontend.sh              Firebase Hosting deploy script
│
├── biased_dataset.csv                ← Sample dataset for auto-scan demo
├── pubspec.yaml                      ← Flutter project config
├── docker-compose.yml                ← Local dev environment
├── .env.example                      ← Environment variable template
└── README.md
```

---

## Quick Start (Local — No Cloud Needed)

### Prerequisites

- Python 3.12+
- Flutter 3.10+ (run `flutter doctor` to verify)
- A Google API key *(optional — structured template reports work without it)*

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
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
python main.py
```

Backend live at **http://localhost:8080/api/docs** (interactive Swagger UI)

### 3. Run the Flutter app

```bash
# From project root
flutter pub get
flutter run -d chrome
```

The app opens in Chrome and connects to your local backend automatically.

---

## Running the Tests

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
tests/test_api.py::TestHealth::test_health_returns_200 PASSED
...
tests/test_api.py::TestMitigation::test_mitigate_after_audit PASSED

82 passed in ~12s
```

### Run targeted test suites

```bash
# Bias engine unit tests only (68 tests)
pytest tests/test_bias_engine.py -v

# API integration tests only (14 tests)
pytest tests/test_api.py -v

# Specific test class
pytest tests/test_bias_engine.py::TestBaseRateAndContext -v   # Dataset composition scenario
pytest tests/test_bias_engine.py::TestIndividualFairness -v   # KNN individual fairness
pytest tests/test_bias_engine.py::TestMitigationEngineFixed -v # Mitigation engine
```

### Test coverage breakdown

| Test Class | Tests | What It Validates |
|---|---|---|
| `TestOriginalMetrics` | 12 | Core DI, DP, EO, accuracy, flags, group metrics |
| `TestIndividualFairness` | 6 | KNN consistency score, flag generation, weight inclusion |
| `TestIntersectionalBias` | 4 | Multi-attribute intersection detection |
| `TestMinimumSampleSize` | 4 | n<10 blocks audit, n<30 warns, n≥30 runs normally |
| `TestDomainAwareScoring` | 5 | Hiring/healthcare/criminal justice weight differences |
| `TestBaseRateAndContext` | 13 | Dataset composition vs model bias |
| `TestEOExtremeBaseRate` | 2 | EO info flag for extreme base rate distributions |
| `TestMitigationEngineFixed` | 8 | Regression-to-threshold, accuracy cost, strategy stacking |
| `TestDatasetLoader` | 13 | Dataset generation, column detection, CSV upload safety |
| `TestDataQualityOutput` | 3 | `data_quality` fields in audit result |
| `TestAPIIntegration` | 14 | All 14 REST endpoints, status codes, response schemas |

### Flutter widget tests

```bash
# From project root
flutter test
```

---

## Manual Testing Guide

### Scenario 1 — Genuine bias (COMPAS)

1. Open the app → **Manual Audit**
2. Select **COMPAS Recidivism** dataset, attribute: `race`
3. Click **Run Bias Audit**

**Expected:** Score ~35–45, Risk: Critical, Verdict: `BIASED`  
Raw DI ~0.63 fails. Conditional DI also fails — genuine model discrimination.

---

### Scenario 2 — Dataset composition, fair model (Adult Income)

1. Open the app → **Manual Audit**
2. Select **Adult Income (UCI)** dataset, attribute: `gender`
3. Click **Run Bias Audit**

**Expected:** Verdict: `PROPORTIONAL`  
Raw DI fails, Conditional DI passes. Recommendation: fix recruitment pipeline, not the model.

---

### Scenario 3 — Auto-detect on your own CSV

1. Open the app → **Auto-Detect**
2. Upload `biased_dataset.csv` (included in repo root)
3. No configuration needed — FairSight detects columns automatically

**Expected:** Sensitive attributes detected (`race`, `gender`), per-attribute heatmap, binarization warnings for continuous attributes.

---

### Scenario 4 — Generate AI report

After any audit:
1. Click **Generate AI Report** on the results screen
2. With `GOOGLE_API_KEY` set: Gemini generates a context-aware, plain-English report
3. Without key: Structured template report with all 5 metrics

**Verify:** Report states `bias_verdict` prominently, distinguishes raw DI vs conditional DI, and gives separate recommendations for model vs upstream fixes.

---

### Scenario 5 — Mitigation projection

After the COMPAS audit:
1. Select strategies: `reweight` + `threshold`
2. Click **Apply Strategies**

**Expected:** Projected score improvement toward threshold, accuracy cost shown per strategy (reweight ~1%, threshold ~3%).

---

### Scenario 6 — Model file audit (security validated)

1. Go to **Audit Model** → **Upload Model** tab
2. Upload a `.pkl` sklearn model + a test CSV
3. FairSight runs predictions and auto-scans for bias

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
| `POST` | `/api/audit-sync` | Run bias audit (synchronous, recommended) |
| `POST` | `/api/audit` | Start audit async (background thread) |
| `GET` | `/api/audit/{id}/status` | Poll async job status |
| `GET` | `/api/audit/{id}/result` | Get async audit results |
| `GET` | `/api/strategies` | List mitigation strategies |
| `POST` | `/api/mitigate` | Apply mitigation and get projected improvement |
| `POST` | `/api/report` | Generate Gemini AI report |
| `POST` | `/api/auto-scan` | Auto-detect bias in uploaded CSV |
| `POST` | `/api/auto-scan-dataset` | Auto-scan a built-in dataset |
| `POST` | `/api/audit-model` | Upload model file + test data for bias audit |
| `POST` | `/api/audit-endpoint` | Audit an external model API endpoint |

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

## Test Summary

```
backend/tests/test_bias_engine.py  —  68 tests  PASSED
backend/tests/test_api.py          —  14 tests  PASSED
══════════════════════════════════════════════════════
  82 passed in ~12s
```

```
bias_engine.py     — DI, DP, EO, Individual Fairness, Intersectional bias,
                     domain weights, base rate context, sample size guards,
                     mitigation projection
dataset_loader.py  — All 4 datasets, CSV column detection, upload security
test_api.py        — Health, datasets, audit, mitigation, strategies, reports
```

---

## Deployment

### Deploy API to Cloud Run

```bash
# Option 1: Script
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
# Option 1: Script
API_URL=https://your-cloud-run-url ./scripts/deploy_frontend.sh

# Option 2: Manual
flutter build web --dart-define="API_URL=https://your-cloud-run-url"
firebase deploy --only hosting
```

---

## Compliance Coverage

| Framework | How FairSight Addresses It |
|---|---|
| **EU AI Act (2024)** | Fairness audit for high-risk AI systems; Demographic Parity ≤ 5% threshold |
| **EEOC Guidelines** | 4/5ths adverse impact rule (DI ≥ 0.80); conditional variant for context |
| **Equal Credit Opportunity Act** | Fair lending bias detection (Equalized Odds ≤ 10%) |
| **India DPDP Act** | Datasets processed locally, not stored externally |

---

## Security

| Concern | Control Applied |
|---|---|
| `pickle.loads()` RCE | Removed entirely — joblib only, with sklearn namespace validation |
| CORS misconfiguration | `allow_origins` set to explicit domain list via `ALLOWED_ORIGINS` env var |
| Oversized model files | 50 MB hard limit enforced before deserialization |
| Untrusted file extensions | Whitelist: `.pkl`, `.joblib` only |
| PII columns as sensitive attrs | `name`, `id`, `email`, `phone` excluded from auto-detection |

---

## Challenges Overcome

| Challenge | Solution |
|---|---|
| **Dataset composition vs model bias** | Conditional Disparate Impact compares each group's prediction rate to its own qualification rate — not just to other groups |
| **Multiple conflicting fairness definitions** | 5 metrics with domain-aware weighted composite score; UI explains which metric applies in which legal context |
| **Making ML fairness accessible** | Gemini-powered plain-English reports replace statistical jargon with actionable recommendations |
| **Intersectional bias invisible to single-attribute audits** | `intersectional_bias()` detects disparities at group intersections (e.g. Black women vs white men) |
| **Real-time audit performance on Cloud Run** | Synchronous `/api/audit-sync` endpoint for reliable single-request audits without polling |
| **No single "right" mitigation** | Projected improvement uses regression-to-threshold logic with per-strategy accuracy cost, letting users choose the trade-off |

---

## License

MIT License — free to use, modify, and deploy.

IP remains with the team as per Solution Challenge 2026 India terms.
