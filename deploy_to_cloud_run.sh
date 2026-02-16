#!/bin/bash

# Cloud Run Deployment Script for Real-Time Log Analysis Agent
# Usage: ./deploy_to_cloud_run.sh <project-id> <region>

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Validate arguments
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: ./deploy_to_cloud_run.sh <gcp-project-id> <region>"
    echo ""
    echo "Example:"
    echo "  ./deploy_to_cloud_run.sh my-project us-central1"
    echo ""
    echo "Supported regions: us-central1, europe-west1, asia-southeast1, etc."
    exit 1
fi

PROJECT_ID=$1
REGION=$2
IMAGE_NAME="realtime-agent"
ARTIFACT_REPO="realtime-agent-repo"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Cloud Run Deployment Script${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "${YELLOW}Project ID:${NC} $PROJECT_ID"
echo -e "${YELLOW}Region:${NC} $REGION"
echo -e "${YELLOW}Image Name:${NC} $IMAGE_NAME"
echo ""

# Step 1: Verify gcloud is installed and authenticated
echo -e "${GREEN}[1/6]${NC} Verifying gcloud CLI..."
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI not found. Please install Google Cloud SDK."
    exit 1
fi

# Set gcloud project
gcloud config set project $PROJECT_ID

# Step 2: Enable required APIs
echo -e "${GREEN}[2/6]${NC} Enabling required GCP APIs..."
gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    container.googleapis.com \
    cloudkms.googleapis.com \
    secretmanager.googleapis.com

# Step 3: Create Artifact Registry repository
echo -e "${GREEN}[3/6]${NC} Creating Artifact Registry repository..."
if ! gcloud artifacts repositories describe $ARTIFACT_REPO --location=$REGION &> /dev/null; then
    gcloud artifacts repositories create $ARTIFACT_REPO \
        --repository-format=docker \
        --location=$REGION
    echo -e "${BLUE}✓ Repository created${NC}"
else
    echo -e "${BLUE}✓ Repository already exists${NC}"
fi

# Step 4: Build and push Docker image
echo -e "${GREEN}[4/6]${NC} Building and pushing Docker image..."
IMAGE_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/${IMAGE_NAME}:latest"

docker build -t $IMAGE_URL .
docker push $IMAGE_URL
echo -e "${BLUE}✓ Image pushed to: $IMAGE_URL${NC}"

# Step 5: Create/update secrets in Secret Manager
echo -e "${GREEN}[5/6]${NC} Setting up secrets..."
if [ -z "$GROQ_API_KEY" ]; then
    echo -e "${YELLOW}⚠ GROQ_API_KEY not set in environment. Skipping...${NC}"
    echo "   Please set manually: gcloud secrets create groq-api-key --data-file=- <<< 'YOUR_KEY'"
else
    # Create secret if it doesn't exist
    if ! gcloud secrets describe groq-api-key &> /dev/null; then
        echo -n "$GROQ_API_KEY" | gcloud secrets create groq-api-key --data-file=-
        echo -e "${BLUE}✓ Secret created${NC}"
    else
        echo -n "$GROQ_API_KEY" | gcloud secrets versions add groq-api-key --data-file=-
        echo -e "${BLUE}✓ Secret updated${NC}"
    fi
fi

# Step 6: Deploy to Cloud Run
echo -e "${GREEN}[6/6]${NC} Deploying to Cloud Run..."

# Determine Temporal address
read -p "Enter Temporal address (or press Enter for 'temporal.example.com:7233'): " TEMPORAL_ADDRESS
TEMPORAL_ADDRESS=${TEMPORAL_ADDRESS:-temporal.example.com:7233}

# Deploy API service
echo -e "${BLUE}Deploying API service...${NC}"
gcloud run deploy ${IMAGE_NAME}-api \
    --image=$IMAGE_URL \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --memory=512Mi \
    --cpu=1 \
    --port=8000 \
    --set-env-vars="ROLE=api,TEMPORAL_ADDRESS=${TEMPORAL_ADDRESS},WAIT_FOR_TEMPORAL=false" \
    --set-secrets="GROQ_API_KEY=groq-api-key:latest" \
    --timeout=3600 \
    --concurrency=80

# Deploy worker service
echo -e "${BLUE}Deploying worker service...${NC}"
gcloud run deploy ${IMAGE_NAME}-worker \
    --image=$IMAGE_URL \
    --region=$REGION \
    --platform=managed \
    --memory=512Mi \
    --cpu=1 \
    --set-env-vars="ROLE=worker,TEMPORAL_ADDRESS=${TEMPORAL_ADDRESS},WAIT_FOR_TEMPORAL=false" \
    --set-secrets="GROQ_API_KEY=groq-api-key:latest" \
    --timeout=3600 \
    --min-instances=1

# Deploy streamer service
echo -e "${BLUE}Deploying streamer service...${NC}"
gcloud run deploy ${IMAGE_NAME}-streamer \
    --image=$IMAGE_URL \
    --region=$REGION \
    --platform=managed \
    --memory=512Mi \
    --cpu=1 \
    --set-env-vars="ROLE=streamer,TEMPORAL_ADDRESS=${TEMPORAL_ADDRESS}" \
    --set-secrets="GROQ_API_KEY=groq-api-key:latest" \
    --timeout=3600 \
    --min-instances=1

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✓ Deployment Complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""

# Get service URLs
echo -e "${YELLOW}Service URLs:${NC}"
API_URL=$(gcloud run services describe ${IMAGE_NAME}-api --region=$REGION --format='value(status.url)')
WORKER_URL=$(gcloud run services describe ${IMAGE_NAME}-worker --region=$REGION --format='value(status.url)')
STREAMER_URL=$(gcloud run services describe ${IMAGE_NAME}-streamer --region=$REGION --format='value(status.url)')

echo -e "${BLUE}API Service:${NC}      $API_URL"
echo -e "${BLUE}Worker Service:${NC}   $WORKER_URL"
echo -e "${BLUE}Streamer Service:${NC} $STREAMER_URL"
echo ""

echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Update TEMPORAL_ADDRESS to your actual Temporal server address"
echo "2. Set GROQ_API_KEY secret: gcloud secrets create groq-api-key --data-file=- <<< 'YOUR_KEY'"
echo "3. Test the API: curl $API_URL/health"
echo "4. Trigger a workflow: curl -X POST $API_URL/api/v1/analyze-log \\
  -H 'Content-Type: application/json' \\
  -d '{\"log_line\": \"ERROR: Test error\"}'"
echo ""
