"""
Core module - Database, MCP tool, notifications, and logging.
"""
import os
import sys
import sqlite3
import base64
import logging
import platform
import uuid
import time
import traceback
import atexit
from typing import Optional, List

from fastmcp import FastMCP
from fastmcp.utilities.types import Image
from plyer import notification
import threading

# Import Feishu service (lazy loading to avoid import errors if lark_oapi not installed)
feishu_service = None
def get_feishu_service():
    global feishu_service
    if feishu_service is None:
        from feishu import feishu_service as fs
        feishu_service = fs
    return feishu_service

# --- Test Hooks ---
class State:
    def __init__(self):
        self.current_question = None
        self.user_answer = None
        self.answer_event = threading.Event()

state = State()

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, ".log")

# Configuration from Environment Variables (MCP Client Config)
DB_PATH = os.getenv("USERINTENT_DB_PATH", os.path.join(DATA_DIR, "intent.db"))
LOG_PATH = os.getenv("USERINTENT_LOG_PATH", os.path.join(LOG_DIR, "intent.log"))
FATAL_LOG_PATH = os.path.join(LOG_DIR, "fatal.log")
ENABLE_SYSTEM_NOTIFY = os.getenv("USERINTENT_ENABLE_SYSTEM_NOTIFY", "false").lower() == "true"
DEFAULT_TIMEOUT = int(os.getenv("USERINTENT_TIMEOUT", "3000"))
# History retention in days (0 = don't keep history)
HISTORY_RETENTION_DAYS = int(os.getenv("USERINTENT_HISTORY_DAYS", "3"))

# Ensure directories exist
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

# Get current process ID
PID = os.getpid()

# --- Logging ---
# Create formatter with process ID
log_formatter = logging.Formatter(f'%(asctime)s - [PID:{PID}] - %(name)s - %(levelname)s - %(message)s')

# File handler
file_handler = logging.FileHandler(LOG_PATH, mode='a', encoding='utf-8')
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.DEBUG)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

# Configure root logger to INFO to suppress debug noise from libraries
logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])

# Set our app's logger to DEBUG
logger = logging.getLogger("user_intent_mcp")
logger.setLevel(logging.DEBUG)

# Silence specific noisy libraries
logging.getLogger("docket").setLevel(logging.WARNING)
logging.getLogger("fakeredis").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


# --- Fatal Error Handler ---
def _extract_exception_group_details(exc, depth=0):
    """Recursively extract details from ExceptionGroup."""
    indent = "  " * depth
    result = []
    
    if hasattr(exc, 'exceptions'):
        result.append(f"{indent}ExceptionGroup: {exc}")
        for i, nested_exc in enumerate(exc.exceptions):
            result.append(f"{indent}  [{i+1}] {type(nested_exc).__name__}: {nested_exc}")
            result.extend(_extract_exception_group_details(nested_exc, depth + 2))
            if nested_exc.__traceback__:
                tb_lines = ''.join(traceback.format_exception(type(nested_exc), nested_exc, nested_exc.__traceback__))
                result.append(f"{indent}  Traceback:\n{tb_lines}")
    return result


def _extract_all_frames_locals(exc_traceback):
    """Extract local variables from all frames in the traceback."""
    frames_info = []
    if not exc_traceback:
        return frames_info
    
    tb = exc_traceback
    frame_num = 0
    while tb:
        frame = tb.tb_frame
        frame_num += 1
        frame_info = {
            'number': frame_num,
            'filename': frame.f_code.co_filename,
            'lineno': tb.tb_lineno,
            'function': frame.f_code.co_name,
            'locals': {}
        }
        try:
            for key, value in frame.f_locals.items():
                try:
                    frame_info['locals'][key] = repr(value)[:200]
                except Exception:
                    frame_info['locals'][key] = '<unable to repr>'
        except Exception:
            pass
        frames_info.append(frame_info)
        tb = tb.tb_next
    
    return frames_info


def log_fatal_error(exc_type, exc_value, exc_traceback):
    """Log unhandled exceptions to fatal.log with detailed context."""
    if issubclass(exc_type, KeyboardInterrupt):
        # Don't log keyboard interrupts as fatal errors
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    
    # Collect additional context
    context_info = []
    context_info.append(f"Python Version: {sys.version}")
    context_info.append(f"Working Directory: {os.getcwd()}")
    context_info.append(f"Command Line: {' '.join(sys.argv)}")
    
    # If it's an ExceptionGroup, extract all nested exceptions recursively
    nested_info = ""
    if hasattr(exc_value, 'exceptions'):
        nested_info = "\n--- Nested Exceptions (Recursive) ---\n"
        nested_details = _extract_exception_group_details(exc_value)
        nested_info += '\n'.join(nested_details)
    
    # Extract chained exceptions (__cause__ and __context__)
    chain_info = ""
    current = exc_value
    chain_depth = 0
    while current and chain_depth < 10:  # Limit depth to prevent infinite loops
        if current.__cause__:
            chain_info += f"\n--- Caused by (depth {chain_depth + 1}) ---\n"
            chain_info += f"Type: {type(current.__cause__).__name__}\n"
            chain_info += f"Message: {current.__cause__}\n"
            if current.__cause__.__traceback__:
                chain_info += ''.join(traceback.format_exception(
                    type(current.__cause__), current.__cause__, current.__cause__.__traceback__
                ))
            current = current.__cause__
            chain_depth += 1
        elif current.__context__ and not current.__suppress_context__:
            chain_info += f"\n--- Context (depth {chain_depth + 1}) ---\n"
            chain_info += f"Type: {type(current.__context__).__name__}\n"
            chain_info += f"Message: {current.__context__}\n"
            if current.__context__.__traceback__:
                chain_info += ''.join(traceback.format_exception(
                    type(current.__context__), current.__context__, current.__context__.__traceback__
                ))
            current = current.__context__
            chain_depth += 1
        else:
            break
    
    # Extract local variables from ALL frames
    local_vars_info = ""
    frames = _extract_all_frames_locals(exc_traceback)
    if frames:
        local_vars_info = "\n--- Stack Frames with Local Variables ---\n"
        for frame in frames:
            local_vars_info += f"\nFrame #{frame['number']}: {frame['function']} "
            local_vars_info += f"({frame['filename']}:{frame['lineno']})\n"
            if frame['locals']:
                for key, value in frame['locals'].items():
                    local_vars_info += f"  {key}: {value}\n"
            else:
                local_vars_info += "  (no locals)\n"
    
    fatal_entry = f"""
{'='*60}
FATAL ERROR at {timestamp} [PID:{PID}]
{'='*60}

--- System Context ---
{chr(10).join(context_info)}

--- Exception Details ---
Type: {exc_type.__name__}
Message: {exc_value}

--- Full Traceback ---
{error_msg}
{nested_info}
{chain_info}
{local_vars_info}
{'='*60}
"""
    
    # Write to fatal.log
    try:
        with open(FATAL_LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(fatal_entry)
    except Exception:
        pass  # Can't log the logging error
    
    # Also log to regular logger with more detail
    logger.critical(f"FATAL ERROR: {exc_type.__name__}: {exc_value}")
    logger.critical(f"Full traceback:\n{error_msg}")
    if nested_info:
        logger.critical(f"Nested exceptions:\n{nested_info}")
    if chain_info:
        logger.critical(f"Exception chain:\n{chain_info}")
    logger.critical(f"See {FATAL_LOG_PATH} for full details including local variables")
    
    # Call the original exception hook
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


# Install the exception handler
sys.excepthook = log_fatal_error


# --- Exit Handler ---
def log_exit():
    """Log process exit."""
    logger.info(f"Process exiting [PID:{PID}]")


# Register exit handler
atexit.register(log_exit)



# --- Database ---
def init_db():
    """Initialize the SQLite database."""
    with sqlite3.connect(DB_PATH) as conn:
        # Create intent_queue table if not exists
        conn.execute('''
            CREATE TABLE IF NOT EXISTS intent_queue (
                id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT,
                image TEXT,
                status TEXT DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''')
        # Add columns if they don't exist (for migration)
        try:
            conn.execute('ALTER TABLE intent_queue ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        except sqlite3.OperationalError:
            pass  # Column already exists
        try:
            conn.execute('ALTER TABLE intent_queue ADD COLUMN completed_at TIMESTAMP')
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Create feishu_config table for persistent configuration storage
        conn.execute('''
            CREATE TABLE IF NOT EXISTS feishu_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
    logger.info(f"Database initialized at {DB_PATH}")


def cleanup_old_history():
    """Remove history records older than HISTORY_RETENTION_DAYS."""
    if HISTORY_RETENTION_DAYS <= 0:
        return
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            DELETE FROM intent_queue 
            WHERE status = 'COMPLETED' 
            AND completed_at < datetime('now', ?)
        ''', (f'-{HISTORY_RETENTION_DAYS} days',))


# Initialize database on import
init_db()


# --- Notifications ---
# --- Notifications ---
def send_notification(title: str, message: str):
    """Send a system notification if enabled."""
    if not ENABLE_SYSTEM_NOTIFY:
        return
        
    try:
        if platform.system() == "Linux":
            os.system(f'notify-send "{title}" "{message}"')
        else:
            notification.notify(title=title, message=message, timeout=10)
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")


# --- MCP Server ---
mcp = FastMCP("User Intent Bridge")


@mcp.tool
async def collect_user_intent(question: str) -> str | list:
    """
    Send a message to the user and collect their intent or response.
    
    This tool displays content in a web interface and waits for user input.
    Users can provide text responses and optionally attach images.
    
    Use cases:
    - Request clarification on ambiguous requirements
    - Get approval before proceeding with changes
    - Collect additional context or preferences
    - Show progress and request next steps
    
    Args:
        question: The message or question to present to the user.
    
    Returns:
        User's response as text, or a list containing text and image data.
    """
    timeout = DEFAULT_TIMEOUT
    request_id = str(uuid.uuid4())
    
    # 获取用户信息（用于消息隔离和飞书通知）
    user_info = _get_user_info_from_api_key()
    
    # 检查是否应该发送飞书通知
    if user_info and user_info.get('feishu_notify_enabled'):
        fs = get_feishu_service()
        # 使用用户的 open_id 作为 receive_id 发送飞书消息
        if _send_feishu_to_user(fs, user_info['open_id'], request_id, question):
            logger.info(f"Feishu notification sent to user {user_info['open_id'][:10]}...")
    
    # 始终使用 Web UI 模式等待回复（飞书只是通知）
    return await _collect_via_web(request_id, question, timeout)


async def _collect_via_feishu(fs, request_id: str, question: str, timeout: int) -> str:
    """Collect user intent via Feishu bot."""
    import asyncio
    logger.info(f"Using Feishu mode for request {request_id}")
    
    # Send message to Feishu
    if not fs.send_message(request_id, question):
        logger.warning("Feishu send failed, falling back to web mode")
        return await _collect_via_web(request_id, question, timeout)
    
    # Wait for reply from Feishu (use asyncio-friendly polling)
    start_time = time.time()
    while time.time() - start_time < timeout:
        reply = fs.get_reply(request_id)
        if reply:
            logger.info(f"Feishu reply received for {request_id}: {reply[:50]}...")
            return reply
        await asyncio.sleep(1)
    
    # Timeout
    fs.cancel_request(request_id)
    return "Timeout: No response received from Feishu."


def _get_user_info_from_api_key() -> dict | None:
    """
    从环境变量获取 API Key 并查询对应的用户信息
    
    返回:
    - 用户信息字典，包含 open_id, name, feishu_notify_enabled 等
    - 如果未配置或用户不存在，返回 None
    """
    api_key = os.getenv("USERINTENT_API_KEY")
    if not api_key:
        return None
    
    try:
        from users import UserManager
        user_manager = UserManager(DB_PATH)
        user = user_manager.get_user_by_api_key(api_key)
        if user:
            # 检查用户是否启用了飞书通知
            feishu_notify_enabled = False
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    cursor = conn.execute(
                        "SELECT value FROM user_settings WHERE user_id = ? AND key = 'feishu_notify_enabled'",
                        (user["open_id"],)
                    )
                    row = cursor.fetchone()
                    feishu_notify_enabled = row[0] == "1" if row else False
            except Exception:
                pass  # 表可能不存在
            
            logger.info(f"API Key authenticated for user: {user.get('name', 'Unknown')} ({user['open_id'][:10]}...), feishu_notify={feishu_notify_enabled}")
            return {
                "open_id": user["open_id"],
                "name": user.get("name"),
                "feishu_notify_enabled": feishu_notify_enabled
            }
    except Exception as e:
        logger.warning(f"Failed to get user info from API Key: {e}")
    
    return None


def _get_user_id_from_api_key() -> str | None:
    """
    从环境变量获取 API Key 并查询对应的用户 ID（兼容旧接口）
    """
    user_info = _get_user_info_from_api_key()
    return user_info["open_id"] if user_info else None


def _send_feishu_to_user(fs, open_id: str, request_id: str, question: str) -> bool:
    """
    向指定用户发送飞书消息
    
    Args:
        fs: FeishuService 实例
        open_id: 用户的飞书 open_id
        request_id: 请求 ID
        question: 问题内容
    
    Returns:
        是否发送成功
    """
    try:
        # 检查飞书服务是否可用（只需要 app_id 和 app_secret）
        if not fs.is_available():
            logger.debug("Feishu SDK not available")
            return False
        
        # 获取系统配置的 app_id 和 app_secret（从 admin_config 表）
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("SELECT key, value FROM admin_config WHERE key IN ('feishu_app_id', 'feishu_app_secret')")
            config = {row[0]: row[1] for row in cursor.fetchall()}
        
        app_id = config.get('feishu_app_id')
        app_secret = config.get('feishu_app_secret')
        
        if not app_id or not app_secret:
            logger.debug("Feishu app credentials not configured in admin_config")
            return False
        
        # 临时配置飞书服务以发送消息
        fs.config.app_id = app_id
        fs.config.app_secret = app_secret
        fs.config.receive_id = open_id
        fs.config.receive_id_type = "open_id"
        fs.config.enabled = True
        fs._init_client()
        
        # 发送消息
        result = fs.send_message(request_id, question)
        logger.info(f"Feishu message sent to user {open_id[:15]}... for request {request_id}")
        return result
    except Exception as e:
        logger.warning(f"Failed to send Feishu message to user: {e}")
        return False


def _get_user_id_from_user_info(user_info: dict | None) -> str | None:
    """从用户信息中提取 user_id"""
    return user_info["open_id"] if user_info else None


async def _collect_via_web(request_id: str, question: str, timeout: int) -> str | list:
    """Collect user intent via Web UI (async implementation for SSE mode)."""
    import asyncio
    
    # 获取用户 ID（用于消息隔离）
    user_id = _get_user_id_from_api_key()
    
    # Store question in database（包含 user_id）
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO intent_queue (id, question, status, user_id) VALUES (?, ?, 'PENDING', ?)",
            (request_id, question, user_id)
        )
    
    logger.info(f"Question stored: {question[:50]}... (ID: {request_id})")
    # Send System Notification (if enabled)
    send_notification("AI Intent Request", f"[{request_id[:8]}] {question}")
    
    # Update state for native testing
    state.current_question = question
    state.user_answer = None
    state.answer_event.clear()
    
    # Poll for response (async to not block event loop)
    start_time = time.time()
    while time.time() - start_time < timeout:
        # Native Test Hook: Check if test state was set manually
        if state.answer_event.is_set():
            logger.info(f"Native reply detected via state hooks (Test Mode)")
            res = state.user_answer
            # Clean up DB for consistency
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("DELETE FROM intent_queue WHERE id = ?", (request_id,))
            return res

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute(
                "SELECT answer, image, status FROM intent_queue WHERE id = ?",
                (request_id,)
            )
            row = cursor.fetchone()
            
            if row:
                answer, image_data, status = row
                
                if status == 'DISMISSED':
                    # Dismissed records are deleted immediately (not kept in history)
                    conn.execute("DELETE FROM intent_queue WHERE id = ?", (request_id,))
                    return "User dismissed this request."
                
                if status == 'COMPLETED' and answer:
                    # Keep completed records for history (cleanup_old_history will remove old ones)
                    logger.info(f"Reply received for {request_id}: text={answer[:30]}..., image={'YES' if image_data else 'NO'}")
                    # Cleanup old history periodically
                    cleanup_old_history()
                    
                    # Return list of content blocks for multimodal response
                    if image_data and image_data.startswith("data:image"):
                        try:
                            header, encoded = image_data.split(",", 1)
                            img_format = header.split("/")[1].split(";")[0]
                            img_bytes = base64.b64decode(encoded)
                            img = Image(data=img_bytes, format=img_format)
                            return [answer, img.to_image_content()]
                        except Exception as e:
                            logger.error(f"Failed to decode image: {e}")
                            return answer
                    
                    return answer
        
        # Use asyncio.sleep to yield control back to event loop
        await asyncio.sleep(1)
    
    # Timeout - cleanup
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM intent_queue WHERE id = ?", (request_id,))
    
    return "Timeout: No response received."
