# User Intent MCP

A multimodal user intent collection MCP (Model Context Protocol) server that enables AI Agents to ask questions and receive responses from users.

## Features

### Core Capabilities
- **Dual Transport Modes** - Supports both SSE (HTTP) and STDIO transport modes
- **Multimodal Input** - Accept text and image responses from users
- **Message Isolation** - Each user can only see their own messages
- **Queue Management** - Automatic question queuing with PENDING/COMPLETED/DISMISSED states

### Authentication & Multi-Tenancy
- **Feishu OAuth** - Enterprise-grade authentication via Feishu (Lark) OAuth 2.0
- **30-Day Session Cache** - Extended login sessions for better UX
- **Multi-Tenant Support** - User-level and enterprise-level isolation
- **Admin Dashboard** - System initialization and user management

### Notification System
- **Feishu Notifications** - Push notifications for new messages
- **WebSocket Listener** - Real-time message reception via Feishu WebSocket API
- **Sound Alerts** - Audio notifications for new questions
- **Configurable Alerts** - Users can enable/disable notifications

### Modern Frontend
- **React 19 + TypeScript** - Type-safe, modern React development
- **Redux Toolkit** - Efficient state management
- **Responsive Design** - Mobile-friendly UI with Tailwind CSS
- **Sidebar Navigation** - Intuitive task history browsing
- **Keyboard Shortcuts** - Quick actions support
- **i18n Support** - Multi-language support (English/Chinese)

## Architecture

### Backend
- **FastAPI** - Modern Python web framework
- **FastMCP** - MCP protocol implementation
- **SQLite** - Lightweight embedded database
- **Uvicorn** - ASGI server
- **lark-oapi** - Feishu/Lark SDK

### Frontend
- **React 19** - Latest React with concurrent features
- **Redux Toolkit** - Predictable state management
- **React Router v7** - Declarative routing
- **Tailwind CSS v4** - Utility-first CSS framework
- **Vite** - Next-generation frontend tooling
- **Vitest** - Unit testing framework
- **i18next** - Internationalization framework

### Project Structure
```
interactive-mcp/
├── src/                      # Backend source code
│   ├── core.py              # MCP server core & configuration
│   ├── server.py            # Unified entry point (SSE/STDIO)
│   ├── web_multi_tenant.py  # FastAPI multi-tenant app
│   ├── auth.py              # Admin authentication
│   ├── users.py             # User management
│   ├── oauth.py             # Feishu OAuth
│   ├── feishu.py            # Feishu notification service
│   ├── feishu_ws_listener.py # WebSocket message listener
│   └── static/              # Static assets (Service Worker)
├── frontend/                # React frontend
│   ├── src/
│   │   ├── features/        # Feature modules
│   │   │   ├── auth/        # Authentication (login/redirect)
│   │   │   ├── admin/       # Admin dashboard
│   │   │   ├── tasks/       # Task/question management
│   │   │   └── user/        # User profile
│   │   ├── components/ui/   # Reusable UI components
│   │   ├── store/           # Redux store
│   │   ├── services/        # API services
│   │   ├── hooks/           # Custom hooks
│   │   └── i18n/            # Internationalization
│   └── package.json
├── docs/                    # Documentation
├── data/                    # SQLite database (created at runtime)
└── pyproject.toml           # Python package config
```

## Quick Start

### Prerequisites
- Python 3.10 or higher
- Node.js 18 or higher (for frontend development)

### Installation

```bash
# Install backend dependencies
pip install -e .

# Install Feishu SDK (optional, for notifications)
pip install lark_oapi

# Install frontend dependencies (optional, for development)
cd frontend && npm install
```

### Running the Server

**Production mode (with pre-built frontend):**
```bash
# Start server with MCP SSE endpoint and built frontend
python -m uvicorn src.web_multi_tenant:app --host 0.0.0.0 --port 8000
```

**Development mode:**
```bash
# Terminal 1: Backend with SSE transport
cd src && PYTHONPATH=. uvicorn web_multi_tenant:app --host 0.0.0.0 --port 8000

# Terminal 2: Frontend dev server
cd frontend && npm run dev
# Access http://localhost:5173
```

**STDIO mode (for MCP clients):**
```bash
# Runs MCP in foreground, web server in background
python -m src.server --mode stdio
```

### First-Time Setup

1. Access `http://localhost:8000`
2. Follow the initialization wizard:
   - Set admin username and password
   - Configure Feishu app (optional, can be done later)
3. Login via Feishu OAuth
4. Get your API Key from user center

## MCP Client Configuration

### Get Your API Key

1. Visit `http://localhost:8000`
2. Click "Login with Feishu"
3. After authorization, copy your API Key from the user center (format: `uk_xxxxxxxx`)

### STDIO Mode

```json
{
  "mcpServers": {
    "user-intent": {
      "command": "uv",
      "args": ["run", "python", "/path/to/src/server.py", "--mode", "stdio"],
      "env": {
        "USERINTENT_API_KEY": "uk_your_api_key"
      }
    }
  }
}
```

### SSE Mode

```json
{
  "mcpServers": {
    "user-intent": {
      "transport": "sse",
      "url": "http://localhost:8000/mcp/sse",
      "headers": {
        "Authorization": "Bearer uk_your_api_key"
      }
    }
  }
}
```

## Environment Variables

| Variable | Description | Default |
|:---|:---|:---|
| `USERINTENT_API_KEY` | User API Key for authentication | - |
| `USERINTENT_DB_PATH` | SQLite database path | `data/intent.db` |
| `USERINTENT_WEB_PORT` | Web server port | `8000` |
| `USERINTENT_WEB_HOST` | Web server host | `0.0.0.0` |
| `USERINTENT_TIMEOUT` | Request timeout (seconds) | `3000` |

## Admin Dashboard

Access `http://localhost:8000/admin` for system administration:

| Feature | Description |
|:---|:---|
| **System Overview** | View user count and request statistics |
| **User Management** | View/disable/enable registered users |
| **Feishu Config** | Configure Feishu app credentials |
| **System Settings** | Change admin password |
| **WebSocket Status** | Monitor/restart Feishu WebSocket listener |

## Feishu App Configuration

### Create Feishu App

1. Create an app at [Feishu Open Platform](https://open.feishu.cn/)
2. Configure OAuth callback: `https://your-domain.com/auth/feishu/callback`
3. Enable permissions:
   - `contact:user.base:readonly` - Get user basic info
   - `im:message:send_as_bot` - Send messages
4. Subscribe to events:
   - Use WebSocket long connection
   - Subscribe `im.message.receive_v1` event

### Environment Setup

**Via Admin UI:**
1. Login to admin dashboard
2. Navigate to "Feishu Configuration"
3. Enter `app_id`, `app_secret`, and `redirect_uri`
4. Save (WebSocket listener will auto-restart)

**Via Database:**
```sql
INSERT INTO admin_config (key, value) VALUES
  ('feishu_app_id', 'cli_xxxxxxxxx'),
  ('feishu_app_secret', 'your_secret'),
  ('feishu_redirect_uri', 'http://localhost:8000/auth/feishu/callback');
```

## Frontend Development

### Tech Stack Details

- **React 19** with Concurrent Features
- **TypeScript** for type safety
- **Redux Toolkit** for state management
- **React Router v7** for routing
- **Tailwind CSS v4** with `@tailwindcss/typography`
- **i18next** + **react-i18next** for i18n
- **Vite** for fast HMR
- **Vitest** for unit testing

### Development Commands

```bash
cd frontend

# Start dev server
npm run dev

# Build for production
npm run build

# Run tests
npm run test

# Run tests with coverage
npm run test:coverage

# Lint code
npm run lint
```

### Feature Modules

- **auth/** - Login page, OAuth redirect handler
- **admin/** - Admin login, dashboard, system initialization
- **tasks/** - Question/reply management, history, sidebar
- **user/** - User profile, API key management

## Production Deployment

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

# Build frontend (optional, use pre-built image instead)
# RUN cd frontend && npm install && npm run build

ENV PYTHONPATH=/app/src
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "web_multi_tenant:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t user-intent-mcp .
docker run -d -p 8000:8000 -v $(pwd)/data:/app/data user-intent-mcp
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

        # SSE & WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # SSE timeout
        proxy_buffering off;
        proxy_read_timeout 86400;
    }
}
```

## Testing

```bash
# Backend unit tests
PYTHONPATH=src pytest tests/test_multi_tenant.py -v

# Backend integration tests
PYTHONPATH=src pytest tests/test_integration.py -v

# Frontend tests
cd frontend && npm run test
```

## Documentation

- [React+Redux Refactor Design](docs/v0.9.0-react-frontend/REFACTOR-react-redux.md)
- [Development Plan](docs/v0.9.0-react-frontend/DEV-PLAN.md)
- [Test Plan](docs/v0.9.0-react-frontend/TEST-PLAN.md)
- [v0.1.0 Design Doc](docs/v0.1.0-multi-tenant/DESIGN-feishu-multi-tenant.md)
- [v0.1.0 Product Requirements](docs/v0.1.0-multi-tenant/PRD-feishu-multi-tenant.md)

## Version History

### v1.0.0 (Current)
- Complete React + Redux frontend rewrite
- Feishu WebSocket listener for real-time messages
- Notification sound alerts
- Sidebar navigation with task history
- Image upload support
- Keyboard shortcuts
- Multi-language support (i18n)
- 30-day session cache
- Production deployment support

### v0.1.0
- Multi-user support with SQLite
- Feishu OAuth integration
- Basic message queuing
- SSE and STDIO transport modes
- Admin dashboard

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

**[中文版文档 (Chinese Version)](README.md)**
