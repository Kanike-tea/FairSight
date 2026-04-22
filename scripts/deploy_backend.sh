#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  Deploy FairSight API to Google Cloud Run                    ║
# ║  v2.0 — Supports auto-scan, model audit, endpoint probing   ║
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
  echo "✔ Loaded environment from .env"
fi

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT in .env}"
REGION="${GOOGLE_CLOUD_REGION:-asia-south1}"
SERVICE_NAME="fairsight-api"

echo "═══════════════════════════════════════════════"
echo "  Deploying $SERVICE_NAME v2.0"
echo "═══════════════════════════════════════════════"
echo "Project:  $PROJECT_ID"
echo "Region:   $REGION"
echo ""

# Build container image
echo "▶ Building container image…"
gcloud builds submit \
  --project "$PROJECT_ID" \
  --tag "gcr.io/$PROJECT_ID/$SERVICE_NAME" \
  "$PROJECT_ROOT/backend"

# Deploy to Cloud Run with increased resources for model loading
echo "▶ Deploying to Cloud Run…"
gcloud run deploy "$SERVICE_NAME" \
  --project "$PROJECT_ID" \
  --image "gcr.io/$PROJECT_ID/$SERVICE_NAME" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 5 \
  --set-env-vars "GOOGLE_API_KEY=${GOOGLE_API_KEY:-}"

echo ""
echo "✅ API deployed successfully!"
API_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --format "value(status.url)")

echo "API URL: $API_URL"
echo ""
echo "Next: deploy frontend with:"
echo "  API_URL=$API_URL bash scripts/deploy_frontend.sh"
