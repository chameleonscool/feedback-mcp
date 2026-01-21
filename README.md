# User Intent MCP

A Model Context Protocol (MCP) server with multimodal user intent collection support, allowing AI agents to ask users questions and receive text and image responses.

## ✨ Features

- **Multi-task Parallelism**: Supports multiple agents initiating requests simultaneously.
- **Task Management**: Users can manually dismiss/ignore requests.
- **Multimodal Input**: Supports uploading or pasting screenshots.
- **Dual Transport Modes**: Supports both SSE (HTTP) and STDIO modes.
- **System Notifications**: Automatic browser notifications for new questions.
- **Persistence**: Uses SQLite to ensure task state reliability.
- **i18n Support**: Bilingual UI (English/Chinese) with configurable preferences.
- **Feishu Integration**: Support Feishu OAuth login and message notifications.
- **Multi-tenant Support**: Multiple users can use the system with isolated message queues.

## 📁 Project Structure

```
user-intent-mcp/
├── src/                      # Source code
│   ├── core.py               # Core logic (Database, MCP tools)
│   ├── web.py                # FastAPI routes (single-user mode)
│   ├── web_multi_tenant.py   # FastAPI routes (multi-tenant mode)
│   ├── server.py             # Unified entry point
│   ├── auth.py               # Admin authentication
│   ├── oauth.py              # Feishu OAuth
│   ├── users.py              # User management
│   ├── feishu.py             # Feishu service (send messages)
│   ├── feishu_ws_listener.py # Feishu WebSocket listener (receive messages)
│   ├── static/               # Static assets (Service Worker)
│   └── templates/            # HTML templates
│       ├── index.html        # Web UI
│       └── multi_tenant.html # Multi-tenant login page
├── data/                     # Runtime data
│   └── intent.db             # SQLite database
├── docs/                     # Documentation
│   ├── PRD-feishu-multi-tenant.md
│   └── DESIGN-feishu-multi-tenant.md
└── tests/                    # Test cases
```

## 🚀 Quick Start

### Installation

```bash
cd user-intent-mcp
pip install -e .
# Or using uv
uv pip install -e .

# Install Feishu SDK for message notifications
pip install lark_oapi
```

### Running

**Multi-tenant Mode (Recommended)**:
```bash
cd src && PYTHONPATH=. python -m uvicorn web_multi_tenant:app --host 0.0.0.0 --port 8000
```

**Single-user Mode (SSE with Web UI)**:
```bash
cd src && python server.py --mode sse
```

**STDIO Mode (for MCP clients)**:
```bash
cd src && python server.py --mode stdio
```

Visit `http://localhost:8000` to view the Web interface.

### MCP Client Configuration

**Multi-tenant Mode with API Key**:
```json
{
  "mcpServers": {
    "user-intent": {
      "command": "uv",
      "args": ["run", "python", "/path/to/server.py", "--mode", "stdio"],
      "env": {
        "USERINTENT_API_KEY": "uk_your_api_key_here"
      }
    }
  }
}
```

**SSE Mode** (`mcp_config.json`):
```json
{
  "mcpServers": {
    "user-intent": {
      "url": "http://localhost:8000/mcp/sse"
    }
  }
}
```

## ⚙️ Configuration Options

### Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `USERINTENT_DB_PATH` | Path to SQLite database file | `data/intent.db` |
| `USERINTENT_WEB_PORT` | Web server port | `8000` |
| `USERINTENT_WEB_HOST` | Web server listen address | `0.0.0.0` |
| `USERINTENT_API_KEY` | User API Key (for multi-tenant mode) | - |
| `USERINTENT_ENABLE_SYSTEM_NOTIFY` | Enable native system notifications | `false` |
| `USERINTENT_LOG_PATH` | Path to log file | `.log/intent.log` |
| `USERINTENT_TIMEOUT` | Default timeout for user responses (seconds) | `3000` |
| `USERINTENT_HISTORY_DAYS` | Number of days to keep completed intent history | `3` |

## 🔐 Multi-tenant Mode

### Initial Setup

1. Start the server in multi-tenant mode
2. Visit `http://localhost:8000`
3. Set up admin username and password
4. Configure Feishu App ID and App Secret (optional)

### User Login

1. Click "Login with Feishu" button
2. Authorize with Feishu account
3. Get your API Key from user center
4. Configure API Key in MCP client

### Message Isolation

- Messages are isolated by user
- Feishu users only see their own messages
- Anonymous WebUI users only see public messages

## 🚀 Production Deployment

### Using systemd (Linux)

Create `/etc/systemd/system/user-intent-mcp.service`:

```ini
[Unit]
Description=User Intent MCP Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/user-intent-mcp
Environment="PYTHONPATH=/opt/user-intent-mcp/src"
ExecStart=/usr/bin/python3 -m uvicorn web_multi_tenant:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable user-intent-mcp
sudo systemctl start user-intent-mcp
```

### Using Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install -e . && pip install lark_oapi

ENV PYTHONPATH=/app/src
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "web_multi_tenant:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t user-intent-mcp .
docker run -d -p 8000:8000 -v $(pwd)/data:/app/data user-intent-mcp
```

### Using Supervisor

Create `/etc/supervisor/conf.d/user-intent-mcp.conf`:

```ini
[program:user-intent-mcp]
command=/usr/bin/python3 -m uvicorn web_multi_tenant:app --host 0.0.0.0 --port 8000
directory=/opt/user-intent-mcp
user=www-data
environment=PYTHONPATH="/opt/user-intent-mcp/src"
autostart=true
autorestart=true
stderr_logfile=/var/log/user-intent-mcp/error.log
stdout_logfile=/var/log/user-intent-mcp/access.log
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name intent.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### HTTPS with Let's Encrypt

```bash
sudo certbot --nginx -d intent.example.com
```

### Feishu Configuration

1. Create a Feishu application at [Feishu Open Platform](https://open.feishu.cn/)
2. Configure OAuth redirect URI: `https://intent.example.com/auth/feishu/callback`
3. Enable required permissions:
   - `contact:user.base:readonly` - Get user basic info
   - `im:message:send_as_bot` - Send messages as bot
4. Configure event subscription:
   - Use WebSocket long connection
   - Subscribe to `im.message.receive_v1` event

### Data Backup

```bash
# Backup database
cp /opt/user-intent-mcp/data/intent.db /backup/intent-$(date +%Y%m%d).db

# Restore
cp /backup/intent-20260122.db /opt/user-intent-mcp/data/intent.db
```

## 🧪 Testing

```bash
# Unit tests
PYTHONPATH=src pytest tests/test_multi_tenant.py -v

# Integration tests
PYTHONPATH=src pytest tests/test_integration.py -v

# MCP tool tests
PYTHONPATH=src pytest tests/test_mcp_tool.py -v
```

## 📚 Documentation

- [Product Requirements Document (PRD)](docs/PRD-feishu-multi-tenant.md)
- [Design Document](docs/DESIGN-feishu-multi-tenant.md)

---
[中文版文档 (Chinese Version)](README_zh.md)
