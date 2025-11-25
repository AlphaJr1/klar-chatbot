#!/bin/bash

# Quick Start - Development (Daemon Mode)
# Terminal langsung free setelah start

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "🚀 Quick Start: Development Mode"
echo ""

# Start in daemon mode
bin/start_daemon.sh 8081
