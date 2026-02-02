# Real-Time Log Analysis Agent

A real-time, multi-agent AI system built in Python using LangGraph and Groq.  
The system continuously monitors application logs, detects critical issues, analyzes them using LLMs, and sends automated email notifications with actionable remediation steps.

---

## 🚀 Features

- **Real-Time Monitoring**  
  Continuously tails the application log file and processes new entries instantly.

- **Intelligent Analysis**  
  Uses `llama-3.1-8b-instant` to efficiently filter and identify ERROR and CRITICAL log events.

- **Root Cause Explanation**  
  Uses `llama-3.3-70b-versatile` to generate detailed explanations and potential fixes for detected issues.

- **Automated Alerts**  
  Sends email notifications with severity levels, issue details, and suggested fixes via SMTP.

- **Simulated Environment**  
  Includes a log generator to simulate user traffic and random system failures for testing.

---

## 🛠️ Architecture

The system follows a multi-agent workflow inspired by LangGraph:

1. Collector Agent – Reads new log lines in real time  
2. Analyzer Agent – Determines whether a log entry represents a real issue using an LLM  
3. Explainer Agent – Generates root-cause explanations and corrective actions  
4. Notifier Agent – Sends real-time email alerts  

```
Log File
   ↓
Collector
   ↓
Analyzer (Groq LLM)
   ↓
Explainer (Groq LLM)
   ↓
Email Notifier (SMTP)
```

---

## 📋 Prerequisites

- Python 3.8+
- Groq API Key
- Gmail App Password (for email alerts)

---

## ⚙️ Installation

### Clone the repository
```bash
git clone <repository-url>
cd realtime_agent
```

### Install dependencies
```bash
pip install langchain-groq langgraph python-dotenv pydantic
```

### Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
LOG_FILE_PATH=app.log

# Email Configuration
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
RECIPIENT_EMAIL=recipient@example.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

---

## 🏃 Usage

### Terminal 1 – Start the log generator
```bash
python generate_logs.py
```

### Terminal 2 – Start the agent system
```bash
python main.py
```

---

## 📁 Project Structure

```
realtime_agent/
├── main.py
├── generate_logs.py
├── config.py
├── app.log
└── agents/
    ├── collector.py
    ├── analyzer.py
    ├── explainer.py
    └── notifier.py
```

---

## ✅ Project Status

✔ Completed  
✔ Tested with simulated logs  
✔ Production-logic ready  

---

## 🧠 Summary

This project demonstrates a real-time, multi-agent log monitoring system that reduces false alerts using LLM reasoning and enables faster incident response through automated email notifications.

---

## 👤 Author

Ragul  
Python Developer | LLM & Multi-Agent Systems
