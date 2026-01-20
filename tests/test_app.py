import asyncio
import threading
import time
import pytest
from fastapi.testclient import TestClient
from web import app
from core import state, collect_user_intent

client = TestClient(app)

# Sample Markdown content for testing
MARKDOWN_QUESTION = """## Task Summary

I have completed the following work:

### 1. Code Changes
- ✅ Added new feature
- ✅ Fixed bug in `core.py`
- ⏳ Pending review

### 2. Code Example
```python
def hello():
    return "Hello, World!"
```

> Please review and provide feedback.

| Item | Status |
|------|--------|
| Tests | Passed |
| Lint | OK |
"""


def user_reply_simulator():
    """Simulates a user replying via the Web UI after a delay."""
    print("[Simulator] Waiting for question...")
    time.sleep(2)
    
    # 1. Poll for question
    response = client.get("/api/poll")
    tasks = response.json()
    print(f"[Simulator] Polled: {tasks}")
    
    if len(tasks) > 0:
        # 2. Submit Reply
        task = tasks[0]
        print(f"[Simulator] Submitting reply for task {task['id']}...")
        reply_response = client.post("/api/reply", json={
            "id": task["id"],
            "answer": "I totally agree!"
        })
        print(f"[Simulator] Reply status: {reply_response.json()}")

@pytest.mark.asyncio
async def test_ask_user_flow():
    print("--- Starting Test Flow ---")
    
    # Start the user simulator in a separate thread
    sim_thread = threading.Thread(target=user_reply_simulator)
    sim_thread.start()
    
    # Call the blocking function directly
    print("[Agent] Asking question (blocking)...")
    from core import collect_user_intent
    # collect_user_intent is decorated with @mcp.tool, making it a FunctionTool object
    # Its underlying function is .fn, which is a regular sync function (not async)
    # FastMCP handles the execution. We need to access .fn to call the original function.
    loop = asyncio.get_event_loop()
    if hasattr(collect_user_intent, "fn"):
        # The tool function itself is sync but performs blocking polling
        answer = await loop.run_in_executor(None, collect_user_intent.fn, "Do you like Python?")
    else:
        # Fallback: if for some reason .fn doesn't exist, try calling directly
        answer = await loop.run_in_executor(None, collect_user_intent, "Do you like Python?")
    print(f"[Agent] Key returned: {answer}")
    
    sim_thread.join()
    
    assert "I totally agree!" in answer
    print("--- Test PASSED ---")


def user_reply_simulator_markdown():
    """Simulates a user replying to a Markdown question."""
    print("[Markdown Simulator] Waiting for question...")
    time.sleep(2)
    
    # 1. Poll for question
    response = client.get("/api/poll")
    tasks = response.json()
    print(f"[Markdown Simulator] Polled: {tasks}")
    
    if len(tasks) > 0:
        task = tasks[0]
        # Verify the Markdown content is preserved
        assert "## Task Summary" in task["question"]
        assert "```python" in task["question"]
        assert "| Item | Status |" in task["question"]
        print(f"[Markdown Simulator] Markdown content verified!")
        
        # Submit Reply
        reply_response = client.post("/api/reply", json={
            "id": task["id"],
            "answer": "Markdown looks good!"
        })
        print(f"[Markdown Simulator] Reply status: {reply_response.json()}")


@pytest.mark.asyncio
async def test_markdown_question_flow():
    """Test that Markdown formatted questions are correctly stored and retrieved."""
    print("--- Starting Markdown Test Flow ---")
    
    # Start the user simulator in a separate thread
    sim_thread = threading.Thread(target=user_reply_simulator_markdown)
    sim_thread.start()
    
    # Call the blocking function with Markdown content
    print("[Agent] Asking Markdown question (blocking)...")
    from core import collect_user_intent
    
    loop = asyncio.get_event_loop()
    if hasattr(collect_user_intent, "fn"):
        answer = await loop.run_in_executor(None, collect_user_intent.fn, MARKDOWN_QUESTION)
    else:
        # Fallback: if for some reason .fn doesn't exist, try calling directly
        answer = await loop.run_in_executor(None, collect_user_intent, MARKDOWN_QUESTION)
    print(f"[Agent] Answer returned: {answer}")
    
    sim_thread.join()
    
    assert "Markdown looks good!" in answer
    print("--- Markdown Test PASSED ---")


if __name__ == "__main__":
    asyncio.run(test_ask_user_flow())
