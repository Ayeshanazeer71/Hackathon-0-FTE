#!/bin/bash
#
# Stop AI Employee System
# Stops all watcher scripts gracefully
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$SCRIPT_DIR/pids"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "  AI Employee System - Stopping..."
echo "=============================================="
echo ""

# Function to stop a script
stop_script() {
    local name="$1"
    local pid_file="$PID_DIR/${name}.pid"

    if [ ! -f "$pid_file" ]; then
        echo -e "${YELLOW}[$name]${NC} No PID file found (not running?)"
        return 0
    fi

    local pid=$(cat "$pid_file")

    if ! ps -p "$pid" > /dev/null 2>&1; then
        echo -e "${YELLOW}[$name]${NC} Process not running (PID: $pid)"
        rm -f "$pid_file"
        return 0
    fi

    echo -e "${YELLOW}[$name]${NC} Stopping (PID: $pid)..."

    # Send SIGTERM for graceful shutdown
    kill -TERM "$pid" 2>/dev/null

    # Wait up to 10 seconds for process to stop
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
    done

    # Force kill if still running
    if ps -p "$pid" > /dev/null 2>&1; then
        echo -e "${YELLOW}[$name]${NC} Force killing..."
        kill -9 "$pid" 2>/dev/null
        sleep 1
    fi

    # Verify stopped
    if ! ps -p "$pid" > /dev/null 2>&1; then
        echo -e "${GREEN}[$name]${NC} Stopped successfully"
        rm -f "$pid_file"
        return 0
    else
        echo -e "${RED}[$name]${NC} Failed to stop"
        return 1
    fi
}

# Stop all scripts
for name in orchestrator gmail_watcher whatsapp_watcher linkedin_watcher hitl_watcher; do
    stop_script "$name"
done

# Clean up any orphaned PID files
echo ""
echo "Cleaning up stale PID files..."
for pid_file in "$PID_DIR"/*.pid; do
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ! ps -p "$pid" > /dev/null 2>&1; then
            rm -f "$pid_file"
        fi
    fi
done

echo ""
echo "=============================================="
echo "  AI Employee System - Stopped"
echo "=============================================="
echo ""
echo "To start again: ./start_ai_employee.sh"
echo ""
