"""
MCP 端到端集成测试 - 测试 MCP 工具与 Web API 的完整交互流程
使用 FastMCP Client 和 HTTP 请求模拟完整用户流程
"""

import asyncio
import os
import sys
import threading
import time
import uuid

import httpx
import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fastmcp import Client
from core import mcp, DB_PATH, init_db
import sqlite3


# 测试配置
BASE_URL = "http://localhost:8000"
# 从飞书登录获取的 API key（测试前需要确保用户已登录）
TEST_API_KEY = os.getenv("TEST_API_KEY", "uk_a8d63ee4ea75112c69e2c2d975a59e42")


class TestMCPWebAPIIntegration:
    """MCP 工具与 Web API 端到端集成测试"""
    
    def setup_method(self):
        """每个测试前清理数据库"""
        init_db()
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM intent_queue")
    
    def teardown_method(self):
        """测试后清理"""
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM intent_queue")
    
    @pytest.mark.asyncio
    async def test_mcp_to_webui_to_reply_flow(self):
        """测试完整流程: MCP发送问题 -> WebUI展示 -> Web API回复 -> MCP收到回复"""
        test_question = f"E2E Test Question {uuid.uuid4()}"
        test_answer = "E2E Test Answer from WebUI"
        received_result = {"value": None}
        
        async def web_api_reply_simulator():
            """模拟 Web API 回复的协程"""
            async with httpx.AsyncClient(base_url=BASE_URL) as client:
                # 轮询等待问题出现
                for _ in range(60):
                    try:
                        response = await client.get("/api/poll")
                        tasks = response.json()
                        
                        # 找到我们的测试问题
                        for task in tasks:
                            if task.get("question") == test_question:
                                request_id = task.get("id")
                                print(f"[WebAPI Simulator] Found task: {request_id}")
                                
                                # 等待一下再回复
                                await asyncio.sleep(0.5)
                                
                                # 发送回复
                                reply_response = await client.post(
                                    "/api/reply",
                                    json={
                                        "id": request_id,
                                        "answer": test_answer,
                                        "image": None
                                    }
                                )
                                print(f"[WebAPI Simulator] Reply sent: {reply_response.status_code}")
                                return
                    except Exception as e:
                        print(f"[WebAPI Simulator] Error: {e}")
                    
                    await asyncio.sleep(0.2)
                
                print("[WebAPI Simulator] Timeout waiting for question")
        
        async def mcp_caller():
            """调用 MCP 工具的协程"""
            async with Client(mcp) as client:
                result = await client.call_tool("collect_user_intent", {"question": test_question})
                received_result["value"] = result
                return result
        
        # 并发运行两个协程
        await asyncio.gather(
            mcp_caller(),
            web_api_reply_simulator()
        )
        
        # 验证结果
        result = received_result["value"]
        assert result is not None
        
        text_content = self._extract_text(result)
        assert test_answer in text_content, f"Expected '{test_answer}' in '{text_content}'"
    
    @pytest.mark.asyncio
    async def test_webui_poll_shows_question(self):
        """测试 WebUI poll API 能正确显示 MCP 发送的问题"""
        test_question = f"Poll Test Question {uuid.uuid4()}"
        question_appeared = {"value": False}
        
        async def check_poll_api():
            """检查 poll API 是否显示问题"""
            async with httpx.AsyncClient(base_url=BASE_URL) as client:
                for _ in range(50):
                    try:
                        response = await client.get("/api/poll")
                        tasks = response.json()
                        
                        for task in tasks:
                            if task.get("question") == test_question:
                                question_appeared["value"] = True
                                print(f"[Poll Check] Question found: {task}")
                                
                                # 发送回复以结束 MCP 等待
                                await client.post(
                                    "/api/reply",
                                    json={
                                        "id": task.get("id"),
                                        "answer": "Ack",
                                        "image": None
                                    }
                                )
                                return
                    except Exception as e:
                        print(f"[Poll Check] Error: {e}")
                    
                    await asyncio.sleep(0.1)
        
        async def mcp_sender():
            """发送 MCP 问题"""
            async with Client(mcp) as client:
                await client.call_tool("collect_user_intent", {"question": test_question})
        
        await asyncio.gather(
            mcp_sender(),
            check_poll_api()
        )
        
        assert question_appeared["value"], "Question did not appear in poll API"
    
    @pytest.mark.asyncio
    async def test_history_api_after_reply(self):
        """测试回复后历史记录 API 正确保存"""
        test_question = f"History Test Question {uuid.uuid4()}"
        test_answer = "History Test Answer"
        saved_request_id = {"value": None}
        
        async def reply_and_check_history():
            """回复并检查历史记录"""
            async with httpx.AsyncClient(base_url=BASE_URL) as client:
                # 等待问题出现
                for _ in range(50):
                    response = await client.get("/api/poll")
                    tasks = response.json()
                    
                    for task in tasks:
                        if task.get("question") == test_question:
                            request_id = task.get("id")
                            saved_request_id["value"] = request_id
                            
                            # 发送回复
                            await client.post(
                                "/api/reply",
                                json={"id": request_id, "answer": test_answer, "image": None}
                            )
                            
                            # 等待一下让数据库更新
                            await asyncio.sleep(0.5)
                            
                            # 检查历史记录 API
                            history_response = await client.get("/api/history")
                            history = history_response.json()
                            
                            for item in history:
                                if item.get("id") == request_id:
                                    assert item.get("question") == test_question
                                    assert item.get("answer") == test_answer
                                    print(f"[History Check] Record found: {item}")
                                    return
                    
                    await asyncio.sleep(0.1)
        
        async def mcp_sender():
            async with Client(mcp) as client:
                await client.call_tool("collect_user_intent", {"question": test_question})
        
        await asyncio.gather(
            mcp_sender(),
            reply_and_check_history()
        )
    
    @pytest.mark.asyncio
    async def test_dismiss_via_web_api(self):
        """测试通过 Web API dismiss 请求"""
        test_question = f"Dismiss API Test {uuid.uuid4()}"
        
        async def dismiss_via_api():
            """通过 API dismiss 请求"""
            async with httpx.AsyncClient(base_url=BASE_URL) as client:
                for _ in range(50):
                    response = await client.get("/api/poll")
                    tasks = response.json()
                    
                    for task in tasks:
                        if task.get("question") == test_question:
                            request_id = task.get("id")
                            
                            # 通过 DELETE API dismiss
                            await client.delete(f"/api/request/{request_id}")
                            print(f"[Dismiss API] Request dismissed: {request_id}")
                            return
                    
                    await asyncio.sleep(0.1)
        
        async def mcp_sender():
            async with Client(mcp) as client:
                result = await client.call_tool("collect_user_intent", {"question": test_question})
                text = self._extract_text(result)
                assert "dismissed" in text.lower(), f"Expected 'dismissed' in '{text}'"
        
        await asyncio.gather(
            mcp_sender(),
            dismiss_via_api()
        )
    
    @pytest.mark.asyncio
    async def test_request_detail_api(self):
        """测试获取单个请求详情的 API"""
        test_question = f"Detail API Test {uuid.uuid4()}"
        
        async def check_detail_api():
            """检查请求详情 API"""
            async with httpx.AsyncClient(base_url=BASE_URL) as client:
                for _ in range(50):
                    response = await client.get("/api/poll")
                    tasks = response.json()
                    
                    for task in tasks:
                        if task.get("question") == test_question:
                            request_id = task.get("id")
                            
                            # 获取详情
                            detail_response = await client.get(f"/api/request/{request_id}")
                            detail = detail_response.json()
                            
                            assert detail.get("question") == test_question
                            assert detail.get("id") == request_id
                            print(f"[Detail API] Request detail: {detail}")
                            
                            # 回复以结束等待
                            await client.post(
                                "/api/reply",
                                json={"id": request_id, "answer": "Detail test reply", "image": None}
                            )
                            return
                    
                    await asyncio.sleep(0.1)
        
        async def mcp_sender():
            async with Client(mcp) as client:
                await client.call_tool("collect_user_intent", {"question": test_question})
        
        await asyncio.gather(
            mcp_sender(),
            check_detail_api()
        )
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_mcp_requests(self):
        """测试多个并发 MCP 请求通过 Web API 回复"""
        num_requests = 3
        questions = [f"Concurrent E2E Q{i} {uuid.uuid4()}" for i in range(num_requests)]
        answers = [f"Concurrent E2E A{i}" for i in range(num_requests)]
        replied = set()
        
        async def web_api_replier():
            """Web API 批量回复器"""
            async with httpx.AsyncClient(base_url=BASE_URL) as client:
                while len(replied) < num_requests:
                    try:
                        response = await client.get("/api/poll")
                        tasks = response.json()
                        
                        for task in tasks:
                            q = task.get("question")
                            if q in questions and q not in replied:
                                idx = questions.index(q)
                                await client.post(
                                    "/api/reply",
                                    json={
                                        "id": task.get("id"),
                                        "answer": answers[idx],
                                        "image": None
                                    }
                                )
                                replied.add(q)
                                print(f"[Replier] Replied to question {idx}")
                    except Exception as e:
                        print(f"[Replier] Error: {e}")
                    
                    await asyncio.sleep(0.1)
        
        async def mcp_caller(question, expected_answer):
            """单个 MCP 调用"""
            async with Client(mcp) as client:
                result = await client.call_tool("collect_user_intent", {"question": question})
                text = self._extract_text(result)
                assert expected_answer in text, f"Expected '{expected_answer}' in '{text}'"
                return result
        
        # 启动 Web API 回复器
        replier_task = asyncio.create_task(web_api_replier())
        
        # 并发发送所有 MCP 请求
        mcp_tasks = [mcp_caller(q, a) for q, a in zip(questions, answers)]
        results = await asyncio.gather(*mcp_tasks)
        
        # 等待回复器完成
        replier_task.cancel()
        try:
            await replier_task
        except asyncio.CancelledError:
            pass
        
        # 验证所有请求都得到了正确回复
        assert len(results) == num_requests
        for i, result in enumerate(results):
            text = self._extract_text(result)
            assert answers[i] in text
    
    def _extract_text(self, result) -> str:
        """从 MCP 工具结果中提取文本内容"""
        text_content = ""
        if hasattr(result, 'content'):
            for content in result.content:
                if hasattr(content, 'text') and content.text:
                    text_content += content.text
                elif isinstance(content, dict) and 'text' in content:
                    text_content += content['text']
                else:
                    text_content += str(content)
        return text_content


class TestMessageIsolation:
    """
    消息用户隔离测试
    
    测试场景：
    - TC-ISO-001: 飞书用户只能看到自己的消息
    - TC-ISO-002: 无登录用户只能看到公共消息（user_id=NULL）
    - TC-ISO-003: 不同飞书用户之间消息隔离
    - TC-ISO-004: 飞书用户看不到无登录用户的消息
    - TC-ISO-005: 无登录用户看不到飞书用户的消息
    """
    
    def setup_method(self):
        """每个测试前清理数据库"""
        init_db()
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM intent_queue")
    
    def teardown_method(self):
        """测试后清理"""
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM intent_queue")
    
    @pytest.mark.asyncio
    async def test_user_can_only_see_own_messages(self):
        """
        TC-ISO-001: 飞书用户只能看到自己的消息
        
        前置条件：
        - 用户 A 已登录，有 API Key uk_A
        - 数据库中有绑定到用户 A 的消息
        
        预期结果：
        - /api/poll?api_key=uk_A 只返回 user_id=ou_A 的消息
        """
        # 准备测试数据
        user_a_open_id = "ou_test_user_a"
        user_a_api_key = "uk_test_user_a_key"
        
        # 创建测试用户 A
        with sqlite3.connect(DB_PATH) as conn:
            # 确保 users 表存在并插入测试用户
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    open_id TEXT PRIMARY KEY,
                    union_id TEXT,
                    user_id TEXT,
                    name TEXT,
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
            conn.execute('''
                INSERT OR REPLACE INTO users (open_id, name, api_key, is_active, created_at, updated_at)
                VALUES (?, ?, ?, 1, ?, ?)
            ''', (user_a_open_id, "Test User A", user_a_api_key, int(time.time()), int(time.time())))
            
            # 插入用户 A 的消息
            conn.execute('''
                INSERT INTO intent_queue (id, question, status, user_id) 
                VALUES (?, ?, 'PENDING', ?)
            ''', ("msg_user_a_1", "Question for User A", user_a_open_id))
            
            # 插入其他用户的消息
            conn.execute('''
                INSERT INTO intent_queue (id, question, status, user_id) 
                VALUES (?, ?, 'PENDING', ?)
            ''', ("msg_user_b_1", "Question for User B", "ou_test_user_b"))
            
            # 插入公共消息（无登录模式）
            conn.execute('''
                INSERT INTO intent_queue (id, question, status, user_id) 
                VALUES (?, ?, 'PENDING', NULL)
            ''', ("msg_public_1", "Public Question", ))
            
            conn.commit()
        
        # 测试：用户 A 只能看到自己的消息
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(f"/api/poll?api_key={user_a_api_key}")
            assert response.status_code == 200
            messages = response.json()
            
            # 应该只有用户 A 的消息
            assert len(messages) == 1
            assert messages[0]["id"] == "msg_user_a_1"
            assert messages[0]["question"] == "Question for User A"
    
    @pytest.mark.asyncio
    async def test_anonymous_user_sees_only_public_messages(self):
        """
        TC-ISO-002: 无登录用户只能看到公共消息（user_id=NULL）
        
        前置条件：
        - 数据库中有公共消息（user_id=NULL）
        - 数据库中有绑定到特定用户的消息
        
        预期结果：
        - /api/poll（不带 api_key）只返回 user_id=NULL 的消息
        """
        # 准备测试数据
        with sqlite3.connect(DB_PATH) as conn:
            # 插入公共消息
            conn.execute('''
                INSERT INTO intent_queue (id, question, status, user_id) 
                VALUES (?, ?, 'PENDING', NULL)
            ''', ("msg_public_1", "Public Question 1",))
            conn.execute('''
                INSERT INTO intent_queue (id, question, status, user_id) 
                VALUES (?, ?, 'PENDING', NULL)
            ''', ("msg_public_2", "Public Question 2",))
            
            # 插入用户专属消息
            conn.execute('''
                INSERT INTO intent_queue (id, question, status, user_id) 
                VALUES (?, ?, 'PENDING', ?)
            ''', ("msg_user_1", "User Specific Question", "ou_some_user"))
            
            conn.commit()
        
        # 测试：无登录用户只能看到公共消息
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/api/poll")  # 不带 api_key
            assert response.status_code == 200
            messages = response.json()
            
            # 应该只有公共消息
            assert len(messages) == 2
            message_ids = [m["id"] for m in messages]
            assert "msg_public_1" in message_ids
            assert "msg_public_2" in message_ids
            assert "msg_user_1" not in message_ids
    
    @pytest.mark.asyncio
    async def test_different_users_isolated(self):
        """
        TC-ISO-003: 不同飞书用户之间消息隔离
        
        前置条件：
        - 用户 A 和用户 B 都已登录
        - 各自有自己的消息
        
        预期结果：
        - 用户 A 看不到用户 B 的消息
        - 用户 B 看不到用户 A 的消息
        """
        # 准备测试数据
        user_a_open_id = "ou_iso_user_a"
        user_a_api_key = "uk_iso_user_a_key"
        user_b_open_id = "ou_iso_user_b"
        user_b_api_key = "uk_iso_user_b_key"
        
        with sqlite3.connect(DB_PATH) as conn:
            # 创建 users 表（如果不存在）
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    open_id TEXT PRIMARY KEY,
                    union_id TEXT,
                    user_id TEXT,
                    name TEXT,
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
            
            # 创建用户 A 和 B
            conn.execute('''
                INSERT OR REPLACE INTO users (open_id, name, api_key, is_active, created_at, updated_at)
                VALUES (?, ?, ?, 1, ?, ?)
            ''', (user_a_open_id, "User A", user_a_api_key, int(time.time()), int(time.time())))
            conn.execute('''
                INSERT OR REPLACE INTO users (open_id, name, api_key, is_active, created_at, updated_at)
                VALUES (?, ?, ?, 1, ?, ?)
            ''', (user_b_open_id, "User B", user_b_api_key, int(time.time()), int(time.time())))
            
            # 插入用户 A 的消息
            conn.execute('''
                INSERT INTO intent_queue (id, question, status, user_id) 
                VALUES (?, ?, 'PENDING', ?)
            ''', ("msg_a_1", "Message for A", user_a_open_id))
            
            # 插入用户 B 的消息
            conn.execute('''
                INSERT INTO intent_queue (id, question, status, user_id) 
                VALUES (?, ?, 'PENDING', ?)
            ''', ("msg_b_1", "Message for B", user_b_open_id))
            
            conn.commit()
        
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            # 用户 A 查询
            response_a = await client.get(f"/api/poll?api_key={user_a_api_key}")
            assert response_a.status_code == 200
            messages_a = response_a.json()
            
            # 用户 B 查询
            response_b = await client.get(f"/api/poll?api_key={user_b_api_key}")
            assert response_b.status_code == 200
            messages_b = response_b.json()
        
        # 验证隔离
        assert len(messages_a) == 1
        assert messages_a[0]["id"] == "msg_a_1"
        
        assert len(messages_b) == 1
        assert messages_b[0]["id"] == "msg_b_1"
    
    @pytest.mark.asyncio
    async def test_feishu_user_cannot_see_public_messages(self):
        """
        TC-ISO-004: 飞书用户看不到无登录用户的消息
        
        前置条件：
        - 用户 A 已登录
        - 数据库中有公共消息（user_id=NULL）
        
        预期结果：
        - /api/poll?api_key=uk_A 不返回 user_id=NULL 的消息
        """
        user_a_open_id = "ou_feishu_user"
        user_a_api_key = "uk_feishu_user_key"
        
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    open_id TEXT PRIMARY KEY,
                    union_id TEXT,
                    user_id TEXT,
                    name TEXT,
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
            conn.execute('''
                INSERT OR REPLACE INTO users (open_id, name, api_key, is_active, created_at, updated_at)
                VALUES (?, ?, ?, 1, ?, ?)
            ''', (user_a_open_id, "Feishu User", user_a_api_key, int(time.time()), int(time.time())))
            
            # 插入公共消息
            conn.execute('''
                INSERT INTO intent_queue (id, question, status, user_id) 
                VALUES (?, ?, 'PENDING', NULL)
            ''', ("msg_public", "Public Question",))
            
            conn.commit()
        
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get(f"/api/poll?api_key={user_a_api_key}")
            assert response.status_code == 200
            messages = response.json()
            
            # 飞书用户看不到公共消息
            assert len(messages) == 0
    
    @pytest.mark.asyncio
    async def test_anonymous_user_cannot_see_feishu_messages(self):
        """
        TC-ISO-005: 无登录用户看不到飞书用户的消息
        
        前置条件：
        - 数据库中有绑定到飞书用户的消息
        
        预期结果：
        - /api/poll（不带 api_key）不返回 user_id 非 NULL 的消息
        """
        with sqlite3.connect(DB_PATH) as conn:
            # 插入飞书用户的消息
            conn.execute('''
                INSERT INTO intent_queue (id, question, status, user_id) 
                VALUES (?, ?, 'PENDING', ?)
            ''', ("msg_feishu", "Feishu User Question", "ou_some_feishu_user"))
            
            conn.commit()
        
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/api/poll")  # 不带 api_key
            assert response.status_code == 200
            messages = response.json()
            
            # 无登录用户看不到飞书用户的消息
            assert len(messages) == 0
    
    @pytest.mark.asyncio
    async def test_invalid_api_key_sees_nothing(self):
        """
        TC-ISO-006: 无效的 API Key 不返回任何消息
        
        前置条件：
        - 数据库中有各种消息
        
        预期结果：
        - /api/poll?api_key=invalid_key 返回空列表
        """
        with sqlite3.connect(DB_PATH) as conn:
            # 插入公共消息
            conn.execute('''
                INSERT INTO intent_queue (id, question, status, user_id) 
                VALUES (?, ?, 'PENDING', NULL)
            ''', ("msg_public", "Public Question",))
            
            # 插入用户消息
            conn.execute('''
                INSERT INTO intent_queue (id, question, status, user_id) 
                VALUES (?, ?, 'PENDING', ?)
            ''', ("msg_user", "User Question", "ou_some_user"))
            
            conn.commit()
        
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/api/poll?api_key=invalid_api_key_12345")
            assert response.status_code == 200
            messages = response.json()
            
            # 无效 API Key 看不到任何消息
            assert len(messages) == 0


class TestWebAPIEndpoints:
    """测试 Web API 端点（无需 MCP 调用）"""
    
    @pytest.mark.asyncio
    async def test_poll_endpoint_returns_list(self):
        """测试 /api/poll 返回列表"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/api/poll")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_history_endpoint_returns_list(self):
        """测试 /api/history 返回列表"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/api/history")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_system_status_endpoint(self):
        """测试 /api/system/status 端点"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/api/system/status")
            assert response.status_code == 200
            data = response.json()
            assert "initialized" in data
    
    @pytest.mark.asyncio
    async def test_webui_page_accessible(self):
        """测试 /webui 页面可访问"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/webui")
            assert response.status_code == 200
            assert "AI" in response.text
    
    @pytest.mark.asyncio
    async def test_main_page_accessible(self):
        """测试首页可访问"""
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/")
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
