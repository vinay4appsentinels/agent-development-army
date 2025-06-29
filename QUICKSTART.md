# Quick Start Guide

A simple guide to spin up the Agent Development Army services and monitor their logs.

## 🚀 Starting Services

### Start All Services (Recommended)
```bash
# Start main-agent + 2 agent-service instances
./scripts/manage-services.sh start

# Or specify number of agent instances
./scripts/manage-services.sh start 3
```

### Start Individual Services
```bash
# Start only the webhook service
./scripts/start-main-agent.sh start

# Start specific agent service instances
./scripts/start-agent-service.sh -i 1 start  # Instance 1 on port 4045
./scripts/start-agent-service.sh -i 2 start  # Instance 2 on port 4046
./scripts/start-agent-service.sh -i 3 start  # Instance 3 on port 4047
```

## 🔍 Checking Service Status

### Quick Status Check
```bash
./scripts/manage-services.sh status
```

### Test Connectivity
```bash
./scripts/manage-services.sh test
```

### List Running Agent Instances
```bash
./scripts/start-agent-service.sh list
```

## 📋 Viewing Logs

### All Service Logs at Once
```bash
./scripts/manage-services.sh logs
```

### Individual Service Logs
```bash
# Main webhook agent logs
./scripts/start-main-agent.sh logs

# Specific agent service instance logs
./scripts/start-agent-service.sh -i 1 logs
./scripts/start-agent-service.sh -i 2 logs
```

### Real-time Log Monitoring
```bash
# Watch main agent logs
tail -f logs/main-agent.log

# Watch agent service instance 1 logs
tail -f logs/agent-service-1.log

# Watch agent service instance 2 logs
tail -f logs/agent-service-2.log

# Watch all logs simultaneously (requires multitail)
multitail logs/main-agent.log logs/agent-service-1.log logs/agent-service-2.log
```

### Log File Locations
- **Main Agent**: `logs/main-agent.log`
- **Agent Service Instance 1**: `logs/agent-service-1.log`
- **Agent Service Instance 2**: `logs/agent-service-2.log`
- **Agent Service Instance N**: `logs/agent-service-N.log`

## 🛑 Stopping Services

### Stop All Services
```bash
./scripts/manage-services.sh stop
```

### Stop Individual Services
```bash
# Stop main agent
./scripts/start-main-agent.sh stop

# Stop specific agent instance
./scripts/start-agent-service.sh -i 1 stop
./scripts/start-agent-service.sh -i 2 stop
```

## 🧪 Testing the Services

### Quick Connectivity Test
```bash
# Test main agent
curl http://localhost:4044/ping

# Test agent service instances
curl http://localhost:4045/ping  # Instance 1
curl http://localhost:4046/ping  # Instance 2
curl http://localhost:4047/ping  # Instance 3
```

### Test Job Creation
```bash
# Create a test job on agent service
curl -X POST http://localhost:4045/agent/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "role": "DEVELOPER",
    "context": {
      "repository": "user/repo",
      "branch": "main"
    },
    "task": {
      "type": "code_review",
      "description": "Test job",
      "priority": "normal"
    }
  }'
```

### Check Service Statistics
```bash
# Get agent service statistics
curl http://localhost:4045/agent/stats

# Get available roles
curl http://localhost:4045/agent/roles

# List all jobs
curl http://localhost:4045/agent/jobs
```

## 📊 Monitoring Dashboard Commands

### System Resource Usage
```bash
# Check port usage
netstat -tulpn | grep :404[4-9]

# Check process status
ps aux | grep python.*app.main

# Check memory usage
ps aux | grep python.*app.main | awk '{print $4, $11}'
```

### Service Health Summary
```bash
# One-liner status check
echo "Main Agent: $(curl -s http://localhost:4044/ping 2>/dev/null && echo "✅ UP" || echo "❌ DOWN")"
echo "Agent Service 1: $(curl -s http://localhost:4045/ping 2>/dev/null && echo "✅ UP" || echo "❌ DOWN")"
echo "Agent Service 2: $(curl -s http://localhost:4046/ping 2>/dev/null && echo "✅ UP" || echo "❌ DOWN")"
```

## 🔧 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Find process using port
   sudo netstat -tulpn | grep :4044
   
   # Kill process if needed
   sudo kill <pid>
   ```

2. **Service Won't Start**
   ```bash
   # Check logs for errors
   ./scripts/start-main-agent.sh logs
   ./scripts/start-agent-service.sh -i 1 logs
   
   # Try starting manually for debug output
   cd main-agent && python -m app.main
   cd agent-service && python -m app.main
   ```

3. **Dependencies Missing**
   ```bash
   # Reinstall dependencies
   ./scripts/install-dependencies.sh
   ```

### Restart Services
```bash
# Restart all services
./scripts/manage-services.sh restart

# Restart specific service
./scripts/start-main-agent.sh restart
./scripts/start-agent-service.sh -i 1 restart
```

## 📁 Log Analysis Tips

### Filter Important Log Messages
```bash
# Show only INFO level and above
grep -E "(INFO|WARN|ERROR)" logs/main-agent.log

# Show job-related messages
grep -i "job" logs/agent-service-1.log

# Show webhook events
grep -i "webhook\|github" logs/main-agent.log

# Show errors only
grep "ERROR" logs/*.log
```

### Log Rotation (for production)
```bash
# Add to crontab for daily log rotation
# 0 2 * * * /usr/sbin/logrotate /path/to/agent-development-army/logrotate.conf

# Create logrotate.conf
cat > logrotate.conf << 'EOF'
/path/to/agent-development-army/logs/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    copytruncate
}
EOF
```

## 🎯 Quick Reference

| Command | Purpose |
|---------|---------|
| `./scripts/manage-services.sh start` | Start all services |
| `./scripts/manage-services.sh status` | Check service status |
| `./scripts/manage-services.sh logs` | View all logs |
| `./scripts/manage-services.sh test` | Test connectivity |
| `./scripts/manage-services.sh stop` | Stop all services |
| `tail -f logs/main-agent.log` | Monitor main agent logs |
| `curl localhost:4044/ping` | Test main agent |
| `curl localhost:4045/agent/stats` | Get agent statistics |

---

**Need help?** Check the main [README.md](README.md) for comprehensive documentation.