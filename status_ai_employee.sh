#!/bin/bash
#
# Check AI Employee System Status
# Shows running/stopped status for each script
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$SCRIPT_DIR/pids"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=============================================="
echo "  AI Employee System - Status Check"
echo "=============================================="
echo ""
printf "%-20s %-10s %-10s\n" "SCRIPT" "STATUS" "PID"
echo "----------------------------------------------"

# Scripts to check
scripts=(
    "orchestrator:orchestrator.py"
    "gmail_watcher:gmail_watcher.py"
    "whatsapp_watcher:whatsapp_watcher.py"
    "linkedin_watcher:linkedin_watcher.py"
    "hitl_watcher:hitl_watcher.py"
)

running_count=0
total_count=${#scripts[@]}

for entry in "${scripts[@]}"; do
    name="${entry%%:*}"
    script="${entry##*:}"
    pid_file="$PID_DIR/${name}.pid"

    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            # Get additional info
            cpu=$(ps -p "$pid" -o %cpu= 2>/dev/null | tr -d ' ' || echo "0.0")
            mem=$(ps -p "$pid" -o %mem= 2>/dev/null | tr -d ' ' || echo "0.0")
            printf "%-20s ${GREEN}RUNNING${NC}  %-10s\n" "$name" "$pid"
            running_count=$((running_count + 1))
        else
            printf "%-20s ${RED}STOPPED${NC}  %-10s\n" "$name" "(stale)"
        fi
    else
        printf "%-20s ${RED}STOPPED${NC}  %-10s\n" "$name" "-"
    fi
done

echo "----------------------------------------------"
echo ""

# Summary
echo -e "${BLUE}Summary:${NC}"
echo "  Running:  ${GREEN}$running_count${NC} / $total_count"
echo "  Stopped:  $((total_count - running_count)) / $total_count"
echo ""

# Quick actions
if [ $running_count -eq 0 ]; then
    echo -e "${YELLOW}No scripts running. Start with:${NC}"
    echo "  ./start_ai_employee.sh"
elif [ $running_count -lt $total_count ]; then
    echo -e "${YELLOW}Some scripts not running.${NC}"
    echo "  Restart all: ./stop_ai_employee.sh && ./start_ai_employee.sh"
else
    echo -e "${GREEN}All systems operational!${NC}"
fi

echo ""
echo "=============================================="
echo ""

# Show recent log activity (last 3 lines of each log)
LOG_DIR="$SCRIPT_DIR/logs"
if [ -d "$LOG_DIR" ]; then
    echo -e "${BLUE}Recent Log Activity:${NC}"
    echo ""
    for name in orchestrator gmail_watcher whatsapp_watcher linkedin_watcher hitl_watcher; do
        log_file="$LOG_DIR/${name}.log"
        if [ -f "$log_file" ] && [ -s "$log_file" ]; then
            echo "  $name:"
            tail -3 "$log_file" | sed 's/^/    /'
        fi
    done
    echo ""
fi
