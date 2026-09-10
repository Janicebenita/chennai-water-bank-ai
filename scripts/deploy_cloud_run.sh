#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT first}"
REGION="${GCP_REGION:-asia-south1}"
SERVICE_NAME="${CLOUD_RUN_SERVICE:-chennai-water-bank}"
DATA_BACKEND_VALUE="${DATA_BACKEND:-memory}"

gcloud config set project "${PROJECT_ID}"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
gcloud run deploy "${SERVICE_NAME}" \
  --source . \
  --region "${REGION}" \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars "DATA_BACKEND=${DATA_BACKEND_VALUE},DEMO_MODE=true" \
  --quiet

gcloud run services describe "${SERVICE_NAME}" \
  --region "${REGION}" \
  --format='value(status.url)'

