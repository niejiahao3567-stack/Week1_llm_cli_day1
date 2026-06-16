"""
main.py
Day 4 验证入口 —— 串行 vs 并发 LLM 调用耗时对比。

运行后你会看到：
- 串行：A 等完 → B 等完 → C 等完，总耗时 ≈ A+B+C
- 并发：A/B/C 几乎同时发，总耗时 ≈ 最慢的那个

这个差距就是"为什么 Agent 系统需要异步"的最直观答案。
"""

import asyncio
import time

from app.config import load_config, ConfigError
from app.llm_client import LLMClient
from app.async_llm_client import AsyncLLMClient

# 用于对比的 3 个问题——每个都需要一定的生成时间
QUESTIONS = [
    "请用一小段话介绍 Python asyncio 是什么。",
    "请用一小段话介绍 HTTP 协议是什么。",
    "请用一小段话介绍 Git 版本控制是什么。",
]


def run_serial(api_key: str, base_url: str, model: str) -> tuple[int, float]:
    """串行模式：一个一个调 LLM API，记录总耗时。"""
    client = LLMClient(api_key=api_key, base_url=base_url, model=model)
    try:
        t0 = time.perf_counter()
        results: list[str] = []
        for i, q in enumerate(QUESTIONS, 1):
            print(f"  [串行] 发送第 {i} 个问题...")
            reply = client.chat(q)
            results.append(reply)
            print(f"  [串行] 第 {i} 个回复收到，长度={len(reply)}字\n回答：{reply}")
        total_ms = (time.perf_counter() - t0) * 1000
        return len(results), total_ms
    finally:
        client.close()


async def run_concurrent(api_key: str, base_url: str, model: str) -> tuple[int, float]:
    """并发模式：用 asyncio.gather 同时发 3 个请求。"""
    async with AsyncLLMClient(api_key=api_key, base_url=base_url, model=model) as client:
        t0 = time.perf_counter()

        # asyncio.gather 同时启动 3 个协程
        tasks = [client.chat(q) for q in QUESTIONS]
        results = await asyncio.gather(*tasks)

        total_ms = (time.perf_counter() - t0) * 1000
        return len(results), total_ms


def main() -> None:
    # 1.加载配置
    try:
        cfg = load_config()
    except ConfigError as exc:
        print(f"❌ 配置错误：{exc}")
        return

    # 2.串行实验
    print("=" * 50)
    print("🔵 串行模式（一个一个来）")
    print("=" * 50)
    serial_count, serial_ms = run_serial(
        cfg.llm_api_key,
        cfg.llm_base_url,
        cfg.llm_model
    )
    print(f"\n>>> 串行总计: {serial_count} 个回复, 耗时 {serial_ms / 1000:.2f}s")

    print()

    # 3. 并发实验
    print("=" * 50)
    print("🟢 并发模式（asyncio.gather）")
    print("=" * 50)
    concurrent_count, concurrent_ms = asyncio.run(
        run_concurrent(cfg.llm_api_key, cfg.llm_base_url, cfg.llm_model)
    )
    print(f"\n>>> 并发总计: {concurrent_count} 个回复, 耗时 {concurrent_ms / 1000:.2f}s")

    # 4. 对比
    print()
    print("=" * 50)
    print("📊 对比结果")
    print("=" * 50)
    print(f"  串行耗时: {serial_ms / 1000:.2f}s")
    print(f"  并发耗时: {concurrent_ms / 1000:.2f}s")
    if concurrent_ms > 0:
        speedup = serial_ms / concurrent_ms
        print(f"  加速比:   {speedup:.1f}x（并发快了 {speedup:.1f} 倍）")
        print(f"  节省时间: {(serial_ms - concurrent_ms) / 1000:.2f}s")
    print()
    print("💡 如果加速比接近 3x：说明 3 个请求完全重叠，这正是 asyncio.gather 的威力。")
    print("💡 并发耗时 ≈ 最慢单次请求的耗时，而不是 3 个请求之和。")


if __name__ == "__main__":
    main()
