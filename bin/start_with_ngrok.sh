#!/bin/bash

# Startup Script dengan Ngrok Tunnel
# Usage: ./start_with_ngrok.sh [port]

PORT=${1:-8081}

echo "═══════════════════════════════════════════════════════════"
echo "🚀 Starting Klar-RAG API Server + Ngrok Tunnel"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Port: $PORT"
echo ""

# Get project root
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# Check if running from correct directory
if [ ! -f "src/api.py" ]; then
    echo "❌ ERROR: Must run from klar-rag root directory!"
    echo "   Current directory: $(pwd)"
    exit 1
fi

# Ensure logs directory
mkdir -p logs

# Kill existing processes on port
echo "🧹 Cleaning up existing processes..."
lsof -ti:$PORT | xargs kill -9 2>/dev/null
pkill -f "ngrok http $PORT" 2>/dev/null
sleep 2

# Start uvicorn in background
echo "🔄 Starting API server on port $PORT..."
source .venv/bin/activate
nohup uvicorn src.api:app --host 0.0.0.0 --port $PORT --reload > logs/server.log 2>&1 &
SERVER_PID=$!

# Wait for server to start
echo "⏳ Waiting for server to start..."
sleep 3

# Check if server is running
if ! lsof -ti:$PORT > /dev/null 2>&1; then
    echo "❌ ERROR: Server failed to start!"
    echo "Check server.log for details"
    exit 1
fi

echo "✅ Server started (PID: $SERVER_PID)"
echo ""

# Start ngrok tunnel
echo "🌐 Starting ngrok tunnel..."
nohup ngrok http $PORT --log=stdout > logs/ngrok.log 2>&1 &
NGROK_PID=$!

# Wait for ngrok to start
sleep 3

# Get ngrok URL
echo "⏳ Getting ngrok URL..."
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*' | grep -o 'https://[^"]*' | head -1)

if [ -z "$NGROK_URL" ]; then
    echo "⚠️  WARNING: Could not get ngrok URL automatically"
    echo "   Check ngrok.log or visit http://localhost:4040"
else
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "✅ ALL SYSTEMS RUNNING"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "🖥️  Local Server:  http://localhost:$PORT"
    echo "🌍 Ngrok Tunnel:  $NGROK_URL"
    echo "📊 Ngrok Admin:   http://localhost:4040"
    echo ""
    echo "Server PID:  $SERVER_PID"
    echo "Ngrok PID:   $NGROK_PID"
    echo ""
    echo "Logs:"
    echo "  - Server: tail -f server.log"
    echo "  - Ngrok:  tail -f ngrok.log"
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    
    # Save ngrok URL to file
    echo "$NGROK_URL" > .ngrok_url
    echo "💾 Ngrok URL saved to .ngrok_url"
    echo ""
fi

echo "Press Ctrl+C to stop all services..."
echo ""

# Monitor logs
tail -f logs/server.log
