"""
User Intent MCP - A multimodal user intent collection server for AI agents.
"""
from core import mcp, collect_user_intent, init_db, DB_PATH, DATA_DIR

__version__ = "1.0.0"
__all__ = ["mcp", "collect_user_intent", "init_db", "DB_PATH", "DATA_DIR"]

