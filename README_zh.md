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
| 📊 系统概览 | 查看用户数量、请求统计 |
| 👥 用户管理 | 查看/管理已注册用户 |
| 🔗 飞书配置 | 配置飞书应用凭据 |
| ⚙️ 系统设置 | 修改管理员密码 |

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

## 🧪 测试

```bash
# 后端测试
PYTHONPATH=src pytest tests/ -v

# 前端测试
cd frontend && npm run test
```

## 📚 文档

- [重构设计文档](docs/v0.9.0-react-frontend/REFACTOR-react-redux.md)
- [开发计划](docs/v0.9.0-react-frontend/DEV-PLAN.md)
- [测试计划](docs/v0.9.0-react-frontend/TEST-PLAN.md)

---
[English Version](README.md)
