# Feedback MCP

A Model Context Protocol (MCP) server with multimodal feedback support, allowing AI agents to ask users questions and receive text and image responses.

## ✨ Features

- **Multi-task Parallelism**: Supports multiple agents initiating requests simultaneously.
- **Task Management**: Users can manually dismiss/ignore requests.
- **Multimodal Feedback**: Supports uploading or pasting screenshots.
- **Dual Transport Modes**: Supports both SSE (HTTP) and STDIO modes.
- **System Notifications**: Automatic browser notifications for new questions.
- **Persistence**: Uses SQLite to ensure task state reliability.
- **i18n Support**: Bilingual UI (English/Chinese) with configurable preferences.

## 📁 Project Structure

```
feedback/
├── src/                      # Source code
│   ├── core.py               # Core logic (Database, MCP tools)
│   ├── web.py                # FastAPI routes
│   ├── server.py             # Unified entry point
│   ├── static/               # Static assets (Service Worker)
│   └── templates/index.html  # Web UI
├── data/                     # Runtime data
│   └── feedback.db           # SQLite database
├── .log/                     # Logs
│   └── feedback.log          # Log file
└── tests/                    # Test cases
```

## 🚀 Quick Start

### Installation

```bash
cd feedback
pip install -e .
# Or using uv
uv pip install -e .
```

### Running

**SSE Mode (with Web UI)**:
```bash
cd src && python server.py --mode sse
# Or
cd src && uv run python server.py --mode sse
```

**STDIO Mode (with Web UI)**:
```bash
cd src && python server.py --mode stdio
```

Visit `http://localhost:8000` to view the Web interface.

### MCP Client Configuration

**SSE Mode** (`mcp_config.json`):
```json
{
  "mcpServers": {
    "feedback": {
      "url": "http://localhost:8000/mcp/sse"
    }
  }
}
```

**Using UV with STDIO (Recommended for local use)**:
```json
{
  "mcpServers": {
    "feedback": {
      "command": "uv",
      "args": [
        "run", 
        "python", 
        "/absolute/path/to/feedback/src/server.py", 
        "--mode", 
        "stdio"
      ]
    }
  }
}
```

## ⚙️ Configuration Options

You can configure the server via environment variables in your MCP client:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `FEEDBACK_DB_PATH` | Path to SQLite database file | `data/feedback.db` |
| `FEEDBACK_WEB_PORT` | Web server port | `8000` |
| `FEEDBACK_WEB_HOST` | Web server listen address | `0.0.0.0` |
| `FEEDBACK_ENABLE_SYSTEM_NOTIFY` | Enable native system notifications (notify-send/plyer) | `false` |
| `FEEDBACK_LOG_PATH` | Path to log file | `.log/feedback.log` |

## 🧪 Testing

```bash
PYTHONPATH=src python tests/test_mcp_native.py
PYTHONPATH=src python tests/test_sse_integration.py
```

---
[中文版文档 (Chinese Version)](README_zh.md)
