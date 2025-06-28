#!/bin/bash

# Install Dependencies Script
# Installs Python dependencies for both services

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "📦 Installing dependencies for agent-development-army services"
echo "=============================================================="
echo ""

# Function to install main-agent dependencies
install_main_agent_deps() {
    echo "📡 Installing main-agent dependencies..."
    cd "$PROJECT_ROOT/main-agent" || {
        echo "❌ Failed to change to main-agent directory"
        return 1
    }
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        echo "✅ Main-agent dependencies installed"
    else
        echo "⚠️  No requirements.txt found in main-agent"
    fi
    echo ""
}

# Function to install agent-service dependencies
install_agent_service_deps() {
    echo "🤖 Installing agent-service dependencies..."
    cd "$PROJECT_ROOT/agent-service" || {
        echo "❌ Failed to change to agent-service directory"
        return 1
    }
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        echo "✅ Agent-service dependencies installed"
    else
        echo "⚠️  No requirements.txt found in agent-service"
    fi
    echo ""
}

# Function to check Python and pip
check_python() {
    echo "🐍 Checking Python installation..."
    
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 is not installed"
        echo "Please install Python 3.8+ first"
        return 1
    fi
    
    python_version=$(python3 --version | cut -d' ' -f2)
    echo "✅ Python $python_version found"
    
    if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
        echo "❌ pip is not installed"
        echo "Please install pip first"
        return 1
    fi
    
    echo "✅ pip found"
    echo ""
}

# Function to install system dependencies (optional)
install_system_deps() {
    echo "🔧 Checking system dependencies..."
    
    # Check for curl (used in scripts)
    if ! command -v curl &> /dev/null; then
        echo "⚠️  curl not found, installing..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y curl
        elif command -v yum &> /dev/null; then
            sudo yum install -y curl
        else
            echo "❌ Please install curl manually"
            return 1
        fi
    else
        echo "✅ curl found"
    fi
    
    # Check for nginx (for load balancing)
    if ! command -v nginx &> /dev/null; then
        echo "⚠️  nginx not found (optional for load balancing)"
        echo "   To install: sudo apt-get install nginx (Ubuntu/Debian)"
        echo "              sudo yum install nginx (CentOS/RHEL)"
    else
        echo "✅ nginx found"
    fi
    
    echo ""
}

# Function to create virtual environment
create_venv() {
    echo "🐍 Setting up virtual environment..."
    
    cd "$PROJECT_ROOT" || {
        echo "❌ Failed to change to project root"
        return 1
    }
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "✅ Virtual environment created"
    else
        echo "✅ Virtual environment already exists"
    fi
    
    echo "To activate: source $PROJECT_ROOT/venv/bin/activate"
    echo ""
}

# Function to setup environment files
setup_env_files() {
    echo "⚙️  Setting up environment files..."
    
    # Main agent .env
    local main_agent_env="$PROJECT_ROOT/main-agent/.env"
    if [ ! -f "$main_agent_env" ]; then
        cat > "$main_agent_env" << 'EOF'
# Main Agent Environment Configuration
# Copy this file and update with your actual values

# GitHub Configuration
GITHUB_WEBHOOK_SECRET=your_webhook_secret_here

# Repository Configuration (optional)
# REPOSITORY_WHITELIST=user/repo1,user/repo2

# Service Configuration
PORT=4044
LOG_LEVEL=INFO
DEBUG=false
EOF
        echo "✅ Created main-agent/.env template"
        echo "   Please edit $main_agent_env with your actual values"
    else
        echo "✅ Main-agent .env already exists"
    fi
    
    # Agent service .env
    local agent_service_env="$PROJECT_ROOT/agent-service/.env"
    if [ ! -f "$agent_service_env" ]; then
        cat > "$agent_service_env" << 'EOF'
# Agent Service Environment Configuration
# Copy this file and update with your actual values

# Service Configuration
PORT=4045
LOG_LEVEL=INFO
DEBUG=false

# Claude CLI Configuration
CLAUDE_CLI_PATH=claude

# Job Configuration
JOB_TIMEOUT=1800
MAX_CONCURRENT_JOBS=3

# Paths
PROMPTS_DIR=prompts
JOBS_STORAGE_PATH=jobs
EOF
        echo "✅ Created agent-service/.env template"
        echo "   Please edit $agent_service_env with your actual values"
    else
        echo "✅ Agent-service .env already exists"
    fi
    
    echo ""
}

# Main installation process
main() {
    echo "Starting installation process..."
    echo ""
    
    # Check prerequisites
    check_python || exit 1
    
    # Install system dependencies
    install_system_deps
    
    # Create virtual environment (optional)
    if [ "$1" = "--venv" ]; then
        create_venv
        echo "Please activate the virtual environment and run this script again:"
        echo "source $PROJECT_ROOT/venv/bin/activate"
        echo "$0"
        exit 0
    fi
    
    # Install Python dependencies
    install_main_agent_deps || exit 1
    install_agent_service_deps || exit 1
    
    # Setup environment files
    setup_env_files
    
    echo "🎉 Installation completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Edit the .env files with your actual configuration"
    echo "2. Install Claude CLI: https://claude.ai/cli"
    echo "3. Start services: $PROJECT_ROOT/scripts/manage-services.sh start"
    echo ""
    echo "Useful commands:"
    echo "  $PROJECT_ROOT/scripts/manage-services.sh status    # Check all services"
    echo "  $PROJECT_ROOT/scripts/manage-services.sh test      # Test connectivity"
    echo "  $PROJECT_ROOT/scripts/manage-services.sh logs      # View logs"
}

# Run main function
main "$@"