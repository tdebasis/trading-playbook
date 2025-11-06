#!/bin/bash
#
# Momentum Hunter - Control Script
#
# Manage the automatic trading system
#
# Usage:
#   ./control.sh start      - Enable automatic startup
#   ./control.sh stop       - Disable automatic startup
#   ./control.sh status     - Check if system is running
#   ./control.sh logs       - View today's trading logs
#   ./control.sh kill       - Emergency stop (kill all processes)
#

PLIST_FILE="$HOME/Library/LaunchAgents/com.momentumhunter.trading.plist"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_DIR="$SCRIPT_DIR/logs"
DATE=$(date +%Y-%m-%d)

case "$1" in
    start)
        echo "🚀 Enabling automatic trading startup..."

        # Create logs directory
        mkdir -p "$LOG_DIR"

        # Load the LaunchAgent
        launchctl load "$PLIST_FILE" 2>/dev/null || launchctl bootout gui/$(id -u)/com.momentumhunter.trading 2>/dev/null
        launchctl bootstrap gui/$(id -u) "$PLIST_FILE" 2>/dev/null || launchctl load "$PLIST_FILE"

        if [ $? -eq 0 ]; then
            echo "✅ Automatic startup enabled"
            echo ""
            echo "System will start automatically at:"
            echo "  Monday-Friday at 6:25 AM PT"
            echo ""
            echo "Next steps:"
            echo "  - Leave your computer ON or sleeping before 6:25 AM"
            echo "  - Check logs: ./control.sh logs"
            echo "  - Monitor live: python3 monitor.py"
        else
            echo "❌ Failed to enable automatic startup"
            echo "Check: $PLIST_FILE"
        fi
        ;;

    stop)
        echo "🛑 Disabling automatic trading startup..."

        # Unload the LaunchAgent
        launchctl bootout gui/$(id -u)/com.momentumhunter.trading 2>/dev/null || launchctl unload "$PLIST_FILE" 2>/dev/null

        echo "✅ Automatic startup disabled"
        echo ""
        echo "System will NOT start automatically"
        echo "To start manually: python3 run.py"
        ;;

    status)
        echo "📊 MOMENTUM HUNTER STATUS"
        echo "=========================================="

        # Check if LaunchAgent is loaded
        if launchctl list | grep -q com.momentumhunter.trading; then
            echo "🟢 Automatic startup: ENABLED"
        else
            echo "🔴 Automatic startup: DISABLED"
        fi

        echo ""

        # Check if trading system is running
        if pgrep -f "python3.*run.py" > /dev/null; then
            PID=$(pgrep -f "python3.*run.py")
            echo "🟢 Trading system: RUNNING (PID: $PID)"

            # Show runtime
            ps -p $PID -o etime= | xargs echo "   Runtime:"

        else
            echo "🔴 Trading system: NOT RUNNING"
        fi

        echo ""

        # Check today's activity
        if [ -f "$LOG_DIR/trading_${DATE}.log" ]; then
            LINES=$(wc -l < "$LOG_DIR/trading_${DATE}.log")
            echo "📝 Today's log: $LINES lines"
            echo "   Location: $LOG_DIR/trading_${DATE}.log"
        else
            echo "📝 No logs for today yet"
        fi

        echo "=========================================="
        ;;

    logs)
        echo "📋 Viewing today's trading logs..."
        echo "Press Ctrl+C to exit"
        echo ""
        sleep 2

        if [ -f "$LOG_DIR/trading_${DATE}.log" ]; then
            tail -f "$LOG_DIR/trading_${DATE}.log"
        else
            echo "No logs for today yet"
            echo ""
            echo "Available logs:"
            ls -lh "$LOG_DIR"/*.log 2>/dev/null || echo "  (none)"
        fi
        ;;

    kill)
        echo "🚨 EMERGENCY STOP"
        echo "=========================================="

        if pgrep -f "python3.*run.py" > /dev/null; then
            PIDS=$(pgrep -f "python3.*run.py")
            echo "Killing trading processes: $PIDS"
            pkill -f "python3.*run.py"
            sleep 2

            if pgrep -f "python3.*run.py" > /dev/null; then
                echo "⚠️  Force killing..."
                pkill -9 -f "python3.*run.py"
            fi

            echo "✅ All trading processes stopped"
        else
            echo "No trading processes found"
        fi

        echo ""
        echo "⚠️  Note: Automatic startup is still enabled"
        echo "To disable: ./control.sh stop"
        ;;

    *)
        echo "Momentum Hunter - Control Script"
        echo ""
        echo "Usage:"
        echo "  ./control.sh start    - Enable automatic startup (weekdays 6:25 AM)"
        echo "  ./control.sh stop     - Disable automatic startup"
        echo "  ./control.sh status   - Check system status"
        echo "  ./control.sh logs     - View today's logs (live tail)"
        echo "  ./control.sh kill     - Emergency stop all processes"
        echo ""
        exit 1
        ;;
esac
