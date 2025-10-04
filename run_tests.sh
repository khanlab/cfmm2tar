#!/bin/bash
#
# Helper script for running tests locally
#
set -e

echo "=== cfmm2tar Test Runner ==="
echo ""

# Check if pytest is installed
if ! python3 -c "import pytest" 2>/dev/null; then
    echo "Installing test dependencies..."
    pip install pytest pytest-docker-compose pydicom numpy
    echo ""
fi

# Parse command line arguments
RUN_INTEGRATION=false
STOP_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--integration)
            RUN_INTEGRATION=true
            shift
            ;;
        -s|--stop)
            STOP_ONLY=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -i, --integration    Run integration tests (requires Docker)"
            echo "  -s, --stop          Stop and clean up Docker containers"
            echo "  -h, --help          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                  # Run unit tests only"
            echo "  $0 -i               # Run integration tests"
            echo "  $0 -s               # Stop PACS server"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# If stop only, stop containers and exit
if [ "$STOP_ONLY" = true ]; then
    echo "Stopping dcm4chee PACS server..."
    cd tests
    docker-compose down -v
    echo "Done!"
    exit 0
fi

# Run unit tests
echo "Running unit tests..."
python3 -m pytest tests/test_dcm4che_utils.py::TestDcm4cheUtilsUnit -v

if [ "$RUN_INTEGRATION" = true ]; then
    echo ""
    echo "=== Starting dcm4chee PACS server for integration tests ==="
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        echo "Error: Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Start docker-compose
    cd tests
    echo "Starting Docker containers..."
    docker-compose up -d
    
    echo "Waiting for dcm4chee to be ready (this may take 1-2 minutes)..."
    sleep 60
    
    echo "Checking container status..."
    docker-compose ps
    
    cd ..
    echo ""
    echo "Running integration tests..."
    python3 -m pytest tests/test_dcm4che_utils.py::TestDcm4cheUtilsIntegration -v
    
    RESULT=$?
    
    echo ""
    echo "=== Stopping dcm4chee PACS server ==="
    cd tests
    docker-compose down -v
    
    exit $RESULT
fi

echo ""
echo "Tests completed successfully!"
echo "Tip: Use '$0 -i' to run integration tests with Docker"
