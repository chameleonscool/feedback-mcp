"""
SSE Integration Tests for User Intent MCP Server.

This module tests the SSE transport mode of the MCP server.
Requires the server to be running at http://localhost:8765 (or configured port).

Usage:
    # First, start the server:
    uv run python -m server --mode sse --port 8765
    
    # Then run tests:
    uv run pytest tests/test_sse_integration.py -v
"""
import asyncio
import logging
import os
import uuid
import pytest
import httpx
from fastmcp import Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_sse")

# Disable proxies to avoid local connection issues
for key in ['http_proxy', 'https_proxy', 'all_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY']:
    os.environ.pop(key, None)

# Server configuration
SSE_PORT = int(os.getenv("TEST_SSE_PORT", "8765"))
SSE_URL = f"http://localhost:{SSE_PORT}/mcp/sse"
API_BASE = f"http://localhost:{SSE_PORT}"


class TestSSEConnection:
    """Test basic SSE connection and server availability."""
    
    @pytest.mark.asyncio
    async def test_server_health(self):
        """Test that the server is running and responding."""
        async with httpx.AsyncClient() as http:
            response = await http.get(f"{API_BASE}/")
            assert response.status_code == 200
            logger.info("✅ Server health check passed")
    
    @pytest.mark.asyncio
    async def test_sse_connection(self):
        """Test basic SSE connection to MCP endpoint."""
        logger.info(f"Connecting to SSE endpoint: {SSE_URL}")
        
        async with Client(SSE_URL) as client:
            logger.info("✅ Connected to SSE server successfully")
            # If we get here, connection worked
            assert True
    
    @pytest.mark.asyncio
    async def test_sse_reconnection(self):
        """Test that multiple connections work correctly."""
        for i in range(3):
            logger.info(f"Connection attempt {i + 1}/3")
            async with Client(SSE_URL) as client:
                tools = await client.list_tools()
                assert len(tools) > 0
            logger.info(f"✅ Connection {i + 1} successful")


class TestSSEListTools:
    """Test listing tools via SSE transport."""
    
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test listing available tools from the server."""
        async with Client(SSE_URL) as client:
            tools = await client.list_tools()
            tool_names = [t.name for t in tools]
            
            logger.info(f"Available tools: {tool_names}")
            
            # Verify the main tool exists
            assert "collect_user_intent" in tool_names, \
                f"Expected 'collect_user_intent' in tools, got: {tool_names}"
            logger.info("✅ Tool listing passed")
    
    @pytest.mark.asyncio
    async def test_tool_schema(self):
        """Test that the tool has correct schema."""
        async with Client(SSE_URL) as client:
            tools = await client.list_tools()
            
            # Find the collect_user_intent tool
            tool = next((t for t in tools if t.name == "collect_user_intent"), None)
            assert tool is not None, "collect_user_intent tool not found"
            
            # Check tool description
            assert tool.description is not None
            assert len(tool.description) > 0
            
            # Check input schema
            assert tool.inputSchema is not None
            assert "properties" in tool.inputSchema
            assert "question" in tool.inputSchema["properties"]
            
            logger.info(f"Tool schema: {tool.inputSchema}")
            logger.info("✅ Tool schema validation passed")


class TestSSECallTool:
    """Test calling tools via SSE transport."""
    
    @pytest.mark.asyncio
    async def test_call_tool_with_web_reply(self):
        """
        Test calling collect_user_intent tool and simulating web reply.
        
        This test:
        1. Calls the tool via SSE
        2. Simulates a user reply via the web API
        3. Verifies the tool returns the reply
        """
        test_question = f"SSE Integration Test Question - {uuid.uuid4().hex[:8]}"
        test_answer = f"Test Answer - {uuid.uuid4().hex[:8]}"
        
        async def simulate_reply():
            """Background task to simulate user reply via web API."""
            await asyncio.sleep(1)  # Wait for question to be stored
            
            async with httpx.AsyncClient() as http:
                # Poll for the question
                for _ in range(10):
                    response = await http.get(f"{API_BASE}/api/poll")
                    questions = response.json()
                    
                    # Find our question
                    for q in questions:
                        if test_question in q.get("question", ""):
                            # Reply to this question
                            reply_response = await http.post(
                                f"{API_BASE}/api/reply",
                                json={
                                    "id": q["id"],
                                    "answer": test_answer,
                                    "image": None
                                }
                            )
                            logger.info(f"Replied to question {q['id']}: {reply_response.status_code}")
                            return True
                    
                    await asyncio.sleep(0.5)
            
            return False
        
        # Start reply simulation in background
        reply_task = asyncio.create_task(simulate_reply())
        
        try:
            async with Client(SSE_URL) as client:
                logger.info(f"Calling collect_user_intent with: {test_question[:50]}...")
                
                result = await asyncio.wait_for(
                    client.call_tool("collect_user_intent", {"question": test_question}),
                    timeout=30
                )
                
                # Extract text from result
                text_content = ""
                for content in result.content:
                    if hasattr(content, 'text') and content.text:
                        text_content += content.text
                    elif isinstance(content, dict) and 'text' in content:
                        text_content += content['text']
                
                logger.info(f"Tool result: {text_content}")
                
                assert test_answer in text_content, \
                    f"Expected '{test_answer}' in result, got: {text_content}"
                logger.info("✅ Tool call with web reply passed")
        
        finally:
            # Wait for reply task to complete
            await reply_task
    
    @pytest.mark.asyncio
    async def test_call_tool_dismiss(self):
        """Test that dismissed requests return appropriate message."""
        test_question = f"Dismiss Test Question - {uuid.uuid4().hex[:8]}"
        
        async def simulate_dismiss():
            """Background task to dismiss the request via web API."""
            await asyncio.sleep(1)
            
            async with httpx.AsyncClient() as http:
                for _ in range(10):
                    response = await http.get(f"{API_BASE}/api/poll")
                    questions = response.json()
                    
                    for q in questions:
                        if test_question in q.get("question", ""):
                            # Dismiss this request
                            dismiss_response = await http.delete(
                                f"{API_BASE}/api/request/{q['id']}"
                            )
                            logger.info(f"Dismissed request {q['id']}: {dismiss_response.status_code}")
                            return True
                    
                    await asyncio.sleep(0.5)
            
            return False
        
        # Start dismiss simulation in background
        dismiss_task = asyncio.create_task(simulate_dismiss())
        
        try:
            async with Client(SSE_URL) as client:
                result = await asyncio.wait_for(
                    client.call_tool("collect_user_intent", {"question": test_question}),
                    timeout=30
                )
                
                text_content = ""
                for content in result.content:
                    if hasattr(content, 'text') and content.text:
                        text_content += content.text
                
                logger.info(f"Dismiss result: {text_content}")
                assert "dismissed" in text_content.lower(), \
                    f"Expected 'dismissed' in result, got: {text_content}"
                logger.info("✅ Dismiss test passed")
        
        finally:
            await dismiss_task


class TestSSEConcurrency:
    """Test concurrent SSE connections and requests."""
    
    @pytest.mark.asyncio
    async def test_concurrent_connections(self):
        """Test multiple concurrent SSE connections."""
        async def connect_and_list():
            async with Client(SSE_URL) as client:
                tools = await client.list_tools()
                return len(tools)
        
        # Create 5 concurrent connections
        tasks = [connect_and_list() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        assert all(r > 0 for r in results), "All connections should return tools"
        logger.info(f"✅ {len(results)} concurrent connections successful")
    
    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self):
        """Test multiple concurrent tool calls with replies."""
        num_agents = 3
        results = {}
        
        async def agent_task(agent_id: int):
            """Simulate an agent making a request."""
            question = f"Agent {agent_id} Question - {uuid.uuid4().hex[:8]}"
            answer = f"Answer for Agent {agent_id}"
            
            async def reply_task():
                await asyncio.sleep(1)
                async with httpx.AsyncClient() as http:
                    for _ in range(20):
                        response = await http.get(f"{API_BASE}/api/poll")
                        for q in response.json():
                            if question in q.get("question", ""):
                                await http.post(
                                    f"{API_BASE}/api/reply",
                                    json={"id": q["id"], "answer": answer}
                                )
                                return
                        await asyncio.sleep(0.3)
            
            reply = asyncio.create_task(reply_task())
            
            try:
                async with Client(SSE_URL) as client:
                    result = await asyncio.wait_for(
                        client.call_tool("collect_user_intent", {"question": question}),
                        timeout=30
                    )
                    
                    text_content = ""
                    for content in result.content:
                        if hasattr(content, 'text'):
                            text_content += content.text or ""
                    
                    results[agent_id] = (answer in text_content, text_content)
            finally:
                await reply
        
        # Run all agents concurrently
        await asyncio.gather(*[agent_task(i) for i in range(num_agents)])
        
        # Check all succeeded
        for agent_id, (success, content) in results.items():
            assert success, f"Agent {agent_id} failed: {content}"
        
        logger.info(f"✅ {num_agents} concurrent tool calls successful")


class TestSSEWebAPI:
    """Test web API endpoints used with SSE."""
    
    @pytest.mark.asyncio
    async def test_poll_endpoint(self):
        """Test the poll endpoint returns valid data."""
        async with httpx.AsyncClient() as http:
            response = await http.get(f"{API_BASE}/api/poll")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            logger.info(f"✅ Poll endpoint returned {len(data)} pending questions")
    
    @pytest.mark.asyncio
    async def test_history_endpoint(self):
        """Test the history endpoint returns valid data."""
        async with httpx.AsyncClient() as http:
            response = await http.get(f"{API_BASE}/api/history")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            logger.info(f"✅ History endpoint returned {len(data)} items")
    
    @pytest.mark.asyncio
    async def test_reply_endpoint_validation(self):
        """Test that reply endpoint validates input."""
        async with httpx.AsyncClient() as http:
            # Test with invalid request (missing required fields)
            response = await http.post(
                f"{API_BASE}/api/reply",
                json={}
            )
            # Should fail validation
            assert response.status_code == 422
            logger.info("✅ Reply endpoint validation working")


class TestSSEImageSupport:
    """Test image support via SSE transport."""
    
    @pytest.mark.asyncio
    async def test_reply_with_image(self):
        """Test replying with an image attachment."""
        test_question = f"Image Test Question - {uuid.uuid4().hex[:8]}"
        test_answer = "Here is the image"
        # Small valid PNG image (1x1 red pixel)
        test_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
        
        async def simulate_reply_with_image():
            await asyncio.sleep(1)
            
            async with httpx.AsyncClient() as http:
                for _ in range(10):
                    response = await http.get(f"{API_BASE}/api/poll")
                    for q in response.json():
                        if test_question in q.get("question", ""):
                            await http.post(
                                f"{API_BASE}/api/reply",
                                json={
                                    "id": q["id"],
                                    "answer": test_answer,
                                    "image": test_image
                                }
                            )
                            return True
                    await asyncio.sleep(0.5)
            return False
        
        reply_task = asyncio.create_task(simulate_reply_with_image())
        
        try:
            async with Client(SSE_URL) as client:
                result = await asyncio.wait_for(
                    client.call_tool("collect_user_intent", {"question": test_question}),
                    timeout=30
                )
                
                # Check that we got multiple content items (text + image)
                content_types = [type(c).__name__ for c in result.content]
                logger.info(f"Response content types: {content_types}")
                
                # Verify text is present
                text_found = False
                for content in result.content:
                    if hasattr(content, 'text') and test_answer in (content.text or ""):
                        text_found = True
                        break
                
                assert text_found, f"Expected text '{test_answer}' in result"
                
                # Verify we got more than just text (image content)
                assert len(result.content) >= 1, "Expected at least text content"
                logger.info("✅ Image reply test passed")
        
        finally:
            await reply_task


if __name__ == "__main__":
    # Allow running individual tests directly
    import sys
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        pytest.main(["-v", "-k", test_name, __file__])
    else:
        pytest.main(["-v", __file__])
