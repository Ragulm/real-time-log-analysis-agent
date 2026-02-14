# Docker & Deployment Guide

## Prerequisites
- Docker & Docker Compose installed
- `GROQ_API_KEY` environment variable set (for LLM-based log explanation)

---

## 1. Local Development — Docker Compose

### Start Everything (One Command)
```bash
docker-compose up --build
```

This starts:
- **PostgreSQL** — Temporal state database
- **Temporal Server** — Workflow orchestration (UI at `http://localhost:8233`)
- **app-worker** — Temporal worker (processes workflows)
- **app-streamer** — Log watcher (triggers workflows when ERROR/CRITICAL logs appear)

### Run Individual Services

**Start only Temporal infrastructure:**
```bash
docker-compose up postgresql temporal temporal-ui
```

**Start only the worker (requires Temporal server running):**
```bash
docker-compose up app-worker
```

**Start only the streamer (requires Temporal server running):**
```bash
docker-compose up app-streamer
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app-worker
docker-compose logs -f app-streamer

# Last 50 lines
docker-compose logs --tail=50 app-streamer
```

### Stop Everything
```bash
docker-compose down
```

### Clean Up (remove volumes/db data)
```bash
docker-compose down -v
```

---

## 2. Local Testing — Build & Run Standalone Container

### Build the Image
```bash
docker build -t realtime-agent:latest .
```

### Run as Worker
```bash
docker run --rm \
  -e TEMPORAL_ADDRESS=host.docker.internal:7233 \
  realtime-agent:latest
```

### Run as Streamer
```bash
docker run --rm \
  -e ROLE=streamer \
  -e TEMPORAL_ADDRESS=host.docker.internal:7233 \
  -v "$(pwd)/app.log:/app/app.log" \
  realtime-agent:latest
```

### Run Log Generator (for testing log collection)
```bash
docker run --rm \
  -e ROLE=generator \
  -v "$(pwd)/app.log:/app/app.log" \
  realtime-agent:latest
```

---

## 3. Cloud Run Deployment

### Prerequisites
- Google Cloud Project set up
- `gcloud` CLI installed & authenticated
- Docker / Artifact Registry access configured

### Build & Push to Artifact Registry

```bash
# Set your GCP project/region
export PROJECT_ID="your-gcp-project"
export REGION="us-central1"
export IMAGE_NAME="realtime-agent"

# Build & push to Artifact Registry
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${IMAGE_NAME}/${IMAGE_NAME}:latest .

docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${IMAGE_NAME}/${IMAGE_NAME}:latest
```

### Deploy Worker to Cloud Run

**Option A: Cloud Run Service (long-running, always-on)**
```bash
gcloud run deploy realtime-agent-worker \
  --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/${IMAGE_NAME}/${IMAGE_NAME}:latest \
  --region ${REGION} \
  --platform=managed \
  --memory=512Mi \
  --cpu=1 \
  --set-env-vars=ROLE=worker,TEMPORAL_ADDRESS=YOUR_TEMPORAL_HOST:7233 \
  --set-secrets=GROQ_API_KEY=groq-api-key:latest \
  --min-instances=1 \
  --max-instances=10 \
  --no-allow-unauthenticated
```

**Option B: Cloud Run Job (batch/one-off execution)**
```bash
gcloud run jobs create realtime-agent-worker \
  --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/${IMAGE_NAME}/${IMAGE_NAME}:latest \
  --region ${REGION} \
  --set-env-vars=ROLE=worker,TEMPORAL_ADDRESS=YOUR_TEMPORAL_HOST:7233 \
  --set-secrets=GROQ_API_KEY=groq-api-key:latest \
  --memory=512Mi \
  --cpu=1

# Execute the job
gcloud run jobs execute realtime-agent-worker --region ${REGION}
```

### Deploy Streamer to Cloud Run Job

```bash
gcloud run jobs create realtime-agent-streamer \
  --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/${IMAGE_NAME}/${IMAGE_NAME}:latest \
  --region ${REGION} \
  --set-env-vars=ROLE=streamer,TEMPORAL_ADDRESS=YOUR_TEMPORAL_HOST:7233 \
  --set-secrets=GROQ_API_KEY=groq-api-key:latest \
  --memory=512Mi \
  --cpu=1
```

---

## 4. Environment Variables & Secrets

### Required Environment Variables
- `TEMPORAL_ADDRESS` — Temporal server address (default: `localhost:7233`)
- `ROLE` — Container role: `worker`, `streamer`, or `generator` (default: `worker`)

### Secrets (GCP Secret Manager)
- `GROQ_API_KEY` — API key for Groq LLM

### Create Secret in GCP
```bash
echo -n "your-groq-api-key" | gcloud secrets create groq-api-key --data-file=-
```

### Pass Secrets to Cloud Run
```bash
gcloud run deploy realtime-agent-worker \
  --set-secrets=GROQ_API_KEY=groq-api-key:latest \
  ...
```

---

## 5. Network Setup (Cloud Run → Temporal)

### If Temporal is On-Premises or Private
Use VPC Connector:
```bash
gcloud run deploy realtime-agent-worker \
  --vpc-connector=projects/PROJECT_ID/locations/REGION/connectors/CONNECTOR_NAME \
  ...
```

### If Temporal is in Same GCP Project
Deploy Temporal in Cloud Run or GKE, and use the private endpoint.

### If Temporal is in Cloud (hosted)
Use the public URL:
```bash
--set-env-vars=TEMPORAL_ADDRESS=temporal.example.com:7233
```

---

## 6. Monitoring & Logs

### View Cloud Run Logs
```bash
gcloud run logs read realtime-agent-worker --region ${REGION} --limit=100
```

### Stream Live Logs
```bash
gcloud run logs read realtime-agent-worker --region ${REGION} --follow
```

### View Temporal UI (if accessible)
```
http://localhost:8233
```

---

## 7. Troubleshooting

### Container won't start — Connection refused
**Cause:** Temporal server not reachable.  
**Fix:** Ensure `TEMPORAL_ADDRESS` is correct and Temporal is running/accessible.

### Permission denied — `/usr/local/bin/entrypoint.sh`
**Cause:** File permissions issue.  
**Fix:** The Dockerfile chmod fixes this; rebuild with `docker build --no-cache .`

### Container exits immediately
**Cause:** Check logs: `docker-compose logs app-worker`

### GROQ_API_KEY not found
**Cause:** Environment variable not set.  
**Fix:** Export locally or set in Cloud Run with `--set-secrets` or `--set-env-vars`.

---

## 8. Quick Start Examples

### Local Development (One Command)
```bash
docker-compose up --build
```
Visit Temporal UI: `http://localhost:8233`

### Local Testing (Standalone)
```bash
# Terminal 1: Start Temporal
docker-compose up postgresql temporal

# Terminal 2: Start Worker
docker run --rm -e TEMPORAL_ADDRESS=host.docker.internal:7233 realtime-agent:latest

# Terminal 3: Start Streamer
docker run --rm -e ROLE=streamer -e TEMPORAL_ADDRESS=host.docker.internal:7233 \
  -v "$(pwd)/app.log:/app/app.log" realtime-agent:latest

# Terminal 4: Generate logs
docker run --rm -e ROLE=generator -v "$(pwd)/app.log:/app/app.log" realtime-agent:latest
```

### Cloud Run Deployment
```bash
export PROJECT_ID="my-project"
export REGION="us-central1"
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/realtime-agent/realtime-agent:latest .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/realtime-agent/realtime-agent:latest
gcloud run deploy realtime-agent-worker \
  --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/realtime-agent/realtime-agent:latest \
  --set-env-vars=ROLE=worker,TEMPORAL_ADDRESS=YOUR_TEMPORAL_ADDRESS:7233
```

---

## Summary

| Scenario | Command |
|----------|---------|
| **Local dev (all services)** | `docker-compose up --build` |
| **Local test (worker only)** | `docker run -e TEMPORAL_ADDRESS=host.docker.internal:7233 realtime-agent:latest` |
| **Cloud Run deploy** | See section 3 above |
| **View logs** | `docker-compose logs -f app-worker` or `gcloud run logs read ...` |
| **Stop everything** | `docker-compose down` |

