#!/bin/bash

# AI Agent Factory - Startup Script
# Quick deployment helper

set -e

echo "🤖 AI Agent Factory - Startup Script"
echo "===================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check for required environment variables
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${RED}❌ Error: ANTHROPIC_API_KEY environment variable not set${NC}"
    echo ""
    echo "Please set it:"
    echo "  export ANTHROPIC_API_KEY='your_api_key_here'"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓${NC} ANTHROPIC_API_KEY found"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.11+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓${NC} Python ${PYTHON_VERSION} found"

# Function to run with Docker
run_docker() {
    echo ""
    echo "Starting with Docker Compose..."
    echo ""
    
    if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not found${NC}"
        exit 1
    fi
    
    # Check if docker-compose.yml exists
    if [ ! -f "docker-compose.yml" ]; then
        echo -e "${RED}❌ docker-compose.yml not found${NC}"
        exit 1
    fi
    
    # Build and start
    echo "Building containers..."
    docker-compose build
    
    echo ""
    echo "Starting services..."
    docker-compose up -d
    
    echo ""
    echo -e "${GREEN}✓${NC} Services started"
    echo ""
    echo "API available at: http://localhost:8000"
    echo "Health check: curl http://localhost:8000/health"
    echo ""
    echo "View logs: docker-compose logs -f"
    echo "Stop services: docker-compose down"
    echo ""
}

# Function to run locally
run_local() {
    echo ""
    echo "Starting locally with Python..."
    echo ""
    
    # Check if requirements are installed
    if ! python3 -c "import fastapi" 2>/dev/null; then
        echo -e "${YELLOW}⚠${NC}  Dependencies not installed. Installing..."
        pip install -r requirements.txt
    fi
    
    echo -e "${GREEN}✓${NC} Dependencies ready"
    echo ""
    
    # Create workspace directory
    mkdir -p /tmp/agent_factory/{jobs,orders,deliveries}
    echo -e "${GREEN}✓${NC} Workspace created"
    
    echo ""
    echo "Starting API server..."
    echo ""
    
    # Run the API
    python3 api_service.py
}

# Function to run tests
run_tests() {
    echo ""
    echo "Running tests..."
    echo ""
    
    python3 test_pipeline.py
}

# Main menu
echo ""
echo "Choose deployment method:"
echo "  1) Docker (recommended for production)"
echo "  2) Local Python (for development)"
echo "  3) Run tests"
echo "  4) Exit"
echo ""
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        run_docker
        ;;
    2)
        run_local
        ;;
    3)
        run_tests
        ;;
    4)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac
