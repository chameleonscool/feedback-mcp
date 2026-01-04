import asyncio
from fastmcp import Client
from core import mcp

# Sample Markdown question for integration testing
MARKDOWN_QUESTION = """## Integration Test Report

I have completed the following work:

### 1. Feature Implementation
- ✅ Added user authentication
- ✅ Implemented API endpoints
- ⏳ Documentation pending

### 2. Code Sample
```python
@app.route('/api/users')
def get_users():
    return jsonify(users)
```

### 3. Test Results

| Test Suite | Status | Coverage |
|------------|--------|----------|
| Unit Tests | ✅ Pass | 85% |
| Integration | ✅ Pass | 72% |
| E2E | ⏳ Pending | - |

> Please review the implementation and provide your feedback.

**Next Steps:**
1. Complete documentation
2. Run E2E tests
3. Deploy to staging
"""


async def run_agent():
    print("--- Integration Agent Starting ---")
    # We essentially use In-Memory client connecting to the 'mcp' object.
    # Because 'mcp' object in main.py now uses SQLite, 
    # THIS instance of 'mcp' (imported here) will connect to the SAME SQLite DB file.
    # So they share state via DB.
    
    async with Client(mcp) as client:
        print("[Agent] Sending Markdown question...")
        result = await client.call_tool("ask_user", {"question": MARKDOWN_QUESTION, "timeout": 30})
        print(f"[Agent] Workflow Completed. Result: {result}")
        
if __name__ == "__main__":
    asyncio.run(run_agent())
