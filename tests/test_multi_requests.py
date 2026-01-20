import asyncio
import sys
import os
from fastmcp import Client

# Disable proxies
for key in ['http_proxy', 'https_proxy', 'all_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY']:
    os.environ.pop(key, None)

async def agent_task(name, duration=60):
    url = "http://localhost:8000/mcp/sse"
    print(f"[{name}] Connecting...")
    async with Client(url) as client:
        print(f"[{name}] Asking question...")
        # Add random suffix to avoid dedup if any
        import random
        qid = random.randint(1000, 9999)
        answer = await client.call_tool("collect_user_intent", {"question": f"Question from Agent {name} ({qid})"})
        print(f"[{name}] Received: {answer}")

async def main():
    print("Starting multi-agent simulation...")
    # Spawn 2 agents
    task1 = asyncio.create_task(agent_task("A"))
    task2 = asyncio.create_task(agent_task("B"))
    
    await asyncio.gather(task1, task2)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
