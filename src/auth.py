"""
认证模块 - 管理员认证和会话管理
"""

import os
import sqlite3
import hashlib
import secrets
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class AdminSession:
    """管理员会话"""
    token: str
    created_at: float
    expires_at: float


class AdminAuth:
    """管理员认证管理器"""
    
    # 会话有效期：24小时
    SESSION_EXPIRY = 24 * 60 * 60
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS admin_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            ''')
            # 会话表 - 持久化存储
            conn.execute('''
                CREATE TABLE IF NOT EXISTS admin_sessions (
                    token TEXT PRIMARY KEY,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL
                )
            ''')
    
    def is_initialized(self) -> bool:
        """检查系统是否已初始化（已设置管理员密码）"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT value FROM admin_config WHERE key = 'password_hash'"
            )
            row = cursor.fetchone()
            return row is not None
    
    def initialize(self, username: str = "admin", password: str = "") -> bool:
        """
        初始化系统，设置管理员用户名和密码
        
        Args:
            username: 管理员用户名（默认 admin）
            password: 管理员密码
            
        Returns:
            bool: 是否初始化成功
            
        Raises:
            ValueError: 密码或用户名不符合要求
        """
        # 验证用户名
        if not username or len(username) < 3:
            raise ValueError("用户名至少3个字符")
        
        # 验证密码强度
        self._validate_password(password)
        
        # 生成密码哈希
        password_hash = self._hash_password(password)
        
        with sqlite3.connect(self.db_path) as conn:
            # 检查是否已初始化
            cursor = conn.execute(
                "SELECT value FROM admin_config WHERE key = 'password_hash'"
            )
            if cursor.fetchone():
                return False  # 已初始化
            
            # 存储用户名
            conn.execute(
                "INSERT INTO admin_config (key, value) VALUES (?, ?)",
                ("admin_username", username)
            )
            
            # 存储密码哈希
            conn.execute(
                "INSERT INTO admin_config (key, value) VALUES (?, ?)",
                ("password_hash", password_hash)
            )
            
            # 记录初始化时间
            conn.execute(
                "INSERT OR REPLACE INTO admin_config (key, value) VALUES (?, ?)",
                ("initialized_at", str(int(time.time())))
            )
        
        return True
    
    def get_admin_username(self) -> str:
        """获取管理员用户名"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT value FROM admin_config WHERE key = 'admin_username'"
            )
            row = cursor.fetchone()
            return row[0] if row else "admin"
    
    def verify_credentials(self, username: str, password: str) -> bool:
        """
        验证管理员用户名和密码
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            bool: 凭证是否正确
        """
        with sqlite3.connect(self.db_path) as conn:
            # 验证用户名
            cursor = conn.execute(
                "SELECT value FROM admin_config WHERE key = 'admin_username'"
            )
            row = cursor.fetchone()
            stored_username = row[0] if row else "admin"
            
            if username != stored_username:
                return False
            
            # 验证密码
            cursor = conn.execute(
                "SELECT value FROM admin_config WHERE key = 'password_hash'"
            )
            row = cursor.fetchone()
            
            if not row:
                return False
            
            stored_hash = row[0]
            return self._verify_hash(password, stored_hash)
    
    def verify_password(self, password: str) -> bool:
        """
        验证管理员密码（向后兼容）
        
        Args:
            password: 待验证的密码
            
        Returns:
            bool: 密码是否正确
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT value FROM admin_config WHERE key = 'password_hash'"
            )
            row = cursor.fetchone()
            
            if not row:
                return False
            
            stored_hash = row[0]
            return self._verify_hash(password, stored_hash)
    
    def change_password(self, old_password: str, new_password: str) -> bool:
        """
        修改管理员密码
        
        Args:
            old_password: 旧密码
            new_password: 新密码
            
        Returns:
            bool: 是否修改成功
            
        Raises:
            ValueError: 新密码不符合要求
        """
        # 验证旧密码
        if not self.verify_password(old_password):
            return False
        
        # 验证新密码强度
        self._validate_password(new_password)
        
        # 更新密码
        new_hash = self._hash_password(new_password)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE admin_config SET value = ? WHERE key = 'password_hash'",
                (new_hash,)
            )
        
        return True
    
    def create_session(self) -> str:
        """
        创建管理员会话
        
        Returns:
            str: 会话令牌
        """
        token = secrets.token_hex(32)  # 64字符
        now = time.time()
        expires_at = now + self.SESSION_EXPIRY
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO admin_sessions (token, created_at, expires_at) VALUES (?, ?, ?)",
                (token, now, expires_at)
            )
        
        self._cleanup_expired_sessions()
        
        return token
    
    def validate_session(self, token: str) -> bool:
        """
        验证会话是否有效
        
        Args:
            token: 会话令牌
            
        Returns:
            bool: 会话是否有效
        """
        now = time.time()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT expires_at FROM admin_sessions WHERE token = ?",
                (token,)
            )
            row = cursor.fetchone()
            
            if not row:
                return False
            
            expires_at = row[0]
            
            if now > expires_at:
                conn.execute("DELETE FROM admin_sessions WHERE token = ?", (token,))
                return False
            
            return True
    
    def invalidate_session(self, token: str):
        """
        使会话失效
        
        Args:
            token: 会话令牌
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM admin_sessions WHERE token = ?", (token,))
    
    def _validate_password(self, password: str):
        """
        验证密码强度
        
        Args:
            password: 待验证的密码
            
        Raises:
            ValueError: 密码不符合要求
        """
        if len(password) < 8:
            raise ValueError("密码至少8个字符")
    
    def _hash_password(self, password: str) -> str:
        """
        生成密码哈希
        
        Args:
            password: 原始密码
            
        Returns:
            str: 密码哈希（salt:hash 格式）
        """
        salt = secrets.token_hex(16)
        hash_value = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        return f"{salt}:{hash_value}"
    
    def _verify_hash(self, password: str, stored_hash: str) -> bool:
        """
        验证密码与哈希是否匹配
        
        Args:
            password: 待验证的密码
            stored_hash: 存储的哈希
            
        Returns:
            bool: 是否匹配
        """
        try:
            salt, hash_value = stored_hash.split(':')
            computed_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            ).hex()
            return secrets.compare_digest(hash_value, computed_hash)
        except (ValueError, AttributeError):
            return False
    
    def _cleanup_expired_sessions(self):
        """清理过期会话"""
        now = time.time()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM admin_sessions WHERE expires_at < ?",
                (now,)
            )


def get_current_user_from_env(db_path: str) -> Optional[Dict[str, Any]]:
    """
    从环境变量中的 API Key 获取当前用户
    
    Args:
        db_path: 数据库路径
        
    Returns:
        用户信息字典，如果未配置 API Key 则返回 None
    """
    api_key = os.getenv("USERINTENT_API_KEY")
    
    if not api_key:
        return None
    
    # 延迟导入避免循环依赖
    from users import UserManager
    
    manager = UserManager(db_path)
    return manager.get_user_by_api_key(api_key)
