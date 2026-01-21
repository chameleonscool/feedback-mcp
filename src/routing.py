"""
消息路由模块 - 处理消息的发送和接收路由
"""

import sqlite3
import time
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger("user_intent_mcp.routing")


class MessageRouter:
    """消息路由器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
        
        # 飞书服务实例（延迟加载）
        self._feishu_service = None
    
    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            # 扩展 intent_queue 表，添加用户关联
            # 先检查表是否存在
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='intent_queue'"
            )
            
            if cursor.fetchone():
                # 表已存在，尝试添加新列
                try:
                    conn.execute("ALTER TABLE intent_queue ADD COLUMN open_id TEXT")
                except sqlite3.OperationalError:
                    pass  # 列已存在
                
                try:
                    conn.execute("ALTER TABLE intent_queue ADD COLUMN api_key TEXT")
                except sqlite3.OperationalError:
                    pass  # 列已存在
            else:
                # 创建新表（包含所有字段）
                conn.execute('''
                    CREATE TABLE intent_queue (
                        id TEXT PRIMARY KEY,
                        question TEXT NOT NULL,
                        answer TEXT,
                        image TEXT,
                        status TEXT DEFAULT 'PENDING',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP,
                        open_id TEXT,
                        api_key TEXT
                    )
                ''')
            
            # 创建索引
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_intent_queue_open_id 
                ON intent_queue(open_id)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_intent_queue_status 
                ON intent_queue(status)
            ''')
    
    def create_pending_request(
        self,
        request_id: str,
        open_id: str,
        question: str,
        api_key: Optional[str] = None
    ) -> bool:
        """
        创建待处理的请求
        
        Args:
            request_id: 请求 ID
            open_id: 用户 open_id
            question: 问题内容
            api_key: 可选，API Key
            
        Returns:
            bool: 是否创建成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO intent_queue 
                    (id, question, status, open_id, api_key, created_at)
                    VALUES (?, ?, 'PENDING', ?, ?, CURRENT_TIMESTAMP)
                ''', (request_id, question, open_id, api_key))
            
            logger.info(f"Created pending request {request_id} for user {open_id}")
            return True
            
        except sqlite3.IntegrityError:
            logger.warning(f"Request {request_id} already exists")
            return False
    
    def get_pending_requests(
        self,
        open_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取待处理的请求
        
        Args:
            open_id: 可选，按用户筛选
            limit: 返回数量限制
            
        Returns:
            待处理请求列表
        """
        query = "SELECT * FROM intent_queue WHERE status = 'PENDING'"
        params = []
        
        if open_id:
            query += " AND open_id = ?"
            params.append(open_id)
        
        query += " ORDER BY created_at ASC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "request_id": row["id"],
                    "question": row["question"],
                    "open_id": row["open_id"],
                    "created_at": row["created_at"]
                })
            
            return results
    
    async def send_to_user(
        self,
        open_id: str,
        message: str,
        request_id: str
    ) -> bool:
        """
        发送消息给指定用户
        
        Args:
            open_id: 用户 open_id
            message: 消息内容
            request_id: 请求 ID
            
        Returns:
            bool: 是否发送成功
        """
        return await self._send_feishu_message(open_id, message, request_id)
    
    async def send_by_api_key(
        self,
        api_key: str,
        message: str,
        request_id: str
    ) -> bool:
        """
        根据 API Key 发送消息给用户
        
        Args:
            api_key: 用户的 API Key
            message: 消息内容
            request_id: 请求 ID
            
        Returns:
            bool: 是否发送成功
        """
        from users import UserManager
        
        manager = UserManager(self.db_path)
        user = manager.get_user_by_api_key(api_key)
        
        if not user:
            logger.warning(f"No user found for API key {api_key[:8]}...")
            return False
        
        return await self._send_feishu_message(
            user["open_id"],
            message,
            request_id
        )
    
    async def receive_reply(
        self,
        open_id: str,
        reply_text: str
    ) -> Dict[str, Any]:
        """
        接收用户回复
        
        Args:
            open_id: 用户 open_id
            reply_text: 回复内容
            
        Returns:
            Dict: 包含匹配信息的字典
        """
        # 查找该用户最早的待处理请求
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT id, question FROM intent_queue 
                WHERE open_id = ? AND status = 'PENDING'
                ORDER BY created_at ASC
                LIMIT 1
            ''', (open_id,))
            
            row = cursor.fetchone()
            
            if not row:
                logger.warning(f"No pending request for user {open_id}")
                return {"matched": False, "request_id": None}
            
            request_id = row["id"]
            
            # 更新请求状态
            conn.execute('''
                UPDATE intent_queue SET
                    answer = ?,
                    status = 'COMPLETED',
                    completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (reply_text, request_id))
            
            logger.info(f"Matched reply to request {request_id} for user {open_id}")
            
            return {
                "matched": True,
                "request_id": request_id,
                "question": row["question"]
            }
    
    def get_reply(self, request_id: str) -> Optional[str]:
        """
        获取请求的回复
        
        Args:
            request_id: 请求 ID
            
        Returns:
            回复内容，如果未回复则返回 None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT answer, status FROM intent_queue WHERE id = ?",
                (request_id,)
            )
            row = cursor.fetchone()
            
            if row and row[1] == 'COMPLETED':
                return row[0]
        
        return None
    
    async def _send_feishu_message(
        self,
        open_id: str,
        message: str,
        request_id: str
    ) -> bool:
        """
        通过飞书发送消息
        
        Args:
            open_id: 用户 open_id
            message: 消息内容
            request_id: 请求 ID
            
        Returns:
            bool: 是否发送成功
        """
        try:
            if self._feishu_service is None:
                from feishu import feishu_service
                self._feishu_service = feishu_service
            
            # 使用飞书服务发送消息
            result = self._feishu_service.send_message_to_user(
                open_id=open_id,
                request_id=request_id,
                message=message
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send Feishu message: {e}")
            return False
    
    def cleanup_old_requests(self, days: int = 3):
        """
        清理旧的已完成请求
        
        Args:
            days: 保留天数
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                DELETE FROM intent_queue 
                WHERE status = 'COMPLETED' 
                AND completed_at < datetime('now', ?)
            ''', (f'-{days} days',))
            
            logger.info(f"Cleaned up requests older than {days} days")
