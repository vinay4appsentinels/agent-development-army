# Agent Development Army

A comprehensive GitHub webhook and AI agent service system for automated development workflows.

## Architecture

This project consists of two main services:

### 🔗 Main Agent (Webhook Service)
- **Purpose**: Receives and processes GitHub webhook events
- **Port**: 4044
- **Features**: 
  - GitHub webhook signature validation
  - @mention detection and attention analysis
  - Event parsing (issues, comments, pull requests)
  - Integration ready for triggering agent workflows

### 🤖 Agent Service
- **Purpose**: Role-based AI agent execution using Claude CLI
- **Port**: 4045+ (supports multiple instances)
- **Features**:
  - 3 specialized agent roles (DEVELOPER, ARCHITECT, ANALYST)
  - Async job processing with queue management
  - Persistent job storage and status tracking
  - Role-specific prompts and configurations
  - REST API for job management

## Quick Start

### 1. Install Dependencies
```bash
# Install all dependencies
./scripts/install-dependencies.sh

# Or with virtual environment
./scripts/install-dependencies.sh --venv
source venv/bin/activate
./scripts/install-dependencies.sh
```

### 2. Configure Environment
Edit the generated `.env` files:
- `main-agent/.env` - GitHub webhook secret and configuration
- `agent-service/.env` - Claude CLI path and service settings

### 3. Install Claude CLI
Follow the installation guide at [claude.ai/cli](https://claude.ai/cli)

### 4. Start Services
```bash
# Start all services (main-agent + 2 agent-service instances)
./scripts/manage-services.sh start

# Or start specific number of agent instances
./scripts/manage-services.sh start 3
```

### 5. Verify Services
```bash
# Check all service status
./scripts/manage-services.sh status

# Test connectivity
./scripts/manage-services.sh test

# View logs
./scripts/manage-services.sh logs
```

## Service Management

### Global Commands
```bash
./scripts/manage-services.sh start [N]     # Start all services with N agent instances
./scripts/manage-services.sh stop         # Stop all services
./scripts/manage-services.sh restart [N]  # Restart all services
./scripts/manage-services.sh status       # Show status of all services
./scripts/manage-services.sh logs         # Show logs for all services
./scripts/manage-services.sh test         # Test connectivity
./scripts/manage-services.sh nginx        # Generate nginx load balancer config
```

### Individual Service Management
```bash
# Main Agent (Webhook Service)
./scripts/start-main-agent.sh {start|stop|restart|status|logs}

# Agent Service Instances
./scripts/start-agent-service.sh [-i instance] [-p port] {start|stop|restart|status|logs|list}

# Examples:
./scripts/start-agent-service.sh -i 2 start        # Start instance 2 on port 4046
./scripts/start-agent-service.sh -i 3 -p 5000 start # Start instance 3 on port 5000
./scripts/start-agent-service.sh list              # List all running instances
```

## API Usage

### Main Agent (Webhook Service)
```bash
# Test webhook service
curl http://localhost:4044/ping

# Webhook endpoint (for GitHub)
POST http://localhost:4044/webhook/github
```

### Agent Service
```bash
# Check available roles
curl http://localhost:4045/agent/roles

# Create a job
curl -X POST http://localhost:4045/agent/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "role": "DEVELOPER",
    "context": {
      "repository": "user/repo",
      "issue_number": 123,
      "branch": "main"
    },
    "task": {
      "type": "code_review",
      "description": "Review the authentication implementation",
      "priority": "high"
    }
  }'

# Check job status
curl http://localhost:4045/agent/jobs/{job_id}

# Get job result
curl http://localhost:4045/agent/jobs/{job_id}/result

# List all jobs
curl http://localhost:4045/agent/jobs

# Get service statistics
curl http://localhost:4045/agent/stats
```

## Agent Roles

### 🔧 DEVELOPER
- **Focus**: Code implementation, debugging, testing
- **Timeout**: 30 minutes
- **Capabilities**: Feature implementation, bug fixes, unit testing, code review

### 🏗️ ARCHITECT
- **Focus**: System design, architecture, technical strategy
- **Timeout**: 40 minutes  
- **Capabilities**: System design, architecture planning, technology selection, performance optimization

### 📊 ANALYST
- **Focus**: Code analysis, documentation, quality assessment
- **Timeout**: 20 minutes
- **Capabilities**: Code analysis, documentation generation, quality assessment, security analysis

## Configuration

### Role Configuration (`agent-service/config/roles.yml`)
- Role-specific timeouts and capabilities
- System prompt file mappings
- CLI argument configurations
- Task type to role mappings

### Environment Variables

#### Main Agent
- `GITHUB_WEBHOOK_SECRET`: GitHub webhook secret for signature validation
- `PORT`: Service port (default: 4044)
- `REPOSITORY_WHITELIST`: Comma-separated list of allowed repositories

#### Agent Service
- `PORT`: Service port (default: 4045)
- `CLAUDE_CLI_PATH`: Path to Claude CLI binary
- `JOB_TIMEOUT`: Default job timeout in seconds
- `MAX_CONCURRENT_JOBS`: Maximum concurrent jobs per instance

## Load Balancing

Generate nginx configuration for load balancing multiple agent service instances:

```bash
./scripts/manage-services.sh nginx
```

This creates an nginx config that provides:
- Load balanced agent services at `http://localhost:8080/agent/`
- Webhook service at `http://localhost:8080/webhook/`

## File Structure

```
agent-development-army/
├── main-agent/                 # Webhook service
│   ├── app/
│   │   ├── main.py            # FastAPI application
│   │   ├── config.py          # Configuration management
│   │   ├── routers/           # API endpoints
│   │   └── utils/             # GitHub utilities and parsers
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Environment configuration
├── agent-service/             # AI agent service
│   ├── app/
│   │   ├── main.py           # FastAPI application
│   │   ├── config.py         # Configuration management
│   │   ├── models/           # Pydantic models
│   │   ├── routers/          # API endpoints
│   │   └── services/         # Business logic
│   ├── config/
│   │   └── roles.yml         # Role configurations
│   ├── prompts/              # Role-specific system prompts
│   ├── requirements.txt      # Python dependencies
│   └── .env                  # Environment configuration
├── scripts/                  # Service management scripts
│   ├── manage-services.sh    # Master service management
│   ├── start-main-agent.sh   # Main agent management
│   ├── start-agent-service.sh # Agent service management
│   └── install-dependencies.sh # Dependency installation
├── logs/                     # Service logs (created at runtime)
├── pids/                     # Process ID files (created at runtime)
└── README.md                 # This file
```

## Development

### Adding New Agent Roles
1. Add role configuration to `agent-service/config/roles.yml`
2. Create system prompt file in `agent-service/prompts/`
3. Update `available_roles` in `agent-service/app/config.py`

### Extending Webhook Processing
1. Add event handlers in `main-agent/app/routers/webhook.py`
2. Extend parser in `main-agent/app/utils/parser.py`
3. Update event type filtering as needed

## Monitoring

- **Logs**: Check `logs/` directory for service logs
- **Status**: Use `./scripts/manage-services.sh status` for overview
- **Health**: Individual service health endpoints at `/health`
- **Metrics**: Agent service provides statistics at `/agent/stats`

## Troubleshooting

### Common Issues

1. **Port conflicts**: Use different ports with `-p` option
2. **Dependencies**: Run `./scripts/install-dependencies.sh` again
3. **Claude CLI**: Ensure Claude CLI is installed and in PATH
4. **Permissions**: Make sure scripts are executable (`chmod +x scripts/*.sh`)

### Debug Commands
```bash
# Check if services are listening
netstat -tulpn | grep :404[4-9]

# View real-time logs
tail -f logs/main-agent.log
tail -f logs/agent-service-1.log

# Check process status
ps aux | grep python.*app.main
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `./scripts/manage-services.sh test`
5. Submit a pull request

## License

This project is licensed under the MIT License.
