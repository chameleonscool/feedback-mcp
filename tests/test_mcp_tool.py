"""
MCP Tool 单元测试 - 使用 FastMCP Client 进行测试
"""

import asyncio
import sqlite3
import threading
import time
import os
import sys
import uuid
import pytest
import base64

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fastmcp import Client
from core import mcp, state, DB_PATH, init_db


class TestMCPCollectUserIntent:
    """测试 collect_user_intent MCP 工具"""
    
    def setup_method(self):
        """每个测试前重置状态"""
        # Reset state
        state.current_question = None
        state.user_answer = None
        state.answer_event.clear()
        
        # Clean up database
        init_db()
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM intent_queue")
    
    def teardown_method(self):
        """每个测试后清理"""
        state.current_question = None
        state.user_answer = None
        state.answer_event.clear()
        
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM intent_queue")
    
    @pytest.mark.asyncio
    async def test_basic_text_response(self):
        """测试基本的文本响应流程"""
        simulator_completed = threading.Event()
        test_question = f"Test Question {uuid.uuid4()}"
        test_answer = "Test Answer from User"
        
        def simulate_user_input():
            """模拟用户通过状态钩子回复"""
            for _ in range(50):
                if state.current_question == test_question:
                    time.sleep(0.3)  # 等待工具设置完成
                    state.user_answer = test_answer
                    state.answer_event.set()
                    simulator_completed.set()
                    return
                time.sleep(0.1)
            simulator_completed.set()
        
        # 启动模拟器线程
        sim_thread = threading.Thread(target=simulate_user_input)
        sim_thread.start()
        
        # 调用 MCP 工具
        async with Client(mcp) as client:
            result = await client.call_tool("collect_user_intent", {"question": test_question})
        
        sim_thread.join(timeout=5)
        
        # 验证结果
        text_content = self._extract_text(result)
        assert test_answer in text_content
        assert simulator_completed.is_set()
    
    @pytest.mark.asyncio
    async def test_database_persistence(self):
        """测试问题被正确写入数据库"""
        test_question = f"DB Test Question {uuid.uuid4()}"
        
        def simulate_quick_reply():
            """快速回复以避免长时间等待"""
            for _ in range(30):
                if state.current_question == test_question:
                    time.sleep(0.1)
                    state.user_answer = "Quick reply"
                    state.answer_event.set()
                    return
                time.sleep(0.1)
        
        sim_thread = threading.Thread(target=simulate_quick_reply)
        sim_thread.start()
        
        async with Client(mcp) as client:
            await client.call_tool("collect_user_intent", {"question": test_question})
        
        sim_thread.join(timeout=5)
        
        # 验证数据库状态（回复后记录应该被清理）
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM intent_queue WHERE question = ? AND status = 'PENDING'",
                (test_question,)
            )
            count = cursor.fetchone()[0]
            # 使用状态钩子回复的请求会被删除
            assert count == 0
    
    @pytest.mark.asyncio
    async def test_web_mode_database_flow(self):
        """测试通过数据库（Web 模式）的完整流程"""
        test_question = f"Web Mode Question {uuid.uuid4()}"
        test_answer = "Web Mode Answer"
        
        request_id_holder = {"id": None}
        
        def simulate_web_reply():
            """模拟通过数据库的 Web 回复"""
            for _ in range(50):
                with sqlite3.connect(DB_PATH) as conn:
                    cursor = conn.execute(
                        "SELECT id FROM intent_queue WHERE question = ? AND status = 'PENDING'",
                        (test_question,)
                    )
                    row = cursor.fetchone()
                    if row:
                        request_id = row[0]
                        request_id_holder["id"] = request_id
                        time.sleep(0.2)
                        # 更新数据库回复
                        conn.execute(
                            "UPDATE intent_queue SET answer = ?, status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                            (test_answer, request_id)
                        )
                        return
                time.sleep(0.1)
        
        sim_thread = threading.Thread(target=simulate_web_reply)
        sim_thread.start()
        
        async with Client(mcp) as client:
            result = await client.call_tool("collect_user_intent", {"question": test_question})
        
        sim_thread.join(timeout=10)
        
        # 验证结果
        text_content = self._extract_text(result)
        assert test_answer in text_content
        
        # 验证历史记录保留（COMPLETED 状态的记录应该保留）
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute(
                "SELECT status FROM intent_queue WHERE id = ?",
                (request_id_holder["id"],)
            )
            row = cursor.fetchone()
            if row:
                assert row[0] == "COMPLETED"
    
    @pytest.mark.asyncio
    async def test_dismiss_functionality(self):
        """测试 dismiss（忽略）功能"""
        test_question = f"Dismiss Test Question {uuid.uuid4()}"
        
        def simulate_dismiss():
            """模拟用户忽略请求"""
            for _ in range(50):
                with sqlite3.connect(DB_PATH) as conn:
                    cursor = conn.execute(
                        "SELECT id FROM intent_queue WHERE question = ? AND status = 'PENDING'",
                        (test_question,)
                    )
                    row = cursor.fetchone()
                    if row:
                        request_id = row[0]
                        time.sleep(0.2)
                        # 设置为 DISMISSED 状态
                        conn.execute(
                            "UPDATE intent_queue SET status = 'DISMISSED' WHERE id = ?",
                            (request_id,)
                        )
                        return
                time.sleep(0.1)
        
        sim_thread = threading.Thread(target=simulate_dismiss)
        sim_thread.start()
        
        async with Client(mcp) as client:
            result = await client.call_tool("collect_user_intent", {"question": test_question})
        
        sim_thread.join(timeout=10)
        
        # 验证结果包含 dismiss 消息
        text_content = self._extract_text(result)
        assert "dismissed" in text_content.lower()
    
    @pytest.mark.asyncio
    async def test_image_response(self):
        """测试图片响应"""
        test_question = f"Image Test Question {uuid.uuid4()}"
        test_answer = "Answer with image"
        
        # 创建一个简单的 1x1 像素 PNG 图片
        png_1x1 = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        image_data = f"data:image/png;base64,{base64.b64encode(png_1x1).decode()}"
        
        def simulate_image_reply():
            """模拟带图片的回复"""
            for _ in range(50):
                with sqlite3.connect(DB_PATH) as conn:
                    cursor = conn.execute(
                        "SELECT id FROM intent_queue WHERE question = ? AND status = 'PENDING'",
                        (test_question,)
                    )
                    row = cursor.fetchone()
                    if row:
                        request_id = row[0]
                        time.sleep(0.2)
                        conn.execute(
                            "UPDATE intent_queue SET answer = ?, image = ?, status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                            (test_answer, image_data, request_id)
                        )
                        return
                time.sleep(0.1)
        
        sim_thread = threading.Thread(target=simulate_image_reply)
        sim_thread.start()
        
        async with Client(mcp) as client:
            result = await client.call_tool("collect_user_intent", {"question": test_question})
        
        sim_thread.join(timeout=10)
        
        # 验证结果 - 应该返回文本和图片
        assert result.content is not None
        assert len(result.content) >= 1
        
        # 检查是否包含文本
        text_content = self._extract_text(result)
        assert test_answer in text_content
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """测试并发请求处理"""
        questions = [f"Concurrent Q{i} {uuid.uuid4()}" for i in range(3)]
        answers = [f"Concurrent A{i}" for i in range(3)]
        results = []
        
        def simulate_reply_for_question(q, a):
            """为特定问题模拟回复"""
            for _ in range(100):
                with sqlite3.connect(DB_PATH) as conn:
                    cursor = conn.execute(
                        "SELECT id FROM intent_queue WHERE question = ? AND status = 'PENDING'",
                        (q,)
                    )
                    row = cursor.fetchone()
                    if row:
                        request_id = row[0]
                        time.sleep(0.1)
                        conn.execute(
                            "UPDATE intent_queue SET answer = ?, status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                            (a, request_id)
                        )
                        return
                time.sleep(0.05)
        
        async def call_tool_for_question(q, a):
            sim_thread = threading.Thread(target=simulate_reply_for_question, args=(q, a))
            sim_thread.start()
            
            async with Client(mcp) as client:
                result = await client.call_tool("collect_user_intent", {"question": q})
            
            sim_thread.join(timeout=15)
            return result
        
        # 并发执行多个请求
        tasks = [call_tool_for_question(q, a) for q, a in zip(questions, answers)]
        results = await asyncio.gather(*tasks)
        
        # 验证所有结果
        for i, result in enumerate(results):
            text_content = self._extract_text(result)
            assert answers[i] in text_content, f"Expected answer {answers[i]} in result {i}"
    
    @pytest.mark.asyncio
    async def test_mcp_tool_metadata(self):
        """测试 MCP 工具元数据（工具列表）"""
        async with Client(mcp) as client:
            tools = await client.list_tools()
        
        # 验证 collect_user_intent 工具存在
        tool_names = [tool.name for tool in tools]
        assert "collect_user_intent" in tool_names
        
        # 验证工具描述
        for tool in tools:
            if tool.name == "collect_user_intent":
                assert tool.description is not None
                assert len(tool.description) > 0
                # 验证参数
                assert "question" in str(tool.inputSchema)
    
    @pytest.mark.asyncio
    async def test_empty_question(self):
        """测试空问题"""
        def simulate_quick_reply():
            for _ in range(30):
                if state.current_question == "":
                    time.sleep(0.1)
                    state.user_answer = "Reply to empty"
                    state.answer_event.set()
                    return
                time.sleep(0.1)
        
        sim_thread = threading.Thread(target=simulate_quick_reply)
        sim_thread.start()
        
        async with Client(mcp) as client:
            result = await client.call_tool("collect_user_intent", {"question": ""})
        
        sim_thread.join(timeout=5)
        
        # 空问题应该也能正常处理
        text_content = self._extract_text(result)
        assert text_content is not None
    
    @pytest.mark.asyncio
    async def test_long_question(self):
        """测试长问题文本"""
        long_question = "A" * 5000 + f" {uuid.uuid4()}"
        test_answer = "Reply to long question"
        
        def simulate_reply():
            for _ in range(50):
                if state.current_question and len(state.current_question) > 4000:
                    time.sleep(0.2)
                    state.user_answer = test_answer
                    state.answer_event.set()
                    return
                time.sleep(0.1)
        
        sim_thread = threading.Thread(target=simulate_reply)
        sim_thread.start()
        
        async with Client(mcp) as client:
            result = await client.call_tool("collect_user_intent", {"question": long_question})
        
        sim_thread.join(timeout=10)
        
        text_content = self._extract_text(result)
        assert test_answer in text_content
    
    @pytest.mark.asyncio
    async def test_special_characters_in_question(self):
        """测试问题中的特殊字符"""
        special_question = f"问题包含特殊字符: <>\"'&%$#@! 🎉 中文 {uuid.uuid4()}"
        test_answer = "回复特殊字符问题"
        
        def simulate_reply():
            for _ in range(50):
                if state.current_question and "🎉" in state.current_question:
                    time.sleep(0.2)
                    state.user_answer = test_answer
                    state.answer_event.set()
                    return
                time.sleep(0.1)
        
        sim_thread = threading.Thread(target=simulate_reply)
        sim_thread.start()
        
        async with Client(mcp) as client:
            result = await client.call_tool("collect_user_intent", {"question": special_question})
        
        sim_thread.join(timeout=10)
        
        text_content = self._extract_text(result)
        assert test_answer in text_content
    
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


class TestMCPServerInfo:
    """测试 MCP 服务器信息"""
    
    @pytest.mark.asyncio
    async def test_server_name(self):
        """测试服务器名称"""
        # FastMCP 的 name 属性
        assert mcp.name == "User Intent Bridge"
    
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """测试列出工具"""
        async with Client(mcp) as client:
            tools = await client.list_tools()
        
        assert len(tools) >= 1
        tool_names = [t.name for t in tools]
        assert "collect_user_intent" in tool_names
    
    @pytest.mark.asyncio
    async def test_tool_schema(self):
        """测试工具的输入 schema"""
        async with Client(mcp) as client:
            tools = await client.list_tools()
        
        for tool in tools:
            if tool.name == "collect_user_intent":
                schema = tool.inputSchema
                assert "properties" in schema
                assert "question" in schema["properties"]
                assert schema["properties"]["question"]["type"] == "string"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
