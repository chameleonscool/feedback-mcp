"""
用户管理模块 - 用户数据存储和 API Key 管理
"""

import sqlite3
import secrets
import time
from typing import Optional, Dict, Any, List


class UserManager:
    """用户管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    open_id TEXT UNIQUE NOT NULL,
                    union_id TEXT,
                    user_id TEXT,
                    name TEXT NOT NULL,
                    en_name TEXT,
                    avatar_url TEXT,
                    avatar_thumb TEXT,
                    email TEXT,
                    mobile TEXT,
                    tenant_key TEXT,
                    api_key TEXT UNIQUE NOT NULL,
                    access_token TEXT,
                    refresh_token TEXT,
                    token_expires_at INTEGER,
                    is_active INTEGER DEFAULT 1,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    last_login_at INTEGER
                )
            ''')
            
            # 创建索引
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_users_api_key 
                ON users(api_key)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_users_tenant_key 
                ON users(tenant_key)
            ''')
    
    def create_user(
        self,
        open_id: str,
        union_id: Optional[str] = None,
        user_id: Optional[str] = None,
        name: str = "",
        en_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        avatar_thumb: Optional[str] = None,
        email: Optional[str] = None,
        mobile: Optional[str] = None,
        tenant_key: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        token_expires_at: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        创建新用户
        
        Args:
            open_id: 飞书 open_id（唯一标识）
            union_id: 飞书 union_id
            user_id: 飞书 user_id
            name: 用户姓名
            en_name: 英文名
            avatar_url: 头像 URL
            avatar_thumb: 头像缩略图 URL
            email: 邮箱
            mobile: 手机号
            tenant_key: 租户 key
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            token_expires_at: token 过期时间
            
        Returns:
            创建的用户信息字典
        """
        api_key = self._generate_api_key()
        now = int(time.time())
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO users (
                        open_id, union_id, user_id, name, en_name,
                        avatar_url, avatar_thumb, email, mobile, tenant_key,
                        api_key, access_token, refresh_token, token_expires_at,
                        is_active, created_at, updated_at, last_login_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                ''', (
                    open_id, union_id, user_id, name, en_name,
                    avatar_url, avatar_thumb, email, mobile, tenant_key,
                    api_key, access_token, refresh_token, token_expires_at,
                    now, now, now
                ))
            
            return self.get_user_by_open_id(open_id)
            
        except sqlite3.IntegrityError:
            # 用户已存在，更新信息
            return self._update_user_info(
                open_id, union_id, user_id, name, en_name,
                avatar_url, avatar_thumb, email, mobile, tenant_key,
                access_token, refresh_token, token_expires_at
            )
    
    def _update_user_info(
        self,
        open_id: str,
        union_id: Optional[str],
        user_id: Optional[str],
        name: str,
        en_name: Optional[str],
        avatar_url: Optional[str],
        avatar_thumb: Optional[str],
        email: Optional[str],
        mobile: Optional[str],
        tenant_key: Optional[str],
        access_token: Optional[str],
        refresh_token: Optional[str],
        token_expires_at: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        """更新已存在用户的信息"""
        now = int(time.time())
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE users SET
                    union_id = COALESCE(?, union_id),
                    user_id = COALESCE(?, user_id),
                    name = ?,
                    en_name = COALESCE(?, en_name),
                    avatar_url = COALESCE(?, avatar_url),
                    avatar_thumb = COALESCE(?, avatar_thumb),
                    email = COALESCE(?, email),
                    mobile = COALESCE(?, mobile),
                    tenant_key = COALESCE(?, tenant_key),
                    access_token = COALESCE(?, access_token),
                    refresh_token = COALESCE(?, refresh_token),
                    token_expires_at = COALESCE(?, token_expires_at),
                    updated_at = ?,
                    last_login_at = ?
                WHERE open_id = ?
            ''', (
                union_id, user_id, name, en_name,
                avatar_url, avatar_thumb, email, mobile, tenant_key,
                access_token, refresh_token, token_expires_at,
                now, now, open_id
            ))
        
        return self.get_user_by_open_id(open_id)
    
    def get_user_by_open_id(self, open_id: str) -> Optional[Dict[str, Any]]:
        """
        根据 open_id 获取用户
        
        Args:
            open_id: 飞书 open_id
            
        Returns:
            用户信息字典，如果不存在则返回 None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM users WHERE open_id = ?",
                (open_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return dict(row)
        
        return None
    
    def get_user_by_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        根据 API Key 获取用户
        
        Args:
            api_key: API Key
            
        Returns:
            用户信息字典，如果不存在或用户已禁用则返回 None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM users WHERE api_key = ? AND is_active = 1",
                (api_key,)
            )
            row = cursor.fetchone()
            
            if row:
                return dict(row)
        
        return None
    
    def regenerate_api_key(self, open_id: str) -> Optional[str]:
        """
        重新生成用户的 API Key
        
        Args:
            open_id: 飞书 open_id
            
        Returns:
            新的 API Key，如果用户不存在则返回 None
        """
        new_api_key = self._generate_api_key()
        now = int(time.time())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE users SET api_key = ?, updated_at = ? WHERE open_id = ?",
                (new_api_key, now, open_id)
            )
            
            if cursor.rowcount > 0:
                return new_api_key
        
        return None
    
    def update_tokens(
        self,
        open_id: str,
        access_token: str,
        refresh_token: str,
        expires_at: int
    ) -> bool:
        """
        更新用户的 OAuth Token
        
        Args:
            open_id: 飞书 open_id
            access_token: 新的 access token
            refresh_token: 新的 refresh token
            expires_at: token 过期时间戳
            
        Returns:
            bool: 是否更新成功
        """
        now = int(time.time())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                UPDATE users SET
                    access_token = ?,
                    refresh_token = ?,
                    token_expires_at = ?,
                    updated_at = ?
                WHERE open_id = ?
            ''', (access_token, refresh_token, expires_at, now, open_id))
            
            return cursor.rowcount > 0
    
    def disable_user(self, open_id: str) -> bool:
        """
        禁用用户
        
        Args:
            open_id: 飞书 open_id
            
        Returns:
            bool: 是否禁用成功
        """
        now = int(time.time())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE users SET is_active = 0, updated_at = ? WHERE open_id = ?",
                (now, open_id)
            )
            
            return cursor.rowcount > 0
    
    def enable_user(self, open_id: str) -> bool:
        """
        启用用户
        
        Args:
            open_id: 飞书 open_id
            
        Returns:
            bool: 是否启用成功
        """
        now = int(time.time())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE users SET is_active = 1, updated_at = ? WHERE open_id = ?",
                (now, open_id)
            )
            
            return cursor.rowcount > 0
    
    def list_users(
        self,
        tenant_key: Optional[str] = None,
        include_disabled: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取用户列表
        
        Args:
            tenant_key: 可选，按租户筛选
            include_disabled: 是否包含已禁用的用户
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            用户列表
        """
        query = "SELECT * FROM users WHERE 1=1"
        params = []
        
        if tenant_key:
            query += " AND tenant_key = ?"
            params.append(tenant_key)
        
        if not include_disabled:
            query += " AND is_active = 1"
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def _generate_api_key(self) -> str:
        """
        生成 API Key
        
        Returns:
            格式: uk_<32位随机字符>
        """
        random_part = secrets.token_hex(16)  # 32字符
        return f"uk_{random_part}"
