# User Intent MCP

一个支持多模态用户意图采集的 MCP 服务器，让 AI Agent 能够向用户提问并获取回复。

## ✨ 功能特性

- 🔐 **飞书登录** - 通过飞书 OAuth 登录，30 天免登录
- 📨 **消息隔离** - 每个用户只能看到自己的消息
- 🖼️ **图文输入** - 支持文字和截图回复
- 🔔 **飞书通知** - 新消息时推送飞书通知
- 📡 **双传输模式** - 支持 SSE 和 STDIO 两种模式
- 🎨 **React 前端** - 现代化 React + Redux 管理界面 (v0.9.0)

## 🚀 快速开始

### 1. 安装依赖

```bash
# 后端依赖
pip install -e .
pip install lark_oapi  # 飞书通知功能

# 前端依赖 (可选，用于开发)
cd frontend && npm install
```

### 2. 启动服务

**后端服务：**
```bash
cd src && PYTHONPATH=. uvicorn web_multi_tenant:app --host 0.0.0.0 --port 8000
```

**前端开发服务（可选）：**
```bash
cd frontend && npm run dev
# 访问 http://localhost:5173
```

### 3. 首次使用

1. 访问 `http://localhost:8000`
2. 首次访问会进入初始化向导：
   - 设置管理员账号密码
   - 配置飞书应用（可稍后配置）
3. 初始化完成后可使用飞书登录

### 4. 管理后台

访问 `http://localhost:8000/admin` 进入管理后台：

| 功能 | 说明 |
|------|------|
| 系统概览 | 查看用户数量、请求统计 |
| 用户管理 | 查看/管理已注册用户 |
| 飞书配置 | 配置飞书应用凭据 |
| 系统设置 | 修改管理员密码 |

## 🔑 MCP 客户端配置

### 获取 API Key

1. 访问 `http://localhost:8000`
2. 点击「使用飞书登录」
3. 授权后在用户中心复制 API Key（格式：`uk_xxxxxxxx`）

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

## 🎨 前端开发 (v0.9.0)

### 技术栈

- **React 19** + **TypeScript**
- **Redux Toolkit** - 状态管理
- **React Router** - 路由
- **Tailwind CSS** - 样式
- **Vite** - 构建工具
- **Vitest** - 测试框架

### 开发命令

```bash
cd frontend

# 开发服务器
npm run dev

# 构建生产版本
npm run build

# 运行测试
npm run test

# 代码检查
npm run lint
```

### 项目结构

```
frontend/
├── src/
│   ├── features/          # 功能模块
│   │   ├── auth/          # 认证模块
│   │   ├── admin/         # 管理模块
│   │   ├── tasks/         # 任务模块
│   │   └── user/          # 用户模块
│   ├── components/ui/     # UI 组件
│   ├── store/             # Redux Store
│   ├── services/          # API 服务
│   ├── hooks/             # 自定义 Hooks
│   ├── i18n/              # 国际化
│   └── types/             # TypeScript 类型
└── vite.config.ts         # Vite 配置
```

## 🚀 生产部署

### 使用 systemd (Linux)

创建 `/etc/systemd/system/user-intent-mcp.service`:

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

启用并启动:
```bash
sudo systemctl enable user-intent-mcp
sudo systemctl start user-intent-mcp
```

### 使用 Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install -e . && pip install lark_oapi

ENV PYTHONPATH=/app/src
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "web_multi_tenant:app", "--host", "0.0.0.0", "--port", "8000"]
```

构建并运行:
```bash
docker build -t user-intent-mcp .
docker run -d -p 8000:8000 -v $(pwd)/data:/app/data user-intent-mcp
```

### Nginx 反向代理

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

### 飞书应用配置

1. 在 [飞书开放平台](https://open.feishu.cn/) 创建应用
2. 配置 OAuth 回调地址: `https://intent.example.com/auth/feishu/callback`
3. 开通权限:
   - `contact:user.base:readonly` - 获取用户基本信息
   - `im:message:send_as_bot` - 发送消息
4. 配置事件订阅:
   - 使用 WebSocket 长连接
   - 订阅 `im.message.receive_v1` 事件

## 🧪 测试

```bash
# 后端单元测试
PYTHONPATH=src pytest tests/test_multi_tenant.py -v

# 后端集成测试
PYTHONPATH=src pytest tests/test_integration.py -v

# 前端测试
cd frontend && npm run test
```

## 📚 文档

- [重构设计文档](docs/v0.9.0-react-frontend/REFACTOR-react-redux.md)
- [开发计划](docs/v0.9.0-react-frontend/DEV-PLAN.md)
- [测试计划](docs/v0.9.0-react-frontend/TEST-PLAN.md)
- [v0.1.0 设计文档](docs/v0.1.0-multi-tenant/DESIGN-feishu-multi-tenant.md)
- [v0.1.0 产品需求](docs/v0.1.0-multi-tenant/PRD-feishu-multi-tenant.md)

## 📝 版本历史

- **v0.9.0** - React + Redux 前端重构
- **v0.1.0** - 多用户支持 + 飞书集成

---
[中文版文档 (Chinese Version)](README_zh.md)
