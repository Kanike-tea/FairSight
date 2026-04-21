#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  Deploy FairSight Flutter App to Firebase Hosting            ║
# ╚══════════════════════════════════════════════════════════════╝

set -euo pipefail

API_URL="${API_URL:?Set API_URL (your Cloud Run URL)}"

echo "═══ Building & deploying Flutter frontend ═══"
echo "API URL:  $API_URL"
echo ""

# Build Flutter web with production API URL
echo "▶ Building Flutter web app…"
flutter build web --dart-define="API_URL=$API_URL"

# Deploy to Firebase Hosting
echo "▶ Deploying to Firebase Hosting…"
firebase deploy --only hosting

echo ""
echo "✅ Frontend deployed successfully!"
