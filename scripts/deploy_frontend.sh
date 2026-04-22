#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  Deploy FairSight Flutter App to Firebase Hosting            ║
# ║  v2.0 — Auto-detects API URL from Cloud Run if not set      ║
# ╚══════════════════════════════════════════════════════════════╝

set -euo pipefail

# ── Load .env from project root ───────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/.."
ENV_FILE="$PROJECT_ROOT/.env"
if [[ -f "$ENV_FILE" ]]; then
  set -o allexport
  # shellcheck source=/dev/null
  source "$ENV_FILE"
  set +o allexport
fi

# Auto-detect API URL from Cloud Run if not provided
if [[ -z "${API_URL:-}" ]]; then
  PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-}"
  REGION="${GOOGLE_CLOUD_REGION:-asia-south1}"
  if [[ -n "$PROJECT_ID" ]]; then
    echo "▶ Auto-detecting API URL from Cloud Run…"
    API_URL=$(gcloud run services describe fairsight-api \
      --project "$PROJECT_ID" \
      --region "$REGION" \
      --format "value(status.url)" 2>/dev/null || true)
  fi
fi

if [[ -z "${API_URL:-}" ]]; then
  echo "❌ API_URL not set and could not auto-detect."
  echo "Usage: API_URL=https://your-cloud-run-url bash scripts/deploy_frontend.sh"
  exit 1
fi

echo "═══════════════════════════════════════════════"
echo "  Deploying FairSight Frontend"
echo "═══════════════════════════════════════════════"
echo "API URL:  $API_URL"
echo ""

# Build Flutter web with production API URL
echo "▶ Building Flutter web app…"
cd "$PROJECT_ROOT"
flutter build web --release --dart-define="API_URL=$API_URL"

# Deploy to Firebase Hosting
echo "▶ Deploying to Firebase Hosting…"
firebase deploy --only hosting

echo ""
echo "✅ Frontend deployed successfully!"
