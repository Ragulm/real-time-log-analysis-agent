#!/bin/sh
set -e

ROLE=${ROLE:-worker}

case "$ROLE" in
  worker)
    echo "🔧 Starting Temporal worker"
    exec python -m temporal_app.worker
    ;;
  streamer)
    echo "📡 Starting stream client"
    exec python -m temporal_app.stream_client
    ;;
  api)
    echo "🌐 Starting REST API server"
    exec python api.py
    ;;
  generator)
    echo "📝 Starting log generator"
    exec python generate_logs.py
    ;;
  *)
    echo "Running custom command: $@"
    exec "$@"
    ;;
esac
