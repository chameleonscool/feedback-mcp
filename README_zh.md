# User Intent MCP

一个支持多模态用户意图采集的 MCP (Model Context Protocol) 服务器，允许 AI Agent 向用户提问并接收文本和图片回复。

## ✨ 功能特性

- **多任务并行处理**: 支持多个 Agent 同时发起请求
- **任务管理**: 用户可以手动忽略不想回答的请求
- **图文混排输入**: 支持上传或粘贴截图
- **双传输模式**: 支持 SSE (HTTP) 和 STDIO 两种模式
- **系统通知**: 新提问时自动弹出浏览器通知
- **持久化存储**: 使用 SQLite 确保状态可靠
- **国际化支持**: 支持中英文界面切换，记住用户偏好

## 📁 项目结构

```
user-intent-mcp/
├── src/                      # 主代码目录
│   ├── core.py               # 核心逻辑（数据库、MCP工具）
│   ├── web.py                # FastAPI 路由
│   ├── server.py             # 统一入口
│   ├── static/               # 静态资源 (Service Worker)
│   └── templates/index.html  # Web UI
├── data/                     # 运行时数据
│   └── intent.db             # SQLite 数据库
├── .log/                     # 日志目录
│   └── intent.log            # 日志文件
└── tests/                    # 测试用例
```

## 🚀 快速开始

### 安装

```bash
cd user-intent-mcp
pip install -e .
# 或使用 uv
uv pip install -e .
```

### 运行

**SSE 模式 (带 Web UI)**：
```bash
cd src && python server.py --mode sse
# 或
cd src && uv run python server.py --mode sse
```

**STDIO 模式 (带 Web UI)**：
```bash
cd src && python server.py --mode stdio
```

访问 `http://localhost:8000` 查看 Web 界面。

### MCP 客户端配置

**SSE 模式** (`mcp_config.json`):
```json
{
  "mcpServers": {
    "user-intent": {
      "url": "http://localhost:8000/mcp/sse"
    }
  }
}
```

**或者使用 UV 启动 (推荐用于本地开发)**:
```json
{
  "mcpServers": {
    "user-intent": {
      "command": "uv",
      "args": [
        "run", 
        "python", 
        "/absolute/path/to/user-intent-mcp/src/server.py", 
        "--mode", 
        "stdio"
      ]
    }
  }
}
```

## ⚙️ 配置选项

### 环境变量

您可以通过环境变量在 MCP 客户端中配置服务器：

| 变量名 | 说明 | 默认值 |
| :--- | :--- | :--- |
| `USERINTENT_DB_PATH` | SQLite 数据库文件路径 | `data/intent.db` |
| `USERINTENT_WEB_PORT` | Web 服务器端口 | `8000` |
| `USERINTENT_WEB_HOST` | Web 服务器监听地址 | `0.0.0.0` |
| `USERINTENT_ENABLE_SYSTEM_NOTIFY` | 是否启用系统级原生通知 (notify-send/plyer) | `false` |
| `USERINTENT_LOG_PATH` | 日志文件路径 | `.log/intent.log` |
| `USERINTENT_TIMEOUT` | 用户响应的默认超时时间（秒） | `3000`（50 分钟） |
| `USERINTENT_HISTORY_DAYS` | 已完成意图采集的历史记录保存天数 | `3` |

自定义超时时间的 MCP 客户端配置示例：
```json
{
  "mcpServers": {
    "user-intent": {
      "command": "uv",
      "args": ["run", "python", "/path/to/server.py", "--mode", "stdio"],
      "env": {
        "USERINTENT_TIMEOUT": "600"
      }
    }
  }
}
```

## 🧪 测试

```bash
PYTHONPATH=src python tests/test_mcp_native.py
PYTHONPATH=src python tests/test_sse_integration.py
```

---
[English Version Documentation](README.md)
