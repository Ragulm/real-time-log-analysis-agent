# Testing & Running Guide

Complete step-by-step guide to test and run the Real-Time Log Analysis Agent locally and in the cloud.

---

## Prerequisites

- Docker & Docker Compose installed
- `curl` or Postman for API testing
- `jq` (optional, for JSON formatting)
- GCP project (for Cloud Run deployment)
- `gcloud` CLI (for Cloud Run deployment)

---

## Part 1: Local Testing (Docker Compose)

### Start All Services

```bash
# Start all services (Temporal, PostgreSQL, API, Worker, Streamer)
docker-compose up -d

# Wait 10-15 seconds for services to be ready
sleep 15

# Verify services are running
docker-compose ps
```

Expected output:
```
NAME                              IMAGE                          STATUS
real-time-log-analysis-agent-postgresql-1   postgres:13            Up 15s
real-time-log-analysis-agent-temporal-1     temporalio/auto-setup  Up 15s
real-time-log-analysis-agent-app-api-1      realtime-agent:local   Up 10s
real-time-log-analysis-agent-app-worker-1   realtime-agent:local   Up 10s
real-time-log-analysis-agent-app-streamer-1 realtime-agent:local   Up 10s
```

---

### Test 1: API Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "temporal_connected": true
}
```

---

### Test 2: API Documentation

View interactive Swagger UI:
```
http://localhost:8000/docs
```

Or get JSON:
```bash
curl http://localhost:8000/
```

---

### Test 3: Trigger a Single Workflow

Start a log analysis for a single ERROR log:

```bash
curl -X POST http://localhost:8000/api/v1/analyze-log \
  -H "Content-Type: application/json" \
  -d '{
    "log_line": "ERROR: Database connection timeout after 30 seconds"
  }'
```

Expected response:
```json
{
  "workflow_id": "log-123456789",
  "status": "started",
  "message": "Workflow started for log analysis: ERROR: Database connection timeout..."
}
```

Save the `workflow_id` to check results later.

---

### Test 4: Check Workflow Result

Get the analysis result (wait 5-10 seconds after triggering):

```bash
curl http://localhost:8000/api/v1/workflow/log-123456789
```

Expected response (if still running):
```json
{
  "workflow_id": "log-123456789",
  "status": "error",
  "message": "workflow execution not found"
}
```

Or (if completed):
```json
{
  "workflow_id": "log-123456789",
  "status": "completed",
  "result": {
    "analysis": "..explanation..",
    "severity": "high"
  }
}
```

---

### Test 5: Batch Analyze Multiple Logs

Analyze multiple logs in parallel:

```bash
curl -X POST http://localhost:8000/api/v1/batch-analyze \
  -H "Content-Type: application/json" \
  -d '{
    "logs": [
      "ERROR: Connection refused on port 5432",
      "CRITICAL: ServiceUnavailable: API gateway timeout",
      "ERROR: Memory allocation failed"
    ]
  }'
```

Expected response:
```json
{
  "status": "submitted",
  "count": 3,
  "workflow_ids": [
    "log-111111",
    "log-222222",
    "log-333333"
  ]
}
```

---

### Test 6: View Temporal UI

Open Temporal dashboard:
```
http://localhost:8233
```

You'll see:
- Workflows being executed
- Activities (analysis, explanation, notification)
- Execution timelines
- Retry attempts

---

### Test 7: View Logs

Watch logs from different services:

```bash
# API logs
docker-compose logs -f app-api

# Worker logs (processes workflows)
docker-compose logs -f app-worker

# Streamer logs (watches log files)
docker-compose logs -f app-streamer

# All logs
docker-compose logs -f
```

---

### Test 8: Test Log Streaming

The streamer watches `app.log` and automatically triggers workflows for ERROR/CRITICAL logs.

Open a new terminal and generate logs:

```bash
# Terminal 1: Generate logs
docker-compose exec app-api sh -c 'python generate_logs.py' &

# Terminal 2: Watch streamer pick them up
docker-compose logs -f app-streamer

# Terminal 3: Monitor worker processing
docker-compose logs -f app-worker
```

---

## Part 2: Testing with Postman

### Import API Collection

Create a Postman request for each endpoint:

#### 1. Health Check
- **Method:** GET
- **URL:** `http://localhost:8000/health`
- **Headers:** None
- **Body:** None

#### 2. Analyze Single Log
- **Method:** POST
- **URL:** `http://localhost:8000/api/v1/analyze-log`
- **Headers:** `Content-Type: application/json`
- **Body:**
  ```json
  {
    "log_line": "ERROR: Critical system failure detected"
  }
  ```

#### 3. Batch Analyze
- **Method:** POST
- **URL:** `http://localhost:8000/api/v1/batch-analyze`
- **Headers:** `Content-Type: application/json`
- **Body:**
  ```json
  {
    "logs": [
      "ERROR: Connection refused",
      "CRITICAL: Out of memory",
      "ERROR: Timeout"
    ]
  }
  ```

#### 4. Get Workflow Result
- **Method:** GET
- **URL:** `http://localhost:8000/api/v1/workflow/{workflow_id}`
- **Headers:** None
- **Body:** None

---

## Part 3: Advanced Testing

### Performance Testing

Test with multiple concurrent requests:

```bash
#!/bin/bash

# Send 10 requests in parallel
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/analyze-log \
    -H "Content-Type: application/json" \
    -d "{\"log_line\": \"ERROR: Test log $i\"}" &
done

# Wait for all to complete
wait
echo "All requests sent"
```

### Load Testing with Apache Bench

```bash
# Send 100 requests with 10 concurrent
ab -n 100 -c 10 http://localhost:8000/health
```

### Network Testing

Check connectivity between services:

```bash
# From API container, reach Temporal
docker-compose exec app-api \
  sh -c 'telnet temporal 7233'

# Check environment variables
docker-compose exec app-api \
  sh -c 'echo $TEMPORAL_ADDRESS'
```

---

## Part 4: Cloud Run Deployment

### Prerequisites

```bash
# Install gcloud CLI (if not already installed)
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID
```

### Automated Deployment

```bash
# Make script executable
chmod +x deploy_to_cloud_run.sh

# Run deployment
./deploy_to_cloud_run.sh YOUR_PROJECT_ID us-central1
```

### Manual Deployment

```bash
# Set variables
export PROJECT_ID="your-project"
export REGION="us-central1"
export IMAGE_NAME="realtime-agent"

# Enable APIs
gcloud services enable run.googleapis.com artifactregistry.googleapis.com

# Create Artifact Registry
gcloud artifacts repositories create realtime-agent-repo \
    --repository-format=docker \
    --location=$REGION

# Build Docker image
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/realtime-agent-repo/${IMAGE_NAME}:latest .

# Push to Artifact Registry
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/realtime-agent-repo/${IMAGE_NAME}:latest

# Deploy API to Cloud Run
gcloud run deploy realtime-agent-api \
    --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/realtime-agent-repo/${IMAGE_NAME}:latest \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --memory=512Mi \
    --set-env-vars="ROLE=api,TEMPORAL_ADDRESS=YOUR_TEMPORAL_ADDRESS:7233,PORT=8000" \
    --port=8000

# Get API URL
gcloud run services describe realtime-agent-api --region=$REGION --format='value(status.url)'
```

### Test Cloud Run API

```bash
# Replace with your actual Cloud Run URL
API_URL="https://realtime-agent-api-ABC123DEF.run.app"

# Health check
curl $API_URL/health

# Trigger workflow
curl -X POST $API_URL/api/v1/analyze-log \
  -H "Content-Type: application/json" \
  -d '{"log_line": "ERROR: Cloud test"}'
```

---

## Part 5: Troubleshooting

### API Container Won't Start

```bash
# Check logs
docker-compose logs app-api

# Check if Temporal is ready
docker-compose exec app-api sh -c 'telnet temporal 7233'

# Rebuild
docker-compose build --no-cache app-api
docker-compose up app-api
```

### Connection Refused

```bash
# Verify Temporal is running
docker-compose ps temporal

# Check Temporal logs
docker-compose logs temporal

# Test connection
docker-compose exec app-api sh -c 'nc -zv temporal 7233'
```

### Workflow Not Processing

```bash
# Check worker is running
docker-compose ps app-worker

# Check worker logs
docker-compose logs app-worker

# Verify task queue
docker-compose exec app-api sh -c 'python -c "from temporalio.client import Client; print(\"OK\")"'
```

### API Returns 503 (Service Unavailable)

```bash
# Temporal client not connected
# Solution: Wait longer or restart
docker-compose restart app-api
sleep 5
curl http://localhost:8000/health
```

---

## Part 6: Cleanup

### Stop Local Services

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (database data)
docker-compose down -v

# Remove local images
docker rmi realtime-agent:latest
```

### Clean Cloud Run

```bash
# Delete Cloud Run service
gcloud run services delete realtime-agent-api --region=us-central1

# Delete Artifact Registry
gcloud artifacts repositories delete realtime-agent-repo --location=us-central1
```

---

## Part 7: Quick Reference

| Action | Command |
|--------|---------|
| Start services | `docker-compose up -d` |
| Stop services | `docker-compose down` |
| View logs | `docker-compose logs -f app-api` |
| Test health | `curl http://localhost:8000/health` |
| Trigger workflow | `curl -X POST http://localhost:8000/api/v1/analyze-log -d '{"log_line":"ERROR: test"}'` |
| View Temporal UI | `http://localhost:8233` |
| View API docs | `http://localhost:8000/docs` |
| Deploy to Cloud Run | `./deploy_to_cloud_run.sh PROJECT_ID REGION` |
| Check Cloud Run logs | `gcloud run logs read SERVICE_NAME --region=REGION` |

---

## Example: Full End-to-End Test

```bash
#!/bin/bash

# 1. Start services
docker-compose up -d
sleep 15

# 2. Health check
echo "Testing health..."
curl http://localhost:8000/health

# 3. Trigger workflow
echo "Triggering workflow..."
RESPONSE=$(curl -X POST http://localhost:8000/api/v1/analyze-log \
  -H "Content-Type: application/json" \
  -d '{"log_line": "ERROR: Integration test"}')

WORKFLOW_ID=$(echo $RESPONSE | grep -o '"workflow_id":"[^"]*"' | cut -d'"' -f4)
echo "Workflow ID: $WORKFLOW_ID"

# 4. Wait for completion
sleep 10

# 5. Get result
echo "Getting result..."
curl http://localhost:8000/api/v1/workflow/$WORKFLOW_ID

# 6. View Temporal UI
echo "Open http://localhost:8233 to view Temporal dashboard"
echo "Open http://localhost:8000/docs for API documentation"
```

