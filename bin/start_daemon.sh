#!/bin/bash

# Startup Script - Fully Daemon Mode
# Server & ngrok jalan di background, terminal langsung free

PORT=${1:-8081}

echo "═══════════════════════════════════════════════════════════"
echo "🚀 Starting Klar-RAG (Daemon Mode)"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check directory
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

if [ ! -f "src/api.py" ]; then
    echo "❌ ERROR: Must run from klar-rag root directory!"
    exit 1
fi

# Ensure logs directory exists
mkdir -p logs

# Cleanup
echo "🧹 Cleaning up existing processes..."
lsof -ti:$PORT | xargs kill -9 2>/dev/null
pkill -f "ngrok http $PORT" 2>/dev/null
sleep 2

# Start uvicorn
echo "🔄 Starting API server on port $PORT..."
source .venv/bin/activate
nohup uvicorn src.api:app --host 0.0.0.0 --port $PORT --reload > logs/server.log 2>&1 &
SERVER_PID=$!
echo "   Server PID: $SERVER_PID"

# Wait for server
sleep 3

# Check server
if ! lsof -ti:$PORT > /dev/null 2>&1; then
    echo "❌ ERROR: Server failed to start!"
    echo "   Check: cat server.log"
    exit 1
fi

# Start ngrok
echo "🌐 Starting ngrok tunnel..."
nohup ngrok http $PORT --log=stdout > logs/ngrok.log 2>&1 &
NGROK_PID=$!
echo "   Ngrok PID: $NGROK_PID"

# Wait for ngrok
sleep 3

# Get ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*' | grep -o 'https://[^"]*' | head -1)

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ ALL SYSTEMS RUNNING (DAEMON MODE)"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "🖥️  Local Server:  http://localhost:$PORT"

if [ -n "$NGROK_URL" ]; then
    echo "🌍 Ngrok Tunnel:  $NGROK_URL"
    echo "$NGROK_URL" > .ngrok_url
    echo ""
    echo "💾 Ngrok URL saved to: .ngrok_url"
else
    echo "⚠️  Ngrok URL not ready yet, check: http://localhost:4040"
fi

echo "📊 Ngrok Admin:   http://localhost:4040"
echo ""
echo "PIDs:"
echo "  Server: $SERVER_PID"
echo "  Ngrok:  $NGROK_PID"
echo ""
echo "Logs:"
echo "  tail -f logs/server.log  # Server logs"
echo "  tail -f logs/ngrok.log   # Ngrok logs"
echo ""
echo "Stop:"
echo "  bin/stop_all.sh          # Stop all services"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "✅ Terminal is now free! Services running in background."
