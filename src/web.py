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

from core import DB_PATH, BASE_DIR


logger = logging.getLogger("feedback_mcp")

# --- FastAPI App ---
app = FastAPI(title="Feedback MCP", description="AI Agent Feedback Interface")

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
            "SELECT id, question FROM feedback_queue WHERE status = 'PENDING'"
        )
        rows = cursor.fetchall()
    return [{"id": row[0], "question": row[1]} for row in rows]


@app.post("/api/reply")
async def receive_reply(reply: ReplyModel):
    """Receives a reply for a specific question."""
    logger.info(f"Received reply for {reply.id}: text={reply.answer[:50] if reply.answer else 'None'}..., image={'YES (' + str(len(reply.image)) + ' chars)' if reply.image else 'NO'}")
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE feedback_queue SET answer = ?, image = ?, status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (reply.answer, reply.image, reply.id)
        )
    return {"status": "success"}


@app.get("/api/history")
async def get_history():
    """Returns list of completed questions (history)."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """SELECT id, question, answer, completed_at 
               FROM feedback_queue 
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
            "UPDATE feedback_queue SET status = 'DISMISSED' WHERE id = ?",
            (request_id,)
        )
    return {"status": "dismissed"}


@app.delete("/api/history/{history_id}")
async def delete_history_item(history_id: str):
    """Deletes a specific history item."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "DELETE FROM feedback_queue WHERE id = ? AND status = 'COMPLETED'",
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
            f"DELETE FROM feedback_queue WHERE id IN ({placeholders}) AND status = 'COMPLETED'",
            data.ids
        )
    return {"status": "deleted", "count": len(data.ids)}
