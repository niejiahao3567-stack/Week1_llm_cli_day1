"""
app/llm_client.py
LLM API 客户端 —— 封装 OpenAI-compatible Chat Completions 调用。

支持单轮对话和多轮对话（传入历史消息）。
你的 LLM_API_KEY 和 LLM_BASE_URL 存储在 .env 中，不出现在代码里。

运行前确保：
1. .env 中已设置 LLM_API_KEY、LLM_BASE_URL、LLM_MODEL
2. 已安装 httpx：pip install httpx
"""
# from __future__ import annotations

import httpx
import time
from typing import Any


class LLMError(Exception):
    """LLM API 调用相关错误。"""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class LLMClient:
    """OpenAI-compatible LLM API 客户端。

        用法：
            client = LLMClient(config)
            reply = client.chat("你好，介绍一下 Python 异步编程")
            # 多轮对话
            reply2 = client.chat("刚才说的那个再详细一点", history=[
                {"role": "user", "content": "你好"},
                {"role": "assistant", "content": reply},
            ])
        """

    def __init__(self, api_key: str, base_url: str, model: str, temperature: float = 0.7,
                 timeout: float = 60.0) -> None:
        # 去掉 base_url 末尾的斜杠，避免路径拼接时出现双斜杠
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._temperature = temperature

        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
        )

    def chat(
            self,
            prompt: str,
            system_prompt: str | None = None,
            history: list[dict[str, str]] | None = None,
    ) -> str:
        """发送对话请求，返回模型回复文本。

        Args:
            prompt: 用户当前输入。
            system_prompt: 系统角色设定，例如"你是一个专业的 Python 导师"。
            history: 之前的对话历史，格式 [{"role":"user","content":"..."}, {"role":"assistant","content":"..."}, ...]。

        Returns:
            模型回复的文本内容，已去除首尾空白。

        Raises:
            LLMError: API 调用失败、返回空响应或网络错误。
        """
        # 构建 messages 列表

        messages: list[dict[str, str]] = []

        # system prompt 放在最前面，设定 AI 的行为
        if system_prompt:
            messages.append({"role": "assistant", "content": system_prompt})

        # 历史消息追加到中间，让模型记住上下文
        if history:
            messages.extend(history)

        # 当前用户输入放在最后
        if prompt:
            messages.append({"role": "user", "content": prompt})

        body = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
        }

        start = time.perf_counter()
        try:
            response = self._client.post("/v1/chat/completions", json=body)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            # 把 API 返回的错误详情带上，方便排查
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
            msg = f"调用LLM API 时网络错误：{exc!r}"
            raise LLMError(msg) from exc

        data: dict[str, Any] = response.json()

        # 安全提取回复内容
        choices = data.get("choices", [])
        if not choices:
            raise LLMError(
                f"LLM API 返回的 choices 为空，完整响应: {data}"
            )

        message: dict[str, Any] = choices[0].get("message")
        if message is None:
            raise LLMError(
                f"choices[0] 中没有 message 字段，完整响应: {choices[0]}"
            )

        content: str | None = message.get("content")
        if content is None:
            raise LLMError(
                f"message 中没有 content 字段，message: {message}"
            )

        elapsed = (time.perf_counter() - start) * 1000
        print(f"[LLM] 模型={self._model} | 耗时={elapsed:.0f}ms | 回复长度={len(content)}字")

        return content.strip()

    def close(self) -> None:
        """释放 HTTP 连接资源。"""
        self._client.close()


