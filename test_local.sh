#!/bin/bash

# Local Testing Guide - Real-Time Log Analysis Agent
# This script demonstrates how to test the API, worker, and streamer locally

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Real-Time Log Analysis Agent - Local Testing${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Step 1: Verify Docker is running
echo -e "${GREEN}[1/6]${NC} Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found${NC}"
    exit 1
fi
echo -e "${BLUE}✓ Docker is installed${NC}"

# Step 2: Start all services
echo ""
echo -e "${GREEN}[2/6]${NC} Starting Docker Compose services (temporal, postgresql, api, worker, streamer)..."
docker-compose up -d
sleep 5

# Check if services started
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${RED}✗ Services failed to start${NC}"
    docker-compose logs
    exit 1
fi
echo -e "${BLUE}✓ Services started${NC}"

# Step 3: Test API health
echo ""
echo -e "${GREEN}[3/6]${NC} Testing API health endpoint..."
MAX_RETRIES=10
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${BLUE}✓ API is healthy${NC}"
        HEALTH=$(curl -s http://localhost:8000/health | grep -o '"status":"[^"]*"')
        echo "  Response: $HEALTH"
        break
    fi
    RETRY=$((RETRY + 1))
    if [ $RETRY -eq $MAX_RETRIES ]; then
        echo -e "${RED}✗ API not responding${NC}"
        docker-compose logs app-api | tail -20
        exit 1
    fi
    echo "  Waiting for API to be ready... (attempt $RETRY/$MAX_RETRIES)"
    sleep 2
done

# Step 4: Test API root endpoint
echo ""
echo -e "${GREEN}[4/6]${NC} Testing API documentation endpoint..."
curl -s http://localhost:8000/ | jq . 2>/dev/null || curl -s http://localhost:8000/
echo ""

# Step 5: Test workflow trigger
echo ""
echo -e "${GREEN}[5/6]${NC} Testing workflow trigger (analyze-log endpoint)..."
echo "  Submitting log: 'ERROR: Database connection timeout'"

RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/analyze-log \
  -H "Content-Type: application/json" \
  -d '{"log_line": "ERROR: Database connection timeout"}')

echo "  Response:"
echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"

# Extract workflow ID
WORKFLOW_ID=$(echo "$RESPONSE" | grep -o '"workflow_id":"[^"]*"' | cut -d'"' -f4)
if [ -z "$WORKFLOW_ID" ]; then
    echo -e "${YELLOW}  ⚠ Could not extract workflow ID${NC}"
else
    echo -e "${BLUE}  ✓ Workflow started with ID: $WORKFLOW_ID${NC}"
    
    # Step 6: Wait and check result
    echo ""
    echo -e "${GREEN}[6/6]${NC} Checking workflow result in 5 seconds..."
    sleep 5
    
    echo "  Fetching result for workflow: $WORKFLOW_ID"
    RESULT=$(curl -s http://localhost:8000/api/v1/workflow/$WORKFLOW_ID)
    echo "  Result:"
    echo "$RESULT" | jq . 2>/dev/null || echo "$RESULT"
fi

echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}✓ Local testing complete!${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

echo -e "${YELLOW}Available Services:${NC}"
echo "  API:           http://localhost:8000"
echo "  API Docs:      http://localhost:8000/docs"
echo "  Temporal UI:   http://localhost:8233"
echo "  PostgreSQL:    localhost:5432"
echo ""

echo -e "${YELLOW}Test Commands:${NC}"
echo "  Health check:"
echo "    curl http://localhost:8000/health"
echo ""
echo "  Analyze single log:"
echo "    curl -X POST http://localhost:8000/api/v1/analyze-log \\"
echo "      -H 'Content-Type: application/json' \\"
echo "      -d '{\"log_line\": \"ERROR: Your log here\"}'"
echo ""
echo "  Batch analyze logs:"
echo "    curl -X POST http://localhost:8000/api/v1/batch-analyze \\"
echo "      -H 'Content-Type: application/json' \\"
echo "      -d '{\"logs\": [\"ERROR: Log 1\", \"CRITICAL: Log 2\"]}'"
echo ""
echo "  Get workflow result:"
echo "    curl http://localhost:8000/api/v1/workflow/WORKFLOW_ID"
echo ""

echo -e "${YELLOW}View Logs:${NC}"
echo "  API:     docker-compose logs -f app-api"
echo "  Worker:  docker-compose logs -f app-worker"
echo "  Streamer: docker-compose logs -f app-streamer"
echo ""

echo -e "${YELLOW}Stop All Services:${NC}"
echo "  docker-compose down"
echo ""
