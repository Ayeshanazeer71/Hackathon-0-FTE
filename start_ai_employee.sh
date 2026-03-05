#!/bin/bash
#
# Start AI Employee System
# Starts all watcher scripts as background processes
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$SCRIPT_DIR/pids"
LOG_DIR="$SCRIPT_DIR/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "  AI Employee System - Starting..."
echo "=============================================="
echo ""

# Create directories
mkdir -p "$PID_DIR" "$LOG_DIR"

# Function to start a script
start_script() {
    local name="$1"
    local script="$2"
    local pid_file="$PID_DIR/${name}.pid"
    local log_file="$LOG_DIR/${name}.log"

    # Check if already running
    if [ -f "$pid_file" ]; then
        local old_pid=$(cat "$pid_file")
        if ps -p "$old_pid" > /dev/null 2>&1; then
            echo -e "${YELLOW}[$name]${NC} Already running (PID: $old_pid)"
            return 0
        else
            rm -f "$pid_file"
        fi
    fi

    # Check if script exists
    if [ ! -f "$SCRIPT_DIR/$script" ]; then
        echo -e "${RED}[$name]${NC} Script not found: $script"
        return 1
    fi

    # Start the script
    echo -e "${YELLOW}[$name]${NC} Starting..."
    nohup python3 "$SCRIPT_DIR/$script" > "$log_file" 2>&1 &
    local pid=$!

    # Save PID
    echo "$pid" > "$pid_file"

    # Wait briefly and check if still running
    sleep 1
    if ps -p "$pid" > /dev/null 2>&1; then
        echo -e "${GREEN}[$name]${NC} Started successfully (PID: $pid)"
        return 0
    else
        echo -e "${RED}[$name]${NC} Failed to start (check $log_file)"
        return 1
    fi
}

# Start all scripts
echo "Starting watcher scripts..."
echo ""

start_script "orchestrator" "orchestrator.py"
start_script "gmail_watcher" "gmail_watcher.py"
start_script "whatsapp_watcher" "whatsapp_watcher.py"
start_script "linkedin_watcher" "linkedin_watcher.py"
start_script "hitl_watcher" "hitl_watcher.py"
start_script "social_media_watcher" "social_media_watcher.py"
start_script "twitter_watcher" "twitter_watcher.py"
start_script "social_mcp_server" "social_mcp_server.js"
start_script "logging_mcp_server" "logging_mcp_server.js"
start_script "health_monitor" "health_monitor.py"

echo ""
echo "=============================================="
echo "  AI Employee System - Status"
echo "=============================================="

# Show status of each
for name in orchestrator gmail_watcher whatsapp_watcher linkedin_watcher hitl_watcher social_media_watcher twitter_watcher social_mcp_server logging_mcp_server health_monitor; do
    pid_file="$PID_DIR/${name}.pid"
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ $name${NC} - RUNNING (PID: $pid)"
        else
            echo -e "${RED}✗ $name${NC} - STOPPED (stale PID file)"
        fi
    else
        echo -e "${RED}✗ $name${NC} - NOT STARTED"
    fi
done

echo ""
echo "=============================================="
echo "  Logs: $LOG_DIR/"
echo "  PIDs: $PID_DIR/"
echo "=============================================="
echo ""
echo "To check status: ./status_ai_employee.sh"
echo "To stop all:     ./stop_ai_employee.sh"
echo ""
