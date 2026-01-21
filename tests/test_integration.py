"""
集成测试用例 - 使用浏览器进行端到端测试
测试账号: admin
测试密码: 12345678
"""

import os
import sys
import time
import pytest
import sqlite3
import tempfile

# 添加 src 目录到 Python 路径
SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
sys.path.insert(0, SRC_DIR)

# 设置测试数据库
TEST_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "test_integration.db"
)
os.environ["USERINTENT_DB_PATH"] = TEST_DB_PATH

# 测试凭证
ADMIN_PASSWORD = "12345678"
TEST_FEISHU_APP_ID = "cli_test_integration"
TEST_FEISHU_APP_SECRET = "test_secret_12345"


# ============================================================================
# 集成测试用例清单
# ============================================================================

"""
## 测试场景 1: 系统初始化流程

### TC-INT-001: 首次访问显示初始化页面
- 前置条件: 系统未初始化（数据库为空）
- 操作步骤:
  1. 访问首页 http://localhost:8000/
- 预期结果:
  - 显示初始化设置页面
  - 包含管理员密码输入框
  - 包含飞书配置输入框（可选）

### TC-INT-002: 完成系统初始化
- 前置条件: 系统未初始化
- 操作步骤:
  1. 访问首页
  2. 输入管理员密码: 12345678
  3. 输入飞书 App ID（可选）
  4. 输入飞书 App Secret（可选）
  5. 点击"完成设置"按钮
- 预期结果:
  - 初始化成功
  - 跳转到登录页面或管理后台

## 测试场景 2: 管理员登录流程

### TC-INT-003: 管理员登录成功
- 前置条件: 系统已初始化
- 操作步骤:
  1. 访问管理后台登录页面
  2. 输入密码: 12345678
  3. 点击"登录"按钮
- 预期结果:
  - 登录成功
  - 跳转到管理后台
  - 显示系统配置页面

### TC-INT-004: 管理员登录失败（错误密码）
- 前置条件: 系统已初始化
- 操作步骤:
  1. 访问管理后台登录页面
  2. 输入错误密码
  3. 点击"登录"按钮
- 预期结果:
  - 登录失败
  - 显示错误提示

## 测试场景 3: 管理后台功能

### TC-INT-005: 查看系统状态
- 前置条件: 管理员已登录
- 操作步骤:
  1. 在管理后台查看系统状态
- 预期结果:
  - 显示系统版本
  - 显示飞书连接状态
  - 显示用户数量

### TC-INT-006: 修改飞书配置
- 前置条件: 管理员已登录
- 操作步骤:
  1. 进入系统配置页面
  2. 修改飞书 App ID
  3. 修改飞书 App Secret
  4. 点击"保存配置"按钮
- 预期结果:
  - 配置保存成功
  - 显示成功提示

### TC-INT-007: 修改管理员密码
- 前置条件: 管理员已登录
- 操作步骤:
  1. 进入密码修改区域
  2. 输入旧密码
  3. 输入新密码
  4. 确认新密码
  5. 点击"修改密码"按钮
- 预期结果:
  - 密码修改成功
  - 需要重新登录

## 测试场景 4: 用户登录页面

### TC-INT-008: 显示用户登录页面
- 前置条件: 系统已初始化，已配置飞书
- 操作步骤:
  1. 访问用户登录页面
- 预期结果:
  - 显示"使用飞书登录"按钮
  - 显示"使用 Web UI"选项

### TC-INT-009: 飞书登录跳转
- 前置条件: 系统已配置飞书
- 操作步骤:
  1. 点击"使用飞书登录"按钮
- 预期结果:
  - 跳转到飞书授权页面
  - URL 包含正确的 app_id 和 redirect_uri

## 测试场景 5: API 端点测试

### TC-INT-010: 系统状态 API
- 操作步骤:
  1. GET /api/system/status
- 预期结果:
  - 返回 JSON 格式
  - 包含 initialized 字段

### TC-INT-011: 初始化 API
- 前置条件: 系统未初始化
- 操作步骤:
  1. POST /api/system/initialize
  2. Body: {"admin_password": "12345678"}
- 预期结果:
  - 返回 success: true

### TC-INT-012: 登录 API
- 前置条件: 系统已初始化
- 操作步骤:
  1. POST /api/admin/login
  2. Body: {"password": "12345678"}
- 预期结果:
  - 返回 session_token
"""


class IntegrationTestSuite:
    """集成测试套件配置"""
    
    BASE_URL = "http://localhost:8000"
    ADMIN_PASSWORD = "12345678"
    
    @classmethod
    def setup_clean_db(cls):
        """清理测试数据库"""
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(TEST_DB_PATH), exist_ok=True)
        
        # 重置 OAuth 单例
        import web_multi_tenant
        web_multi_tenant._oauth_instance = None
        web_multi_tenant._oauth_config_hash = None
    
    @classmethod
    def initialize_system(cls):
        """通过 API 初始化系统"""
        import httpx
        
        response = httpx.post(
            f"{cls.BASE_URL}/api/system/initialize",
            json={
                "admin_password": ADMIN_PASSWORD,
                "feishu_app_id": TEST_FEISHU_APP_ID,
                "feishu_app_secret": TEST_FEISHU_APP_SECRET
            }
        )
        return response.json()


# ============================================================================
# 自动化测试用例（使用 pytest）
# ============================================================================

class TestSystemStatusAPI:
    """系统状态 API 测试"""
    
    def test_get_status_uninitialized(self):
        """TC-INT-010: 未初始化时获取系统状态"""
        from fastapi.testclient import TestClient
        from web_multi_tenant import app
        
        # 清理数据库
        IntegrationTestSuite.setup_clean_db()
        
        client = TestClient(app)
        response = client.get("/api/system/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "initialized" in data
        assert data["initialized"] == False


class TestInitializationAPI:
    """初始化 API 测试"""
    
    def test_initialize_system(self):
        """TC-INT-011: 初始化系统"""
        from fastapi.testclient import TestClient
        from web_multi_tenant import app
        
        # 清理数据库
        IntegrationTestSuite.setup_clean_db()
        
        client = TestClient(app)
        response = client.post("/api/system/initialize", json={
            "admin_password": ADMIN_PASSWORD,
            "feishu_app_id": TEST_FEISHU_APP_ID,
            "feishu_app_secret": TEST_FEISHU_APP_SECRET
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    def test_cannot_reinitialize(self):
        """系统已初始化后不能重新初始化"""
        from fastapi.testclient import TestClient
        from web_multi_tenant import app
        
        client = TestClient(app)
        
        # 先初始化
        IntegrationTestSuite.setup_clean_db()
        client.post("/api/system/initialize", json={
            "admin_password": ADMIN_PASSWORD
        })
        
        # 尝试再次初始化
        response = client.post("/api/system/initialize", json={
            "admin_password": "new_password"
        })
        
        assert response.status_code == 400


class TestAdminLoginAPI:
    """管理员登录 API 测试"""
    
    def test_login_success(self):
        """TC-INT-012: 管理员登录成功"""
        from fastapi.testclient import TestClient
        from web_multi_tenant import app
        
        client = TestClient(app)
        
        # 初始化
        IntegrationTestSuite.setup_clean_db()
        client.post("/api/system/initialize", json={
            "admin_password": ADMIN_PASSWORD
        })
        
        # 登录
        response = client.post("/api/admin/login", json={
            "password": ADMIN_PASSWORD
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "session_token" in data
        assert data["success"] == True
    
    def test_login_wrong_password(self):
        """TC-INT-004: 管理员登录失败（错误密码）"""
        from fastapi.testclient import TestClient
        from web_multi_tenant import app
        
        client = TestClient(app)
        
        # 初始化
        IntegrationTestSuite.setup_clean_db()
        client.post("/api/system/initialize", json={
            "admin_password": ADMIN_PASSWORD
        })
        
        # 使用错误密码登录
        response = client.post("/api/admin/login", json={
            "password": "wrong_password"
        })
        
        assert response.status_code == 401


class TestFeishuConfigAPI:
    """飞书配置 API 测试"""
    
    def test_update_feishu_config(self):
        """TC-INT-006: 更新飞书配置"""
        from fastapi.testclient import TestClient
        from web_multi_tenant import app
        
        # 初始化并登录
        IntegrationTestSuite.setup_clean_db()
        
        client = TestClient(app)
        client.post("/api/system/initialize", json={
            "admin_password": ADMIN_PASSWORD
        })
        
        login_response = client.post("/api/admin/login", json={
            "password": ADMIN_PASSWORD
        })
        session_token = login_response.json()["session_token"]
        
        # 更新飞书配置
        response = client.post(
            "/api/admin/feishu/config",
            json={
                "app_id": "new_app_id",
                "app_secret": "new_app_secret"
            },
            headers={"Authorization": f"Bearer {session_token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["success"] == True


class TestOAuthRedirect:
    """OAuth 重定向测试"""
    
    def test_oauth_redirect(self):
        """TC-INT-009: 飞书登录跳转"""
        from fastapi.testclient import TestClient
        from web_multi_tenant import app
        import web_multi_tenant
        
        # 确保使用正确的数据库路径
        os.environ["USERINTENT_DB_PATH"] = TEST_DB_PATH
        web_multi_tenant.DB_PATH = TEST_DB_PATH
        
        client = TestClient(app)
        
        # 初始化（会重置 OAuth 单例）
        IntegrationTestSuite.setup_clean_db()
        client.post("/api/system/initialize", json={
            "admin_password": ADMIN_PASSWORD,
            "feishu_app_id": TEST_FEISHU_APP_ID,
            "feishu_app_secret": TEST_FEISHU_APP_SECRET
        })
        
        # 访问 OAuth 登录
        response = client.get("/auth/feishu/login", follow_redirects=False)
        
        assert response.status_code == 307
        location = response.headers.get("location", "")
        assert "open.feishu.cn" in location
        assert TEST_FEISHU_APP_ID in location


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
