# Deploy to Google Cloud Run - Step-by-Step Guide

**Follow these exact steps to deploy your Real-Time Log Analysis Agent to Google Cloud Run and expose it with a public URL.**

---

## ⏱️ Total Time: ~10-15 minutes

---

## STEP 1: Set Up Google Cloud Project (2 minutes)

### 1.1 Create a GCP Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown at the top
3. Click **"NEW PROJECT"**
4. Enter project name: `realtime-log-agent`
5. Click **CREATE**
6. Wait 30 seconds for project to load

### 1.2 Install gcloud CLI
```bash
# macOS (using Homebrew)
brew install google-cloud-sdk

# Windows (download installer)
# https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe

# Linux
curl https://sdk.cloud.google.com | bash
```

### 1.3 Authenticate with Google
```bash
gcloud auth login
```
This opens a browser. Sign in with your Google account.

---

## STEP 2: Configure gcloud (1 minute)

```bash
# Set your project ID (from step 1)
gcloud config set project YOUR_PROJECT_ID

# Verify it's set
gcloud config list
```

Replace `YOUR_PROJECT_ID` with your actual project ID.

---

## STEP 3: Enable Required APIs (1 minute)

```bash
gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    container.googleapis.com \
    secretmanager.googleapis.com
```

---

## STEP 4: Create Artifact Registry (1 minute)

This is where Docker images are stored in GCP.

```bash
# Set variables
export PROJECT_ID=$(gcloud config get-value project)
export REGION="us-central1"
export REPO_NAME="realtime-agent-repo"

# Create repository
gcloud artifacts repositories create $REPO_NAME \
    --repository-format=docker \
    --location=$REGION \
    --description="Real-Time Log Analysis Agent"
```

---

## STEP 5: Build and Push Docker Image (3-5 minutes)

### 5.1 Configure Docker Authentication
```bash
gcloud auth configure-docker ${REGION}-docker.pkg.dev
```

### 5.2 Build Docker Image
```bash
export IMAGE_NAME="realtime-agent"
export IMAGE_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest"

docker build -t $IMAGE_URL .
```

### 5.3 Push Image to Artifact Registry
```bash
docker push $IMAGE_URL

# Verify it was pushed
gcloud artifacts docker images list ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}
```

---

## STEP 6: Set Up Secrets (2 minutes)

### 6.1 Create GROQ_API_KEY Secret
```bash
# Replace YOUR_GROQ_API_KEY with your actual key
echo -n "YOUR_GROQ_API_KEY" | gcloud secrets create groq-api-key --data-file=-

# Verify secret was created
gcloud secrets list
```

### 6.2 Grant Cloud Run Service Account Access
```bash
# Get the default service account
export SA_EMAIL=$(gcloud iam service-accounts list --filter="displayName:Default compute service account" --format='value(email)')

# Grant secret access
gcloud secrets add-iam-policy-binding groq-api-key \
    --member=serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com \
    --role=roles/secretmanager.secretAccessor
```

---

## STEP 7: Create Temporal Server (Optional but Recommended)

If you have an existing Temporal server, skip this. Otherwise:

```bash
# Option A: Use Cloud Run for Temporal
# (This requires a separate deployment - out of scope for this guide)

# Option B: Use Temporal Cloud (managed service)
# https://temporal.io/cloud

# Option C: Self-hosted Temporal in GKE
# (More complex - see CLOUD_RUN_GUIDE.md for details)

# For now, set your Temporal address:
export TEMPORAL_ADDRESS="YOUR_TEMPORAL_SERVER:7233"
```

---

## STEP 8: Deploy API Service to Cloud Run (2 minutes)

This creates a **public HTTPS URL** for your API.

```bash
gcloud run deploy realtime-agent-api \
    --image=$IMAGE_URL \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --memory=512Mi \
    --cpu=1 \
    --port=8000 \
    --set-env-vars="ROLE=api,TEMPORAL_ADDRESS=${TEMPORAL_ADDRESS},PORT=8000" \
    --set-secrets="GROQ_API_KEY=groq-api-key:latest" \
    --timeout=3600 \
    --concurrency=80 \
    --max-instances=10
```

### Output Example:
```
Service [realtime-agent-api] revision [realtime-agent-api-00001-abc] has been deployed and is serving 100 percent of traffic.
Service URL: https://realtime-agent-api-abc123.run.app
```

**Save this URL!** This is your public endpoint.

---

## STEP 9: Deploy Worker Service (Optional)

For background processing of workflows:

```bash
gcloud run deploy realtime-agent-worker \
    --image=$IMAGE_URL \
    --region=$REGION \
    --platform=managed \
    --memory=512Mi \
    --cpu=1 \
    --set-env-vars="ROLE=worker,TEMPORAL_ADDRESS=${TEMPORAL_ADDRESS}" \
    --set-secrets="GROQ_API_KEY=groq-api-key:latest" \
    --timeout=3600 \
    --min-instances=1 \
    --max-instances=5
```

---

## STEP 10: Test Your Deployment (1 minute)

### 10.1 Get Your Service URL
```bash
# If you didn't save it earlier
gcloud run services describe realtime-agent-api \
    --region=$REGION \
    --format='value(status.url)'
```

### 10.2 Test Health Endpoint
```bash
# Replace with your actual URL
curl https://YOUR_SERVICE_URL/health
```

Expected response:
```json
{"status":"healthy","temporal_connected":true}
```

### 10.3 View Dashboard
```
https://YOUR_SERVICE_URL/dashboard
```

### 10.4 Trigger a Workflow
```bash
curl -X POST https://YOUR_SERVICE_URL/api/v1/analyze-log \
  -H "Content-Type: application/json" \
  -d '{"log_line": "ERROR: Cloud deployment test"}'
```

---

## STEP 11: View Logs (Ongoing)

### Watch Real-Time Logs
```bash
gcloud run logs read realtime-agent-api --region=$REGION --follow
```

### View Service Details
```bash
# Check memory, CPU usage, traffic
gcloud run describe realtime-agent-api --region=$REGION --format=yaml
```

---

## 🎉 COMPLETE!

Your Real-Time Log Analysis Agent is now **deployed and accessible** at:

```
https://YOUR_SERVICE_URL
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Get service URL | `gcloud run services describe realtime-agent-api --region=us-central1 --format='value(status.url)'` |
| View logs | `gcloud run logs read realtime-agent-api --region=us-central1 --follow` |
| Scale up | `gcloud run deploy realtime-agent-api --min-instances=2 --region=us-central1 --image=$IMAGE_URL` |
| Update code | `docker build -t $IMAGE_URL . && docker push $IMAGE_URL && gcloud run deploy realtime-agent-api --image=$IMAGE_URL --region=us-central1` |
| Delete service | `gcloud run services delete realtime-agent-api --region=us-central1` |

---

## 💡 Common Issues & Solutions

### Issue: "Service account does not have permission to access secret"
**Solution:**
```bash
gcloud secrets add-iam-policy-binding groq-api-key \
    --member=serviceAccount:PROJECT_ID@appspot.gserviceaccount.com \
    --role=roles/secretmanager.secretAccessor
```

### Issue: "Error: failed to authenticate to gcloud"
**Solution:**
```bash
gcloud auth login
gcloud auth application-default login
```

### Issue: "Cloud Run service not connecting to Temporal"
**Solution:**
- Use VPC connector: `--vpc-connector=projects/PROJECT/locations/REGION/connectors/CONNECTOR`
- Or use public Temporal address
- Check firewall rules

### Issue: "Docker push fails"
**Solution:**
```bash
docker logout
gcloud auth configure-docker ${REGION}-docker.pkg.dev
```

---

## 🔗 Next: Connect to Your Systems

Once deployed, you can:

1. **Use the API**: Your Cloud Run URL is a public REST endpoint
2. **View Dashboard**: Open `https://YOUR_URL/dashboard` in browser
3. **Send Logs**: POST to `https://YOUR_URL/api/v1/analyze-log`
4. **Integrate**: Connect with:
   - Log aggregators (CloudLogging, Datadog, etc.)
   - Monitoring tools
   - Alert systems
   - Custom applications

---

## 📊 Monitoring Dashboard

Your dashboard is automatically available at:
```
https://YOUR_SERVICE_URL/dashboard
```

Features:
- ✅ Real-time workflow status
- ✅ Charts and statistics
- ✅ Log analysis history
- ✅ Performance metrics

---

## 💰 Cost Estimation

Approximate monthly costs (as of 2024):
- **Cloud Run**: $0 - $20 (free tier + usage)
- **Artifact Registry**: ~$0.10 (storage)
- **Secret Manager**: Free for < 100 secrets
- **Logging**: Free tier usually sufficient

Total: Typically under $10-20/month for moderate usage.

---

## 🆘 Need Help?

1. Check logs: `gcloud run logs read realtime-agent-api --follow`
2. View service details: `gcloud run describe realtime-agent-api --format=yaml`
3. Check API status: `curl https://YOUR_URL/health`

---

**Your deployment is complete! 🚀**

Share your Cloud Run URL:
```
https://realtime-agent-api-ABC123.run.app
```

Anyone can now access the dashboard and trigger log analysis workflows!

