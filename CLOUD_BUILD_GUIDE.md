# Cloud Build Deployment Guide

This guide explains how to build and deploy the Real-Time Log Analysis Agent worker to Google Cloud Run using Google Cloud Build, which avoids local network upload issues.

## Prerequisites

1. **Google Cloud Project**: `project-294f73a2-90e4-4430-b84`
2. **gcloud CLI**: Installed and authenticated
3. **Cloud Build**: Enabled in your GCP project
4. **Artifact Registry**: Repository `realtime-agent-repo` in `us-central1`
5. **Service Account**: `realtime-agent-sa` with Cloud Run and Artifact Registry permissions

## Set Up GCP Resources (One-time)

### 1. Enable Cloud Build API
```bash
gcloud services enable cloudbuild.googleapis.com --project=project-294f73a2-90e4-4430-b84
```

### 2. Create Service Account (if not exists)
```bash
gcloud iam service-accounts create realtime-agent-sa \
  --display-name="Real-Time Agent Service Account" \
  --project=project-294f73a2-90e4-4430-b84

# Grant Cloud Run Admin role
gcloud projects add-iam-policy-binding project-294f73a2-90e4-4430-b84 \
  --member=serviceAccount:realtime-agent-sa@project-294f73a2-90e4-4430-b84.iam.gserviceaccount.com \
  --role=roles/run.admin

# Grant Artifact Registry Writer role
gcloud projects add-iam-policy-binding project-294f73a2-90e4-4430-b84 \
  --member=serviceAccount:realtime-agent-sa@project-294f73a2-90e4-4430-b84.iam.gserviceaccount.com \
  --role=roles/artifactregistry.writer
```

### 3. Grant Cloud Build Service Account Permissions
```bash
# Get Cloud Build service account
export CLOUD_BUILD_SA=$(gcloud projects describe project-294f73a2-90e4-4430-b84 \
  --format='value(projectNumber)')@cloudbuild.gserviceaccount.com

# Grant Cloud Run and Artifact Registry access
gcloud projects add-iam-policy-binding project-294f73a2-90e4-4430-b84 \
  --member=serviceAccount:$CLOUD_BUILD_SA \
  --role=roles/run.admin

gcloud projects add-iam-policy-binding project-294f73a2-90e4-4430-b84 \
  --member=serviceAccount:$CLOUD_BUILD_SA \
  --role=roles/artifactregistry.writer
```

## Build Strategies

### Strategy 1: Worker Only (Recommended)

Build and deploy just the worker service to Cloud Run:

```bash
gcloud builds submit \
  --config=cloudbuild-worker.yaml \
  --project=project-294f73a2-90e4-4430-b84
```

**Pros:**
- Fast build (~2-3 min)
- Minimal resource usage
- Simple rollback

**Cons:**
- Requires separate API deployment
- No version coordination

### Strategy 2: All Services

Build API, worker, and streamer images in parallel:

```bash
gcloud builds submit \
  --config=cloudbuild.yaml \
  --project=project-294f73a2-90e4-4430-b84
```

**Pros:**
- All services built in one go
- Consistent versioning across services
- Suitable for staging/production deployments

**Cons:**
- Longer build time (~5-7 min)
- Higher resource consumption

## Using the PowerShell Deployment Script

Run the Cloud Build deployment script from the repo root:

```powershell
# Using PowerShell with Windows
.\scripts\cloud-build-worker.ps1

# Or with configuration options
.\scripts\cloud-build-worker.ps1 -BuildId "v2.5" -SkipDeploy $false -ConfigFile "cloudbuild-worker.yaml"
```

Script options:
- `-BuildId`: Optional tag for the build (default: "latest")
- `-SkipDeploy`: Skip automatic deployment and just build/push (default: $false)
- `-ConfigFile`: Path to Cloud Build config file (default: "cloudbuild-worker.yaml")

## Manual Deployment Steps

If you prefer to deploy manually after Cloud Build completes:

### 1. List available images
```bash
gcloud artifacts docker images list us-central1-docker.pkg.dev/project-294f73a2-90e4-4430-b84/realtime-agent-repo \
  --project=project-294f73a2-90e4-4430-b84
```

### 2. Deploy specific image tag
```bash
gcloud run deploy realtime-agent-worker \
  --image=us-central1-docker.pkg.dev/project-294f73a2-90e4-4430-b84/realtime-agent-repo/realtime-agent:worker-<BUILD_ID> \
  --region=us-central1 \
  --platform=managed \
  --no-allow-unauthenticated \
  --set-env-vars=ROLE=worker,TEMPORAL_ADDRESS=temporal.example.com:7233 \
  --service-account=realtime-agent-sa@project-294f73a2-90e4-4430-b84.iam.gserviceaccount.com \
  --project=project-294f73a2-90e4-4430-b84
```

## View Build Logs

### In Console
https://console.cloud.google.com/cloud-build/builds?project=project-294f73a2-90e4-4430-b84

### Via CLI
```bash
# List recent builds
gcloud builds list --project=project-294f73a2-90e4-4430-b84

# View specific build logs
gcloud builds log <BUILD_ID> --project=project-294f73a2-90e4-4430-b84
```

## Troubleshooting

### Build Fails with Permission Denied
- Verify Cloud Build service account has Artifact Registry Writer role
- Check that the service account is the one running the build

### Image Push Fails
- Ensure Artifact Registry API is enabled
- Verify the repository `realtime-agent-repo` exists in `us-central1`
- Check Cloud Build service account has push permissions

### Deployment Fails
- Verify the service account has Cloud Run Admin role
- Check that Cloud Run API is enabled
- Ensure the image URI is correct

## Next Steps

1. **Set up Secret Manager** for `GROQ_API_KEY` to avoid passing secrets in build config
2. **Add VPC Service Controls** to restrict Artifact Registry access
3. **Enable Continuous Deployment** with Cloud Source Repositories or GitHub integration
4. **Monitor deployments** via Cloud Logging and Cloud Trace

## Related Files

- `cloudbuild.yaml` - All-services build configuration
- `cloudbuild-worker.yaml` - Worker-only build configuration
- `scripts/cloud-build-worker.ps1` - PowerShell deployment script
- `Dockerfile` - Multi-role Docker image definition
- `.dockerignore` - Build context optimization
