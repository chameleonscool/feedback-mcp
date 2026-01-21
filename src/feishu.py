"""
Feishu (Lark) integration module - Send messages and receive replies via Feishu bot.

This module provides:
1. Send messages to users via Feishu bot
2. Receive user replies via WebSocket long connection
3. Configuration management with persistent storage
"""
import json
import logging
import sqlite3
import threading
import queue
import time
from typing import Optional, Callable
from dataclasses import dataclass, field

# Import DB_PATH from core for configuration persistence
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from core import DB_PATH

logger = logging.getLogger("user_intent_mcp")

# Try to import lark_oapi, but make it optional
try:
    import lark_oapi as lark
    from lark_oapi.api.im.v1 import (
        CreateMessageRequest,
        CreateMessageRequestBody,
        CreateMessageResponse,
    )
    LARK_AVAILABLE = True
except ImportError:
    LARK_AVAILABLE = False
    logger.warning("lark_oapi not installed. Feishu mode will not be available. Install with: pip install lark_oapi")


@dataclass
class FeishuConfig:
    """Feishu bot configuration."""
    app_id: str = ""
    app_secret: str = ""
    # Target user/chat to send messages to
    receive_id: str = ""
    # Type of receive_id: open_id, user_id, union_id, email, chat_id
    receive_id_type: str = "open_id"
    # Whether Feishu mode is enabled
    enabled: bool = False


@dataclass
class PendingMessage:
    """A message waiting for reply."""
    request_id: str
    question: str
    message_id: Optional[str] = None
    reply: Optional[str] = None
    replied: bool = False


class FeishuService:
    """
    Feishu service for sending messages and receiving replies.
    
    Uses WebSocket long connection to receive message events from Feishu.
    """
    
    def __init__(self):
        self.config = FeishuConfig()
        self._client: Optional['lark.Client'] = None
        self._ws_client: Optional['lark.ws.Client'] = None
        self._pending_messages: dict[str, PendingMessage] = {}
        self._reply_queues: dict[str, queue.Queue] = {}
        self._lock = threading.Lock()
        self._ws_thread: Optional[threading.Thread] = None
        self._running = False

        # Load configuration from persistent storage on startup
        self.load_config()

    def is_available(self) -> bool:
        """Check if Feishu SDK is available."""
        return LARK_AVAILABLE
    
    def is_configured(self) -> bool:
        """Check if Feishu is properly configured."""
        return (
            self.config.enabled and
            bool(self.config.app_id) and
            bool(self.config.app_secret) and
            bool(self.config.receive_id)
        )

    def load_config(self) -> None:
        """Load configuration from persistent storage (database)."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.execute(
                    "SELECT key, value FROM feishu_config"
                )
                config_dict = {}
                for key, value in cursor.fetchall():
                    config_dict[key] = value

                if config_dict:
                    self.config.app_id = config_dict.get("app_id", "")
                    self.config.app_secret = config_dict.get("app_secret", "")
                    self.config.receive_id = config_dict.get("receive_id", "")
                    self.config.receive_id_type = config_dict.get("receive_id_type", "open_id")
                    self.config.enabled = config_dict.get("enabled", "false").lower() == "true"

                    logger.info(f"Loaded Feishu config from database: enabled={self.config.enabled}")

                    # Initialize client if configured
                    if self.config.enabled and self.config.app_id and self.config.app_secret:
                        self._init_client()
                        # Start WebSocket listener
                        if not self._running:
                            self._start_ws_listener()

        except sqlite3.OperationalError:
            # Table doesn't exist yet, will be created by init_db()
            logger.debug("feishu_config table not found, using default config")
        except Exception as e:
            logger.error(f"Error loading Feishu config: {e}")

    def configure(self, config: dict) -> dict:
        """
        Update Feishu configuration.

        Args:
            config: Dictionary with configuration values

        Returns:
            Status dictionary
        """
        if not LARK_AVAILABLE:
            return {"status": "error", "message": "lark_oapi not installed"}

        # Update in-memory config
        # Handle enabled field - convert from various types to bool
        if "enabled" in config:
            enabled_value = config["enabled"]
            if isinstance(enabled_value, bool):
                self.config.enabled = enabled_value
            elif isinstance(enabled_value, str):
                self.config.enabled = enabled_value.lower() == "true"
            else:
                self.config.enabled = bool(enabled_value)
        self.config.app_id = config.get("app_id", self.config.app_id)
        self.config.app_secret = config.get("app_secret", self.config.app_secret)
        self.config.receive_id = config.get("receive_id", self.config.receive_id)
        self.config.receive_id_type = config.get("receive_id_type", self.config.receive_id_type)

        # Save to persistent storage (database)
        try:
            with sqlite3.connect(DB_PATH) as conn:
                # Use INSERT OR REPLACE to upsert each config value
                # Always save enabled as string "true" or "false"
                conn.execute(
                    "INSERT OR REPLACE INTO feishu_config (key, value) VALUES (?, ?)",
                    ("app_id", self.config.app_id or "")
                )
                conn.execute(
                    "INSERT OR REPLACE INTO feishu_config (key, value) VALUES (?, ?)",
                    ("app_secret", self.config.app_secret or "")
                )
                conn.execute(
                    "INSERT OR REPLACE INTO feishu_config (key, value) VALUES (?, ?)",
                    ("receive_id", self.config.receive_id or "")
                )
                conn.execute(
                    "INSERT OR REPLACE INTO feishu_config (key, value) VALUES (?, ?)",
                    ("receive_id_type", self.config.receive_id_type or "open_id")
                )
                # Explicitly convert enabled to string for storage
                enabled_str = "true" if self.config.enabled else "false"
                conn.execute(
                    "INSERT OR REPLACE INTO feishu_config (key, value) VALUES (?, ?)",
                    ("enabled", enabled_str)
                )
                logger.info("Feishu config saved to database")
        except Exception as e:
            logger.error(f"Failed to save Feishu config: {e}")

        # Reinitialize client if configuration changed
        if self.config.enabled and self.config.app_id and self.config.app_secret:
            self._init_client()
            # Start WebSocket listener if not already running
            if not self._running:
                self._start_ws_listener()
        else:
            self._stop_ws_listener()

        logger.info(f"Feishu config updated: enabled={self.config.enabled}, receive_id_type={self.config.receive_id_type}")
        return {"status": "success", "enabled": self.config.enabled}

    def get_config(self) -> dict:
        """Get current configuration (without secrets)."""
        # Connection status: true if either WebSocket is running OR API client is configured
        # WebSocket is needed for receiving replies, but API client is enough for sending
        connected = self._running or (self.is_configured() and self._client is not None)
        return {
            "enabled": self.config.enabled,
            "app_id": self.config.app_id or "",  # Return full app_id for form usage
            "app_id_display": self.config.app_id[:8] + "..." if len(self.config.app_id) > 8 else (self.config.app_id or ""),  # Display version
            "receive_id": self.config.receive_id,
            "receive_id_type": self.config.receive_id_type,
            "available": LARK_AVAILABLE,
            "connected": connected,
        }

    def _init_client(self):
        """Initialize Feishu API client."""
        if not LARK_AVAILABLE:
            return
            
        self._client = lark.Client.builder() \
            .app_id(self.config.app_id) \
            .app_secret(self.config.app_secret) \
            .log_level(lark.LogLevel.WARNING) \
            .build()
        logger.info("Feishu API client initialized")
    
    def _handle_message_receive(self, data) -> None:
        """Handle incoming message events from Feishu."""
        try:
            event = data.event
            message = event.message
            
            # Get message content
            msg_type = message.message_type
            content = message.content
            sender_id = event.sender.sender_id.open_id if event.sender else None
            
            logger.info(f"Received Feishu message: type={msg_type}, sender={sender_id}")
            
            # Parse text content
            reply_text = ""
            if msg_type == "text":
                try:
                    content_dict = json.loads(content)
                    reply_text = content_dict.get("text", "")
                except json.JSONDecodeError:
                    reply_text = content
            else:
                reply_text = f"[{msg_type} message]"
            
            # Find pending message and deliver reply
            with self._lock:
                # For simplicity, deliver to the oldest pending message
                # In production, you might want to track conversation context
                for request_id, pending in list(self._pending_messages.items()):
                    if not pending.replied:
                        pending.reply = reply_text
                        pending.replied = True
                        # Signal the waiting queue
                        if request_id in self._reply_queues:
                            self._reply_queues[request_id].put(reply_text)
                        logger.info(f"Delivered reply to request {request_id}: {reply_text[:50]}...")
                        break
                        
        except Exception as e:
            logger.error(f"Error handling Feishu message: {e}")
    
    def _start_ws_listener(self):
        """Start WebSocket listener for incoming messages."""
        if not LARK_AVAILABLE or self._running:
            return

        import asyncio

        def run_ws():
            # Create a new event loop for this thread
            loop = None
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Create event handler
                event_handler = lark.EventDispatcherHandler.builder("", "") \
                    .register_p2_im_message_receive_v1(self._handle_message_receive) \
                    .build()

                # Create WebSocket client
                self._ws_client = lark.ws.Client(
                    self.config.app_id,
                    self.config.app_secret,
                    event_handler=event_handler,
                    log_level=lark.LogLevel.WARNING
                )

                self._running = True
                logger.info("Feishu WebSocket listener started")

                # This blocks until connection is closed
                self._ws_client.start()

            except Exception as e:
                logger.error(f"Feishu WebSocket error: {e}")
            finally:
                self._running = False
                logger.info("Feishu WebSocket listener stopped")
                if loop:
                    loop.close()

        self._ws_thread = threading.Thread(target=run_ws, daemon=True)
        self._ws_thread.start()

    def _stop_ws_listener(self):
        """Stop WebSocket listener."""
        self._running = False
        # Note: lark_oapi doesn't provide a clean way to stop the ws client
        # The thread is daemon so it will stop when the main process exits
        logger.info("Feishu WebSocket listener stop requested")
    
    def send_message(self, request_id: str, question: str) -> bool:
        """
        Send a message to the configured Feishu user/chat.

        Args:
            request_id: Unique ID for this request
            question: The question/message to send

        Returns:
            True if message was sent successfully
        """
        result = self.send_message_with_result(request_id, question)
        return result.get("success", False)

    def send_message_with_result(self, request_id: str, question: str) -> dict:
        """
        Send a message to the configured Feishu user/chat.

        Args:
            request_id: Unique ID for this request
            question: The question/message to send

        Returns:
            Dict with keys: success (bool), message (str), code (int), error (str)
        """
        if not self.is_configured():
            return {"success": False, "message": "Feishu not configured"}
        if not self._client:
            return {"success": False, "message": "Feishu client not initialized"}

        try:
            # Build message content
            content = json.dumps({"text": f"🤖 AI Assistant:\n\n{question}\n\n---\n请直接回复此消息"})

            # Create request
            request = CreateMessageRequest.builder() \
                .receive_id_type(self.config.receive_id_type) \
                .request_body(
                    CreateMessageRequestBody.builder()
                    .receive_id(self.config.receive_id)
                    .msg_type("text")
                    .content(content)
                    .build()
                ) \
                .build()

            # Send message
            response: CreateMessageResponse = self._client.im.v1.message.create(request)

            if not response.success():
                error_msg = response.msg or "Unknown error"
                error_code = response.code if response.code is not None else -1

                # Try to get more error details from response
                error_detail = f"code={error_code}, msg={error_msg}"

                logger.error(f"Feishu send failed: {error_detail}")
                return {
                    "success": False,
                    "message": error_msg,
                    "code": error_code,
                    "error": error_detail
                }

            message_id = response.data.message_id if response.data else None
            logger.info(f"Feishu message sent: request_id={request_id}, message_id={message_id}")

            # Track pending message
            with self._lock:
                self._pending_messages[request_id] = PendingMessage(
                    request_id=request_id,
                    question=question,
                    message_id=message_id
                )
                self._reply_queues[request_id] = queue.Queue()

            return {"success": True, "message": "Message sent successfully", "message_id": message_id}

        except Exception as e:
            logger.error(f"Feishu send error: {e}")
            # Try to extract error code from exception message
            error_msg = str(e)
            error_code = -1
            if "code:" in error_msg:
                try:
                    code_part = error_msg.split("code:")[1].split(",")[0].strip()
                    error_code = int(code_part)
                except:
                    pass
            return {"success": False, "message": error_msg, "code": error_code}

    def wait_for_reply(self, request_id: str, timeout: int = 3000) -> Optional[str]:
        """
        Wait for a reply to a specific message.
        
        Args:
            request_id: The request ID to wait for
            timeout: Timeout in seconds
            
        Returns:
            Reply text or None if timeout
        """
        if request_id not in self._reply_queues:
            return None
        
        try:
            reply = self._reply_queues[request_id].get(timeout=timeout)
            return reply
        except queue.Empty:
            logger.warning(f"Feishu reply timeout for request {request_id}")
            return None
        finally:
            # Cleanup
            with self._lock:
                self._pending_messages.pop(request_id, None)
                self._reply_queues.pop(request_id, None)
    
    def get_reply(self, request_id: str) -> Optional[str]:
        """
        Non-blocking check for a reply to a specific message.
        
        Args:
            request_id: The request ID to check
            
        Returns:
            Reply text if available, None otherwise
        """
        if request_id not in self._reply_queues:
            return None
        
        try:
            reply = self._reply_queues[request_id].get_nowait()
            # Cleanup after getting reply
            with self._lock:
                self._pending_messages.pop(request_id, None)
                self._reply_queues.pop(request_id, None)
            return reply
        except queue.Empty:
            return None
    
    def cancel_request(self, request_id: str):
        """Cancel a pending request."""
        with self._lock:
            self._pending_messages.pop(request_id, None)
            self._reply_queues.pop(request_id, None)


# Global singleton instance
feishu_service = FeishuService()
