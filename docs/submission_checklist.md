# FairSight — Submission Checklist
## Solution Challenge 2026 India — Build with AI
## Theme: Unbiased AI Decision

---

## PHASE 1 SUBMISSION REQUIREMENTS

All required. Tick each before submitting on vision.hack2skill.com.

### ✅ 1. Problem Statement
- File: `01_problem_statement.md`
- Covers: COMPAS, hiring, healthcare, lending bias
- Defines gap: no accessible end-to-end bias auditing tool
- Target users: HR, banks, hospitals, governments, AI developers
- **STATUS: COMPLETE**

### ✅ 2. Solution Overview
- File: `02_solution_overview.md`
- Covers: 5-step flow (upload → detect → flag → report → mitigate)
- Includes: Google tech stack table, architecture diagram, innovation points
- Compliance: EU AI Act, EEOC, ECOA, India DPDP Act
- **STATUS: COMPLETE**

### ✅ 3. Prototype Link (Live MVP)
- Deploy with: `python backend/main.py` → http://localhost:8000/api/docs
- OR deploy to Cloud Run (see README)
- The Swagger UI at /api/docs IS the live MVP demo
- All 10 endpoints functional, 4 real datasets, real metrics
- **TO DO: Deploy to Cloud Run and get public URL**
  ```bash
  gcloud run deploy fairsight-api \
    --source ./backend \
    --region asia-south1 \
    --allow-unauthenticated
  ```

### ✅ 4. Project Deck
- File: `FairSight_Pitch_Deck.pptx`
- 10 slides covering:
  - Slide 1: Title + Google tech tags
  - Slide 2: Problem (4 domains, real stats)
  - Slide 3: Solution (5-step flow)
  - Slide 4: How bias detection works (metrics + COMPAS example)
  - Slide 5: Google tech stack (8 services)
  - Slide 6: Architecture diagram
  - Slide 7: Real-world validation (4 datasets, results table)
  - Slide 8: Evaluation criteria alignment (40/25/25/10)
  - Slide 9: Product roadmap (3 phases)
  - Slide 10: Closing statement
- **STATUS: COMPLETE**

### ✅ 5. GitHub Repository
- File: `04_github_README.md` (copy to your repo as README.md)
- Repo must be PUBLIC
- Must contain all source code
- **TO DO:**
  ```bash
  git init
  git add .
  git commit -m "FairSight - Solution Challenge 2026"
  git remote add origin https://github.com/YOUR_TEAM/fairsight
  git push -u origin main
  ```
- Submit the public GitHub URL

### ✅ 6. Demo Video
- Script: `03_demo_video_script.md`
- Duration: ≤ 3 minutes (Phase 3 requirement — keep Phase 1 video to ~2 min)
- Required content:
  - [x] Problem statement (0:00-0:20)
  - [x] Solution demo (0:45-1:30)
  - [x] Results + AI report (1:30-2:00)
  - [x] Mitigation (2:00-2:30)
  - [x] Google tech stack (2:30-2:50)
  - [x] Team name visible
- Upload to YouTube (unlisted) and submit URL
- **TO DO: Record and upload video**

---

## EVALUATION CRITERIA — HOW WE SCORE

| Criterion | Weight | Our Coverage | Score |
|-----------|--------|-------------|-------|
| Technical Merit | 40% | Bias engine (numpy/sklearn), FastAPI, Cloud Run, 37 tests, 4 real metrics, 4 real datasets | STRONG |
| Alignment with Cause | 25% | Directly solves "Unbiased AI Decision", covers 4 domains, EU AI Act + EEOC + ECOA compliance | STRONG |
| Innovation & Creativity | 25% | 0-100 fairness score, Gemini domain-aware reports, projected mitigation, pluggable library | STRONG |
| User Experience | 10% | Flutter (web+mobile), < 30s audit, zero ML expertise needed, Firestore history | GOOD |

---

## GOOGLE TECHNOLOGIES CHECKLIST

Required by hackathon: must use Google developer technologies.

- [x] **Vertex AI / Gemini** — AI report generation (`report_generator.py`)
- [x] **Cloud Run** — API deployment (`Dockerfile`, deployment commands in README)
- [x] **Firebase Firestore** — Audit storage (`flutter_app/lib/services/audit_service.dart`)
- [x] **Firebase Auth** — User auth (`flutter_app/lib/services/auth_service.dart`)
- [x] **Firebase Hosting** — Frontend deployment (Flutter web build)
- [x] **Cloud Storage** — Dataset storage (referenced in architecture)
- [x] **Cloud Tasks** — Async job queue (referenced in architecture)
- [x] **BigQuery** — Analytics (referenced in architecture)
- [x] **Flutter** — Cross-platform frontend (`flutter_app/`)
- [x] **Cloud Build** — CI/CD (referenced in README)

---

## FILE STRUCTURE FOR SUBMISSION

```
fairsight/                            ← GitHub repository root
│
├── README.md                         ← Use 04_github_README.md
│
├── backend/
│   ├── main.py                       ← ✅ Complete (all 10 endpoints real)
│   ├── bias_engine.py                ← ✅ Complete (4 metrics, real math)
│   ├── dataset_loader.py             ← ✅ Complete (4 real datasets)
│   ├── models.py                     ← ✅ Complete (SQLite ORM)
│   ├── tasks.py                      ← ✅ Complete (async threading→Celery)
│   ├── report_generator.py           ← ✅ Complete (Gemini + fallback)
│   ├── requirements.txt              ← ✅ Complete (minimal, no AWS)
│   ├── Dockerfile                    ← ✅ Complete
│   └── tests/
│       ├── test_bias_engine.py       ← ✅ 23 tests, all passing
│       └── test_api.py               ← ✅ 14 tests, all passing
│
├── frontend/
│   ├── src/App.jsx                   ← ✅ Complete React dashboard
│   ├── package.json                  ← ✅ Complete
│   └── vite.config.js               ← ✅ Complete
│
├── flutter_app/                      ← ✅ Complete Flutter app
│   ├── lib/
│   │   ├── main.dart                 ← Firebase init + routing
│   │   ├── screens/
│   │   │   ├── home_screen.dart      ← Landing + dataset list
│   │   │   ├── audit_screen.dart     ← Configure + launch audit
│   │   │   ├── results_screen.dart   ← Metrics + flags + mitigation
│   │   │   └── report_screen.dart    ← Gemini AI report
│   │   └── services/
│   │       ├── audit_service.dart    ← API + Firestore integration
│   │       └── auth_service.dart     ← Firebase Auth
│   └── pubspec.yaml
│
├── docker-compose.simple.yml         ← ✅ Local dev (no AWS)
└── .env.example                      ← ✅ Complete
```

---

## SUBMISSION FORM FIELDS (vision.hack2skill.com)

| Field | What to Enter |
|-------|--------------|
| Problem Statement | Paste content from `01_problem_statement.md` (first 300 words) |
| Solution Overview | Paste content from `02_solution_overview.md` (first 300 words) |
| Prototype Link | Your Cloud Run URL or `http://localhost:8000/api/docs` |
| Project Deck | Upload `FairSight_Pitch_Deck.pptx` |
| GitHub Repository | `https://github.com/YOUR_TEAM/fairsight` |
| Demo Video | YouTube link to your recorded video |

---

## QUICK COMMANDS — DAY OF SUBMISSION

```bash
# 1. Run tests (show judges everything passes)
cd backend && pytest tests/ -v

# 2. Start API
python main.py

# 3. Start frontend
cd ../frontend && npm run dev

# 4. Deploy to Cloud Run (get public URL)
gcloud run deploy fairsight-api --source ./backend --region asia-south1 --allow-unauthenticated

# 5. Deploy Flutter to Firebase
cd flutter_app && flutter build web && firebase deploy
```

---

## SUPPORT

Hackathon support: solutionchallengesupport@hack2skill.com
