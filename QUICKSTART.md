# Quick Start - Real-Time Log Analysis Agent

**Status: ✅ All systems running and tested locally**

---

## 🚀 Start Testing RIGHT NOW (5 seconds)

### 1. Services Already Running
All services are up and connected:
- ✅ API on `http://localhost:8000`
- ✅ Temporal on `http://localhost:7233`
- ✅ PostgreSQL on `localhost:5432`
- ✅ Worker processing workflows
- ✅ Streamer watching logs

### 2. Test API Health
```bash
curl http://localhost:8000/health
```

Response:
```json
{"status": "healthy", "temporal_connected": true}
```

### 3. Trigger a Workflow
```bash
curl -X POST http://localhost:8000/api/v1/analyze-log \
  -H "Content-Type: application/json" \
  -d '{"log_line": "ERROR: Database connection timeout"}'
```

Response:
```json
{
  "workflow_id": "log-1234567890",
  "status": "started",
  "message": "Workflow started for log analysis: ERROR: Database connection timeout"
}
```

### 4. View Results
```bash
curl http://localhost:8000/api/v1/workflow/log-1234567890
```

---

## 📊 View Workflow Execution

Open **Temporal UI** to see workflows running:
```
http://localhost:8233
```

You'll see:
- Workflow executions
- Activity timelines (analysis, explanation, notification)
- Retries and failures
- Full audit trail

---

## 📚 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Health check |
| GET | `/docs` | Interactive API documentation (Swagger UI) |
| POST | `/api/v1/analyze-log` | Analyze single log |
| POST | `/api/v1/batch-analyze` | Analyze multiple logs |
| GET | `/api/v1/workflow/{id}` | Get workflow result |

---

## 💻 Common Commands

### Test Individual Endpoints

**Health:**
```bash
curl http://localhost:8000/health
```

**Single Log Analysis:**
```bash
curl -X POST http://localhost:8000/api/v1/analyze-log \
  -H "Content-Type: application/json" \
  -d '{"log_line": "CRITICAL: Service unavailable"}'
```

**Batch Analysis:**
```bash
curl -X POST http://localhost:8000/api/v1/batch-analyze \
  -H "Content-Type: application/json" \
  -d '{
    "logs": [
      "ERROR: Connection refused",
      "CRITICAL: Out of memory",
      "ERROR: Timeout"
    ]
  }'
```

**Get Workflow Result:**
```bash
curl http://localhost:8000/api/v1/workflow/WORKFLOW_ID
```

---

## 📋 View Logs

Watch what's happening in real-time:

```bash
# API logs
docker-compose logs -f app-api

# Worker logs (processing workflows)
docker-compose logs -f app-worker

# Streamer logs (watching log files)
docker-compose logs -f app-streamer

# All logs
docker-compose logs -f
```

---

## 🛑 Stop/Start Services

### Stop all services
```bash
docker-compose down
```

### Restart all services
```bash
docker-compose up -d
```

### Rebuild and restart (if code changed)
```bash
docker-compose up --build -d
```

---

## ☁️ Deploy to Google Cloud Run

### Prerequisites
- Google Cloud Project with billing enabled
- `gcloud` CLI installed
- `GROQ_API_KEY` environment variable set

### Quick Deploy (3 commands)
```bash
# 1. Set your project ID
export PROJECT_ID="your-gcp-project-id"

# 2. Run automated deployment
chmod +x deploy_to_cloud_run.sh
./deploy_to_cloud_run.sh $PROJECT_ID us-central1

# 3. Script handles:
# - Building Docker image
# - Pushing to Artifact Registry
# - Deploying API service (public HTTPS URL)
# - Deploying worker service (background processing)
# - Deploying streamer service (log watching)
```

### Get Your Cloud Run URL
```bash
gcloud run services describe realtime-agent-api \
  --region=us-central1 \
  --format='value(status.url)'
```

### Test Cloud Run API
```bash
API_URL="https://realtime-agent-api-ABC123.run.app"

# Health check
curl $API_URL/health

# Trigger workflow
curl -X POST $API_URL/api/v1/analyze-log \
  -H "Content-Type: application/json" \
  -d '{"log_line": "ERROR: Cloud test"}'
```

---

## 🧪 Full Testing Workflow

```bash
#!/bin/bash

# 1. Health check
echo "1. Checking API health..."
curl http://localhost:8000/health

# 2. Single workflow
echo "2. Triggering single workflow..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/analyze-log \
  -H "Content-Type: application/json" \
  -d '{"log_line": "ERROR: Test"}')
WORKFLOW_ID=$(echo $RESPONSE | grep -o '"workflow_id":"[^"]*"' | cut -d'"' -f4)
echo "Workflow ID: $WORKFLOW_ID"

# 3. Wait for processing
echo "3. Waiting for workflow to process..."
sleep 5

# 4. Check result
echo "4. Checking workflow result..."
curl http://localhost:8000/api/v1/workflow/$WORKFLOW_ID

# 5. View Temporal UI
echo "5. Open http://localhost:8233 to see workflow in Temporal UI"

# 6. Batch test
echo "6. Testing batch analysis..."
curl -X POST http://localhost:8000/api/v1/batch-analyze \
  -H "Content-Type: application/json" \
  -d '{
    "logs": [
      "ERROR: Connection failed",
      "CRITICAL: System down"
    ]
  }'
```

---

## 📦 Files Overview

| File | Purpose |
|------|---------|
| `api.py` | FastAPI application with REST endpoints |
| `Dockerfile` | Multi-role Docker image (api, worker, streamer, generator) |
| `docker-compose.yml` | Container orchestration (Temporal, PostgreSQL, app services) |
| `deploy_to_cloud_run.sh` | Automated Cloud Run deployment script |
| `temporal_app/workflow.py` | Temporal workflow definition |
| `temporal_app/activities.py` | Workflow activities (analysis, explanation, notification) |
| `TESTING_GUIDE.md` | Comprehensive testing documentation |
| `CLOUD_RUN_GUIDE.md` | Detailed Cloud Run deployment guide |
| `DOCKER_RUN_GUIDE.md` | Docker and local testing guide |

---

## 🔧 Troubleshooting

### API not responding
```bash
# Check if container is running
docker-compose ps app-api

# Check logs
docker-compose logs app-api

# Restart
docker-compose restart app-api
sleep 5
curl http://localhost:8000/health
```

### Workflow not processing
```bash
# Check worker is running
docker-compose ps app-worker

# Check worker logs
docker-compose logs app-worker

# Verify Temporal is accessible
docker-compose exec app-api \
  sh -c 'nc -zv temporal 7233'
```

### Connection to Temporal failed
```bash
# Check Temporal status
docker-compose ps temporal

# Check Temporal logs
docker-compose logs temporal

# Restart Temporal
docker-compose restart temporal
sleep 10
curl http://localhost:8000/health
```

---

## 📞 Support

### Check System Status
```bash
docker-compose ps
```

### View All Logs
```bash
docker-compose logs --tail=100
```

### Full System Reset
```bash
# Stop and remove everything (keeps images)
docker-compose down

# Stop and remove everything including volumes
docker-compose down -v

# Restart
docker-compose up -d
```

---

## 🎯 Next Steps

1. **Test locally** (you're here! ✅)
   - API is responding
   - Workflows are processing
   - Temporal UI shows execution

2. **Deploy to Cloud Run**
   ```bash
   ./deploy_to_cloud_run.sh YOUR_PROJECT_ID us-central1
   ```

3. **Monitor & Scale**
   - View logs: `gcloud run logs read realtime-agent-api`
   - Scale up: `gcloud run deploy --min-instances=2`
   - Set up alerts

4. **Integrate with Your Systems**
   - Connect to your log sources
   - Set up notifications (Slack, email, PagerDuty)
   - Create custom analysis rules

---

## ✨ You're All Set!

Your Real-Time Log Analysis Agent is:
- ✅ Built and containerized
- ✅ Running locally with all services
- ✅ Ready to deploy to Cloud Run
- ✅ Has REST API for integration

**Start testing now:**
```bash
curl http://localhost:8000/health
```

**Deploy to cloud:**
```bash
./deploy_to_cloud_run.sh YOUR_PROJECT_ID us-central1
```

---

**Questions or issues?** Check the detailed guides:
- `TESTING_GUIDE.md` — Complete testing reference
- `CLOUD_RUN_GUIDE.md` — Cloud deployment details
- `DOCKER_RUN_GUIDE.md` — Docker configuration

