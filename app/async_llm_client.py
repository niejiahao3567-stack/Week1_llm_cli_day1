"""
app/async_llm_client.py
LLM API 异步客户端 —— 用 httpx.AsyncClient 封装。

和 Day 3 的同步 LLMClient 功能一致，但所有网络请求都是异步的。
配合 asyncio.gather 可以同时发多个请求，总耗时接近最慢的那个。

运行前确保：
1. .env 中已设置 LLM_API_KEY、LLM_BASE_URL、LLM_MODEL
2. 已安装 httpx：pip install httpx
"""
import time
from typing import Any

import httpx


class LLMError(Exception):
    """LLM API 调用相关错误。"""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class AsyncLLMClient:
    """OpenAI-compatible LLM API 异步客户端。

    用法：
        async with AsyncLLMClient(api_key, base_url, model) as client:
            reply = await client.chat("你好")
    """

    def __init__(
            self,
            api_key: str,
            base_url: str,
            model: str,
            temperature: float = 0.7,
            timeout: float = 60.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._temperature = temperature
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "AsyncLLMClient":
        """async with 入口：创建底层 AsyncClient。"""
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(self._timeout, connect=10.0, ),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        """async with 出口：自动关闭连接。"""
        if self._client:
            await self._client.aclose()

    async def chat(
            self,
            prompt: str,
            system_prompt: str | None = None,
            history: list[dict[str, str]] | None = None,
    ) -> str:
        """发送异步对话请求，返回模型回复文本。

        Args:
            prompt: 用户当前输入。
            system_prompt: 系统角色设定。
            history: 之前的对话历史。

        Returns:
            模型回复的文本内容，已去除首尾空白。

        Raises:
            LLMError: API 调用失败、返回空响应或网络错误。
        """
        if self._client is None:
            raise LLMError("AsyncLLMClient 必须用 async with 打开")

        # 构建 messages：system -> history -> user
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        body = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
        }

        start = time.perf_counter()
        try:
            response = await self._client.post("/v1/chat/completions", json=body)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = ""
            try:
                detail = exc.response.json()
            except Exception:
                detail = exc.response.text[:300]
            msg = (
                f"LLM API 返回 HTTP {exc.response.status_code}\n"
                f"请求 URL: {self._base_url}/v1/chat/completions\n"
                f"模型: {self._model}\n"
                f"响应详情: {detail}"
            )
            raise LLMError(msg, status_code=exc.response.status_code) from exc
        except httpx.RequestError as exc:
            msg = f"调用 LLM API 时网络错误: {exc!r}"
            raise LLMError(msg) from exc

        data: dict[str, Any] = response.json()

        choices: list[dict[str, Any]] = data.get("choices", [])
        if not choices:
            raise LLMError(f"LLM API 返回的 choices 为空，完整响应: {data}")

        message: dict[str, Any] | None = choices[0].get("message")
        if message is None:
            raise LLMError(f"choices[0] 中没有 message 字段，完整响应: {choices[0]}")

        content: str | None = message.get("content")
        if content is None:
            raise LLMError(f"message 中没有 content 字段，message: {message}")

        elapsed = (time.perf_counter() - start) * 1000
        print(f"[ASYNC LLM] 模型={self._model} | 耗时={elapsed:.0f}ms | 回复长度={len(content)}字\n回答：{content}")

        return content.strip()
