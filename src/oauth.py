"""
飞书 OAuth 模块 - 处理 OAuth 2.0 授权流程
"""

import secrets
import time
import urllib.parse
from typing import Optional, Dict, Any, Tuple


class FeishuOAuth:
    """飞书 OAuth 2.0 认证"""
    
    # 飞书 OAuth 端点
    AUTHORIZE_URL = "https://open.feishu.cn/open-apis/authen/v1/authorize"
    TOKEN_URL = "https://open.feishu.cn/open-apis/authen/v1/oidc/access_token"
    USER_INFO_URL = "https://open.feishu.cn/open-apis/authen/v1/user_info"
    REFRESH_TOKEN_URL = "https://open.feishu.cn/open-apis/authen/v1/oidc/refresh_access_token"
    APP_ACCESS_TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"
    
    # State 有效期：10分钟
    STATE_EXPIRY = 10 * 60
    
    def __init__(
        self,
        app_id: str,
        app_secret: str,
        redirect_uri: str
    ):
        """
        初始化飞书 OAuth
        
        Args:
            app_id: 飞书应用 App ID
            app_secret: 飞书应用 App Secret
            redirect_uri: OAuth 回调地址
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.redirect_uri = redirect_uri
        
        # 存储有效的 state（用于防止 CSRF）
        self._valid_states: Dict[str, float] = {}
        
        # 缓存 app_access_token
        self._app_access_token: Optional[str] = None
        self._app_token_expires_at: float = 0
    
    def get_authorize_url(self, scope: str = "contact:user.base:readonly") -> Tuple[str, str]:
        """
        生成飞书 OAuth 授权 URL
        
        Args:
            scope: 权限范围，默认读取用户基本信息
            
        Returns:
            Tuple[str, str]: (授权 URL, state 参数)
        """
        state = self._generate_state()
        
        params = {
            "app_id": self.app_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "state": state,
            "scope": scope
        }
        
        url = f"{self.AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"
        
        return url, state
    
    def validate_state(self, state: str) -> bool:
        """
        验证 OAuth state 参数（防止 CSRF 攻击）
        
        Args:
            state: 待验证的 state 参数
            
        Returns:
            bool: state 是否有效
        """
        self._cleanup_expired_states()
        
        if state not in self._valid_states:
            return False
        
        # 验证后删除，防止重放攻击
        del self._valid_states[state]
        return True
    
    async def get_app_access_token(self) -> str:
        """
        获取应用访问令牌（app_access_token）
        
        Returns:
            str: app_access_token
        """
        # 检查缓存
        if self._app_access_token and time.time() < self._app_token_expires_at:
            return self._app_access_token
        
        response = await self._request(
            "POST",
            self.APP_ACCESS_TOKEN_URL,
            json={
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }
        )
        
        if response.get("code") != 0:
            raise OAuthError(
                f"获取 app_access_token 失败: {response.get('msg')}"
            )
        
        self._app_access_token = response.get("app_access_token")
        # 提前5分钟过期
        self._app_token_expires_at = time.time() + response.get("expire", 7200) - 300
        
        return self._app_access_token
    
    async def exchange_code(self, code: str) -> Dict[str, Any]:
        """
        用授权码换取用户访问令牌
        
        Args:
            code: 授权码
            
        Returns:
            Dict: 包含 access_token, refresh_token 等的字典
        """
        app_token = await self.get_app_access_token()
        
        response = await self._request(
            "POST",
            self.TOKEN_URL,
            headers={"Authorization": f"Bearer {app_token}"},
            json={
                "grant_type": "authorization_code",
                "code": code
            }
        )
        
        if response.get("code") != 0:
            raise OAuthError(
                f"换取 access_token 失败: {response.get('msg')}"
            )
        
        return response.get("data", {})
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        刷新用户访问令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            Dict: 包含新的 access_token, refresh_token 等的字典
        """
        app_token = await self.get_app_access_token()
        
        response = await self._request(
            "POST",
            self.REFRESH_TOKEN_URL,
            headers={"Authorization": f"Bearer {app_token}"},
            json={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }
        )
        
        if response.get("code") != 0:
            raise OAuthError(
                f"刷新 access_token 失败: {response.get('msg')}"
            )
        
        return response.get("data", {})
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        获取用户信息
        
        Args:
            access_token: 用户访问令牌
            
        Returns:
            Dict: 用户信息
        """
        response = await self._request(
            "GET",
            self.USER_INFO_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.get("code") != 0:
            raise OAuthError(
                f"获取用户信息失败: {response.get('msg')}"
            )
        
        return response.get("data", {})
    
    async def _request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        发送 HTTP 请求
        
        Args:
            method: HTTP 方法
            url: 请求 URL
            headers: 请求头
            json: JSON 请求体
            
        Returns:
            Dict: 响应 JSON
        """
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=json,
                timeout=30
            )
            
            return response.json()
    
    def _generate_state(self) -> str:
        """
        生成 OAuth state 参数
        
        Returns:
            str: 32字符的随机字符串
        """
        state = secrets.token_hex(16)
        self._valid_states[state] = time.time() + self.STATE_EXPIRY
        
        self._cleanup_expired_states()
        
        return state
    
    def _cleanup_expired_states(self):
        """清理过期的 state"""
        now = time.time()
        expired = [
            state for state, expires_at in self._valid_states.items()
            if now > expires_at
        ]
        for state in expired:
            del self._valid_states[state]


class OAuthError(Exception):
    """OAuth 相关错误"""
    pass
