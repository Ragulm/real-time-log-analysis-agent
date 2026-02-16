param(
    [string]$ProjectId = "",
    [string]$Region = "us-central1",
    [string]$TemporalAddress = "temporal.example.com:7233",
    [string]$GroqApiKey = ""
)

if (-not $ProjectId) {
    Write-Host "Usage: .\deploy_to_cloud_run.ps1 -ProjectId <PROJECT_ID>"
    Write-Host "Example: .\deploy_to_cloud_run.ps1 -ProjectId 'my-project' -GroqApiKey 'gsk_...'"
    exit 1
}

Write-Host "`n=== Cloud Run Deployment ===" -ForegroundColor Cyan
$ARTIFACT_REPO = "realtime-agent-repo"
$IMAGE_NAME = "realtime-agent"
$IMAGE_URL = "$Region-docker.pkg.dev/$ProjectId/$ARTIFACT_REPO/$IMAGE_NAME`:latest"

# 1. Check gcloud
Write-Host "[1/7] Checking gcloud..." -ForegroundColor Green
$gcloudCheck = Get-Command gcloud -ErrorAction SilentlyContinue
if (-not $gcloudCheck) {
    Write-Host "ERROR: gcloud not found" -ForegroundColor Red
    exit 1
}
Write-Host "  OK`n" -ForegroundColor Green

# 2. Set project
Write-Host "[2/7] Setting project..." -ForegroundColor Green
gcloud config set project $ProjectId 2>&1 | Out-Null
Write-Host "  OK`n" -ForegroundColor Green

# 3. Enable APIs
Write-Host "[3/7] Enabling APIs..." -ForegroundColor Green
gcloud services enable run.googleapis.com artifactregistry.googleapis.com container.googleapis.com secretmanager.googleapis.com --quiet 2>&1 | Out-Null
Write-Host "  OK`n" -ForegroundColor Green

# 4. Create registry
Write-Host "[4/7] Creating Artifact Registry..." -ForegroundColor Green
gcloud artifacts repositories describe $ARTIFACT_REPO --location=$Region 2>&1 | Out-Null
$registryExists = $LASTEXITCODE -eq 0
if (-not $registryExists) {
    gcloud artifacts repositories create $ARTIFACT_REPO --repository-format=docker --location=$Region 2>&1 | Out-Null
}
Write-Host "  OK`n" -ForegroundColor Green

# 5. Build and push image
Write-Host "[5/7] Building Docker image..." -ForegroundColor Green
gcloud auth configure-docker "$Region-docker.pkg.dev" --quiet 2>&1 | Out-Null
docker build -t $IMAGE_URL . 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker build failed" -ForegroundColor Red
    exit 1
}
Write-Host "  Pushing image..." -ForegroundColor Green
docker push $IMAGE_URL 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker push failed" -ForegroundColor Red
    exit 1
}
Write-Host "  OK`n" -ForegroundColor Green

# 6. Setup secret
Write-Host "[6/7] Setting up secret..." -ForegroundColor Green
if ($GroqApiKey) {
    gcloud secrets describe groq-api-key 2>&1 | Out-Null
    $secretExists = $LASTEXITCODE -eq 0
    if ($secretExists) {
        $GroqApiKey | gcloud secrets versions add groq-api-key --data-file=- 2>&1 | Out-Null
    }
    else {
        $GroqApiKey | gcloud secrets create groq-api-key --data-file=- 2>&1 | Out-Null
    }
    Write-Host "  OK`n" -ForegroundColor Green
}
else {
    Write-Host "  Skipped (no key provided)`n" -ForegroundColor Yellow
}

# 7. Deploy
Write-Host "[7/7] Deploying services...`n" -ForegroundColor Green

Write-Host "  API Service..." -NoNewline
gcloud run deploy "$IMAGE_NAME-api" --image=$IMAGE_URL --region=$Region --platform=managed --allow-unauthenticated --memory=512Mi --cpu=1 --port=8000 --set-env-vars="ROLE=api,TEMPORAL_ADDRESS=$TemporalAddress,WAIT_FOR_TEMPORAL=false" --set-secrets="GROQ_API_KEY=groq-api-key:latest" --timeout=3600 --concurrency=80 --quiet 2>&1 | Out-Null
Write-Host " OK" -ForegroundColor Green

Write-Host "  Worker Service..." -NoNewline
gcloud run deploy "$IMAGE_NAME-worker" --image=$IMAGE_URL --region=$Region --platform=managed --memory=512Mi --cpu=1 --set-env-vars="ROLE=worker,TEMPORAL_ADDRESS=$TemporalAddress,WAIT_FOR_TEMPORAL=false" --set-secrets="GROQ_API_KEY=groq-api-key:latest" --timeout=3600 --min-instances=1 --quiet 2>&1 | Out-Null
Write-Host " OK" -ForegroundColor Green

Write-Host "  Streamer Service..." -NoNewline
gcloud run deploy "$IMAGE_NAME-streamer" --image=$IMAGE_URL --region=$Region --platform=managed --memory=512Mi --cpu=1 --set-env-vars="ROLE=streamer,TEMPORAL_ADDRESS=$TemporalAddress" --set-secrets="GROQ_API_KEY=groq-api-key:latest" --timeout=3600 --min-instances=1 --quiet 2>&1 | Out-Null
Write-Host " OK`n" -ForegroundColor Green

# Get URLs
$API_URL = gcloud run services describe "$IMAGE_NAME-api" --region=$Region --format='value(status.url)' 2>&1

Write-Host "================================" -ForegroundColor Green
Write-Host "DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "================================`n" -ForegroundColor Green

Write-Host "Your API URL: " -NoNewline
Write-Host "$API_URL" -ForegroundColor Cyan
Write-Host "Dashboard:    " -NoNewline
Write-Host "$API_URL/dashboard`n" -ForegroundColor Cyan

Write-Host "Next: Test the health endpoint"
Write-Host "curl $API_URL/health`n" -ForegroundColor Yellow
