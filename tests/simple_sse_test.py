#!/usr/bin/env python3
"""
Simple SSE Test Script - 测试 MCP SSE 连接

用法:
    uv run python tests/simple_sse_test.py
"""
import asyncio
import os
import sys

# 禁用代理
for key in ['http_proxy', 'https_proxy', 'all_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY']:
    os.environ.pop(key, None)

SSE_URL = "http://localhost:8765/mcp/sse"


async def test_connection():
    """测试基本 SSE 连接"""
    print(f"[1] 测试连接到 {SSE_URL}...")
    
    from fastmcp import Client
    
    try:
        async with Client(SSE_URL) as client:
            print("    ✅ SSE 连接成功!")
            return True
    except Exception as e:
        print(f"    ❌ SSE 连接失败: {e}")
        return False


async def test_list_tools():
    """测试列出工具"""
    print(f"\n[2] 测试列出工具...")
    
    from fastmcp import Client
    
    try:
        async with Client(SSE_URL) as client:
            tools = await client.list_tools()
            print(f"    工具列表: {[t.name for t in tools]}")
            
            if "collect_user_intent" in [t.name for t in tools]:
                print("    ✅ 找到 collect_user_intent 工具!")
                return True
            else:
                print("    ❌ 未找到 collect_user_intent 工具!")
                return False
    except Exception as e:
        print(f"    ❌ 列出工具失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_call_tool_with_simulated_reply():
    """测试调用工具（带模拟回复）"""
    print(f"\n[3] 测试调用工具（带模拟回复）...")
    
    import httpx
    import uuid
    from fastmcp import Client
    
    test_question = f"测试问题 - {uuid.uuid4().hex[:8]}"
    test_answer = f"测试回复 - {uuid.uuid4().hex[:8]}"
    
    async def simulate_reply():
        """后台模拟用户通过 Web API 回复"""
        await asyncio.sleep(1)  # 等待问题被存储
        
        async with httpx.AsyncClient() as http:
            for i in range(20):
                try:
                    response = await http.get("http://localhost:8765/api/poll")
                    questions = response.json()
                    print(f"    [模拟器] 第{i+1}次轮询, 找到 {len(questions)} 个待处理问题")
                    
                    for q in questions:
                        if test_question in q.get("question", ""):
                            print(f"    [模拟器] 找到测试问题, 回复中...")
                            await http.post(
                                "http://localhost:8765/api/reply",
                                json={"id": q["id"], "answer": test_answer}
                            )
                            print(f"    [模拟器] ✅ 回复已发送!")
                            return True
                except Exception as e:
                    print(f"    [模拟器] 轮询错误: {e}")
                
                await asyncio.sleep(0.5)
        
        print("    [模拟器] ❌ 超时未找到问题")
        return False
    
    # 启动模拟回复任务
    reply_task = asyncio.create_task(simulate_reply())
    
    try:
        async with Client(SSE_URL) as client:
            print(f"    调用 collect_user_intent: {test_question[:30]}...")
            
            result = await asyncio.wait_for(
                client.call_tool("collect_user_intent", {"question": test_question}),
                timeout=30
            )
            
            # 提取文本内容
            text_content = ""
            for content in result.content:
                if hasattr(content, 'text') and content.text:
                    text_content += content.text
            
            print(f"    收到结果: {text_content[:100]}...")
            
            if test_answer in text_content:
                print("    ✅ 工具调用成功，收到正确回复!")
                return True
            else:
                print(f"    ❌ 回复内容不匹配! 期望包含: {test_answer}")
                return False
                
    except asyncio.TimeoutError:
        print("    ❌ 工具调用超时!")
        return False
    except Exception as e:
        print(f"    ❌ 工具调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await reply_task


async def test_web_api():
    """测试 Web API 是否正常"""
    print(f"\n[0] 测试 Web API 连通性...")
    
    import httpx
    
    try:
        async with httpx.AsyncClient() as http:
            # 测试首页
            response = await http.get("http://localhost:8765/")
            if response.status_code == 200:
                print("    ✅ Web UI 可访问")
            else:
                print(f"    ❌ Web UI 返回状态码: {response.status_code}")
                return False
            
            # 测试 poll API
            response = await http.get("http://localhost:8765/api/poll")
            if response.status_code == 200:
                print(f"    ✅ Poll API 可访问, 当前待处理: {len(response.json())} 个")
            else:
                print(f"    ❌ Poll API 返回状态码: {response.status_code}")
                return False
            
            return True
    except Exception as e:
        print(f"    ❌ Web API 连接失败: {e}")
        return False


async def main():
    print("=" * 60)
    print("简单 SSE 测试脚本")
    print("=" * 60)
    
    results = {}
    
    # 测试 Web API
    results["web_api"] = await test_web_api()
    
    if not results["web_api"]:
        print("\n⚠️ Web API 不可用，无法继续测试")
        return
    
    # 测试 SSE 连接
    results["connection"] = await test_connection()
    
    if not results["connection"]:
        print("\n⚠️ SSE 连接失败，无法继续测试")
        return
    
    # 测试列出工具
    results["list_tools"] = await test_list_tools()
    
    # 测试调用工具
    results["call_tool"] = await test_call_tool_with_simulated_reply()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试结果总结:")
    print("=" * 60)
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
    
    all_passed = all(results.values())
    print("\n" + ("🎉 所有测试通过!" if all_passed else "⚠️ 部分测试失败"))
    
    return all_passed


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n测试被中断")
        sys.exit(130)
