"""
多租户 Web API 模块 - FastAPI 应用
"""

import os
import time
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Header, Request, Query
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 数据库路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
TEMPLATES_DIR = os.path.join(SRC_DIR, "templates")
DB_PATH = os.getenv("USERINTENT_DB_PATH", os.path.join(DATA_DIR, "intent.db"))

# 确保数据目录存在
os.makedirs(DATA_DIR, exist_ok=True)

# 创建 FastAPI 应用
app = FastAPI(
    title="User Intent MCP - Multi-Tenant",
    description="AI 意图收集系统 - 支持多租户",
    version="2.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 飞书服务实例（全局）
_feishu_service = None

def get_feishu_service():
    """获取飞书服务实例"""
    global _feishu_service
    if _feishu_service is None:
        from feishu import FeishuService
        _feishu_service = FeishuService()
    return _feishu_service

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化飞书服务和 WebSocket 监听器"""
    import logging
    logger = logging.getLogger("user_intent_mcp")
    
    # 初始化数据库表
    init_intent_db()
    
    # 初始化飞书服务（用于发送消息）
    fs = get_feishu_service()
    logger.info(f"Feishu service initialized: available={fs.is_available()}, app_id={fs.config.app_id[:8] if fs.config.app_id else 'N/A'}...")
    
    # 启动 WebSocket 监听器子进程（用于接收消息）
    from feishu_ws_listener import get_ws_manager, LARK_AVAILABLE
    
    if not LARK_AVAILABLE:
        logger.warning("lark_oapi not installed, Feishu WebSocket listener will not be available")
    else:
        ws_manager = get_ws_manager(DB_PATH)
        
        if ws_manager.start():
            logger.info(f"Feishu WebSocket listener started in subprocess (PID: {ws_manager._process.pid})")
        else:
            logger.info("Feishu WebSocket listener not started (credentials may not be configured)")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    import logging
    logger = logging.getLogger("user_intent_mcp")
    
    # 停止 WebSocket 监听器子进程
    try:
        from feishu_ws_listener import get_ws_manager, LARK_AVAILABLE
        if LARK_AVAILABLE:
            ws_manager = get_ws_manager(DB_PATH)
            ws_manager.stop()
            logger.info("Feishu WebSocket listener stopped")
    except Exception as e:
        logger.error(f"Error stopping WebSocket listener: {e}")


# ============================================================================
# Pydantic 模型
# ============================================================================

class SystemInitRequest(BaseModel):
    """系统初始化请求"""
    admin_username: str = "admin"
    admin_password: str
    feishu_app_id: Optional[str] = None
    feishu_app_secret: Optional[str] = None


class AdminLoginRequest(BaseModel):
    """管理员登录请求"""
    username: str = "admin"
    password: str


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str


class FeishuConfigRequest(BaseModel):
    """飞书配置请求"""
    app_id: str
    app_secret: str
    redirect_uri: Optional[str] = None


# ============================================================================
# 依赖项
# ============================================================================

def get_admin_auth():
    """获取管理员认证实例"""
    from auth import AdminAuth
    return AdminAuth(DB_PATH)


def get_user_manager():
    """获取用户管理器实例"""
    from users import UserManager
    return UserManager(DB_PATH)


# OAuth 单例缓存
_oauth_instance = None
_oauth_config_hash = None


def get_oauth():
    """获取 OAuth 实例（单例模式）"""
    global _oauth_instance, _oauth_config_hash
    from oauth import FeishuOAuth
    
    # 从数据库获取飞书配置
    import sqlite3
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "SELECT value FROM admin_config WHERE key = 'feishu_app_id'"
        )
        row = cursor.fetchone()
        app_id = row[0] if row else None
        
        cursor = conn.execute(
            "SELECT value FROM admin_config WHERE key = 'feishu_app_secret'"
        )
        row = cursor.fetchone()
        app_secret = row[0] if row else None
        
        cursor = conn.execute(
            "SELECT value FROM admin_config WHERE key = 'feishu_redirect_uri'"
        )
        row = cursor.fetchone()
        redirect_uri = row[0] if row else "http://localhost:8000/auth/feishu/callback"
    
    if not app_id or not app_secret:
        return None
    
    # 计算配置哈希，如果配置变化则重新创建实例
    config_hash = f"{app_id}:{app_secret}:{redirect_uri}"
    
    if _oauth_instance is None or _oauth_config_hash != config_hash:
        _oauth_instance = FeishuOAuth(app_id, app_secret, redirect_uri)
        _oauth_config_hash = config_hash
    
    return _oauth_instance


async def verify_admin_session(
    authorization: Optional[str] = Header(None)
) -> bool:
    """验证管理员会话"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未授权")
    
    token = authorization[7:]
    auth = get_admin_auth()
    
    if not auth.validate_session(token):
        raise HTTPException(status_code=401, detail="会话已过期")
    
    return True


async def get_current_user(
    authorization: Optional[str] = Header(None)
):
    """获取当前用户"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未授权")
    
    api_key = authorization[7:]
    manager = get_user_manager()
    user = manager.get_user_by_api_key(api_key)
    
    if not user:
        raise HTTPException(status_code=401, detail="无效的 API Key")
    
    return user


# ============================================================================
# 系统 API
# ============================================================================

@app.get("/api/system/status")
async def get_system_status():
    """获取系统状态"""
    auth = get_admin_auth()
    
    result = {
        "initialized": auth.is_initialized(),
        "version": "2.0.0"
    }
    
    if auth.is_initialized():
        result["admin_username"] = auth.get_admin_username()
    
    return result


@app.post("/api/system/initialize")
async def initialize_system(request: SystemInitRequest):
    """初始化系统"""
    auth = get_admin_auth()
    
    if auth.is_initialized():
        raise HTTPException(status_code=400, detail="系统已初始化")
    
    try:
        # 设置管理员用户名和密码
        auth.initialize(username=request.admin_username, password=request.admin_password)
        
        # 保存飞书配置（如果提供）
        if request.feishu_app_id and request.feishu_app_secret:
            import sqlite3
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO admin_config (key, value) VALUES (?, ?)",
                    ("feishu_app_id", request.feishu_app_id)
                )
                conn.execute(
                    "INSERT OR REPLACE INTO admin_config (key, value) VALUES (?, ?)",
                    ("feishu_app_secret", request.feishu_app_secret)
                )
        
        return {"success": True, "message": "系统初始化成功"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# 管理员 API
# ============================================================================

@app.post("/api/admin/login")
async def admin_login(request: AdminLoginRequest):
    """管理员登录"""
    auth = get_admin_auth()
    
    if not auth.is_initialized():
        raise HTTPException(status_code=400, detail="系统未初始化")
    
    if not auth.verify_credentials(request.username, request.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    session_token = auth.create_session()
    
    return {
        "success": True,
        "session_token": session_token,
        "username": request.username
    }


@app.post("/api/admin/logout")
async def admin_logout(
    authorization: Optional[str] = Header(None)
):
    """管理员登出"""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        auth = get_admin_auth()
        auth.invalidate_session(token)
    
    return {"success": True}


@app.post("/api/admin/change-password")
async def change_admin_password(
    request: ChangePasswordRequest,
    _: bool = Depends(verify_admin_session)
):
    """修改管理员密码"""
    auth = get_admin_auth()
    
    try:
        if not auth.change_password(request.old_password, request.new_password):
            raise HTTPException(status_code=400, detail="旧密码错误")
        
        return {"success": True, "message": "密码修改成功"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/admin/users")
async def list_users(
    _: bool = Depends(verify_admin_session)
):
    """获取用户列表"""
    manager = get_user_manager()
    users = manager.list_users(include_disabled=True)
    
    # 脱敏处理
    for user in users:
        if user.get("api_key"):
            user["api_key"] = user["api_key"][:8] + "..."
        if user.get("access_token"):
            user["access_token"] = "***"
        if user.get("refresh_token"):
            user["refresh_token"] = "***"
    
    return {"users": users}


@app.post("/api/admin/users/{open_id}/disable")
async def disable_user(
    open_id: str,
    _: bool = Depends(verify_admin_session)
):
    """禁用用户"""
    manager = get_user_manager()
    
    if not manager.disable_user(open_id):
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {"success": True}


@app.post("/api/admin/users/{open_id}/enable")
async def enable_user(
    open_id: str,
    _: bool = Depends(verify_admin_session)
):
    """启用用户"""
    manager = get_user_manager()
    
    if not manager.enable_user(open_id):
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {"success": True}


@app.get("/api/admin/feishu/config")
async def get_feishu_config(
    _: bool = Depends(verify_admin_session)
):
    """获取飞书配置（管理员）"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "SELECT key, value FROM admin_config WHERE key LIKE 'feishu_%'"
        )
        config = {}
        for key, value in cursor.fetchall():
            # 移除 feishu_ 前缀
            config_key = key.replace("feishu_", "")
            # 不返回 app_secret 的完整值，只返回是否已配置
            if config_key == "app_secret":
                config["app_secret_configured"] = bool(value)
            else:
                config[config_key] = value
        
        return config


@app.post("/api/admin/feishu/config")
async def update_feishu_config(
    request: FeishuConfigRequest,
    _: bool = Depends(verify_admin_session)
):
    """更新飞书配置
    
    保存配置后会自动重启 WebSocket 监听器以应用新配置。
    """
    import logging
    logger = logging.getLogger("user_intent_mcp")
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO admin_config (key, value) VALUES (?, ?)",
            ("feishu_app_id", request.app_id)
        )
        conn.execute(
            "INSERT OR REPLACE INTO admin_config (key, value) VALUES (?, ?)",
            ("feishu_app_secret", request.app_secret)
        )
        if request.redirect_uri:
            conn.execute(
                "INSERT OR REPLACE INTO admin_config (key, value) VALUES (?, ?)",
                ("feishu_redirect_uri", request.redirect_uri)
            )
    
    # 重新加载飞书服务配置（用于发送消息）
    fs = get_feishu_service()
    fs.load_config()
    
    # 重启 WebSocket 监听器（用于接收消息）
    ws_restarted = False
    try:
        from feishu_ws_listener import get_ws_manager, LARK_AVAILABLE
        if LARK_AVAILABLE:
            ws_manager = get_ws_manager(DB_PATH)
            # 无论之前是否运行，都尝试重启以应用新配置
            if ws_manager.restart():
                logger.info("Feishu WebSocket listener restarted with new config")
                ws_restarted = True
            else:
                logger.warning("Failed to restart Feishu WebSocket listener")
    except Exception as e:
        logger.error(f"Error restarting WebSocket listener: {e}")
    
    return {
        "success": True,
        "ws_restarted": ws_restarted,
        "message": "配置已保存" + ("，WebSocket 监听器已重启" if ws_restarted else "")
    }


@app.get("/api/admin/feishu/ws-status")
async def get_feishu_ws_status(
    _: bool = Depends(verify_admin_session)
):
    """获取飞书 WebSocket 监听器状态"""
    from feishu_ws_listener import get_ws_manager
    ws_manager = get_ws_manager(DB_PATH)
    return ws_manager.get_status()


@app.post("/api/admin/feishu/ws-restart")
async def restart_feishu_ws(
    _: bool = Depends(verify_admin_session)
):
    """手动重启飞书 WebSocket 监听器"""
    import logging
    logger = logging.getLogger("user_intent_mcp")
    
    from feishu_ws_listener import get_ws_manager
    ws_manager = get_ws_manager(DB_PATH)
    
    if ws_manager.restart():
        logger.info("Feishu WebSocket listener manually restarted")
        return {"success": True, "message": "WebSocket 监听器已重启"}
    else:
        return {"success": False, "message": "重启失败，可能未配置飞书凭证"}


# ============================================================================
# OAuth API
# ============================================================================

@app.get("/auth/feishu/login")
async def feishu_login():
    """飞书 OAuth 登录"""
    oauth = get_oauth()
    
    if not oauth:
        raise HTTPException(status_code=400, detail="飞书未配置")
    
    url, state = oauth.get_authorize_url()
    
    return RedirectResponse(url=url, status_code=307)


@app.get("/auth/feishu/callback")
async def feishu_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None
):
    """飞书 OAuth 回调"""
    if error:
        raise HTTPException(status_code=400, detail=f"授权失败: {error}")
    
    if not code or not state:
        raise HTTPException(status_code=400, detail="缺少参数")
    
    oauth = get_oauth()
    
    if not oauth:
        raise HTTPException(status_code=400, detail="飞书未配置")
    
    # 验证 state
    if not oauth.validate_state(state):
        raise HTTPException(status_code=400, detail="无效的 state 参数")
    
    try:
        # 换取 token
        token_data = await oauth.exchange_code(code)
        
        # 获取用户信息
        user_info = await oauth.get_user_info(token_data["access_token"])
        
        # 创建或更新用户
        manager = get_user_manager()
        user = manager.create_user(
            open_id=user_info["open_id"],
            union_id=user_info.get("union_id"),
            user_id=user_info.get("user_id"),
            name=user_info.get("name", ""),
            en_name=user_info.get("en_name"),
            avatar_url=user_info.get("avatar_url"),
            avatar_thumb=user_info.get("avatar_thumb"),
            email=user_info.get("email"),
            mobile=user_info.get("mobile"),
            tenant_key=user_info.get("tenant_key"),
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_expires_at=int(time.time()) + token_data.get("expires_in", 7200)
        )
        
        # 返回用户信息和 API Key
        return RedirectResponse(
            url=f"/user?api_key={user['api_key']}",
            status_code=302
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 用户 API
# ============================================================================

@app.get("/api/user/profile")
async def get_user_profile(
    user: dict = Depends(get_current_user)
):
    """获取用户信息"""
    # 返回安全的用户信息
    return {
        "open_id": user["open_id"],
        "name": user["name"],
        "avatar_url": user.get("avatar_url"),
        "email": user.get("email"),
        "api_key": user["api_key"],
        "created_at": user["created_at"]
    }


@app.post("/api/user/regenerate-api-key")
async def regenerate_api_key(
    user: dict = Depends(get_current_user)
):
    """重新生成 API Key"""
    manager = get_user_manager()
    new_api_key = manager.regenerate_api_key(user["open_id"])
    
    if not new_api_key:
        raise HTTPException(status_code=500, detail="生成 API Key 失败")
    
    return {
        "success": True,
        "api_key": new_api_key
    }


# ============================================================================
# 前端页面路由
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def index():
    """首页 - 根据状态显示不同页面"""
    template_path = os.path.join(TEMPLATES_DIR, "multi_tenant.html")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Template not found</h1>", status_code=500)


@app.get("/admin")
async def admin_page():
    """管理后台页面"""
    return RedirectResponse(url="/")


@app.get("/login")
async def login_page():
    """登录页面"""
    return RedirectResponse(url="/")


@app.get("/user", response_class=HTMLResponse)
async def user_page(api_key: Optional[str] = None):
    """用户中心页面"""
    # 如果没有 api_key 参数，重定向到首页
    if not api_key:
        return RedirectResponse(url="/")
    
    # 验证 API Key 是否有效
    manager = get_user_manager()
    user = manager.get_user_by_api_key(api_key)
    
    if not user:
        return RedirectResponse(url="/")
    
    # 返回用户中心页面
    return HTMLResponse(content=f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>用户中心 - AI Intent Center</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .container {{
            background: white;
            border-radius: 20px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            padding: 40px;
            max-width: 500px;
            width: 100%;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .avatar {{
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
            font-size: 36px;
            color: white;
        }}
        h1 {{
            color: #1a1a2e;
            font-size: 24px;
            margin-bottom: 8px;
        }}
        .subtitle {{
            color: #6b7280;
            font-size: 14px;
        }}
        .info-card {{
            background: #f8fafc;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .info-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #e2e8f0;
        }}
        .info-item:last-child {{
            border-bottom: none;
        }}
        .info-label {{
            color: #6b7280;
            font-size: 14px;
        }}
        .info-value {{
            color: #1a1a2e;
            font-weight: 500;
            font-size: 14px;
            word-break: break-all;
            text-align: right;
            max-width: 250px;
        }}
        .api-key-section {{
            background: #f0fdf4;
            border: 1px solid #86efac;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .api-key-title {{
            color: #166534;
            font-weight: 600;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .api-key-value {{
            background: white;
            border: 1px solid #d1d5db;
            border-radius: 8px;
            padding: 12px;
            font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
            font-size: 13px;
            color: #166534;
            word-break: break-all;
            margin-bottom: 12px;
        }}
        .copy-btn {{
            background: #22c55e;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
        }}
        .copy-btn:hover {{
            background: #16a34a;
        }}
        .actions {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        .btn {{
            padding: 14px 20px;
            border-radius: 10px;
            font-size: 15px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            text-align: center;
            text-decoration: none;
        }}
        .btn-primary {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
        }}
        .btn-primary:hover {{
            opacity: 0.9;
            transform: translateY(-1px);
        }}
        .btn-secondary {{
            background: #f3f4f6;
            color: #374151;
            border: 1px solid #d1d5db;
        }}
        .btn-secondary:hover {{
            background: #e5e7eb;
        }}
        .btn-danger {{
            background: #fee2e2;
            color: #dc2626;
            border: 1px solid #fca5a5;
        }}
        .btn-danger:hover {{
            background: #fecaca;
        }}
        .note {{
            background: #eff6ff;
            border: 1px solid #93c5fd;
            border-radius: 8px;
            padding: 12px;
            margin-top: 20px;
            color: #1e40af;
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="avatar">👤</div>
            <h1>欢迎回来，{user.get('name', '用户')}!</h1>
            <p class="subtitle">AI Intent Center 用户中心</p>
        </div>
        
        <div class="info-card">
            <div class="info-item">
                <span class="info-label">飞书 ID</span>
                <span class="info-value">{user.get('open_id', '-')[:20]}...</span>
            </div>
            <div class="info-item">
                <span class="info-label">状态</span>
                <span class="info-value">{'✅ 已启用' if user.get('is_active') else '❌ 已禁用'}</span>
            </div>
            <div class="info-item">
                <span class="info-label">注册时间</span>
                <span class="info-value">{user.get('created_at', '-')}</span>
            </div>
        </div>
        
        <div class="api-key-section">
            <div class="api-key-title">
                🔑 您的 API Key
            </div>
            <div class="api-key-value" id="apiKey">{api_key}</div>
            <button class="copy-btn" onclick="copyApiKey()">📋 复制 API Key</button>
        </div>
        
        <div class="note">
            💡 <strong>提示：</strong>您可以使用此 API Key 在 MCP 客户端中进行身份验证。
            将此 Key 配置到您的 AI 应用中即可接收反馈消息。
        </div>
        
        <div class="actions" style="margin-top: 24px;">
            <a href="/webui?api_key={api_key}" class="btn btn-primary">💻 进入 Web UI</a>
            <button onclick="logout()" class="btn btn-secondary">🚪 退出登录</button>
            <a href="/" class="btn btn-secondary">🏠 返回首页</a>
        </div>
        
        <div class="note" style="margin-top: 16px; background: #fef3c7; border-color: #fcd34d; color: #92400e;">
            🔒 <strong>登录缓存：</strong>您的登录状态将保存 30 天，下次访问可直接使用。
        </div>
    </div>
    
    <script>
        // API Key Cache Functions (30 days)
        const API_KEY_STORAGE_KEY = 'userApiKey';
        const API_KEY_EXPIRY_KEY = 'userApiKeyExpiry';
        const API_KEY_CACHE_DAYS = 30;
        
        function saveApiKeyToCache(apiKey) {{
            const expiryDate = new Date();
            expiryDate.setDate(expiryDate.getDate() + API_KEY_CACHE_DAYS);
            localStorage.setItem(API_KEY_STORAGE_KEY, apiKey);
            localStorage.setItem(API_KEY_EXPIRY_KEY, expiryDate.getTime().toString());
        }}
        
        function clearApiKeyCache() {{
            localStorage.removeItem(API_KEY_STORAGE_KEY);
            localStorage.removeItem(API_KEY_EXPIRY_KEY);
        }}
        
        function copyApiKey() {{
            const apiKey = document.getElementById('apiKey').textContent;
            navigator.clipboard.writeText(apiKey).then(() => {{
                const btn = document.querySelector('.copy-btn');
                const originalText = btn.textContent;
                btn.textContent = '✅ 已复制!';
                setTimeout(() => {{
                    btn.textContent = originalText;
                }}, 2000);
            }});
        }}
        
        function logout() {{
            clearApiKeyCache();
            window.location.href = '/';
        }}
        
        // Save API Key to cache on page load
        (function() {{
            const apiKey = document.getElementById('apiKey').textContent;
            if (apiKey && apiKey.startsWith('uk_')) {{
                saveApiKeyToCache(apiKey);
            }}
        }})();
    </script>
</body>
</html>
    """)


@app.get("/webui", response_class=HTMLResponse)
async def webui_page():
    """单用户模式 - 原始 Web UI（无需登录）"""
    # 加载原始的 index.html 模板
    original_template = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(original_template):
        with open(original_template, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    
    # 如果没有原始模板，返回简单的 Web UI
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>AI Intent Center - Web UI</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: system-ui; max-width: 800px; margin: 50px auto; padding: 20px; }
        h1 { color: #333; }
        .info { background: #f0f0f0; padding: 20px; border-radius: 8px; }
    </style>
</head>
<body>
    <h1>🤖 AI Intent Center - 单用户模式</h1>
    <div class="info">
        <p>单用户模式已启用。此模式下无需登录即可使用。</p>
        <p>请配置 MCP 客户端连接到此服务。</p>
    </div>
</body>
</html>
    """)


# ============================================================================
# 单用户模式 API 端点（无需认证）
# ============================================================================

import sqlite3

# 静态文件
STATIC_DIR = os.path.join(SRC_DIR, "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/sw.js")
async def get_sw():
    """Service Worker"""
    sw_path = os.path.join(STATIC_DIR, "sw.js")
    if os.path.exists(sw_path):
        return FileResponse(sw_path)
    raise HTTPException(status_code=404, detail="sw.js not found")


class ReplyModel(BaseModel):
    """回复模型"""
    id: str
    answer: str
    image: Optional[str] = None


class DeleteHistoryModel(BaseModel):
    """批量删除历史模型"""
    ids: list[str]


def init_intent_db():
    """初始化 intent_queue 表"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS intent_queue (
                id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT,
                image TEXT,
                status TEXT DEFAULT 'PENDING',
                user_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''')


def _get_api_key_from_header(authorization: Optional[str]) -> Optional[str]:
    """
    从 Authorization Header 获取 API Key
    
    格式: Authorization: Bearer uk_xxx
    """
    if not authorization:
        return None
    if authorization.startswith("Bearer "):
        return authorization[7:].strip()
    return None


@app.get("/api/poll")
async def poll_question(authorization: Optional[str] = Header(None)):
    """
    返回待处理的问题
    
    认证: Authorization: Bearer uk_xxx
    
    消息隔离规则：
    - 如果提供有效 API Key：只返回该用户的消息
    - 如果不提供 API Key：只返回公共消息（user_id IS NULL）
    - 如果 API Key 无效：返回空列表
    """
    init_intent_db()
    api_key = _get_api_key_from_header(authorization)
    
    with sqlite3.connect(DB_PATH) as conn:
        if api_key:
            # 飞书用户模式：根据 API Key 查找用户，只返回该用户的消息
            user_manager = get_user_manager()
            user = user_manager.get_user_by_api_key(api_key)
            
            if user:
                # 有效用户：只返回该用户的消息
                cursor = conn.execute(
                    "SELECT id, question FROM intent_queue WHERE status = 'PENDING' AND user_id = ?",
                    (user["open_id"],)
                )
            else:
                # 无效 API Key：返回空列表
                return []
        else:
            # 无登录模式：只返回公共消息（user_id IS NULL）
            cursor = conn.execute(
                "SELECT id, question FROM intent_queue WHERE status = 'PENDING' AND user_id IS NULL"
            )
        
        rows = cursor.fetchall()
    
    return [{"id": row[0], "question": row[1]} for row in rows]


@app.post("/api/reply")
async def receive_reply(reply: ReplyModel):
    """接收问题的回复"""
    init_intent_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE intent_queue SET answer = ?, image = ?, status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (reply.answer, reply.image, reply.id)
        )
    return {"status": "success"}


@app.get("/api/user/info")
async def get_user_info_by_api_key(authorization: Optional[str] = Header(None)):
    """
    获取当前用户信息
    
    认证: Authorization: Bearer uk_xxx
    """
    api_key = _get_api_key_from_header(authorization)
    if not api_key:
        return JSONResponse(
            status_code=401,
            content={"error": "Missing Authorization header"}
        )
    
    user_manager = get_user_manager()
    user = user_manager.get_user_by_api_key(api_key)
    
    if not user:
        return JSONResponse(
            status_code=404,
            content={"error": "User not found"}
        )
    
    # 返回安全的用户信息（不包含敏感数据）
    return {
        "open_id": user.get("open_id", "")[:20] + "...",  # 截断显示
        "name": user.get("name", "User"),
        "avatar_url": user.get("avatar_url"),
        "email": user.get("email"),
        "is_active": user.get("is_active", True)
    }


class FeishuNotifyRequest(BaseModel):
    enabled: bool


@app.get("/api/user/feishu-notify")
async def get_feishu_notify_status(authorization: Optional[str] = Header(None)):
    """
    获取用户的飞书通知状态
    
    认证: Authorization: Bearer uk_xxx
    """
    api_key = _get_api_key_from_header(authorization)
    if not api_key:
        return JSONResponse(status_code=401, content={"error": "Missing Authorization header"})
    
    user_manager = get_user_manager()
    user = user_manager.get_user_by_api_key(api_key)
    
    if not user:
        return JSONResponse(status_code=404, content={"error": "User not found"})
    
    # 从用户配置中获取飞书通知状态
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "SELECT value FROM user_settings WHERE user_id = ? AND key = 'feishu_notify_enabled'",
            (user["open_id"],)
        )
        row = cursor.fetchone()
        enabled = row[0] == "1" if row else False
    
    return {"enabled": enabled, "open_id": user["open_id"]}


@app.post("/api/user/feishu-notify")
async def set_feishu_notify_status(
    request: FeishuNotifyRequest,
    authorization: Optional[str] = Header(None)
):
    """
    设置用户的飞书通知状态
    
    认证: Authorization: Bearer uk_xxx
    """
    api_key = _get_api_key_from_header(authorization)
    if not api_key:
        return JSONResponse(status_code=401, content={"error": "Missing Authorization header"})
    
    user_manager = get_user_manager()
    user = user_manager.get_user_by_api_key(api_key)
    
    if not user:
        return JSONResponse(status_code=404, content={"error": "User not found"})
    
    # 确保 user_settings 表存在
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                PRIMARY KEY (user_id, key)
            )
        ''')
        
        # 更新或插入设置
        conn.execute('''
            INSERT OR REPLACE INTO user_settings (user_id, key, value)
            VALUES (?, 'feishu_notify_enabled', ?)
        ''', (user["open_id"], "1" if request.enabled else "0"))
        conn.commit()
    
    return {"success": True, "enabled": request.enabled}


@app.get("/api/history")
async def get_history():
    """返回已完成的问题历史"""
    init_intent_db()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """SELECT id, question, answer, completed_at 
               FROM intent_queue 
               WHERE status = 'COMPLETED' 
               ORDER BY completed_at DESC
               LIMIT 50"""
        )
        rows = cursor.fetchall()
    return [
        {
            "id": row[0], 
            "question": row[1], 
            "answer": row[2],
            "completed_at": row[3]
        } 
        for row in rows
    ]


@app.get("/api/request/{request_id}")
async def get_request_detail(request_id: str):
    """获取单个请求的详情"""
    init_intent_db()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "SELECT id, question, answer, status, created_at, completed_at FROM intent_queue WHERE id = ?",
            (request_id,)
        )
        row = cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Request not found")
    
    return {
        "id": row[0],
        "question": row[1],
        "answer": row[2],
        "status": row[3],
        "created_at": row[4],
        "completed_at": row[5]
    }


@app.delete("/api/request/{request_id}")
async def delete_request(request_id: str):
    """忽略/取消一个请求"""
    init_intent_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE intent_queue SET status = 'DISMISSED' WHERE id = ?",
            (request_id,)
        )
    return {"status": "dismissed"}


@app.delete("/api/history/{history_id}")
async def delete_history_item(history_id: str):
    """删除一条历史记录"""
    init_intent_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "DELETE FROM intent_queue WHERE id = ? AND status = 'COMPLETED'",
            (history_id,)
        )
    return {"status": "deleted"}


@app.post("/api/history/delete")
async def delete_history_batch(data: DeleteHistoryModel):
    """批量删除历史记录"""
    init_intent_db()
    with sqlite3.connect(DB_PATH) as conn:
        placeholders = ','.join(['?' for _ in data.ids])
        conn.execute(
            f"DELETE FROM intent_queue WHERE id IN ({placeholders}) AND status = 'COMPLETED'",
            data.ids
        )
    return {"status": "deleted", "count": len(data.ids)}


# 飞书配置（单用户模式）
class FeishuConfigModel(BaseModel):
    """飞书配置模型"""
    enabled: Optional[bool] = None
    app_id: Optional[str] = None
    app_secret: Optional[str] = None
    receive_id: Optional[str] = None
    receive_id_type: Optional[str] = None


@app.get("/api/feishu/config")
async def get_feishu_config_single():
    """获取飞书配置（单用户模式）"""
    # 返回飞书服务的实际状态
    fs = get_feishu_service()
    return fs.get_config()


@app.post("/api/feishu/config")
async def update_feishu_config_single(config: FeishuConfigModel):
    """更新飞书配置（单用户模式）"""
    # 单用户模式下飞书配置由管理后台管理
    return {"status": "success", "message": "请在管理后台配置飞书"}


# ============================================================================
# 健康检查
# ============================================================================

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "timestamp": int(time.time())}


# ============================================================================
# React 前端静态文件服务（生产模式）
# ============================================================================

# 前端构建目录
FRONTEND_DIST_DIR = os.path.join(os.path.dirname(SRC_DIR), "frontend", "dist")

if os.path.exists(FRONTEND_DIST_DIR):
    # 挂载前端静态资源（/app/assets 路径）
    assets_dir = os.path.join(FRONTEND_DIST_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/app/assets", StaticFiles(directory=assets_dir), name="frontend_assets")
    
    # 前端静态文件（如 vite.svg）
    @app.get("/app/vite.svg")
    async def serve_vite_svg():
        svg_path = os.path.join(FRONTEND_DIST_DIR, "vite.svg")
        if os.path.exists(svg_path):
            return FileResponse(svg_path)
        raise HTTPException(status_code=404)
    
    @app.get("/app/{full_path:path}")
    async def serve_frontend_spa(full_path: str):
        """服务 React 前端 SPA（/app 路径下）"""
        # 首先检查是否有静态文件
        file_path = os.path.join(FRONTEND_DIST_DIR, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        # 否则返回 index.html（SPA 路由）
        index_path = os.path.join(FRONTEND_DIST_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="Frontend not built")
    
    @app.get("/app")
    async def serve_frontend_root():
        """React 前端入口"""
        index_path = os.path.join(FRONTEND_DIST_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="Frontend not built")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
