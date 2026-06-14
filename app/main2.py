"""
main.py
Day 2 验证入口 —— 分别用同步和异步客户端请求 httpbin，打印结果。
"""

import asyncio
import time

from app.api_client import APIError, SyncAPIClient, AsyncAPIClient

# httpbin.org 是免费的 HTTP 测试服务，不需要 API Key
HTTPBIN = "https://httpbin.org"


def sync_demo() -> None:
    """同步请求演示：GET 取 JSON，POST 发自定义 Body。"""
    print("=" * 50)
    print("同步客户端演示")
    print("=" * 50)

    client = SyncAPIClient(base_url=HTTPBIN)

    try:
        # 1. GET 请求：httpbin.org/json 返回一个示例 JSON
        data = client.get_json("/json")
        print(f"GET 返回的 keys: {list(data.keys())}")

        # 2. POST 请求：发送自定义 Body，httpbin 会原样回显
        echo = client.post_json(
            "/post",
            body={"message": "你好，这是 Day 2 的测试数据"},
        )
        print(f"POST 回显的 json 字段: {echo.get('json')}")

    except APIError as exc:
        print(f"同步请求失败: {exc}")
        if exc.status_code:
            print(f"  HTTP 状态码: {exc.status_code}")
    finally:
        client.close()


async def async_demo() -> None:
    """异步请求演示：和同步版本功能一致，用 async with 管理生命周期。"""
    print()
    print("=" * 50)
    print("异步客户端演示")
    print("=" * 50)

    async with AsyncAPIClient(base_url=HTTPBIN) as client:
        try:
            # 1. 异步 GET
            data = await client.get_json("/json")
            print(f"ASYNC GET 返回的 keys: {list(data.keys())}")

            # 2. 异步 POST
            echo = await client.post_json(
                "/post",
                body={"message": "这是异步测试"}
            )
            print(f"ASYNC POST 回显的 json字段: {echo.get('json')}")

        except APIError as exc:
            print(f"异步请求失败: {exc}")
            if exc.status_code:
                print(f"  HTTP 状态码: {exc.status_code}")

async def error_demo() -> None:
    """故意触发错误的演示：请求一个不存在的路径，观察异常处理。"""
    print()
    print("=" * 50)
    print("错误处理演示（故意 404）")
    print("=" * 50)

    async with AsyncAPIClient(base_url=HTTPBIN) as client:
        try:
            # /status/404 会让 httpbin 返回 404 状态码
            await client.get_json("/status/404")
        except APIError as exc:
            print(f"捕获到预期的 APIError: {exc}")

if __name__ == "__main__":
    start_all = time.perf_counter()

    # 先跑同步演示
    sync_demo()

    # 再跑异步演示（asyncio.run 统一管理事件循环）
    asyncio.run(async_demo())
    asyncio.run(error_demo())

    total = (time.perf_counter() - start_all) * 1000
    print(f"\n全部演示完成，总耗时 {total:.0f}ms")
