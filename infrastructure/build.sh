#!/bin/bash
# Build script for Fly.io deployment
# This ensures the build context is the project root

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Get project root (parent of infrastructure/)
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Change to project root for build context
cd "$PROJECT_ROOT"

# Build with dockerfile from infrastructure directory
docker build -f infrastructure/Dockerfile -t roll20-chatbot:latest .

