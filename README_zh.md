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
        "USERINTENT_API_KEY": "uk_您的API_Key"
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
        "Authorization": "Bearer uk_您的API_Key"
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

## 🧪 测试

```bash
PYTHONPATH=src pytest tests/test_multi_tenant.py -v
```

---
[English Version](README.md)
