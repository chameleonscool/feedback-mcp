"""
多租户功能测试用例 - TDD 驱动开发
按照 TDD 原则，先编写测试用例，再实现功能代码
"""

import asyncio
import os
import sys
import sqlite3
import tempfile
import time
import pytest
from unittest.mock import Mock, patch, AsyncMock

# 添加 src 目录到 Python 路径
SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
sys.path.insert(0, SRC_DIR)

# 设置测试环境
TEST_DB_PATH = tempfile.mktemp(suffix=".db")
os.environ["USERINTENT_DB_PATH"] = TEST_DB_PATH


# ============================================================================
# 1. 管理员认证测试
# ============================================================================

class TestAdminAuth:
    """管理员认证测试"""
    
    def setup_method(self):
        """每个测试方法前重置数据库"""
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
    
    def test_system_not_initialized(self):
        """测试：系统未初始化时，应返回未初始化状态"""
        from auth import AdminAuth
        auth = AdminAuth(TEST_DB_PATH)
        
        assert auth.is_initialized() == False
    
    def test_initialize_admin_password(self):
        """测试：初始化管理员密码"""
        from auth import AdminAuth
        auth = AdminAuth(TEST_DB_PATH)
        
        # 设置管理员密码
        result = auth.initialize(password="SecurePass123!")
        
        assert result == True
        assert auth.is_initialized() == True
    
    def test_verify_admin_password_correct(self):
        """测试：验证正确的管理员密码"""
        from auth import AdminAuth
        auth = AdminAuth(TEST_DB_PATH)
        auth.initialize(password="SecurePass123!")
        
        # 验证正确密码
        assert auth.verify_password("SecurePass123!") == True
    
    def test_verify_admin_password_incorrect(self):
        """测试：验证错误的管理员密码"""
        from auth import AdminAuth
        auth = AdminAuth(TEST_DB_PATH)
        auth.initialize(password="SecurePass123!")
        
        # 验证错误密码
        assert auth.verify_password("WrongPassword") == False
    
    def test_change_admin_password(self):
        """测试：修改管理员密码"""
        from auth import AdminAuth
        auth = AdminAuth(TEST_DB_PATH)
        auth.initialize(password="OldPass123!")
        
        # 修改密码
        result = auth.change_password(
            old_password="OldPass123!",
            new_password="NewPass456!"
        )
        
        assert result == True
        assert auth.verify_password("NewPass456!") == True
        assert auth.verify_password("OldPass123!") == False
    
    def test_password_validation_min_length(self):
        """测试：密码最小长度验证"""
        from auth import AdminAuth
        auth = AdminAuth(TEST_DB_PATH)
        
        # 短密码应该失败
        with pytest.raises(ValueError, match="至少8个字符"):
            auth.initialize(password="short")
    
    def test_create_admin_session(self):
        """测试：创建管理员会话"""
        from auth import AdminAuth
        auth = AdminAuth(TEST_DB_PATH)
        auth.initialize(password="SecurePass123!")
        
        # 创建会话
        session_token = auth.create_session()
        
        assert session_token is not None
        assert len(session_token) == 64  # SHA256 hex
    
    def test_validate_admin_session(self):
        """测试：验证管理员会话"""
        from auth import AdminAuth
        auth = AdminAuth(TEST_DB_PATH)
        auth.initialize(password="SecurePass123!")
        session_token = auth.create_session()
        
        # 验证有效会话
        assert auth.validate_session(session_token) == True
        
        # 验证无效会话
        assert auth.validate_session("invalid_token") == False


# ============================================================================
# 2. 飞书 OAuth 登录测试
# ============================================================================

class TestFeishuOAuth:
    """飞书 OAuth 登录测试"""
    
    def setup_method(self):
        """每个测试方法前重置数据库"""
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
    
    def test_generate_oauth_url(self):
        """测试：生成飞书 OAuth 授权 URL"""
        from oauth import FeishuOAuth
        
        oauth = FeishuOAuth(
            app_id="cli_test123",
            app_secret="test_secret",
            redirect_uri="http://localhost:8080/auth/callback"
        )
        
        url, state = oauth.get_authorize_url()
        
        assert "open.feishu.cn" in url
        assert "cli_test123" in url
        assert state is not None
        assert len(state) == 32
    
    def test_validate_oauth_state(self):
        """测试：验证 OAuth state 参数（防止 CSRF）"""
        from oauth import FeishuOAuth
        
        oauth = FeishuOAuth(
            app_id="cli_test123",
            app_secret="test_secret",
            redirect_uri="http://localhost:8080/auth/callback"
        )
        
        _, state = oauth.get_authorize_url()
        
        # 验证正确的 state
        assert oauth.validate_state(state) == True
        
        # 验证错误的 state
        assert oauth.validate_state("wrong_state") == False
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_token(self):
        """测试：用授权码换取 access token"""
        from oauth import FeishuOAuth
        
        oauth = FeishuOAuth(
            app_id="cli_test123",
            app_secret="test_secret",
            redirect_uri="http://localhost:8080/auth/callback"
        )
        
        # Mock HTTP 响应
        mock_response = {
            "code": 0,
            "data": {
                "access_token": "u-test_access_token",
                "refresh_token": "ur-test_refresh_token",
                "token_type": "Bearer",
                "expires_in": 7200,
                "refresh_expires_in": 2592000
            }
        }
        
        with patch.object(oauth, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            token_data = await oauth.exchange_code("test_auth_code")
            
            assert token_data["access_token"] == "u-test_access_token"
            assert token_data["refresh_token"] == "ur-test_refresh_token"
    
    @pytest.mark.asyncio
    async def test_get_user_info(self):
        """测试：获取用户信息"""
        from oauth import FeishuOAuth
        
        oauth = FeishuOAuth(
            app_id="cli_test123",
            app_secret="test_secret",
            redirect_uri="http://localhost:8080/auth/callback"
        )
        
        # Mock 用户信息响应
        mock_response = {
            "code": 0,
            "data": {
                "open_id": "ou_test_open_id_123",
                "union_id": "on_test_union_id_456",
                "user_id": "test_user_id",
                "name": "测试用户",
                "en_name": "Test User",
                "avatar_url": "https://example.com/avatar.png",
                "avatar_thumb": "https://example.com/avatar_thumb.png",
                "email": "test@example.com",
                "mobile": "+86138xxxxxxxx",
                "tenant_key": "tenant_key_123"
            }
        }
        
        with patch.object(oauth, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            user_info = await oauth.get_user_info("u-test_access_token")
            
            assert user_info["open_id"] == "ou_test_open_id_123"
            assert user_info["name"] == "测试用户"
            assert user_info["tenant_key"] == "tenant_key_123"


# ============================================================================
# 3. 用户数据表测试
# ============================================================================

class TestUserManagement:
    """用户数据管理测试"""
    
    def setup_method(self):
        """每个测试方法前重置数据库"""
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
    
    def test_create_user(self):
        """测试：创建用户"""
        from users import UserManager
        
        manager = UserManager(TEST_DB_PATH)
        
        user = manager.create_user(
            open_id="ou_test_open_id",
            union_id="on_test_union_id",
            name="张三",
            avatar_url="https://example.com/avatar.png",
            tenant_key="tenant_123"
        )
        
        assert user is not None
        assert user["open_id"] == "ou_test_open_id"
        assert user["name"] == "张三"
        assert user["api_key"] is not None
        assert user["api_key"].startswith("uk_")
    
    def test_get_user_by_open_id(self):
        """测试：根据 open_id 获取用户"""
        from users import UserManager
        
        manager = UserManager(TEST_DB_PATH)
        manager.create_user(
            open_id="ou_test_open_id",
            union_id="on_test_union_id",
            name="张三"
        )
        
        user = manager.get_user_by_open_id("ou_test_open_id")
        
        assert user is not None
        assert user["name"] == "张三"
    
    def test_get_user_by_api_key(self):
        """测试：根据 API Key 获取用户"""
        from users import UserManager
        
        manager = UserManager(TEST_DB_PATH)
        created_user = manager.create_user(
            open_id="ou_test_open_id",
            union_id="on_test_union_id",
            name="张三"
        )
        api_key = created_user["api_key"]
        
        user = manager.get_user_by_api_key(api_key)
        
        assert user is not None
        assert user["open_id"] == "ou_test_open_id"
    
    def test_regenerate_api_key(self):
        """测试：重新生成 API Key"""
        from users import UserManager
        
        manager = UserManager(TEST_DB_PATH)
        user = manager.create_user(
            open_id="ou_test_open_id",
            union_id="on_test_union_id",
            name="张三"
        )
        old_api_key = user["api_key"]
        
        new_api_key = manager.regenerate_api_key("ou_test_open_id")
        
        assert new_api_key != old_api_key
        assert new_api_key.startswith("uk_")
        
        # 旧 Key 应该失效
        assert manager.get_user_by_api_key(old_api_key) is None
        
        # 新 Key 应该有效
        assert manager.get_user_by_api_key(new_api_key) is not None
    
    def test_update_user_tokens(self):
        """测试：更新用户的 OAuth Token"""
        from users import UserManager
        
        manager = UserManager(TEST_DB_PATH)
        manager.create_user(
            open_id="ou_test_open_id",
            union_id="on_test_union_id",
            name="张三"
        )
        
        result = manager.update_tokens(
            open_id="ou_test_open_id",
            access_token="new_access_token",
            refresh_token="new_refresh_token",
            expires_at=int(time.time()) + 7200
        )
        
        assert result == True
        
        user = manager.get_user_by_open_id("ou_test_open_id")
        assert user["access_token"] == "new_access_token"
    
    def test_disable_user(self):
        """测试：禁用用户"""
        from users import UserManager
        
        manager = UserManager(TEST_DB_PATH)
        user = manager.create_user(
            open_id="ou_test_open_id",
            union_id="on_test_union_id",
            name="张三"
        )
        api_key = user["api_key"]
        
        result = manager.disable_user("ou_test_open_id")
        
        assert result == True
        
        # 禁用后 API Key 应该失效
        assert manager.get_user_by_api_key(api_key) is None
    
    def test_list_users(self):
        """测试：获取用户列表"""
        from users import UserManager
        
        manager = UserManager(TEST_DB_PATH)
        manager.create_user(open_id="ou_1", union_id="on_1", name="用户1")
        manager.create_user(open_id="ou_2", union_id="on_2", name="用户2")
        manager.create_user(open_id="ou_3", union_id="on_3", name="用户3")
        
        users = manager.list_users()
        
        assert len(users) == 3


# ============================================================================
# 4. API Key 认证测试
# ============================================================================

class TestApiKeyAuth:
    """API Key 认证测试"""
    
    def setup_method(self):
        """每个测试方法前重置数据库"""
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
    
    def test_api_key_format(self):
        """测试：API Key 格式正确"""
        from users import UserManager
        
        manager = UserManager(TEST_DB_PATH)
        user = manager.create_user(
            open_id="ou_test",
            union_id="on_test",
            name="测试"
        )
        api_key = user["api_key"]
        
        # API Key 格式: uk_<32位随机字符>
        assert api_key.startswith("uk_")
        assert len(api_key) == 35  # "uk_" + 32 characters
    
    def test_environment_api_key_auth(self):
        """测试：通过环境变量中的 API Key 认证用户"""
        from users import UserManager
        from auth import get_current_user_from_env
        
        manager = UserManager(TEST_DB_PATH)
        user = manager.create_user(
            open_id="ou_env_test",
            union_id="on_env_test",
            name="环境变量测试用户"
        )
        api_key = user["api_key"]
        
        # 模拟环境变量
        with patch.dict(os.environ, {"USERINTENT_API_KEY": api_key}):
            current_user = get_current_user_from_env(TEST_DB_PATH)
            
            assert current_user is not None
            assert current_user["open_id"] == "ou_env_test"
    
    def test_no_api_key_returns_none(self):
        """测试：无 API Key 时返回 None（降级到 Web UI 模式）"""
        from auth import get_current_user_from_env
        
        # 确保环境变量未设置
        if "USERINTENT_API_KEY" in os.environ:
            del os.environ["USERINTENT_API_KEY"]
        
        current_user = get_current_user_from_env(TEST_DB_PATH)
        
        assert current_user is None


# ============================================================================
# 5. 消息路由测试
# ============================================================================

class TestMessageRouting:
    """消息路由测试"""
    
    def setup_method(self):
        """每个测试方法前重置数据库"""
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
    
    @pytest.mark.asyncio
    async def test_route_message_to_user_feishu(self):
        """测试：根据用户的 open_id 路由消息到飞书"""
        from users import UserManager
        from routing import MessageRouter
        
        manager = UserManager(TEST_DB_PATH)
        manager.create_user(
            open_id="ou_target_user",
            union_id="on_target_user",
            name="目标用户"
        )
        
        router = MessageRouter(TEST_DB_PATH)
        
        # Mock Feishu 发送
        with patch.object(router, '_send_feishu_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True
            
            result = await router.send_to_user(
                open_id="ou_target_user",
                message="Hello, this is a test message",
                request_id="req_123"
            )
            
            assert result == True
            mock_send.assert_called_once_with(
                "ou_target_user",
                "Hello, this is a test message",
                "req_123"
            )
    
    @pytest.mark.asyncio
    async def test_route_message_by_api_key(self):
        """测试：根据 API Key 自动识别用户并路由消息"""
        from users import UserManager
        from routing import MessageRouter
        
        manager = UserManager(TEST_DB_PATH)
        user = manager.create_user(
            open_id="ou_api_user",
            union_id="on_api_user",
            name="API用户"
        )
        api_key = user["api_key"]
        
        router = MessageRouter(TEST_DB_PATH)
        
        # Mock Feishu 发送
        with patch.object(router, '_send_feishu_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True
            
            result = await router.send_by_api_key(
                api_key=api_key,
                message="Message via API Key",
                request_id="req_456"
            )
            
            assert result == True
            mock_send.assert_called_once_with(
                "ou_api_user",
                "Message via API Key",
                "req_456"
            )
    
    @pytest.mark.asyncio
    async def test_receive_reply_and_route_back(self):
        """测试：接收用户回复并路由回对应的请求"""
        from users import UserManager
        from routing import MessageRouter
        
        manager = UserManager(TEST_DB_PATH)
        manager.create_user(
            open_id="ou_reply_user",
            union_id="on_reply_user",
            name="回复用户"
        )
        
        router = MessageRouter(TEST_DB_PATH)
        
        # 创建一个待处理的请求
        router.create_pending_request(
            request_id="req_789",
            open_id="ou_reply_user",
            question="你好，这是一个测试问题"
        )
        
        # 模拟接收回复
        result = await router.receive_reply(
            open_id="ou_reply_user",
            reply_text="这是我的回复"
        )
        
        assert result["request_id"] == "req_789"
        assert result["matched"] == True
    
    def test_intent_queue_with_user_id(self):
        """测试：intent_queue 表支持用户 ID"""
        from routing import MessageRouter
        
        router = MessageRouter(TEST_DB_PATH)
        
        # 创建带用户 ID 的请求
        router.create_pending_request(
            request_id="req_multi_001",
            open_id="ou_user_1",
            question="用户1的问题"
        )
        router.create_pending_request(
            request_id="req_multi_002",
            open_id="ou_user_2",
            question="用户2的问题"
        )
        
        # 获取特定用户的待处理请求
        user1_requests = router.get_pending_requests("ou_user_1")
        user2_requests = router.get_pending_requests("ou_user_2")
        
        assert len(user1_requests) == 1
        assert user1_requests[0]["request_id"] == "req_multi_001"
        
        assert len(user2_requests) == 1
        assert user2_requests[0]["request_id"] == "req_multi_002"


# ============================================================================
# 6. Web API 端点测试
# ============================================================================

class TestWebAPI:
    """Web API 端点测试"""
    
    def setup_method(self):
        """每个测试方法前重置数据库"""
        # 删除测试数据库
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        
        # 也删除 web 模块使用的数据库
        from web_multi_tenant import DB_PATH
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
    
    def test_system_status_not_initialized(self):
        """测试：系统状态 API - 未初始化"""
        from fastapi.testclient import TestClient
        from web_multi_tenant import app
        
        client = TestClient(app)
        response = client.get("/api/system/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["initialized"] == False
    
    def test_initialize_system(self):
        """测试：初始化系统 API"""
        from fastapi.testclient import TestClient
        from web_multi_tenant import app
        
        client = TestClient(app)
        response = client.post("/api/system/initialize", json={
            "admin_password": "SecurePass123!",
            "feishu_app_id": "cli_test_app",
            "feishu_app_secret": "test_secret"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    def test_admin_login(self):
        """测试：管理员登录 API"""
        from fastapi.testclient import TestClient
        from web_multi_tenant import app
        
        client = TestClient(app)
        
        # 先初始化
        client.post("/api/system/initialize", json={
            "admin_password": "SecurePass123!"
        })
        
        # 登录
        response = client.post("/api/admin/login", json={
            "password": "SecurePass123!"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "session_token" in data
    
    def test_oauth_redirect(self):
        """测试：OAuth 重定向 API"""
        from fastapi.testclient import TestClient
        from web_multi_tenant import app
        
        client = TestClient(app)
        
        # 初始化系统
        client.post("/api/system/initialize", json={
            "admin_password": "SecurePass123!",
            "feishu_app_id": "cli_test_app",
            "feishu_app_secret": "test_secret"
        })
        
        response = client.get("/auth/feishu/login", follow_redirects=False)
        
        assert response.status_code == 307  # Temporary Redirect
        assert "open.feishu.cn" in response.headers["location"]
    
    def test_user_profile_api(self):
        """测试：用户信息 API"""
        from fastapi.testclient import TestClient
        from web_multi_tenant import app, DB_PATH
        from users import UserManager
        
        # 先清理并初始化
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        client = TestClient(app)
        
        # 先初始化系统
        client.post("/api/system/initialize", json={
            "admin_password": "12345678"
        })
        
        # 创建测试用户 - 使用与 web 模块相同的 DB_PATH
        manager = UserManager(DB_PATH)
        user = manager.create_user(
            open_id="ou_profile_test",
            union_id="on_profile_test",
            name="个人信息测试"
        )
        api_key = user["api_key"]
        
        # 使用 API Key 访问用户信息
        response = client.get(
            "/api/user/profile",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "个人信息测试"
        assert data["api_key"] == api_key


# ============================================================================
# 清理
# ============================================================================

def teardown_module():
    """测试结束后清理测试数据库"""
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
