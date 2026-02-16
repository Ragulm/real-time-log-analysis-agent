#!/bin/bash
# Quick reference commands for Cloud Build operations
# Usage: source cloud-build-commands.sh (or copy individual commands)

PROJECT_ID="project-294f73a2-90e4-4430-b84"
REGION="us-central1"
REGISTRY="us-central1-docker.pkg.dev"
REPO="realtime-agent-repo"
IMAGE_NAME="realtime-agent"

# ====== BUILD COMMANDS ======

# Build and deploy worker only (fastest)
build_worker() {
    echo "🏗️ Building worker image..."
    gcloud builds submit \
        --config=cloudbuild-worker.yaml \
        --project=$PROJECT_ID
}

# Build all services at once
build_all() {
    echo "🏗️ Building all services..."
    gcloud builds submit \
        --config=cloudbuild.yaml \
        --project=$PROJECT_ID
}

# Build with no cache (for fresh builds)
build_worker_nocache() {
    echo "🏗️ Building worker image (no cache)..."
    gcloud builds submit \
        --config=cloudbuild-worker.yaml \
        --substitutions _NO_CACHE="--no-cache" \
        --project=$PROJECT_ID
}

# ====== DEPLOYMENT COMMANDS ======

# Deploy worker from latest image
deploy_worker() {
    echo "🚀 Deploying worker..."
    gcloud run deploy realtime-agent-worker \
        --image=$REGISTRY/$PROJECT_ID/$REPO/$IMAGE_NAME:worker-latest \
        --region=$REGION \
        --platform=managed \
        --no-allow-unauthenticated \
        --set-env-vars=ROLE=worker,TEMPORAL_ADDRESS=temporal.example.com:7233 \
        --project=$PROJECT_ID
}

# Deploy API from latest image
deploy_api() {
    echo "🚀 Deploying API..."
    gcloud run deploy realtime-agent-api \
        --image=$REGISTRY/$PROJECT_ID/$REPO/$IMAGE_NAME:api-latest \
        --region=$REGION \
        --platform=managed \
        --allow-unauthenticated \
        --set-env-vars=ROLE=api,TEMPORAL_ADDRESS=temporal.example.com:7233,PORT=8000 \
        --project=$PROJECT_ID
}

# ====== IMAGE MANAGEMENT ======

# List all images in repository
list_images() {
    echo "📦 Images in repository:"
    gcloud artifacts docker images list \
        $REGISTRY/$PROJECT_ID/$REPO \
        --project=$PROJECT_ID
}

# List all versions of worker image
list_worker_versions() {
    echo "📦 Worker image versions:"
    gcloud artifacts docker images list \
        $REGISTRY/$PROJECT_ID/$REPO \
        --include-tags \
        --project=$PROJECT_ID | grep worker
}

# Delete old image tag (cleanup)
delete_image_tag() {
    local tag=$1
    if [ -z "$tag" ]; then
        echo "Usage: delete_image_tag <tag>"
        return 1
    fi
    echo "🗑️ Deleting image tag: $tag"
    gcloud artifacts docker images delete \
        $REGISTRY/$PROJECT_ID/$REPO/$IMAGE_NAME:$tag \
        --project=$PROJECT_ID \
        --quiet
}

# ====== MONITORING ======

# List recent builds
list_builds() {
    echo "📋 Recent builds:"
    gcloud builds list \
        --limit=10 \
        --project=$PROJECT_ID
}

# Watch build logs (real-time)
watch_build() {
    local build_id=$1
    if [ -z "$build_id" ]; then
        echo "Usage: watch_build <build_id>"
        return 1
    fi
    echo "👀 Watching build: $build_id"
    gcloud builds log \
        $build_id \
        --stream \
        --project=$PROJECT_ID
}

# Get build status
build_status() {
    local build_id=$1
    if [ -z "$build_id" ]; then
        echo "Usage: build_status <build_id>"
        return 1
    fi
    gcloud builds describe $build_id --project=$PROJECT_ID
}

# ====== CLOUD RUN ======

# Show worker service details
describe_worker() {
    echo "📋 Worker service details:"
    gcloud run services describe realtime-agent-worker \
        --region=$REGION \
        --project=$PROJECT_ID
}

# Show latest worker deployment logs
worker_logs() {
    echo "📜 Worker service logs:"
    gcloud run services logs read realtime-agent-worker \
        --region=$REGION \
        --limit=50 \
        --project=$PROJECT_ID
}

# Stream worker logs (real-time)
worker_logs_stream() {
    echo "📜 Streaming worker logs..."
    gcloud run services logs read realtime-agent-worker \
        --region=$REGION \
        --stream \
        --project=$PROJECT_ID
}

# Get worker service URL
worker_url() {
    gcloud run services describe realtime-agent-worker \
        --region=$REGION \
        --format='value(status.url)' \
        --project=$PROJECT_ID
}

# ====== HEALTH CHECKS ======

# Test worker health endpoint
test_worker_health() {
    local url=$(worker_url)
    if [ -z "$url" ]; then
        echo "❌ Could not get worker URL"
        return 1
    fi
    echo "🏥 Testing worker health: $url/health"
    curl -s "$url/health" | jq .
}

# ====== UTILITY ======

# Show all available functions
show_help() {
    echo "Available functions:"
    echo "  build_worker           - Build and deploy worker only"
    echo "  build_all              - Build all services"
    echo "  deploy_worker          - Deploy worker from latest image"
    echo "  deploy_api             - Deploy API from latest image"
    echo "  list_images            - List all images in repository"
    echo "  list_builds            - List recent builds"
    echo "  watch_build <id>       - Stream build logs"
    echo "  worker_logs            - Show worker service logs"
    echo "  worker_logs_stream     - Stream worker logs (real-time)"
    echo "  test_worker_health     - Test worker health endpoint"
    echo "  worker_url             - Get worker service URL"
}

# Show help if sourced with 'help' argument
if [ "$1" = "help" ]; then
    show_help
fi
