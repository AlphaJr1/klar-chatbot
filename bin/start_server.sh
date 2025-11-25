#!/bin/bash

# Quick Start Script untuk Klar-RAG API Server
# Usage: ./start_server.sh [port] [mode]
# Example: ./start_server.sh 8080 dev

PORT=${1:-8080}
MODE=${2:-dev}

echo "═══════════════════════════════════════════════════════════"
echo "🚀 Starting Klar-RAG API Server"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Port: $PORT"
echo "Mode: $MODE"
echo ""

# Check if running from correct directory
if [ ! -f "src/api.py" ]; then
    echo "❌ ERROR: Must run from klar-rag root directory!"
    echo "   Current directory: $(pwd)"
    echo "   Expected: /Users/adrianalfajri/Projects/klar-rag"
    echo ""
    exit 1
fi

# Check if dependencies installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "⚠️  WARNING: FastAPI not installed!"
    echo "   Installing dependencies..."
    pip install -r requirements.txt
    echo ""
fi

echo "Starting server..."
echo ""

if [ "$MODE" == "dev" ] || [ "$MODE" == "development" ]; then
    echo "🔄 Development mode (auto-reload enabled)"
    uvicorn src.api:app --host 0.0.0.0 --port $PORT --reload
else
    echo "🚀 Production mode (no reload)"
    uvicorn src.api:app --host 0.0.0.0 --port $PORT
fi
