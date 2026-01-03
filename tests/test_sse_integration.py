import asyncio
import logging
import sys
import os
import pytest
from fastmcp import Client

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_sse")

@pytest.mark.asyncio
async def test_sse_integration():
    """
    Tests the SSE connection to the running Feedback MCP server.
    Assumes server is running at http://localhost:8000
    """
    # The URL we configured in main.py
    sse_url = "http://localhost:8000/mcp/sse"
    
    # Disable proxies to avoid local connection issues
    for key in ['http_proxy', 'https_proxy', 'all_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY']:
        os.environ.pop(key, None)
    
    logger.info(f"Connecting to SSE endpoint: {sse_url}")
    
    try:
        # FastMCP Client automatically handles SSE transport if hinted or configured
        async with Client(sse_url) as client:
            logger.info("✅ Connected to SSE server")
            
            # 1. List Tools
            logger.info("Listing tools...")
            tools = await client.list_tools()
            tool_names = [t.name for t in tools]
            logger.info(f"Available tools: {tool_names}")
            
            if "ask_user" not in tool_names:
                logger.error("❌ 'ask_user' tool not found!")
                sys.exit(1)
            else:
                logger.info("✅ Found 'ask_user' tool")
                
            # 2. Call Tool (Longer Timeout for Browser Interaction)
            logger.info("Calling 'ask_user' with timeout (30s)...")
            result = await client.call_tool("ask_user", {"question": "Browser Integration Test Question", "timeout": 30})
            
            logger.info(f"Tool Result: {result}")
            
            # Check if we got a timeout reply (which means the tool ran successfully logic-wise)
            if "Timed out" in str(result) or "User replied" in str(result):
                logger.info("✅ Tool invocation successful (received expected response)")
            else:
                logger.warning(f"⚠️ Unexpected result content: {result}")

    except Exception as e:
        logger.error(f"❌ Test Failed: {e}")
        # Print detailed helper in case of connection refused
        if "Connection refused" in str(e):
            logger.info("Hint: Is the 'feedback_mcp/main.py' server running?")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(test_sse_integration())
    except KeyboardInterrupt:
        pass
