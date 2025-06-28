#!/bin/bash

# Start Main Agent (Webhook Service) Script
# This script starts the main webhook agent service

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MAIN_AGENT_DIR="$PROJECT_ROOT/main-agent"

# Configuration
SERVICE_NAME="main-agent"
LOG_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/pids"
LOG_FILE="$LOG_DIR/${SERVICE_NAME}.log"
PID_FILE="$PID_DIR/${SERVICE_NAME}.pid"

# Create directories
mkdir -p "$LOG_DIR" "$PID_DIR"

# Function to check if service is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Function to start the service
start_service() {
    if is_running; then
        echo "❌ $SERVICE_NAME is already running (PID: $(cat $PID_FILE))"
        return 1
    fi

    echo "🚀 Starting $SERVICE_NAME..."
    
    # Change to main-agent directory
    cd "$MAIN_AGENT_DIR" || {
        echo "❌ Failed to change to directory: $MAIN_AGENT_DIR"
        exit 1
    }

    # Start the service in background
    nohup python -m app.main > "$LOG_FILE" 2>&1 &
    local pid=$!
    
    # Save PID
    echo $pid > "$PID_FILE"
    
    # Wait a moment and check if it started successfully
    sleep 2
    if is_running; then
        echo "✅ $SERVICE_NAME started successfully"
        echo "   PID: $pid"
        echo "   Port: 4044"
        echo "   Log: $LOG_FILE"
        echo "   Test: curl http://localhost:4044/ping"
        return 0
    else
        echo "❌ Failed to start $SERVICE_NAME"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Function to stop the service
stop_service() {
    if ! is_running; then
        echo "⚠️  $SERVICE_NAME is not running"
        return 1
    fi

    local pid=$(cat "$PID_FILE")
    echo "🛑 Stopping $SERVICE_NAME (PID: $pid)..."
    
    kill "$pid"
    
    # Wait for graceful shutdown
    local count=0
    while [ $count -lt 10 ] && ps -p "$pid" > /dev/null 2>&1; do
        sleep 1
        count=$((count + 1))
    done
    
    # Force kill if still running
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "⚠️  Force killing $SERVICE_NAME..."
        kill -9 "$pid"
    fi
    
    rm -f "$PID_FILE"
    echo "✅ $SERVICE_NAME stopped"
}

# Function to restart the service
restart_service() {
    stop_service
    sleep 1
    start_service
}

# Function to show status
show_status() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        echo "✅ $SERVICE_NAME is running"
        echo "   PID: $pid"
        echo "   Port: 4044"
        echo "   Log: $LOG_FILE"
        
        # Test connectivity
        if curl -s http://localhost:4044/ping > /dev/null 2>&1; then
            echo "   Status: ✅ Responsive"
        else
            echo "   Status: ❌ Not responding"
        fi
    else
        echo "❌ $SERVICE_NAME is not running"
    fi
}

# Function to show logs
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "📋 Recent logs for $SERVICE_NAME:"
        tail -n 20 "$LOG_FILE"
    else
        echo "⚠️  No log file found: $LOG_FILE"
    fi
}

# Main script logic
case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the main-agent service"
        echo "  stop    - Stop the main-agent service"
        echo "  restart - Restart the main-agent service"
        echo "  status  - Show service status"
        echo "  logs    - Show recent logs"
        exit 1
        ;;
esac

exit $?