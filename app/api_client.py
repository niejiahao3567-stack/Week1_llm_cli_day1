"""
app/api_client.py
HTTP API 客户端 —— 同步版和异步版。

Day 2 核心：封装 httpx.Client 和 httpx.AsyncClient，
统一处理 timeout、异常、请求头、JSON 解析。

在你的 week1_llm_cli 项目里：
1. 把这段代码放到 app/api_client.py
2. 创建 main.py（见下方）验证
3. 运行前确保已安装 httpx：pip install httpx
"""

from __future__ import annotations

import time
from typing import Any

import httpx


# ── 自定义异常 ────────────────────────────────────────────

class APIError(Exception):
    """HTTP 请求失败时抛出，附带状态码和响应体摘要。"""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


# ── 同步客户端 ────────────────────────────────────────────

class SyncAPIClient:
    """同步 HTTP 客户端，封装了 timeout、Header、异常处理。"""

    def __init__(self, base_url: str = "", timeout: float = 30.0, connect_timeout: float = 10.0) -> None:
        # 用 httpx 的 Timeout 结构分别控制连接和读取超时
        self._timeout = httpx.Timeout(
            connect=connect_timeout,
            read=timeout,
            write=timeout,
            pool=connect_timeout,
        )
        self._client = httpx.Client(
            base_url=base_url,
            timeout=self._timeout,
            headers={"Content-Type": "application/json"},
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        start = time.perf_counter()
        try:
            response = self._client.request(method, path, **kwargs)
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            elapsed = (time.perf_counter() - start) * 1000
            print(f"[{method} {path}] {response.status_code} | {elapsed:.0f}ms")
            return data
        except httpx.HTTPStatusError as exc:
            # 服务器返回了 4xx 或 5xx，把状态码和响应体前 200 字带上
            body_preview = exc.response.text[:200] if exc.response.text else "(空)"
            msg = (
                f"HTTP {exc.response.status_code} 调用 {path} 失败\n"
                f"响应预览: {body_preview}"
            )
            raise APIError(msg, status_code=exc.response.status_code) from exc
        except httpx.RequestError as exc:
            # 网络层错误：DNS 失败、连接拒绝、超时
            msg = f"请求 {path} 时网络错误: {exc!r}"
            raise APIError(msg) from exc

    def get_json(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """GET 请求，返回 JSON 字典。"""

        return self._request("GET", path, **kwargs)

    def post_json(self, path: str, body: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """POSt 请求，返回 JSON 字典。"""

        return self._request("POST", path, json=body, **kwargs)

    def close(self) -> None:
        """释放连接池资源。"""
        self._client.close()


# ── 异步客户端 ────────────────────────────────────────────

class AsyncAPIClient:
    """异步 HTTP 客户端，用法和同步版一致，但支持 `async/await`。"""

    def __init__(
            self,
            base_url: str = "",
            timeout: float = 30.0,
            connect_timeout: float = 10.0,
    ) -> None:
        self._timeout = httpx.Timeout(
            connect=connect_timeout,
            read=timeout,
            write=timeout,
            pool=connect_timeout,
        )
        self.base_url = base_url
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "AsyncAPIClient":
        """async with 入口：创建底层 AsyncClient。"""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self._timeout,
            headers={"Content-Type": "application/json"},
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        """async with 出口：自动关闭连接。"""
        if self._client:
            await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        if self._client is None:
            raise APIError("AsyncAPIClient 必须用 async with 打开")
        start = time.perf_counter()
        try:
            response = await self._client.request(method, path, **kwargs)
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            elapsed = (time.perf_counter() - start) * 1000
            print(f"[ASYNC {method} {path}] {response.status_code} | {elapsed:.0f}ms")
            return data
        except httpx.HTTPStatusError as exc:
            body_preview = exc.response.text[:200] if exc.response.text else "空"
            msg = (
                f"HTTP {exc.response.status_code} 调用 {path} 失败\n"
                f"响应预览: {body_preview}"
            )
            raise APIError(msg, status_code=exc.response.status_code) from exc
        except httpx.RequestError as exc:
            msg = f"请求 {path} 时网络错误: {exc!r}"
            raise APIError(msg) from exc

    async def get_json(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """异步 GET 请求，返回 JSON 字典。"""

        return await self._request("GET", path, **kwargs)

    async def post_json(self, path: str, body: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """异步 POST 请求，发送 JSON Body，返回 JSON 字典。"""

        return await self._request("POST", path, json=body, **kwargs)
