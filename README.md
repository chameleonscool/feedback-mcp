# User Intent MCP

一个支持多模态用户意图采集的 MCP（Model Context Protocol）服务器，让 AI Agent 能够向用户提问并获取回复。

## 功能特性

### 核心能力
- **双传输模式** - 支持 SSE（HTTP）和 STDIO 两种传输模式
- **多模态输入** - 接受文字和图片回复
- **消息隔离** - 每个用户只能看到自己的消息
- **队列管理** - 自动问题队列，支持 PENDING/COMPLETED/DISMISSED 状态

### 认证与多租户
- **飞书 OAuth** - 企业级认证，支持飞书（Lark）OAuth 2.0
- **30天会话缓存** - 长期登录会话，提升用户体验
- **多租户支持** - 用户级和企业级隔离
- **管理后台** - 系统初始化和用户管理

### 通知系统
- **飞书通知** - 新消息推送通知
- **WebSocket 监听器** - 通过飞书 WebSocket API 实时接收消息
- **声音提醒** - 新问题的音频通知
- **可配置提醒** - 用户可自主启用/禁用通知

### 现代化前端
- **React 19 + TypeScript** - 类型安全的现代 React 开发
- **Redux Toolkit** - 高效的状态管理
- **响应式设计** - 基于 Tailwind CSS 的移动友好界面
- **侧边栏导航** - 直观的任务历史浏览
- **快捷键支持** - 快速操作支持
- **国际化支持** - 多语言支持（中英文）

## 架构

### 后端技术栈
- **FastAPI** - 现代化 Python Web 框架
- **FastMCP** - MCP 协议实现
- **SQLite** - 轻量级嵌入式数据库
- **Uvicorn** - ASGI 服务器
- **lark-oapi** - 飞书/Lark SDK

### 前端技术栈
- **React 19** - 最新 React，支持并发特性
- **Redux Toolkit** - 可预测的状态管理
- **React Router v7** - 声明式路由
- **Tailwind CSS v4** - 原子化 CSS 框架
- **Vite** - 下一代前端构建工具
- **Vitest** - 单元测试框架
- **i18next** - 国际化框架

### 项目结构
```
interactive-mcp/
├── src/                      # 后端源代码
│   ├── core.py              # MCP 服务器核心与配置
│   ├── server.py            # 统一入口（SSE/STDIO）
│   ├── web_multi_tenant.py  # FastAPI 多租户应用
│   ├── auth.py              # 管理员认证
│   ├── users.py             # 用户管理
│   ├── oauth.py             # 飞书 OAuth
│   ├── feishu.py            # 飞书通知服务
│   ├── feishu_ws_listener.py # WebSocket 消息监听器
│   └── static/              # 静态资源（Service Worker）
├── frontend/                # React 前端
│   ├── src/
│   │   ├── features/        # 功能模块
│   │   │   ├── auth/        # 认证（登录/重定向）
│   │   │   ├── admin/       # 管理后台
│   │   │   ├── tasks/       # 任务/问题管理
│   │   │   └── user/        # 用户资料
│   │   ├── components/ui/   # 可复用 UI 组件
│   │   ├── store/           # Redux Store
│   │   ├── services/        # API 服务
│   │   ├── hooks/           # 自定义 Hooks
│   │   └── i18n/            # 国际化
│   └── package.json
├── docs/                    # 文档
├── data/                    # SQLite 数据库（运行时创建）
└── pyproject.toml           # Python 包配置
```

## 快速开始

### 环境要求
- Python 3.10 或更高版本
- Node.js 18 或更高版本（前端开发需要）

### 安装依赖

```bash
# 安装后端依赖
pip install -e .

# 安装飞书 SDK（可选，用于通知功能）
pip install lark_oapi

# 安装前端依赖（可选，用于开发）
cd frontend && npm install
```

### 启动服务

**生产模式（使用预构建前端）：**
```bash
# 启动服务器，包含 MCP SSE 端点和内置前端
python -m uvicorn src.web_multi_tenant:app --host 0.0.0.0 --port 8000
```

**开发模式：**
```bash
# 终端 1：后端服务（SSE 传输模式）
cd src && PYTHONPATH=. uvicorn web_multi_tenant:app --host 0.0.0.0 --port 8000

# 终端 2：前端开发服务器
cd frontend && npm run dev
# 访问 http://localhost:5173
```

**STDIO 模式（用于 MCP 客户端）：**
```bash
# MCP 前台运行，Web 服务器后台运行
python -m src.server --mode stdio
```

### 首次使用

1. 访问 `http://localhost:8000`
2. 按照初始化向导操作：
   - 设置管理员账号密码
   - 配置飞书应用（可稍后配置）
3. 通过飞书 OAuth 登录
4. 在用户中心获取 API Key

## MCP 客户端配置

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
      "args": ["run", "python", "/path/to/src/server.py", "--mode", "stdio"],
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

## 环境变量

| 变量 | 说明 | 默认值 |
|:---|:---|:---|
| `USERINTENT_API_KEY` | 用户 API Key（用于认证） | - |
| `USERINTENT_DB_PATH` | SQLite 数据库路径 | `data/intent.db` |
| `USERINTENT_WEB_PORT` | Web 服务器端口 | `8000` |
| `USERINTENT_WEB_HOST` | Web 服务器主机 | `0.0.0.0` |
| `USERINTENT_TIMEOUT` | 请求超时时间（秒） | `3000` |

## 管理后台

访问 `http://localhost:8000/admin` 进入系统管理：

| 功能 | 说明 |
|:---|:---|
| **系统概览** | 查看用户数量和请求统计 |
| **用户管理** | 查看/禁用/启用已注册用户 |
| **飞书配置** | 配置飞书应用凭据 |
| **系统设置** | 修改管理员密码 |
| **WebSocket 状态** | 监控/重启飞书 WebSocket 监听器 |

## 飞书应用配置

### 创建飞书应用

1. 在[飞书开放平台](https://open.feishu.cn/)创建应用
2. 配置 OAuth 回调地址：`https://your-domain.com/auth/feishu/callback`
3. 开通权限：
   - `contact:user.base:readonly` - 获取用户基本信息
   - `im:message:send_as_bot` - 发送消息
4. 配置事件订阅：
   - 使用 WebSocket 长连接
   - 订阅 `im.message.receive_v1` 事件

### 环境配置

**通过管理后台：**
1. 登录管理后台
2. 进入「飞书配置」页面
3. 输入 `app_id`、`app_secret` 和 `redirect_uri`
4. 保存（WebSocket 监听器将自动重启）

**通过数据库：**
```sql
INSERT INTO admin_config (key, value) VALUES
  ('feishu_app_id', 'cli_xxxxxxxxx'),
  ('feishu_app_secret', 'your_secret'),
  ('feishu_redirect_uri', 'http://localhost:8000/auth/feishu/callback');
```

## 前端开发

### 技术栈详情

- **React 19** 支持并发特性
- **TypeScript** 类型安全
- **Redux Toolkit** 状态管理
- **React Router v7** 路由管理
- **Tailwind CSS v4** 及 `@tailwindcss/typography`
- **i18next** + **react-i18next** 国际化
- **Vite** 快速 HMR
- **Vitest** 单元测试

### 开发命令

```bash
cd frontend

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 运行测试
npm run test

# 运行测试（含覆盖率）
npm run test:coverage

# 代码检查
npm run lint
```

### 功能模块

- **auth/** - 登录页面、OAuth 重定向处理
- **admin/** - 管理员登录、仪表板、系统初始化
- **tasks/** - 问题/回复管理、历史记录、侧边栏
- **user/** - 用户资料、API Key 管理

## 生产部署

### 使用 systemd（Linux）

创建 `/etc/systemd/system/user-intent-mcp.service`：

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

启用并启动：
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

# 构建前端（可选，也可使用预构建镜像）
# RUN cd frontend && npm install && npm run build

ENV PYTHONPATH=/app/src
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "web_multi_tenant:app", "--host", "0.0.0.0", "--port", "8000"]
```

构建并运行：
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

        # SSE 和 WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # SSE 超时设置
        proxy_buffering off;
        proxy_read_timeout 86400;
    }
}
```

## 测试

```bash
# 后端单元测试
PYTHONPATH=src pytest tests/test_multi_tenant.py -v

# 后端集成测试
PYTHONPATH=src pytest tests/test_integration.py -v

# 前端测试
cd frontend && npm run test
```

## 文档

- [React+Redux 重构设计文档](docs/v0.9.0-react-frontend/REFACTOR-react-redux.md)
- [开发计划](docs/v0.9.0-react-frontend/DEV-PLAN.md)
- [测试计划](docs/v0.9.0-react-frontend/TEST-PLAN.md)
- [v0.1.0 设计文档](docs/v0.1.0-multi-tenant/DESIGN-feishu-multi-tenant.md)
- [v0.1.0 产品需求](docs/v0.1.0-multi-tenant/PRD-feishu-multi-tenant.md)

## 版本历史

### v1.0.0（当前版本）
- 完整的 React + Redux 前端重构
- 飞书 WebSocket 监听器，实时接收消息
- 通知声音提醒
- 侧边栏导航与任务历史
- 图片上传支持
- 快捷键支持
- 多语言支持（i18n）
- 30天会话缓存
- 生产部署支持

### v0.1.0
- SQLite 多用户支持
- 飞书 OAuth 集成
- 基础消息队列
- SSE 和 STDIO 传输模式
- 管理后台

## 许可证

MIT License

## 贡献

欢迎贡献！请随时提交 Pull Request。

---

**[English Version](README_en.md)**
