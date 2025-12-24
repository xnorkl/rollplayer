#!/bin/bash
# Quick curl-based smoke tests

set -e

echo "=========================================="
echo "GM Chatbot Curl Smoke Tests"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if curl is available
if ! command -v curl &> /dev/null; then
    echo -e "${RED}✗${NC} curl not found. Please install curl."
    exit 1
fi

echo -e "${GREEN}✓${NC} curl found"
echo ""

# Start health check server in background
echo "Starting health check server..."
python3 health_check.py > /dev/null 2>&1 &
HEALTH_PID=$!

# Wait for server to start
sleep 2

# Test health endpoint
echo "Test 1: Health check endpoint"
HEALTH_RESPONSE=$(curl -s http://localhost:8080/health)
if echo "$HEALTH_RESPONSE" | grep -q '"status": "healthy"'; then
    echo -e "${GREEN}✓${NC} Health check passed"
    echo "$HEALTH_RESPONSE" | python3 -m json.tool
else
    echo -e "${RED}✗${NC} Health check failed"
    echo "$HEALTH_RESPONSE"
fi

echo ""

# Test 404 endpoint
echo "Test 2: 404 handling"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/invalid)
if [ "$HTTP_CODE" == "404" ]; then
    echo -e "${GREEN}✓${NC} 404 handling works (HTTP $HTTP_CODE)"
else
    echo -e "${RED}✗${NC} Expected 404, got $HTTP_CODE"
fi

echo ""

# Cleanup
echo "Stopping health check server..."
kill $HEALTH_PID 2>/dev/null || true
wait $HEALTH_PID 2>/dev/null || true

echo ""
echo "=========================================="
echo -e "${GREEN}✓${NC} Curl tests completed!"
echo "=========================================="

