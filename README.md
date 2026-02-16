# 🚀 Real-Time Log Analysis Agent with Temporal Workflows

A **production-ready real-time log monitoring system** with AI-powered analysis, built using **Temporal Workflows** for reliable orchestration, automatic retries, and complete execution visibility.

**Key Features:**
- ✨ Real-time log analysis with LLM-powered explanations
- 📊 Interactive dashboard with real-time monitoring charts
- 🔄 Durable workflows with automatic retry logic
- 🐳 Fully containerized for Cloud Run deployment
- 📈 Comprehensive workflow statistics and tracking
- ✉️ Automated email alerting
- 🌐 REST API for programmatic access

---

## 📌 Overview

The system continuously monitors application logs, classifies errors, generates AI-powered explanations, and sends notifications—all orchestrated through **Temporal Workflows** for maximum reliability.

### Workflow Pipeline:
```
Logs → Analyzer (LLM) → Explainer (LLM) → Notifier (Email) → Dashboard
```

Each workflow:
1. **Analyzes** logs to detect critical issues
2. **Explains** root causes using Groq LLM
3. **Notifies** via email with actionable insights
4. **Tracks** execution with full visibility

---

## 🧠 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MONITORING PIPELINE                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  generate_logs.py     Generates sample error logs           │
│         ↓                                                    │
│  app.log              Log file with errors                  │
│         ↓                                                    │
│  Streamer Service     Reads logs → sends to API             │
│         ↓                                                    │
│  API Service          POST /analyze-log → Temporal          │
│         ↓                                                    │
│  Temporal Workflow    Durable workflow orchestration        │
│         ↓                                                    │
│  Worker Service       Executes activities on task queue     │
│         ↓                                                    │
│  ┌─────────────────────────────────────────┐               │
│  │ Analyzer Activity (LLM)                 │               │
│  │ • Classify log type                     │               │
│  │ • Detect severity                       │               │
│  │ • Extract error details                 │               │
│  └─────────────────────────────────────────┘               │
│         ↓                                                    │
│  ┌─────────────────────────────────────────┐               │
│  │ Explainer Activity (LLM)                │               │
│  │ • Generate root cause analysis          │               │
│  │ • Suggest fixes                         │               │
│  │ • Add context                           │               │
│  └─────────────────────────────────────────┘               │
│         ↓                                                    │
│  ┌─────────────────────────────────────────┐               │
│  │ Notifier Activity                       │               │
│  │ • Send email alerts                     │               │
│  │ • Log to database                       │               │
│  └─────────────────────────────────────────┘               │
│         ↓                                                    │
│  Dashboard            Real-time monitoring & charts         │
│  • Status Distribution Chart                               │
│  • Issue Categories Chart                                  │
│  • Success Rate Chart                                      │
│  • Workflow History Table                                  │
│  • Live Statistics                                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Language** | Python 3.11+ |
| **Workflow Engine** | Temporal (DDD pattern) |
| **LLM Provider** | Groq API (llama models) |
| **Web Framework** | FastAPI |
| **Containers** | Docker & Docker Compose |
| **Cloud Platform** | Google Cloud Run |
| **Frontend** | HTML5 + Chart.js |
| **Database** | In-memory (extensible to persistent DB) |

---

## 📂 Project Structure

```
real-time-log-analysis-agent/
│
├── README.md                         # This file
├── QUICKSTART.md                     # Quick start guide
├── CLOUD_RUN_GUIDE.md                # GCP Cloud Run deployment
├── CLOUD_BUILD_GUIDE.md              # Cloud Build CI/CD setup
├── GCP_DEPLOY_SIMPLE.md              # Simple one-command deployment
│
├── api.py                            # FastAPI server + dashboard host
├── config.py                         # Configuration & env vars
├── dashboard.html                    # Real-time monitoring dashboard
├── generate_logs.py                  # Log generator for testing
│
├── temporal_app/                     # Temporal workflow code
│   ├── __init__.py
│   ├── workflow.py                   # LogWorkflow orchestration
│   ├── activities.py                 # Analyzer, Explainer, Notifier
│   ├── worker.py                     # Worker process
│   ├── client.py                     # Workflow client
│   └── stream_client.py              # Log file streamer
│
├── agents/                           # AI agents (backup implementation)
│   ├── __init__.py
│   ├── analyzer.py                   # Log classification
│   ├── explainer.py                  # Explanation generation
│   ├── notifier.py                   # Email notifications
│   └── collector.py                  # Log collection
│
├── docker/                           # Docker configuration
│   └── entrypoint.sh                 # Multi-role entry point
│
├── scripts/                          # Deployment scripts
│   ├── build_push_deploy_worker.ps1  # PowerShell: Build & deploy
│   └── cloud-build-worker.ps1        # Cloud Build integration
│
├── docs/                             # Additional documentation
│   ├── README.md                     # Original docs
│   └── TEST_REPORT.md                # Test results
│
├── Dockerfile                        # Multi-stage production build
├── docker-compose.yml                # Local Temporal server
├── .dockerignore                     # Docker build ignore list
│
├── cloudbuild.yaml                   # Cloud Build config (API/Streamer)
├── cloudbuild-worker.yaml            # Cloud Build config (Worker)
├── cloud-build-commands.sh           # Cloud Build CLI commands
│
├── deploy_to_cloud_run.sh            # Bash deployment script
├── deploy_to_cloud_run.ps1           # PowerShell deployment script
│
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment template
└── .gitignore                        # Git ignore rules
```

---

## 🚀 Quick Start (Local)

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Groq API key: [Get free key](https://console.groq.com)
- (Optional) SMTP credentials for email alerts

### 1️⃣ Clone & Setup

```bash
git clone https://github.com/Ragulm/real-time-log-analysis-agent.git
cd real-time-log-analysis-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy env template and fill in secrets
cp .env.example .env
# Edit .env with your GROQ_API_KEY, SMTP settings, etc.
```

### 2️⃣ Start Temporal Server

```bash
docker-compose up -d
```

Check Temporal UI: `http://localhost:8233`

### 3️⃣ Start Services (in separate terminals)

**Terminal 1 - Worker (listens for tasks)**
```bash
python -m temporal_app.worker
```

**Terminal 2 - Streamer (watches logs & sends to API)**
```bash
python -m temporal_app.stream_client
```

**Terminal 3 - API Server**
```bash
uvicorn api:app --reload --port 8000
```

**Terminal 4 - Log Generator (optional)**
```bash
python generate_logs.py
```

### 4️⃣ Access Dashboard

Open browser: `http://localhost:8000/dashboard`

You'll see:
- ✅ Real-time workflow status
- 📊 Charts: Status distribution, issue categories, success rate
- 📋 Workflow history with details
- 🔍 Search and filter capabilities

---

## 🐳 Docker Deployment

### Local Docker

```bash
# Build image
docker build -t realtime-agent:latest .

# Run worker (default role)
docker run -e TEMPORAL_ADDRESS=host.docker.internal:7233 \
           -e GROQ_API_KEY=your-key-here \
           realtime-agent:latest

# Run streamer
docker run -e ROLE=streamer \
           -e TEMPORAL_ADDRESS=host.docker.internal:7233 \
           -e API_URL=http://host.docker.internal:8000 \
           realtime-agent:latest

# Run API
docker run -p 8000:8000 \
           -e ROLE=api \
           -e TEMPORAL_ADDRESS=host.docker.internal:7233 \
           realtime-agent:latest
```

---

## ☁️ Google Cloud Run Deployment

### Quickest Method: One Command

```bash
bash GCP_DEPLOY_SIMPLE.md
```

### Manual Deployment (Step by Step)

See [CLOUD_RUN_GUIDE.md](CLOUD_RUN_GUIDE.md) for detailed instructions.

**Summary:**
```bash
# 1. Set variables
PROJECT_ID="your-gcp-project"
REGION="us-central1"

# 2. Build and push to Artifact Registry
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/realtime-agent/app:latest .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/realtime-agent/app:latest

# 3. Deploy API service
gcloud run deploy realtime-agent-api \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/realtime-agent/app:latest \
  --region=${REGION} \
  --set-env-vars="ROLE=api,TEMPORAL_ADDRESS=YOUR_TEMPORAL_IP:7233,GROQ_API_KEY=your-key"

# 4. Deploy Worker service (keep-alive)
gcloud run deploy realtime-agent-worker \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/realtime-agent/app:latest \
  --region=${REGION} \
  --set-env-vars="ROLE=worker,TEMPORAL_ADDRESS=YOUR_TEMPORAL_IP:7233,GROQ_API_KEY=your-key" \
  --min-instances=1

# 5. Deploy Streamer service
gcloud run deploy realtime-agent-streamer \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/realtime-agent/app:latest \
  --region=${REGION} \
  --set-env-vars="ROLE=streamer,TEMPORAL_ADDRESS=YOUR_TEMPORAL_IP:7233,API_URL=https://realtime-agent-api-xxx.run.app"
```

---

## 📊 Dashboard Features

### Real-Time Monitoring Charts

1. **Status Distribution (Doughnut Chart)**
   - Shows count of Completed, Running, Error workflows
   - Color-coded for quick status assessment

2. **Issue Categories (Pie Chart)**
   - Breaks down problems by type
   - Examples: Disk Space, Database, API Rate Limit, etc.

3. **Success Rate (Bar Chart)**
   - Compares successful vs failed workflows
   - Useful for SLA tracking

### Workflow Table
- Workflow ID, log details, status, category
- Duration tracking
- Search and filter capabilities
- Real-time updates every 3 seconds

### Statistics Dashboard
- Total workflows processed
- Completed workflows count
- Currently running workflows
- Error count

---

## 🔌 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check + Temporal status |
| `/dashboard` | GET | Interactive monitoring dashboard |
| `/api/v1/analyze-log` | POST | Trigger workflow for log analysis |
| `/api/v1/workflow/{id}` | GET | Get workflow result |
| `/api/v1/workflows` | GET | Get all workflows + statistics |
| `/diag` | GET | Diagnostic info (Temporal, Groq, DNS) |

### Example: Analyze a Log

```bash
curl -X POST http://localhost:8000/api/v1/analyze-log \
  -H "Content-Type: application/json" \
  -d '{
    "log_line": "ERROR - CRITICAL FAILURE: Database connection timeout"
  }'
```

Response:
```json
{
  "workflow_id": "log-abc123def456",
  "status": "started",
  "message": "Workflow started"
}
```

### Get Workflow Result

```bash
curl http://localhost:8000/api/v1/workflow/log-abc123def456
```

Response:
```json
{
  "workflow_id": "log-abc123def456",
  "status": "completed",
  "result": {
    "is_issue": true,
    "issue_type": "Database Connection",
    "explanation": "Database connection failed due to network timeout...",
    "category": "database"
  }
}
```

---

## ⚙️ Environment Configuration

Create `.env` file (or set environment variables):

```env
# Temporal Server
TEMPORAL_ADDRESS=localhost:7233
WAIT_FOR_TEMPORAL=true

# Groq LLM
GROQ_API_KEY=your-groq-api-key-here
GROQ_CALL_TIMEOUT=30

# Email Notifications (SMTP)
SENDER_EMAIL=alerts@example.com
SENDER_PASSWORD=your-smtp-password
RECIPIENT_EMAIL=oncall@example.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Application
PORT=8000
ROLE=api  # or 'worker', 'streamer', 'generator'
```

### For Cloud Run: Use Secret Manager

```bash
# Store sensitive data in GCP Secret Manager
echo -n "your-api-key" | gcloud secrets create groq-api-key --data-file=-
echo -n "your-smtp-password" | gcloud secrets create smtp-password --data-file=-

# Deploy with secrets
gcloud run deploy realtime-agent-api \
  --set-secrets="GROQ_API_KEY=groq-api-key:latest,SENDER_PASSWORD=smtp-password:latest" \
  --set-env-vars="SENDER_EMAIL=alerts@example.com,RECIPIENT_EMAIL=oncall@example.com"
```

---

## 🔄 Workflow Retry Policy

Temporal automatically retries on transient failures:

- ✅ SMTP connection errors → Retry 3x
- ✅ Network timeouts → Exponential backoff
- ✅ LLM API throttling → Automatic retry
- ✅ Database errors → Smart retry logic

No manual retry loops needed!

---

## 🖥️ Web Interfaces

### Temporal UI (Workflow Monitoring)
```
http://localhost:8233
```
- View all workflows and executions
- Timeline of activities
- Execution history
- Retry attempts and failures

### Application Dashboard (Real-Time Analysis)
```
http://localhost:8000/dashboard
```
- Real-time charts and statistics
- Workflow monitoring
- Search and filter logs
- Issue categorization

---

## 📝 Environment Variables Explained

| Variable | Purpose | Example |
|----------|---------|---------|
| `TEMPORAL_ADDRESS` | Temporal server connection | `localhost:7233` |
| `GROQ_API_KEY` | LLM API authentication | `gsk_...` |
| `GROQ_CALL_TIMEOUT` | LLM request timeout (seconds) | `30` |
| `SENDER_EMAIL` | Source email for alerts | `alerts@company.com` |
| `SENDER_PASSWORD` | SMTP password (store securely!) | Secret Manager |
| `RECIPIENT_EMAIL` | Destination for alerts | `oncall@company.com` |
| `SMTP_SERVER` | Mail server | `smtp.gmail.com` |
| `SMTP_PORT` | Mail server port | `587` |
| `ROLE` | Service role | `api`, `worker`, `streamer` |
| `PORT` | API server port | `8000` |

---

## 🔍 Monitoring & Debugging

### Check Worker Health
```bash
curl http://localhost:8000/health
```

### View Temporal Workflows
```bash
# Using Temporal CLI
temporal workflow list

# Via API
curl http://localhost:8000/api/v1/workflows | python -m json.tool
```

---

## ✅ Key Benefits

| Traditional Approach | Temporal Workflow |
|---------------------|-------------------|
| Infinite loops | Durable workflows |
| Manual retry logic | Built-in retries |
| Crash = data loss | Automatic recovery |
| No observability | Full execution history |
| Hard debugging | Timeline-based debugging |

---

## 📚 Additional Resources

- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[CLOUD_RUN_GUIDE.md](CLOUD_RUN_GUIDE.md)** - Complete GCP deployment guide
- **[CLOUD_BUILD_GUIDE.md](CLOUD_BUILD_GUIDE.md)** - Set up CI/CD with Cloud Build
- **[GCP_DEPLOY_SIMPLE.md](GCP_DEPLOY_SIMPLE.md)** - One-command deployment
- **[DOCKER_RUN_GUIDE.md](DOCKER_RUN_GUIDE.md)** - Docker local setup
- **[Temporal Docs](https://docs.temporal.io/)** - Temporal workflow documentation

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 📞 Support

- **Issues**: Open an issue on [GitHub](https://github.com/Ragulm/real-time-log-analysis-agent/issues)
- **Discussions**: Join conversations on GitHub Discussions
- **Temporal Community**: [Temporal Community Slack](https://temporal.io/slack)

---

**Last Updated**: February 2026  
**GitHub**: https://github.com/Ragulm/real-time-log-analysis-agent
