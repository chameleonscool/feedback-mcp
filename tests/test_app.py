import asyncio
import threading
import time
from fastapi.testclient import TestClient
from web import app
from core import state, ask_user

client = TestClient(app)

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

async def test_ask_user_flow():
    print("--- Starting Test Flow ---")
    
    # Start the user simulator in a separate thread
    sim_thread = threading.Thread(target=user_reply_simulator)
    sim_thread.start()
    
    # Call the blocking function directly
    print("[Agent] Asking question (blocking)...")
    from core import ask_user
    # ask_user is decorated with @mcp.tool, making it a FunctionTool object
    # Its underlying function is .fn, which is a regular sync function (not async)
    # FastMCP handles the execution. Here we should call it as a regular function.
    if hasattr(ask_user, "fn"):
        # The tool function itself is sync but performs blocking polling
        loop = asyncio.get_event_loop()
        answer = await loop.run_in_executor(None, ask_user.fn, "Do you like Python?", 10)
    else:
        answer = ask_user("Do you like Python?", timeout=10)
    print(f"[Agent] Key returned: {answer}")
    
    sim_thread.join()
    
    assert "I totally agree!" in answer
    print("--- Test PASSED ---")

if __name__ == "__main__":
    asyncio.run(test_ask_user_flow())
