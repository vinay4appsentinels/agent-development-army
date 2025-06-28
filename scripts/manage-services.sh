#!/bin/bash

# Service Management Script
# Master script to manage both main-agent and agent-service instances

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Service scripts
MAIN_AGENT_SCRIPT="$SCRIPT_DIR/start-main-agent.sh"
AGENT_SERVICE_SCRIPT="$SCRIPT_DIR/start-agent-service.sh"

# Make scripts executable
chmod +x "$MAIN_AGENT_SCRIPT" "$AGENT_SERVICE_SCRIPT"

# Function to show overall status
show_all_status() {
    echo "🔍 Service Status Overview"
    echo "=========================="
    echo ""
    
    echo "📡 Main Agent (Webhook Service):"
    "$MAIN_AGENT_SCRIPT" status
    echo ""
    
    echo "🤖 Agent Service Instances:"
    "$AGENT_SERVICE_SCRIPT" list
    echo ""
}

# Function to start all services
start_all() {
    local agent_instances=${1:-2}  # Default to 2 agent service instances
    
    echo "🚀 Starting all services..."
    echo ""
    
    # Start main agent
    echo "Starting main-agent..."
    "$MAIN_AGENT_SCRIPT" start
    echo ""
    
    # Start agent service instances
    echo "Starting $agent_instances agent-service instances..."
    for i in $(seq 1 $agent_instances); do
        echo "Starting agent-service instance $i..."
        "$AGENT_SERVICE_SCRIPT" -i "$i" start
        sleep 1  # Small delay between starts
    done
    echo ""
    
    echo "🔍 Final status:"
    show_all_status
}

# Function to stop all services
stop_all() {
    echo "🛑 Stopping all services..."
    echo ""
    
    # Stop main agent
    echo "Stopping main-agent..."
    "$MAIN_AGENT_SCRIPT" stop
    echo ""
    
    # Stop all agent service instances
    echo "Stopping all agent-service instances..."
    local pid_dir="$PROJECT_ROOT/pids"
    
    if [ -d "$pid_dir" ]; then
        for pid_file in "$pid_dir"/agent-service-*.pid; do
            if [ -f "$pid_file" ]; then
                local instance_name=$(basename "$pid_file" .pid)
                local instance_num=$(echo "$instance_name" | sed 's/agent-service-//')
                echo "Stopping agent-service instance $instance_num..."
                "$AGENT_SERVICE_SCRIPT" -i "$instance_num" stop
            fi
        done
    fi
    echo ""
    
    echo "✅ All services stopped"
}

# Function to restart all services
restart_all() {
    local agent_instances=${1:-2}
    echo "🔄 Restarting all services..."
    stop_all
    sleep 2
    start_all "$agent_instances"
}

# Function to show logs for all services
show_all_logs() {
    echo "📋 Service Logs"
    echo "==============="
    echo ""
    
    echo "📡 Main Agent Logs:"
    "$MAIN_AGENT_SCRIPT" logs
    echo ""
    
    echo "🤖 Agent Service Logs:"
    local log_dir="$PROJECT_ROOT/logs"
    
    if [ -d "$log_dir" ]; then
        for log_file in "$log_dir"/agent-service-*.log; do
            if [ -f "$log_file" ]; then
                local instance_name=$(basename "$log_file" .log)
                local instance_num=$(echo "$instance_name" | sed 's/agent-service-//')
                echo "Instance $instance_num logs:"
                tail -n 10 "$log_file"
                echo ""
            fi
        done
    fi
}

# Function to test all services
test_services() {
    echo "🧪 Testing all services..."
    echo ""
    
    # Test main agent
    echo "Testing main-agent (port 4044):"
    if curl -s http://localhost:4044/ping > /dev/null 2>&1; then
        echo "   ✅ Main agent responsive"
    else
        echo "   ❌ Main agent not responding"
    fi
    echo ""
    
    # Test agent service instances
    echo "Testing agent-service instances:"
    local found=false
    for port in $(seq 4045 4050); do
        if curl -s "http://localhost:$port/ping" > /dev/null 2>&1; then
            local instance=$((port - 4044))
            echo "   ✅ Agent service instance $instance (port $port) responsive"
            found=true
        fi
    done
    
    if [ "$found" = false ]; then
        echo "   ⚠️  No agent service instances responding"
    fi
    echo ""
}

# Function to create a sample load balancer config
create_nginx_config() {
    local config_file="$PROJECT_ROOT/nginx-agent-services.conf"
    
    cat > "$config_file" << 'EOF'
# Nginx configuration for load balancing agent services
# Add this to your nginx sites-available and enable it

upstream agent_services {
    server 127.0.0.1:4045;
    server 127.0.0.1:4046;
    server 127.0.0.1:4047;
    # Add more instances as needed
}

server {
    listen 8080;
    server_name localhost;
    
    location /agent/ {
        proxy_pass http://agent_services;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Health check
        proxy_next_upstream error timeout http_500 http_502 http_503 http_504;
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location /webhook/ {
        proxy_pass http://127.0.0.1:4044;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

    echo "📝 Nginx configuration created: $config_file"
    echo ""
    echo "To use this configuration:"
    echo "1. sudo cp $config_file /etc/nginx/sites-available/agent-services"
    echo "2. sudo ln -s /etc/nginx/sites-available/agent-services /etc/nginx/sites-enabled/"
    echo "3. sudo nginx -t"
    echo "4. sudo systemctl reload nginx"
    echo ""
    echo "This will provide:"
    echo "- Load balanced agent services at http://localhost:8080/agent/"
    echo "- Webhook service at http://localhost:8080/webhook/"
}

# Main script logic
case "$1" in
    start)
        start_all "${2:-2}"
        ;;
    stop)
        stop_all
        ;;
    restart)
        restart_all "${2:-2}"
        ;;
    status)
        show_all_status
        ;;
    logs)
        show_all_logs
        ;;
    test)
        test_services
        ;;
    nginx)
        create_nginx_config
        ;;
    main-agent)
        shift
        "$MAIN_AGENT_SCRIPT" "$@"
        ;;
    agent-service)
        shift
        "$AGENT_SERVICE_SCRIPT" "$@"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|test|nginx|main-agent|agent-service} [options]"
        echo ""
        echo "Global Commands:"
        echo "  start [N]       - Start main-agent and N agent-service instances (default: 2)"
        echo "  stop            - Stop all services"
        echo "  restart [N]     - Restart all services with N agent instances (default: 2)"
        echo "  status          - Show status of all services"
        echo "  logs            - Show logs for all services"
        echo "  test            - Test connectivity to all services"
        echo "  nginx           - Generate nginx load balancer configuration"
        echo ""
        echo "Individual Service Commands:"
        echo "  main-agent {start|stop|restart|status|logs}"
        echo "  agent-service [options] {start|stop|restart|status|logs|list}"
        echo ""
        echo "Examples:"
        echo "  $0 start 3                          # Start main-agent + 3 agent-service instances"
        echo "  $0 agent-service -i 2 start         # Start agent-service instance 2"
        echo "  $0 main-agent status                # Check main-agent status"
        echo "  $0 status                           # Check all services status"
        echo "  $0 nginx                            # Generate nginx config"
        exit 1
        ;;
esac

exit $?