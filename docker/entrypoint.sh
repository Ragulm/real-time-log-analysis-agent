#!/bin/sh
set -e

# Explicitly source environment variables if .env exists
if [ -f /app/.env ]; then
  . /app/.env
fi

wait_for_temporal() {
  ADDRESS="${TEMPORAL_ADDRESS:-temporal:7233}"
  echo "Waiting for Temporal at $ADDRESS..."
  python3 - <<'PY'
import socket, time, sys, os
address = os.getenv("TEMPORAL_ADDRESS", "temporal:7233")
host, port = address.split(":")
port = int(port)
for _ in range(30):
    try:
        s = socket.create_connection((host, port), 2)
        s.close()
        print("Temporal reachable")
        sys.exit(0)
    except Exception:
        time.sleep(1)
print("Timed out waiting for Temporal")
sys.exit(1)
PY
}

# Get the ROLE - default to api if not set
ROLE="${ROLE:-api}"
# Allow skipping Temporal readiness check in managed environments  
WAIT_FOR_TEMPORAL="${WAIT_FOR_TEMPORAL:-true}"
PORT="${PORT:-8080}"

# Debug output
echo ""
echo "========== CONTAINER STARTUP =========="
echo "ROLE = $ROLE"
echo "PORT = $PORT"
echo "WAIT_FOR_TEMPORAL = $WAIT_FOR_TEMPORAL"
if [ -n "$TEMPORAL_ADDRESS" ]; then
  echo "TEMPORAL_ADDRESS = $TEMPORAL_ADDRESS"
fi
echo "======================================="
echo ""

case "$ROLE" in

  api)
    echo "🌐 Starting FastAPI server on port ${PORT:-8080}"
    if [ "${WAIT_FOR_TEMPORAL}" != "false" ]; then
      wait_for_temporal
    else
      echo "Skipping Temporal readiness check (WAIT_FOR_TEMPORAL=false)"
    fi
    exec uvicorn api:app --host 0.0.0.0 --port ${PORT:-8080}
    ;;

  worker)
    echo "🔧 Starting HTTP health server and Temporal worker"

    cat > /tmp/health_server.py << 'EOF'
import http.server
import socketserver
import json
import os

class HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path.startswith('/health'):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = json.dumps({"status": "healthy", "role": "worker"})
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

PORT = int(os.getenv("PORT", "8080"))

with socketserver.TCPServer(("", PORT), HealthHandler) as httpd:
    print(f"Health server listening on port {PORT}")
    httpd.serve_forever()
EOF

    nohup python /tmp/health_server.py > /tmp/http_server.log 2>&1 &

    sleep 2

    if [ "${WAIT_FOR_TEMPORAL}" != "false" ]; then
      wait_for_temporal
    else
      echo "Skipping Temporal readiness check for worker (WAIT_FOR_TEMPORAL=false)"
    fi

    echo "Starting Temporal worker..."
    python3 -m temporal_app.worker 2>&1
    ;;

  streamer)
    echo "📡 Starting stream client"

    # Start an HTTP health server so Cloud Run sees the container as listening on $PORT
    cat > /tmp/health_server.py << 'EOF'
import http.server
import socketserver
import json
import os

class HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path.startswith('/health'):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = json.dumps({"status": "healthy", "role": "streamer"})
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

PORT = int(os.getenv("PORT", "8080"))

with socketserver.TCPServer(("", PORT), HealthHandler) as httpd:
    print(f"Health server listening on port {PORT}")
    httpd.serve_forever()
EOF

    nohup python /tmp/health_server.py > /tmp/http_server.log 2>&1 &

    sleep 1

    if [ "${WAIT_FOR_TEMPORAL}" != "false" ]; then
      wait_for_temporal
    else
      echo "Skipping Temporal readiness check for streamer (WAIT_FOR_TEMPORAL=false)"
    fi

    exec python -m temporal_app.stream_client
    ;;

  generator)
    echo "📝 Starting log generator"
    exec python generate_logs.py
    ;;

  *)
    echo "Unknown role. Starting API by default."
    exec uvicorn api:app --host 0.0.0.0 --port ${PORT:-8080}
    ;;

esac
