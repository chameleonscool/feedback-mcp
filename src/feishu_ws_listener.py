#!/usr/bin/env python3
"""
飞书 WebSocket 长连接监听器

此模块提供飞书 WebSocket 长连接功能，可以：
1. 作为独立进程运行：python feishu_ws_listener.py
2. 作为子进程被主服务启动

环境变量:
    USERINTENT_DB_PATH: 数据库路径（可选，默认为 ../data/intent.db）
"""

import os
import sys
import json
import time
import sqlite3
import logging
import signal
import multiprocessing
from typing import Optional, Callable

# 设置路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.getenv("USERINTENT_DB_PATH", os.path.join(DATA_DIR, "intent.db"))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [PID:%(process)d] - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("feishu_ws_listener")

# 尝试导入 lark_oapi
try:
    import lark_oapi as lark
    LARK_AVAILABLE = True
except ImportError:
    LARK_AVAILABLE = False
    logger.warning("lark_oapi not installed. Feishu WebSocket will not be available.")


class FeishuWSListener:
    """飞书 WebSocket 监听器"""
    
    def __init__(self, app_id: str, app_secret: str, db_path: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.db_path = db_path
        self._running = False
        self._ws_client: Optional[lark.ws.Client] = None
        
    def _handle_message_receive(self, data) -> None:
        """处理接收到的消息事件"""
        try:
            event = data.event
            message = event.message
            
            # 获取消息内容
            msg_type = message.message_type
            content = message.content
            sender_id = event.sender.sender_id.open_id if event.sender else None
            
            logger.info(f"Received Feishu message: type={msg_type}, sender={sender_id[:20] if sender_id else 'unknown'}...")
            
            # 解析文本内容
            reply_text = ""
            if msg_type == "text":
                try:
                    content_dict = json.loads(content)
                    reply_text = content_dict.get("text", "")
                except json.JSONDecodeError:
                    reply_text = content
            else:
                reply_text = f"[{msg_type} message]"
            
            # 将回复写入数据库
            if sender_id:
                self._store_reply(sender_id, reply_text)
                
        except Exception as e:
            logger.error(f"Error handling Feishu message: {e}")
    
    def _store_reply(self, sender_id: str, reply_text: str) -> bool:
        """将回复存储到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 查找该用户的待处理请求
                cursor = conn.execute(
                    """SELECT id FROM intent_queue 
                       WHERE user_id = ? AND status = 'PENDING' 
                       ORDER BY created_at ASC LIMIT 1""",
                    (sender_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    request_id = row[0]
                    # 更新数据库中的响应（使用 answer 字段和 COMPLETED 状态，与 web_multi_tenant.py 保持一致）
                    conn.execute(
                        """UPDATE intent_queue 
                           SET answer = ?, status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP
                           WHERE id = ?""",
                        (reply_text, request_id)
                    )
                    logger.info(f"Reply stored for user {sender_id[:20]}..., request {request_id}")
                    return True
                else:
                    logger.warning(f"No pending request found for Feishu user {sender_id[:20]}...")
                    return False
                    
        except Exception as e:
            logger.error(f"Database error storing reply: {e}")
            return False
    
    def start(self):
        """启动 WebSocket 监听"""
        if self._running:
            logger.warning("WebSocket listener is already running")
            return
        
        logger.info(f"Starting Feishu WebSocket listener...")
        logger.info(f"App ID: {self.app_id[:8]}...")
        logger.info(f"Database: {self.db_path}")
        
        try:
            # 创建事件处理器
            event_handler = lark.EventDispatcherHandler.builder("", "") \
                .register_p2_im_message_receive_v1(self._handle_message_receive) \
                .build()
            
            # 创建 WebSocket 客户端
            self._ws_client = lark.ws.Client(
                self.app_id,
                self.app_secret,
                event_handler=event_handler,
                log_level=lark.LogLevel.INFO
            )
            
            self._running = True
            logger.info("Feishu WebSocket listener started successfully")
            
            # 阻塞运行，直到连接关闭
            self._ws_client.start()
            
        except Exception as e:
            logger.error(f"Feishu WebSocket error: {e}")
        finally:
            self._running = False
            logger.info("Feishu WebSocket listener stopped")
    
    def stop(self):
        """停止 WebSocket 监听"""
        self._running = False
        logger.info("Stop requested")


def get_feishu_credentials(db_path: str) -> tuple[Optional[str], Optional[str]]:
    """从数据库获取飞书凭证"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(
                "SELECT key, value FROM admin_config WHERE key IN ('feishu_app_id', 'feishu_app_secret')"
            )
            config = {row[0]: row[1] for row in cursor.fetchall()}
            
            app_id = config.get('feishu_app_id')
            app_secret = config.get('feishu_app_secret')
            
            return app_id, app_secret
    except Exception as e:
        logger.error(f"Error reading credentials from database: {e}")
        return None, None


def get_credentials_hash(db_path: str) -> str:
    """获取凭证的哈希值，用于检测配置变化"""
    import hashlib
    app_id, app_secret = get_feishu_credentials(db_path)
    if app_id and app_secret:
        return hashlib.md5(f"{app_id}:{app_secret}".encode()).hexdigest()
    return ""


class FeishuWSManager:
    """飞书 WebSocket 进程管理器
    
    用于在主服务中管理 WebSocket 监听子进程，支持：
    - 启动/停止子进程
    - 监控配置变化并自动重启
    """
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._process: Optional[multiprocessing.Process] = None
        self._credentials_hash: str = ""
        self._monitor_running = False
        
    def _run_listener(self, app_id: str, app_secret: str, db_path: str):
        """在子进程中运行监听器"""
        if not LARK_AVAILABLE:
            logger.error("lark_oapi not available, cannot start WebSocket listener")
            return
            
        listener = FeishuWSListener(app_id, app_secret, db_path)
        
        # 处理信号
        def signal_handler(signum, frame):
            listener.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 持续运行，断线重连
        while True:
            try:
                listener.start()
            except Exception as e:
                logger.error(f"Listener error: {e}")
            
            logger.info("Reconnecting in 5 seconds...")
            time.sleep(5)
    
    def start(self) -> bool:
        """启动 WebSocket 监听子进程"""
        if not LARK_AVAILABLE:
            logger.warning("lark_oapi not installed, WebSocket listener will not start")
            return False
            
        if self._process and self._process.is_alive():
            logger.warning("WebSocket listener process is already running")
            return False
        
        app_id, app_secret = get_feishu_credentials(self.db_path)
        
        if not app_id or not app_secret:
            logger.warning("Feishu credentials not configured, WebSocket listener will not start")
            return False
        
        self._credentials_hash = get_credentials_hash(self.db_path)
        
        logger.info(f"Starting Feishu WebSocket listener subprocess...")
        logger.info(f"App ID: {app_id[:8]}...")
        
        self._process = multiprocessing.Process(
            target=self._run_listener,
            args=(app_id, app_secret, self.db_path),
            daemon=True
        )
        self._process.start()
        
        logger.info(f"WebSocket listener subprocess started with PID: {self._process.pid}")
        return True
    
    def stop(self):
        """停止 WebSocket 监听子进程"""
        if self._process and self._process.is_alive():
            logger.info(f"Stopping WebSocket listener subprocess (PID: {self._process.pid})...")
            self._process.terminate()
            self._process.join(timeout=5)
            if self._process.is_alive():
                logger.warning("Process did not terminate gracefully, killing...")
                self._process.kill()
            logger.info("WebSocket listener subprocess stopped")
        self._process = None
    
    def restart(self):
        """重启 WebSocket 监听子进程"""
        logger.info("Restarting WebSocket listener...")
        self.stop()
        time.sleep(1)  # 短暂等待
        return self.start()
    
    def ensure_running(self) -> bool:
        """确保 WebSocket 监听器正在运行
        
        如果进程异常退出，会尝试重启。
        
        Returns:
            bool: 是否进行了重启
        """
        # 检查进程是否异常退出
        if self._credentials_hash and (not self._process or not self._process.is_alive()):
            logger.warning("WebSocket listener process died unexpectedly, restarting...")
            return self.start()
        
        return False
    
    def is_running(self) -> bool:
        """检查子进程是否在运行"""
        return self._process is not None and self._process.is_alive()
    
    def get_status(self) -> dict:
        """获取监听器状态"""
        return {
            "running": self.is_running(),
            "pid": self._process.pid if self._process else None,
            "credentials_configured": bool(self._credentials_hash)
        }


# 全局管理器实例
_ws_manager: Optional[FeishuWSManager] = None


def get_ws_manager(db_path: str = DB_PATH) -> FeishuWSManager:
    """获取全局 WebSocket 管理器实例"""
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = FeishuWSManager(db_path)
    return _ws_manager


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("飞书 WebSocket 长连接监听器")
    logger.info("=" * 60)
    
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # 检查数据库是否存在
    if not os.path.exists(DB_PATH):
        logger.error(f"Database not found: {DB_PATH}")
        logger.error("Please initialize the system first by running the main web server.")
        sys.exit(1)
    
    # 获取飞书凭证
    app_id, app_secret = get_feishu_credentials(DB_PATH)
    
    if not app_id or not app_secret:
        logger.error("Feishu credentials not found in database.")
        logger.error("Please configure Feishu App ID and App Secret in the admin panel.")
        sys.exit(1)
    
    logger.info(f"Loaded Feishu credentials: app_id={app_id[:8]}...")
    
    # 创建并启动监听器
    listener = FeishuWSListener(app_id, app_secret, DB_PATH)
    
    # 处理信号
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, stopping...")
        listener.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 启动监听
    while True:
        try:
            listener.start()
        except Exception as e:
            logger.error(f"Listener error: {e}")
        
        if not listener._running:
            logger.info("Reconnecting in 5 seconds...")
            time.sleep(5)


if __name__ == "__main__":
    main()
