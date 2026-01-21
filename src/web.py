"""
Web module - FastAPI application for the Web UI.
"""
import sqlite3
import logging
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os

from core import DB_PATH, BASE_DIR, get_feishu_service


logger = logging.getLogger("user_intent_mcp")

# --- FastAPI App ---
app = FastAPI(title="User Intent MCP", description="AI Agent User Intent Collection Interface")

# Templates & Static
STATIC_DIR = os.path.join(BASE_DIR, "src", "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "src", "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/sw.js")
async def get_sw():
    return FileResponse(os.path.join(STATIC_DIR, "sw.js"))


# --- Pydantic Models ---
class ReplyModel(BaseModel):
    id: str
    answer: str
    image: Optional[str] = None


# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main Web UI."""
    return templates.TemplateResponse(request, "index.html")


@app.get("/api/poll")
async def poll_question():
    """Returns list of all pending questions."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "SELECT id, question FROM intent_queue WHERE status = 'PENDING'"
        )
        rows = cursor.fetchall()
    return [{"id": row[0], "question": row[1]} for row in rows]


@app.post("/api/reply")
async def receive_reply(reply: ReplyModel):
    """Receives a reply for a specific question."""
    logger.info(f"Received reply for {reply.id}: text={reply.answer[:50] if reply.answer else 'None'}..., image={'YES (' + str(len(reply.image)) + ' chars)' if reply.image else 'NO'}")
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE intent_queue SET answer = ?, image = ?, status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (reply.answer, reply.image, reply.id)
        )
    return {"status": "success"}


@app.get("/api/history")
async def get_history():
    """Returns list of completed questions (history)."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """SELECT id, question, answer, completed_at 
               FROM intent_queue 
               WHERE status = 'COMPLETED' 
               ORDER BY completed_at DESC
               LIMIT 50"""
        )
        rows = cursor.fetchall()
    return [
        {
            "id": row[0], 
            "question": row[1], 
            "answer": row[2],
            "completed_at": row[3]
        } 
        for row in rows
    ]


@app.delete("/api/request/{request_id}")
async def delete_request(request_id: str):
    """Dismisses a specific request."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE intent_queue SET status = 'DISMISSED' WHERE id = ?",
            (request_id,)
        )
    return {"status": "dismissed"}


@app.delete("/api/history/{history_id}")
async def delete_history_item(history_id: str):
    """Deletes a specific history item."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "DELETE FROM intent_queue WHERE id = ? AND status = 'COMPLETED'",
            (history_id,)
        )
    return {"status": "deleted"}


class DeleteHistoryModel(BaseModel):
    ids: list[str]


@app.post("/api/history/delete")
async def delete_history_batch(data: DeleteHistoryModel):
    """Deletes multiple history items."""
    with sqlite3.connect(DB_PATH) as conn:
        placeholders = ','.join(['?' for _ in data.ids])
        conn.execute(
            f"DELETE FROM intent_queue WHERE id IN ({placeholders}) AND status = 'COMPLETED'",
            data.ids
        )
    return {"status": "deleted", "count": len(data.ids)}


# --- Feishu API Endpoints ---
class FeishuConfigModel(BaseModel):
    enabled: Optional[bool] = None
    app_id: Optional[str] = None
    app_secret: Optional[str] = None
    receive_id: Optional[str] = None
    receive_id_type: Optional[str] = None


@app.get("/api/feishu/config")
async def get_feishu_config():
    """Get current Feishu configuration (without secrets)."""
    fs = get_feishu_service()
    return fs.get_config()


@app.post("/api/feishu/config")
async def update_feishu_config(config: FeishuConfigModel):
    """Update Feishu configuration."""
    fs = get_feishu_service()
    config_dict = {k: v for k, v in config.model_dump().items() if v is not None}
    return fs.configure(config_dict)


@app.post("/api/feishu/test")
async def test_feishu_connection():
    """Test Feishu connection by sending a test message."""
    fs = get_feishu_service()
    if not fs.is_available():
        return {"status": "error", "message": "lark_oapi not installed"}
    if not fs.is_configured():
        return {"status": "error", "message": "Feishu not configured"}

    # Send a test message with detailed error info
    import uuid
    test_id = str(uuid.uuid4())
    result = fs.send_message_with_result(
        test_id,
        "🔔 Test message from AI Intent Center\n\nThis is a test to verify the Feishu connection is working."
    )
    fs.cancel_request(test_id)  # Don't wait for reply

    if result.get("success"):
        return {"status": "success", "message": result.get("message", "Test message sent successfully")}
    else:
        # Return detailed error information
        error_code = result.get("code")
        error_msg = result.get("message", "Unknown error")
        error_detail = result.get("error", "")

        # Map common error codes to helpful messages
        error_help = {
            "99991401": "用户不在可用范围内",
            "99991402": "机器人不在该群组中",
            "99991403": "机器人能力未激活",
            "99991404": "没有权限发送消息",
            "99991406": "receive_id 无效",
            "99991603": "App ID 或 App Secret 无效",
            "10003": "认证失败，请检查 App ID 和 App Secret",
            "1000040346": "应用未发布或 App ID 无效",
        }

        help_text = error_help.get(str(error_code), "")

        return {
            "status": "error",
            "message": error_msg,
            "code": error_code,
            "error": error_detail,
            "help": help_text
        }
