#!/bin/bash
# Better French Max - Scheduler Process Manager
# Ensures the scheduler keeps running and restarts if it crashes

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PIDFILE="$PROJECT_DIR/scheduler.pid"
LOGFILE="$PROJECT_DIR/logs/scheduler_runner.log"

# Ensure logs directory exists
mkdir -p "$PROJECT_DIR/logs"

cd "$PROJECT_DIR"

# Function to log with timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" >> "$LOGFILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1"
}

# Check if already running
if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if ps -p $PID > /dev/null 2>&1; then
        log "Scheduler already running with PID $PID"
        exit 0
    else
        log "Removing stale PID file"
        rm "$PIDFILE"
    fi
fi

# Check if Python dependencies are installed
if ! python3 -c "import schedule, requests, feedparser" > /dev/null 2>&1; then
    log "Installing Python dependencies..."
    pip3 install -r requirements.txt
fi

# Set up environment
export PYTHONPATH="$PROJECT_DIR"

# Start the scheduler
log "Starting Better French Max scheduler"
python3 scripts/scheduler_main.py &
PID=$!
echo $PID > "$PIDFILE"

log "Scheduler started with PID $PID"

# Optional: wait a moment and verify it's still running
sleep 5
if ps -p $PID > /dev/null 2>&1; then
    log "Scheduler startup successful"
    exit 0
else
    log "ERROR: Scheduler failed to start properly"
    rm "$PIDFILE" 2>/dev/null
    exit 1
fi 