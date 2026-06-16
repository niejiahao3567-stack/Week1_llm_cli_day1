"""
app/timer.py
异步函数计时装饰器，用于测量协程执行耗时。

用法：
    @async_timer
    async def my_func():
        await asyncio.sleep(1)

    result, elapsed_ms = await my_func()
"""

import time
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, TypeVar

T = TypeVar("T")


def async_timer(
        func: Callable[..., Coroutine[Any, Any, T]]
) -> Callable[..., Coroutine[Any, Any, tuple[T, float]]]:
    """装饰器：让异步函数返回 (原始返回值, 执行耗时毫秒)。"""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> tuple[T, float]:
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        return result, elapsed
    return wrapper