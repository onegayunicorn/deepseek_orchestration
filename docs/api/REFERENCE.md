# 🦅 DeepSeek Orchestrator - API Reference

## Authentication
All requests must include the `X-API-Key` header.

## Endpoints

### 1. System Health
`GET /api/v1/status`
Returns the status of all tmux windows and core services.

### 2. Command Execution
`POST /api/v1/execute`
**Payload:** `{"command": "your command here"}`
**Response:** Command result or audit ID if pending approval.

### 3. Metrics
`GET /api/v1/metrics`
Returns system performance metrics and command statistics.

### 4. Audit Logs
`GET /api/v1/audit?limit=50`
Returns recent command history from the SQLite database.

### 5. Webhooks
`POST /api/v1/webhook/register`
**Payload:** `{"url": "https://your-server.com/callback"}`
Registers a URL to receive event notifications.
