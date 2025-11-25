#!/bin/bash

# Stop semua services (server + ngrok)

echo "🛑 Stopping all services..."

# Kill server
echo "  Stopping API server..."
lsof -ti:8081 | xargs kill -9 2>/dev/null
lsof -ti:8080 | xargs kill -9 2>/dev/null

# Kill ngrok
echo "  Stopping ngrok..."
pkill -f ngrok 2>/dev/null

sleep 1

echo "✅ All services stopped"

# Cleanup
if [ -f ".ngrok_url" ]; then
    rm .ngrok_url
fi
