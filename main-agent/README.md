# GitHub Webhook Service - Stage 1

## Overview

This is the Stage 1 implementation of the GitHub Webhook Service that listens to GitHub issue events and provides the foundation for automated command execution based on issue labels.

## Features Implemented in Stage 1

- FastAPI webhook endpoint (`POST /webhook/github`)
- GitHub webhook signature validation (HMAC-SHA256)
- Request logging for all incoming events
- Configuration management via environment variables and YAML
- Docker containerization with volume mounts
- Health check endpoint
- Ping endpoint for service testing
- Repository whitelist support

## Project Structure

```
main-agent/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── routers/
│   │   └── webhook.py       # GitHub webhook endpoint
│   └── utils/
│       └── github.py        # GitHub signature validation
├── config/
│   └── config.yml           # Application configuration
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container definition
├── docker-compose.yml      # Local development setup
└── .env.example            # Environment variables template
```

## Setup Instructions

### 1. Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` and set your GitHub webhook secret:
```
GITHUB_WEBHOOK_SECRET=your-webhook-secret-here
```

### 2. Running with Docker Compose

```bash
docker-compose up -d
```

The service will be available at `http://localhost:4044`

### 3. Running Locally (Development)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the service
python -m app.main
```

## API Endpoints

- `GET /` - Service information
- `GET /health` - Health check endpoint
- `GET /ping` - Ping endpoint (returns pong with service status)
- `POST /webhook/github` - GitHub webhook receiver

## Testing the Webhook

1. Configure your GitHub repository webhook:
   - URL: `http://your-server:4044/webhook/github`
   - Content type: `application/json`
   - Secret: Same as `GITHUB_WEBHOOK_SECRET`
   - Events: Select "Issues" events

2. Test the ping endpoint:
```bash
curl http://localhost:4044/ping
```

3. Test the webhook endpoint:
```bash
curl -X POST http://localhost:4044/webhook/github \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: issues" \
  -H "X-GitHub-Delivery: test-delivery-id" \
  -H "X-Hub-Signature-256: sha256=YOUR_SIGNATURE" \
  -d '{"action": "opened", "issue": {"id": 1, "number": 1, "title": "Test Issue"}}'
```

## What's Next (Stage 2)

- Command execution based on issue labels
- Workspace management for repository operations
- Integration with coding agent services
- Advanced error handling and retry logic