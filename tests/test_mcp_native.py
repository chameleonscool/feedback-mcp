import asyncio
import threading
import time
import pytest
from fastmcp import Client
from core import mcp, state

# Using pytest-asyncio for async tests
# If not installed, we can run with standard asyncio.run() block

@pytest.mark.asyncio
async def test_collect_user_intent_tool():
    """
    Demonstrates testing the MCP tool in isolation using FastMCP's Client.
    Note: 'collect_user_intent' blocks, so we need to simulate the answer mechanism
    even in this unit test.
    """
    print("\n--- Starting Native MCP Test ---")
    
    # Reset state before test to avoid interference from other tests
    state.current_question = None
    state.user_answer = None
    state.answer_event.clear()
    
    # Track if simulator completed successfully
    simulator_completed = threading.Event()
    
    # We need to simulate the user reply in a background THREAD
    # because the ask_user tool may run in a thread pool executor
    # and we need proper thread synchronization
    def simulate_user_input_thread():
        print("[Simulator Thread] Waiting for question to be set...")
        # Wait for the tool to set the question
        for i in range(50):
            print(f"[Simulator Thread] Check {i}: state.current_question={state.current_question}")
            if state.current_question == "Unit Test Question?":
                print(f"[Simulator Thread] Question detected: {state.current_question}")
                # Wait for the tool to call answer_event.clear() and start polling
                # The tool sequence is: set current_question -> set user_answer=None -> clear event -> poll
                # We need to wait until after clear() before setting
                time.sleep(0.5)  # Brief wait for clear() to execute
                state.user_answer = "Native Test Reply"
                state.answer_event.set()
                print("[Simulator Thread] Answer event SET")
                simulator_completed.set()
                return
            time.sleep(0.2)  # Check frequently
        print("[Simulator Thread] Timeout waiting for question!")
        simulator_completed.set()

    # Start the simulator thread before calling the tool
    sim_thread = threading.Thread(target=simulate_user_input_thread)
    sim_thread.start()
    
    # Connect to the MCP server object directly (In-Memory)
    async with Client(mcp) as client:
        # Call the tool - timeout is controlled by USERINTENT_TIMEOUT env var, not a parameter
        print("[Client] Calling collect_user_intent...")
        result = await client.call_tool("collect_user_intent", {"question": "Unit Test Question?"})
    
    # Wait for simulator thread to complete
    sim_thread.join(timeout=5)
        
    # Verify
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
    asyncio.run(test_collect_user_intent_tool())
