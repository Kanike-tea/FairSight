#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  Deploy FairSight API to Google Cloud Run                    ║
# ╚══════════════════════════════════════════════════════════════╝

set -euo pipefail

# ── Load .env from project root ───────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"
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

echo "═══ Building & deploying $SERVICE_NAME ═══"
echo "Project:  $PROJECT_ID"
echo "Region:   $REGION"
echo ""

# Build container image
echo "▶ Building container image…"
gcloud builds submit \
  --project "$PROJECT_ID" \
  --tag "gcr.io/$PROJECT_ID/$SERVICE_NAME" \
  ./backend

# Deploy to Cloud Run
echo "▶ Deploying to Cloud Run…"
gcloud run deploy "$SERVICE_NAME" \
  --project "$PROJECT_ID" \
  --image "gcr.io/$PROJECT_ID/$SERVICE_NAME" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_API_KEY=${GOOGLE_API_KEY:-}"

echo ""
echo "✅ API deployed successfully!"
gcloud run services describe "$SERVICE_NAME" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --format "value(status.url)"
