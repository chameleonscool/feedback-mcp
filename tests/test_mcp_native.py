import asyncio
import pytest
from fastmcp import Client
from core import mcp, state

# Using pytest-asyncio for async tests
# If not installed, we can run with standard asyncio.run() block

async def test_ask_user_tool():
    """
    Demonstrates testing the MCP tool in isolation using FastMCP's Client.
    Note: 'ask_user' blocks, so we need to simulate the answer mechanism
    even in this unit test.
    """
    print("\n--- Starting Native MCP Test ---")
    
    # We need to simulate the user reply in a background task
    # because 'ask_user' will block the current flow.
    async def simulate_user_input():
        print("[Simulator] Waiting for question to be set...")
        # Wait for the tool to set the question
        for i in range(20):
            print(f"[Simulator] Check {i}: state.current_question={state.current_question}")
            if state.current_question:
                print(f"[Simulator] Question detected: {state.current_question}")
                # Simulate answering
                await asyncio.sleep(0.5)
                state.user_answer = "Native Test Reply"
                state.answer_event.set()
                print("[Simulator] Answer event SET")
                return
            await asyncio.sleep(1.0)
        print("[Simulator] Timeout waiting for question!")

    # Connect to the MCP server object directly (In-Memory)
    async with Client(mcp) as client:
        # Start simulator
        task = asyncio.create_task(simulate_user_input())
        
        # Call the tool
        print("[Client] Calling ask_user...")
        result = await client.call_tool("ask_user", {"question": "Unit Test Question?", "timeout": 5})
        
    # Verify
    await task
    print(f"[Client] Result: {result}")
    print(f"[Client] Result Type: {type(result)}")
    if hasattr(result, 'content'):
        print(f"[Client] Content Type: {type(result.content)}")
        for i, c in enumerate(result.content):
            print(f"[Client] Content[{i}] Type: {type(c)}")
            print(f"[Client] Content[{i}] Dir: {dir(c)}")
    
    # FastMCP Client returns a CallToolResult which has a 'content' attribute (list of content blocks)
    text_content = ""
    for content in result.content:
        # FastMCP content blocks can be dict-like or have attributes
        if hasattr(content, 'text') and content.text:
            text_content += content.text
        elif isinstance(content, dict) and 'text' in content:
            text_content += content['text']
        else:
            # Fallback to string representation if it's a TextContent object but doesn't have .text
            text_content += str(content)
    
    print(f"[Client] Extracted Text: '{text_content}'")
    assert "Native Test Reply" in text_content
    print("--- Native MCP Test PASSED ---")

if __name__ == "__main__":
    asyncio.run(test_ask_user_tool())
