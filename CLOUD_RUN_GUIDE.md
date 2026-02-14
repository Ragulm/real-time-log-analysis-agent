# Cloud Run Deployment Guide

Deploy the Real-Time Log Analysis Agent to Google Cloud Run with public HTTP APIs.

---

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **gcloud CLI** installed and configured
3. **Docker** installed locally
4. **GROQ_API_KEY** for LLM-based log analysis
5. **Temporal Server** (managed or self-hosted)

### Install gcloud CLI
```bash
# macOS
brew install google-cloud-sdk

# Windows
# Download from: https://cloud.google.com/sdk/docs/install

# Linux
curl https://sdk.cloud.google.com | bash
```

### Verify gcloud is configured
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

---

## 1. Quick Deployment (Automated Script)

### Make script executable
```bash
chmod +x deploy_to_cloud_run.sh
```

### Run deployment
```bash
./deploy_to_cloud_run.sh my-project-id us-central1
```

This script will:
- Enable required GCP APIs
- Create Artifact Registry repository
- Build and push Docker image
- Deploy API, Worker, and Streamer services
- Configure secrets

---

## 2. Manual Step-by-Step Deployment

### Step 1: Set environment variables
```bash
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"  # or your preferred region
export IMAGE_NAME="realtime-agent"
export ARTIFACT_REPO="realtime-agent-repo"
```

### Step 2: Enable required APIs
```bash
gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    container.googleapis.com \
    secretmanager.googleapis.com
```

### Step 3: Create Artifact Registry repository
```bash
gcloud artifacts repositories create $ARTIFACT_REPO \
    --repository-format=docker \
    --location=$REGION
```

### Step 4: Configure Docker authentication
```bash
gcloud auth configure-docker ${REGION}-docker.pkg.dev
```

### Step 5: Build Docker image
```bash
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/${IMAGE_NAME}:latest .
```

### Step 6: Push image to Artifact Registry
```bash
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/${IMAGE_NAME}:latest
```

### Step 7: Create secrets in Secret Manager
```bash
# Create GROQ_API_KEY secret
echo -n "your-groq-api-key" | gcloud secrets create groq-api-key --data-file=-

# Grant Cloud Run service account access to secrets
gcloud secrets add-iam-policy-binding groq-api-key \
    --member=serviceAccount:PROJECT_ID@appspot.gserviceaccount.com \
    --role=roles/secretmanager.secretAccessor
```

### Step 8: Deploy API Service (public HTTP endpoint)
```bash
gcloud run deploy realtime-agent-api \
    --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/${IMAGE_NAME}:latest \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --memory=512Mi \
    --cpu=1 \
    --port=8000 \
    --set-env-vars="ROLE=api,TEMPORAL_ADDRESS=YOUR_TEMPORAL_ADDRESS:7233,PORT=8000" \
    --set-secrets="GROQ_API_KEY=groq-api-key:latest" \
    --timeout=3600 \
    --concurrency=80
```

### Step 9: Deploy Worker Service (background processing)
```bash
gcloud run deploy realtime-agent-worker \
    --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/${IMAGE_NAME}:latest \
    --region=$REGION \
    --platform=managed \
    --memory=512Mi \
    --cpu=1 \
    --set-env-vars="ROLE=worker,TEMPORAL_ADDRESS=YOUR_TEMPORAL_ADDRESS:7233" \
    --set-secrets="GROQ_API_KEY=groq-api-key:latest" \
    --timeout=3600 \
    --min-instances=1
```

### Step 10: Deploy Streamer Service (background processing)
```bash
gcloud run deploy realtime-agent-streamer \
    --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/${IMAGE_NAME}:latest \
    --region=$REGION \
    --platform=managed \
    --memory=512Mi \
    --cpu=1 \
    --set-env-vars="ROLE=streamer,TEMPORAL_ADDRESS=YOUR_TEMPORAL_ADDRESS:7233" \
    --set-secrets="GROQ_API_KEY=groq-api-key:latest" \
    --timeout=3600 \
    --min-instances=1
```

---

## 3. Get Deployed Service URLs

### Retrieve API endpoint
```bash
gcloud run services describe realtime-agent-api \
    --region=$REGION \
    --format='value(status.url)'
```

### Retrieve Worker service URL
```bash
gcloud run services describe realtime-agent-worker \
    --region=$REGION \
    --format='value(status.url)'
```

### Retrieve Streamer service URL
```bash
gcloud run services describe realtime-agent-streamer \
    --region=$REGION \
    --format='value(status.url)'
```

---

## 4. Test the Deployed API

### Health check
```bash
curl https://YOUR_API_URL/health
```

Expected response:
```json
{
  "status": "healthy",
  "temporal_connected": true
}
```

### Trigger workflow
```bash
curl -X POST https://YOUR_API_URL/api/v1/analyze-log \
  -H "Content-Type: application/json" \
  -d '{
    "log_line": "ERROR: Database connection timeout. Check credentials."
  }'
```

Expected response:
```json
{
  "workflow_id": "log-123456",
  "status": "started",
  "message": "Workflow started for log analysis: ERROR: Database connection timeout..."
}
```

### Get workflow result
```bash
curl https://YOUR_API_URL/api/v1/workflow/log-123456
```

### Batch analyze logs
```bash
curl -X POST https://YOUR_API_URL/api/v1/batch-analyze \
  -H "Content-Type: application/json" \
  -d '{
    "logs": [
      "ERROR: Connection timeout",
      "CRITICAL: Service unavailable"
    ]
  }'
```

### View API documentation
```
https://YOUR_API_URL/docs
```

---

## 5. Network Configuration (Temporal Connectivity)

### Option A: Temporal Server in Same GCP Project

If hosting Temporal in Cloud Run or GKE within the same project:
```bash
gcloud run deploy realtime-agent-api \
    --set-env-vars=TEMPORAL_ADDRESS=temporal-service-url:7233 \
    ...
```

### Option B: Temporal Server External/On-Premises

Use VPC Connector to access private networks:
```bash
# Create VPC connector
gcloud compute networks vpc-access connectors create temporal-connector \
    --region=$REGION \
    --subnet=default

# Deploy with VPC connector
gcloud run deploy realtime-agent-api \
    --vpc-connector=projects/$PROJECT_ID/locations/$REGION/connectors/temporal-connector \
    --set-env-vars=TEMPORAL_ADDRESS=INTERNAL_TEMPORAL_ADDRESS:7233 \
    ...
```

### Option C: Managed Temporal Cloud

Use Temporal Cloud's managed service:
```bash
# Set Temporal Cloud namespace and credentials
gcloud run deploy realtime-agent-api \
    --set-env-vars=TEMPORAL_ADDRESS=temporal-cloud-namespace.tmprl.cloud:7233 \
    --set-secrets=TEMPORAL_MAPI_KEY=temporal-cloud-key:latest \
    ...
```

---

## 6. Troubleshooting

### API service not responding
```bash
gcloud run logs read realtime-agent-api --region=$REGION --limit=50
```

### Worker/Streamer not processing workflows
```bash
gcloud run logs read realtime-agent-worker --region=$REGION --limit=50
gcloud run logs read realtime-agent-streamer --region=$REGION --limit=50
```

### Secret access denied
```bash
# Check service account permissions
gcloud run services describe realtime-agent-api --region=$REGION | grep serviceAccount

# Grant permissions
gcloud secrets add-iam-policy-binding groq-api-key \
    --member=serviceAccount:PROJECT_ID@appspot.gserviceaccount.com \
    --role=roles/secretmanager.secretAccessor
```

### Temporal connection failed
Check:
1. `TEMPORAL_ADDRESS` is correct
2. Temporal server is accessible from Cloud Run (check firewall, VPC)
3. Temporal server is running

---

## 7. Scaling & Performance Tuning

### Increase concurrency (for API)
```bash
gcloud run deploy realtime-agent-api \
    --concurrency=100 \
    ...
```

### Increase min instances (for always-on availability)
```bash
gcloud run deploy realtime-agent-api \
    --min-instances=2 \
    ...
```

### Increase memory/CPU
```bash
gcloud run deploy realtime-agent-api \
    --memory=1Gi \
    --cpu=2 \
    ...
```

---

## 8. Monitoring & Logging

### View real-time logs
```bash
gcloud run logs read realtime-agent-api \
    --region=$REGION \
    --follow
```

### Export logs to BigQuery
```bash
gcloud logging sinks create cloud-run-bigquery \
    bigquery.googleapis.com/projects/$PROJECT_ID/datasets/cloud_run_logs \
    --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="realtime-agent-api"'
```

### View metrics in Cloud Console
```
https://console.cloud.google.com/run
```

---

## 9. Cost Estimation

Rough monthly cost estimates (us-central1):
- **API Service** (public HTTP): ~$10-20/month (includes free tier usage)
- **Worker Service** (min-instances=1): ~$30-50/month
- **Streamer Service** (min-instances=1): ~$30-50/month
- **Artifact Registry**: ~$0.10/GB storage
- **Cloud Logging**: Included in free tier for most use cases

---

## 10. CI/CD Integration (GitHub Actions Example)

### Create `.github/workflows/deploy-cloud-run.yml`
```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [ main/develop ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}
          export_default_credentials: true

      - name: Configure Docker
        run: gcloud auth configure-docker ${{ secrets.GCP_REGION }}-docker.pkg.dev

      - name: Build & Push
        run: |
          docker build -t ${{ secrets.GCP_REGION }}-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/realtime-agent-repo/realtime-agent:$GITHUB_SHA .
          docker push ${{ secrets.GCP_REGION }}-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/realtime-agent-repo/realtime-agent:$GITHUB_SHA

      - name: Deploy API
        run: |
          gcloud run deploy realtime-agent-api \
            --image=${{ secrets.GCP_REGION }}-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/realtime-agent-repo/realtime-agent:$GITHUB_SHA
```

---

## Summary

| Task | Command |
|------|---------|
| **Quick deploy** | `./deploy_to_cloud_run.sh PROJECT_ID REGION` |
| **View API URL** | `gcloud run services describe realtime-agent-api --region=REGION --format='value(status.url)'` |
| **Test API** | `curl https://API_URL/health` |
| **View logs** | `gcloud run logs read realtime-agent-api --region=REGION` |
| **Scale up** | `gcloud run deploy realtime-agent-api --min-instances=2 ...` |
| **Delete service** | `gcloud run services delete realtime-agent-api --region=REGION` |

