"""
app/llm_client.py
LLM API 客户端 —— 封装 OpenAI-compatible Chat Completions 调用。

支持单轮对话和多轮对话（传入历史消息）。
你的 LLM_API_KEY 和 LLM_BASE_URL 存储在 .env 中，不出现在代码里。

运行前确保：
1. .env 中已设置 LLM_API_KEY、LLM_BASE_URL、LLM_MODEL
2. 已安装 httpx：pip install httpx
"""

"""
app/llm_client.py（Day 6 重构版）
同步 LLM 客户端 —— 接入 LLMAPIError + 耗时记录。

改动点：
  1. 用 LLMAPIError 替换原来的 LLMError（来自 exceptions.py）。
  2. 每次 API 请求用 time.perf_counter() 记录耗时并返回。
  3. 增加 HTTP 状态码的精确分类处理。
"""

import httpx
import time
from app.exceptions import LLMAPIError


class LLMError(Exception):
    """LLM API 调用相关错误。"""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class LLMClient:
    """OpenAI-compatible Chat Completions API 同步封装。"""

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
                 timeout: float = 30.0) -> None:
        # 去掉 base_url 末尾的斜杠，避免路径拼接时出现双斜杠
        """初始化 LLM 客户端。

        Args:
            api_key: API Key，不含 "Bearer " 前缀。
            base_url: API 基础地址，例如 https://api.deepseek.com。
            model: 模型名称，例如 deepseek-chat。
            timeout: HTTP 请求超时秒数，默认 30 秒。
        """
        # self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        #   self._temperature = temperature

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
    ) -> tuple[str, float]:
        """发送聊天请求，返回 (回复文本, 耗时秒数)。

        Args:
            prompt: 用户消息。
            system_prompt: 系统提示，可选。
            history: 历史消息列表，每条包含 role 和 content。

        Returns:
            (模型回复文本, 请求耗时秒数)

        Raises:
            LLMAPIError: API 调用失败，包含错误消息和可选的 HTTP 状态码。
        """
        # 构建 messages 列表

        messages: list[dict[str, str]] = []

        # system prompt 放在最前面，设定 AI 的行为
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # 历史消息追加到中间，让模型记住上下文
        if history:
            messages.extend(history)

        # 当前用户输入放在最后
        messages.append({"role": "user", "content": prompt})

        url = f"{self._base_url}/v1/chat/completions"
        payload = {"model": self._model, "messages": messages}

        # 发请求并计时
        t_start = time.perf_counter()
        try:
            response = self._client.post(url, json=payload)
        except httpx.TimeoutException:
            elapsed = time.perf_counter() - t_start
            raise LLMAPIError(
                f"请求超时（{elapsed:.1f}s），请检查网络或增加 timeout 设置"
            )
        except httpx.NetworkError as exc:
            elapsed = time.perf_counter() - t_start
            raise LLMAPIError(
                f"网络连接失败（{elapsed:.1f}s）: {exc}"
            )
        elapsed = time.perf_counter() - t_start

        # 状态码分类处理
        if response.status_code == 401:
            raise LLMAPIError(
                "API Key 无效或已过期，请检查 .env 中的 LLM_API_KEY",
                status_code=401,
            )
        if response.status_code == 429:
            raise LLMAPIError(
                "API 调用频率超限，请稍后重试",
                status_code=429,
            )
        if response.status_code >= 500:
            raise LLMAPIError(
                f"API 服务器错误 {response.status_code}，可稍后重试",
                status_code=response.status_code,
            )
        if response.status_code != 200:
            raise LLMAPIError(
                f"API 返回非预期状态码 {response.status_code}: {response.text[:200]}",
                status_code=response.status_code,
            )

        # 安全解析响应
        try:
            data = response.json()
        except ValueError as exc:
            raise LLMAPIError(f"API 响应不是有效 JSON: {exc}")

        if not isinstance(data, dict):
            raise LLMAPIError(f"API 响应格式异常: 期望 dict，实际 {type(data).__name__}")

        choices = data.get("choices")
        if not choices or not isinstance(choices, list) or len(choices) == 0:
            raise LLMAPIError(f"API 响应中没有 choices 字段或为空: {data}")

        message = choices[0].get("message")
        if not message or not isinstance(message, dict):
            raise LLMAPIError(f"choices[0].message 缺失或格式异常")

        content = message.get("content")
        if content is None:
            finish = choices[0].get("finish_reason", "unknown")
            raise LLMAPIError(f"模型返回 content 为空，finish_reason={finish}")

        return str(content), elapsed

    def close(self) -> None:
        """释放 HTTP 连接资源。"""
        self._client.close()
