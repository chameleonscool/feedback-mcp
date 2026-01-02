import asyncio
from fastmcp import Client
from core import mcp

async def run_agent():
    print("--- Integration Agent Starting ---")
    # We essentially use In-Memory client connecting to the 'mcp' object.
    # Because 'mcp' object in main.py now uses SQLite, 
    # THIS instance of 'mcp' (imported here) will connect to the SAME SQLite DB file.
    # So they share state via DB.
    
    async with Client(mcp) as client:
        print("[Agent] Sending question: Please upload a test image.")
        result = await client.call_tool("ask_user", {"question": "Please upload a test image.", "timeout": 30})
        print(f"[Agent] Workflow Completed. Result: {result}")
        
if __name__ == "__main__":
    asyncio.run(run_agent())
