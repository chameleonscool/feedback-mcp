# User Intent MCP

一个支持多模态用户意图采集的 MCP 服务器，让 AI Agent 能够向用户提问并获取回复。

## ✨ 功能特性

- 🔐 **飞书登录** - 通过飞书 OAuth 登录，30 天免登录
- 📨 **消息隔离** - 每个用户只能看到自己的消息
- 🖼️ **图文输入** - 支持文字和截图回复
- 🔔 **飞书通知** - 新消息时推送飞书通知
- 📡 **双传输模式** - 支持 SSE 和 STDIO 两种模式

## 🚀 快速开始

### 安装

```bash
pip install -e .
pip install lark_oapi  # 飞书通知功能
```

### 启动服务

```bash
cd src && PYTHONPATH=. uvicorn web_multi_tenant:app --host 0.0.0.0 --port 8000
```

### 获取 API Key

1. 访问 `http://localhost:8000`
2. 点击「使用飞书登录」
3. 授权后在用户中心复制 API Key

## 🔑 MCP 客户端配置

### STDIO 模式

```json
{
  "mcpServers": {
    "user-intent": {
      "command": "uv",
      "args": ["run", "python", "/path/to/server.py", "--mode", "stdio"],
      "env": {
        "USERINTENT_API_KEY": "uk_your_api_key"
      }
    }
  }
}
```

### SSE 模式

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

## ⚙️ 环境变量

| 变量 | 说明 | 默认值 |
| :--- | :--- | :--- |
| `USERINTENT_API_KEY` | 用户 API Key | - |
| `USERINTENT_DB_PATH` | 数据库路径 | `data/intent.db` |
| `USERINTENT_WEB_PORT` | Web 端口 | `8000` |
| `USERINTENT_TIMEOUT` | 超时时间（秒） | `3000` |

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
