# 🚀 Temporal Log Monitoring Workflow

A real-time log monitoring system implemented using **Temporal Workflows** to provide reliable orchestration, automatic retries, and full execution visibility for log analysis and alerting.

This project demonstrates how a traditional async-based monitoring system can be upgraded into a **durable, fault-tolerant workflow architecture**.

---

## 📌 Overview

The system continuously monitors application logs and triggers a Temporal workflow whenever a critical error is detected.

Each workflow execution performs:

1. Log analysis  
2. Root cause explanation using LLM  
3. Alert notification via email  

Temporal ensures reliability even if workers crash or restart.

---

## 🧠 Architecture Flow

```
generate_logs.py
        ↓
app.log
        ↓
stream_client.py
        ↓
Temporal Client
        ↓
Temporal Workflow
        ↓
Analyzer → Explainer → Notifier
```

---

## ⚙️ Tech Stack

- Python 3.10+
- Temporal (Docker)
- Temporal Python SDK
- Groq LLM
- Async Programming
- Docker & Docker Compose

---

## 📂 Project Structure

```
realtime_agent/
│
├── README.md                         # Main documentation (Temporal version)
│
├── docs/
│   ├── OLD_README.md                 # Old project documentation
│   └── TEST_REPORT.md                # Previous test report
│
├── main.py                           # Initial non-Temporal implementation (reference)
│
├── temporal_app/
│   ├── __init__.py
│   ├── workflow.py                   # Temporal workflow orchestration
│   ├── activities.py                 # Analyzer, Explainer, Notifier activities
│   ├── worker.py                     # Temporal worker
│   ├── client.py                     # Workflow starter
│   └── stream_client.py              # Watches logs & triggers workflows
│
├── agents/
│   ├── __init__.py
│   ├── collector.py                  # Log file watcher
│   ├── analyzer.py                   # Issue classification
│   ├── explainer.py                  # LLM-based explanation
│   └── notifier.py                   # Email notification
│
├── generate_logs.py                  # Log generator
├── config.py                         # Environment configuration
├── docker-compose.yml                # Temporal server setup
├── requirements.txt
└── .gitignore
```

---

## ▶️ How to Run (Correct Order)

### 1️⃣ Start Temporal Server

```bash
docker-compose up
```

Check Temporal UI:

```
http://localhost:8233
```

---

### 2️⃣ Start Temporal Worker

```bash
python -m temporal_app.worker
```

Keep this terminal running.

---

### 3️⃣ Start Log Generator

```bash
python generate_logs.py
```

This continuously writes logs into `app.log`.

---

### 4️⃣ Start Stream Client

```bash
python -m temporal_app.stream_client
```

This watches the log file and triggers Temporal workflows for error logs.

---

## 🐳 Docker & Google Cloud Run (quick guide)

This repository did not previously include an application image — it only provided Docker Compose for Temporal itself. Added a multi-role `Dockerfile` so you can run the **worker**, **streamer**, or **log generator** from a single image.

- Default role: `worker` (set `ROLE` to `streamer` or `generator` to change behavior)
- Location of entrypoint: `docker/entrypoint.sh`

Build & run locally (example):

```bash
# build
docker build -t realtime-agent:latest .

# run worker (default)
docker run --rm realtime-agent:latest

# run streamer
docker run --rm -e ROLE=streamer realtime-agent:latest
```

Deploy to Cloud Run (recommended: deploy the `worker` as a Cloud Run **service** or use **Cloud Run Jobs** for batch runs):

```bash
# build and push to Google Container Registry or Artifact Registry
docker build -t gcr.io/PROJECT-ID/realtime-agent:latest .
docker push gcr.io/PROJECT-ID/realtime-agent:latest

# deploy worker to Cloud Run (set min-instances > 0 if you need always-on)
gcloud run deploy realtime-agent-worker \
  --image gcr.io/PROJECT-ID/realtime-agent:latest \
  --region=REGION \
  --platform=managed \
  --set-env-vars=ROLE=worker \
  --concurrency=1 \
  --memory=512Mi

# OR deploy streamer as a separate service
gcloud run deploy realtime-agent-streamer \
  --image gcr.io/PROJECT-ID/realtime-agent:latest \
  --set-env-vars=ROLE=streamer
```

Notes:
- Cloud Run is request-driven; for long-running workers consider Cloud Run Jobs or set `min-instances` to keep a worker warm.
- Ensure your Cloud Run service can reach your Temporal server (VPC connector or deploy Temporal in same project / network).

---

### 5️⃣ Start the API Server (Optional)

```bash
python -m api
```

This hosts an interactive dashboard at:

```
http://localhost:8000/dashboard
```

The API also provides:
- `/api/v1/analyze-log` — POST endpoint to trigger log analysis
- `/api/v1/workflow/{workflow_id}` — GET workflow results
- `/api/v1/batch-analyze` — Analyze multiple logs
- `/health` — Health check endpoint

---

### 6️⃣ Observe Results

- New workflows appear in Temporal UI
- Activity execution timeline is visible
- Retry attempts are recorded
- Email notifications are triggered
- (If API running) Dashboard updates in real-time

---

## 🔄 Retry Policy

Temporal RetryPolicy automatically handles transient failures such as:

- SMTP errors
- Network instability
- Temporary API failures

Retries occur without manual loops or custom logic.

---

## 🖥️ Web Interfaces

### Temporal UI

Access Temporal Workflow Dashboard:

```
http://localhost:8233
```

Features:

- Workflow execution history
- Activity timelines
- Retry attempts
- Failure diagnostics

### Application Dashboard

Access the Real-Time Log Analysis Dashboard (when API is running):

```
http://localhost:8000/dashboard
```

Features:

- Interactive UI to submit logs for analysis
- Real-time workflow status
- Analysis results and explanations
- Error tracking and notifications

---

## 📘 Documentation Note

- `main.py` is kept for reference (non-Temporal version).
- Active production logic uses Temporal workflows.
- Previous documentation is preserved under the `docs/` directory.

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

## 🎯 Learning Outcomes

- Temporal workflow orchestration
- Activity-based backend design
- Retry & timeout handling
- Event-driven systems
- LLM integration
- Production-grade reliability patterns

---
