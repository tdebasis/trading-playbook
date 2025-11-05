#!/bin/bash
#
# Momentum Hunter - Automatic Startup Script
#
# This script runs automatically and starts trading when market opens.
# Logs everything to files for review.
#
# Author: Claude AI + Tanam Bam Sinha
#

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_DIR="$SCRIPT_DIR/logs"
DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)

# Create logs directory
mkdir -p "$LOG_DIR"

# Log files
MAIN_LOG="$LOG_DIR/trading_${DATE}.log"
ERROR_LOG="$LOG_DIR/errors_${DATE}.log"
STARTUP_LOG="$LOG_DIR/startup_${TIMESTAMP}.log"

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$STARTUP_LOG"
}

log "========================================="
log "MOMENTUM HUNTER - AUTOMATIC STARTUP"
log "========================================="

# Change to script directory
cd "$SCRIPT_DIR"
log "Working directory: $SCRIPT_DIR"

# Check if .env file exists
if [ ! -f ".env" ]; then
    log "ERROR: .env file not found!"
    log "Please create .env with API keys"
    exit 1
fi

log "✓ Environment file found"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    log "ERROR: python3 not found!"
    exit 1
fi

log "✓ Python3 available"

# Check current time and market status
CURRENT_HOUR=$(date +%H)
CURRENT_MINUTE=$(date +%M)
DAY_OF_WEEK=$(date +%u)  # 1-7 (Monday is 1, Sunday is 7)

log "Current time: $(date +'%H:%M %Z')"
log "Day of week: $DAY_OF_WEEK"

# Check if it's a weekday (1-5 = Monday-Friday)
if [ "$DAY_OF_WEEK" -gt 5 ]; then
    log "It's the weekend - markets are closed"
    log "Next trading day: Monday"
    exit 0
fi

# Market hours: 6:30 AM - 1:00 PM PT (9:30 AM - 4:00 PM ET)
# Start at 6:25 AM to be ready when market opens
START_HOUR=6
START_MINUTE=25

# Don't start after 12:00 PM (too late in trading day)
CUTOFF_HOUR=12

CURRENT_TIME_MINUTES=$((CURRENT_HOUR * 60 + CURRENT_MINUTE))
START_TIME_MINUTES=$((START_HOUR * 60 + START_MINUTE))
CUTOFF_TIME_MINUTES=$((CUTOFF_HOUR * 60))

if [ $CURRENT_TIME_MINUTES -lt $START_TIME_MINUTES ]; then
    log "Too early - market hasn't opened yet"
    log "Will start at ${START_HOUR}:${START_MINUTE} AM PT"
    exit 0
fi

if [ $CURRENT_TIME_MINUTES -gt $CUTOFF_TIME_MINUTES ]; then
    log "Too late - trading day is ending soon"
    log "Skipping today's session"
    exit 0
fi

log "✓ Time is within trading window"

# Check if already running
if pgrep -f "python3.*run.py" > /dev/null; then
    log "Trading system is already running"
    log "PID: $(pgrep -f 'python3.*run.py')"
    exit 0
fi

log "✓ No existing instance found"

# Start the trading system
log "========================================="
log "STARTING MOMENTUM HUNTER"
log "========================================="
log "Mode: Paper Trading"
log "Account: $100,000 simulated"
log "Main log: $MAIN_LOG"
log "Error log: $ERROR_LOG"
log "========================================="

# Run the trading system in background with logging
nohup python3 run.py \
    >> "$MAIN_LOG" 2>> "$ERROR_LOG" &

TRADING_PID=$!

log "✓ Trading system started (PID: $TRADING_PID)"
log "Monitor with: tail -f $MAIN_LOG"
log "Or run: python3 monitor.py"
log "========================================="

# Wait a few seconds and check if it's still running
sleep 5

if ps -p $TRADING_PID > /dev/null; then
    log "✓ System running successfully"

    # Send notification (macOS)
    osascript -e 'display notification "Momentum Hunter is now trading" with title "Trading System Started" sound name "Glass"' 2>/dev/null || true

    exit 0
else
    log "ERROR: System failed to start"
    log "Check error log: $ERROR_LOG"
    exit 1
fi
