#!/bin/bash

# Start Agent Service Script
# This script starts agent service instances with support for multiple instances

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
AGENT_SERVICE_DIR="$PROJECT_ROOT/agent-service"

# Default configuration
DEFAULT_PORT=4045
DEFAULT_INSTANCE="1"
SERVICE_NAME="agent-service"
LOG_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/pids"

# Parse command line arguments
INSTANCE="$DEFAULT_INSTANCE"
PORT="$DEFAULT_PORT"
ACTION="start"

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--instance)
            INSTANCE="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        start|stop|restart|status|logs|list)
            ACTION="$1"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Calculate port if not explicitly set
if [ "$PORT" = "$DEFAULT_PORT" ] && [ "$INSTANCE" != "1" ]; then
    PORT=$((DEFAULT_PORT + INSTANCE - 1))
fi

# File paths
INSTANCE_NAME="${SERVICE_NAME}-${INSTANCE}"
LOG_FILE="$LOG_DIR/${INSTANCE_NAME}.log"
PID_FILE="$PID_DIR/${INSTANCE_NAME}.pid"

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
        echo "❌ $INSTANCE_NAME is already running (PID: $(cat $PID_FILE))"
        return 1
    fi

    echo "🚀 Starting $INSTANCE_NAME on port $PORT..."
    
    # Change to agent-service directory
    cd "$AGENT_SERVICE_DIR" || {
        echo "❌ Failed to change to directory: $AGENT_SERVICE_DIR"
        exit 1
    }

    # Set environment variables
    export PORT="$PORT"
    export INSTANCE_ID="$INSTANCE"
    
    # Start the service in background
    nohup python -m app.main > "$LOG_FILE" 2>&1 &
    local pid=$!
    
    # Save PID
    echo $pid > "$PID_FILE"
    
    # Wait a moment and check if it started successfully
    sleep 3
    if is_running; then
        echo "✅ $INSTANCE_NAME started successfully"
        echo "   Instance: $INSTANCE"
        echo "   PID: $pid"
        echo "   Port: $PORT"
        echo "   Log: $LOG_FILE"
        echo "   Test: curl http://localhost:$PORT/ping"
        return 0
    else
        echo "❌ Failed to start $INSTANCE_NAME"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Function to stop the service
stop_service() {
    if ! is_running; then
        echo "⚠️  $INSTANCE_NAME is not running"
        return 1
    fi

    local pid=$(cat "$PID_FILE")
    echo "🛑 Stopping $INSTANCE_NAME (PID: $pid)..."
    
    kill "$pid"
    
    # Wait for graceful shutdown
    local count=0
    while [ $count -lt 10 ] && ps -p "$pid" > /dev/null 2>&1; do
        sleep 1
        count=$((count + 1))
    done
    
    # Force kill if still running
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "⚠️  Force killing $INSTANCE_NAME..."
        kill -9 "$pid"
    fi
    
    rm -f "$PID_FILE"
    echo "✅ $INSTANCE_NAME stopped"
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
        echo "✅ $INSTANCE_NAME is running"
        echo "   Instance: $INSTANCE"
        echo "   PID: $pid"
        echo "   Port: $PORT"
        echo "   Log: $LOG_FILE"
        
        # Test connectivity
        if curl -s "http://localhost:$PORT/ping" > /dev/null 2>&1; then
            echo "   Status: ✅ Responsive"
            
            # Get service stats
            local stats=$(curl -s "http://localhost:$PORT/agent/stats" 2>/dev/null)
            if [ $? -eq 0 ]; then
                local total_jobs=$(echo "$stats" | python3 -c "import sys,json; print(json.load(sys.stdin)['total_jobs'])" 2>/dev/null || echo "N/A")
                local running_jobs=$(echo "$stats" | python3 -c "import sys,json; print(json.load(sys.stdin)['running_jobs'])" 2>/dev/null || echo "N/A")
                echo "   Jobs: $running_jobs running, $total_jobs total"
            fi
        else
            echo "   Status: ❌ Not responding"
        fi
    else
        echo "❌ $INSTANCE_NAME is not running"
    fi
}

# Function to show logs
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "📋 Recent logs for $INSTANCE_NAME:"
        tail -n 20 "$LOG_FILE"
    else
        echo "⚠️  No log file found: $LOG_FILE"
    fi
}

# Function to list all running instances
list_instances() {
    echo "📋 Agent Service Instances:"
    local found=false
    
    for pid_file in "$PID_DIR"/${SERVICE_NAME}-*.pid; do
        if [ -f "$pid_file" ]; then
            local instance_name=$(basename "$pid_file" .pid)
            local instance_num=$(echo "$instance_name" | sed "s/${SERVICE_NAME}-//")
            local pid=$(cat "$pid_file")
            
            if ps -p "$pid" > /dev/null 2>&1; then
                local instance_port=$((DEFAULT_PORT + instance_num - 1))
                echo "   ✅ Instance $instance_num (PID: $pid, Port: $instance_port)"
                found=true
            else
                rm -f "$pid_file"
            fi
        fi
    done
    
    if [ "$found" = false ]; then
        echo "   No running instances found"
    fi
}

# Main script logic
case "$ACTION" in
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
    list)
        list_instances
        ;;
    *)
        echo "Usage: $0 [options] {start|stop|restart|status|logs|list}"
        echo ""
        echo "Options:"
        echo "  -i, --instance NUM   Instance number (default: 1)"
        echo "  -p, --port PORT      Port number (default: 4045 + instance - 1)"
        echo ""
        echo "Commands:"
        echo "  start    - Start the agent service instance"
        echo "  stop     - Stop the agent service instance"
        echo "  restart  - Restart the agent service instance"
        echo "  status   - Show service status"
        echo "  logs     - Show recent logs"
        echo "  list     - List all running instances"
        echo ""
        echo "Examples:"
        echo "  $0 start                    # Start instance 1 on port 4045"
        echo "  $0 -i 2 start              # Start instance 2 on port 4046"
        echo "  $0 -i 3 -p 5000 start      # Start instance 3 on port 5000"
        echo "  $0 -i 2 stop               # Stop instance 2"
        echo "  $0 list                     # List all running instances"
        exit 1
        ;;
esac

exit $?