<p align="center">
  <img src="https://img.shields.io/badge/build-passing-brightgreen" alt="Build">
  <img src="https://img.shields.io/badge/tests-37%20passed-brightgreen" alt="Tests">
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
2. **Detect** bias using 4 industry-standard fairness metrics
3. **Flag** violations with severity levels and legal references
4. **Generate** plain-English audit reports powered by **Google Gemini**
5. **Apply** mitigation strategies and preview projected improvement

> **Full solution overview →** [`docs/solution_overview.md`](docs/solution_overview.md)

---

## Google Technologies Used

| Technology | Role in FairSight |
|-----------|-------------------|
| **Vertex AI (Gemini)** | AI-powered plain-English fairness report generation |
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
| Demographic Parity | \|P(Y=1\|A=0) − P(Y=1\|A=1)\| | ≤ 5% | EU AI Act |
| Equalized Odds | max(\|FPR diff\|, \|FNR diff\|) | ≤ 10% | Fair Lending |
| Individual Fairness | KNN consistency score | ≥ 0.85 | General Fairness |

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
├── lib/                          ← Flutter application source
│   ├── main.dart                   Entry point, Firebase init, routing
│   ├── firebase_options.dart       Firebase configuration (generated)
│   ├── screens/
│   │   ├── home_screen.dart        Landing page + dataset browser
│   │   ├── audit_screen.dart       Configure & launch bias audit
│   │   ├── results_screen.dart     Metrics, charts, flags, mitigation
│   │   └── report_screen.dart      Gemini AI-generated audit report
│   └── services/
│       ├── audit_service.dart      API + Firestore integration
│       └── auth_service.dart       Firebase Auth wrapper
├── test/                         ← Flutter widget tests
│   └── widget_test.dart
├── backend/                      ← Python FastAPI backend
│   ├── main.py                     10 REST endpoints
│   ├── bias_engine.py              Core fairness math (DI, DP, EO, IF)
│   ├── dataset_loader.py           4 real-world datasets + CSV upload
│   ├── models.py                   SQLAlchemy ORM (SQLite / Postgres)
│   ├── tasks.py                    Async audit jobs
│   ├── report_generator.py         Gemini API integration + fallback
│   ├── requirements.txt            Python dependencies
│   ├── Dockerfile                  Cloud Run container
│   └── tests/
│       ├── test_bias_engine.py     23 unit tests
│       └── test_api.py             14 integration tests
├── docs/                         ← Hackathon documentation
│   ├── problem_statement.md
│   ├── solution_overview.md
│   └── submission_checklist.md
├── scripts/                      ← Deployment automation
│   ├── deploy_backend.sh           Cloud Run deploy
│   └── deploy_frontend.sh          Firebase Hosting deploy
├── pubspec.yaml                  ← Flutter project config
├── analysis_options.yaml         ← Dart linter rules
├── docker-compose.yml            ← Local dev environment
├── .env.example                  ← Environment variable template
├── .gitignore
├── LICENSE                       ← MIT License
└── README.md                     ← This file
```

---

## Quick Start (Local — No Cloud Needed)

### Prerequisites

- Python 3.12+
- Flutter 3.10+ (`flutter doctor`)
- A Google API key (optional — fallback reports work without it)

### 1. Clone & set up environment

```bash
git clone https://github.com/Kanike-tea/FairSight
cd fairsight
cp .env.example .env
# Optional: add GOOGLE_API_KEY to .env for Gemini reports
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

API live at **http://localhost:8000/api/docs**

### 3. Run the Flutter app

```bash
# From project root
flutter pub get
flutter run -d chrome
```

App opens in Chrome at **http://localhost:PORT**

### 4. Run the tests

```bash
# Backend tests (37 total)
cd backend && pytest tests/ -v

# Flutter tests
cd .. && flutter test
```

---

## Deploy to Google Cloud (Production)

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
  --set-env-vars GOOGLE_API_KEY=your-key
```

### Deploy Flutter frontend to Firebase Hosting

```bash
# Option 1: Use the deployment script
API_URL=https://your-cloud-run-url ./scripts/deploy_frontend.sh

# Option 2: Manual
flutter build web --dart-define="API_URL=https://your-cloud-run-url"
firebase init hosting
firebase deploy
```

### Set up Firestore

```bash
firebase init firestore
# Collections created automatically on first audit run
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/datasets` | List demo datasets |
| `POST` | `/api/upload` | Upload custom CSV |
| `POST` | `/api/audit` | Start a bias audit (async) |
| `GET` | `/api/audit/{id}/status` | Poll job status |
| `GET` | `/api/audit/{id}/result` | Get full results |
| `GET` | `/api/strategies` | List mitigation strategies |
| `POST` | `/api/mitigate` | Apply mitigation |
| `POST` | `/api/report` | Generate AI report |

Full interactive docs: **http://localhost:8000/api/docs**

---

## Real-World Validation

| Dataset | Attribute | Finding | Result |
|---------|-----------|---------|--------|
| COMPAS Recidivism (ProPublica) | Race | DI: 0.63 | Legal violation |
| Adult Income (UCI) | Gender | Parity gap: 22% | Significant bias |
| Healthcare Allocation | Race + SES | DI: 0.66 | Critical bias |
| Loan Approval (synthetic) | Race + Gender | DI: 0.69 | High risk |

---

## Test Results

```
backend/tests/test_bias_engine.py  — 23 tests PASSED
backend/tests/test_api.py          — 14 tests PASSED
═══════════════════════════════════════════════
  37 passed in 9.43s
```

---

## Compliance Coverage

| Framework | How FairSight Addresses It |
|-----------|---------------------------|
| **EU AI Act (2024)** | Fairness audit for high-risk AI systems |
| **EEOC Guidelines** | 4/5ths adverse impact rule (DI ≥ 0.80) |
| **Equal Credit Opportunity Act** | Fair lending bias detection |
| **India DPDP Act** | Data privacy — datasets processed locally |

---

## Challenges Overcome

| Challenge | How We Solved It |
|-----------|-----------------|
| **Multiple conflicting fairness definitions** | Implemented 4 metrics with weighted composite score; UI explains which metric applies in which legal context |
| **Making ML fairness accessible to non-technical users** | Gemini-powered plain-English reports replace statistical jargon with actionable recommendations |
| **Real-time audit performance** | Async job architecture (threading → Cloud Tasks) delivers results in < 30 seconds |
| **No single "right" mitigation** | Projected improvement preview lets teams compare trade-offs before applying any strategy |
| **Cross-platform accessibility** | Flutter enables single codebase for web + mobile; Firebase provides real-time sync |

---

## Team

**Team FairSight** — Solution Challenge 2026 India

| Member | Role |
|--------|------|
| Member A | ML/Backend — Bias Engine, FastAPI, Cloud Run |
| Member B | Frontend/UX — Flutter, React, Firebase |
| Member C | Data & Research — Datasets, Metrics, Documentation |

---

## License

MIT License — free to use, modify, and deploy.

IP remains with the team as per Solution Challenge 2026 terms.
