param(
    [string]$ProjectId = $env:GOOGLE_CLOUD_PROJECT,
    [string]$Region = "asia-south1",
    [string]$ServiceName = "chennai-water-bank",
    [ValidateSet("memory", "firestore")]
    [string]$DataBackend = "memory"
)

$ErrorActionPreference = "Stop"
if (-not $ProjectId) { throw "Pass -ProjectId or set GOOGLE_CLOUD_PROJECT." }

gcloud config set project $ProjectId
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
gcloud run deploy $ServiceName `
    --source . `
    --region $Region `
    --allow-unauthenticated `
    --port 8080 `
    --set-env-vars "DATA_BACKEND=$DataBackend,DEMO_MODE=true" `
    --quiet
gcloud run services describe $ServiceName --region $Region --format "value(status.url)"

