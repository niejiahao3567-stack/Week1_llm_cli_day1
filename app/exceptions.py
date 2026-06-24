"""
app/exceptions.py
LLM CLI 统一自定义异常体系。

每个异常对应一层：
  ConfigError   — 配置层（.env 缺失、API Key 为空）
  LLMAPIError   — API 调用层（HTTP 错误、响应解析失败）
  HistoryError  — 历史层（JSON 读写失败）

原则：
  1. 所有异常都继承自 LLMCLIError 基类，调用方可以一把抓。
  2. 每个异常必须有有意义的错误消息，不允许 pass 空壳。
  3. LLMAPIError 额外携带 status_code，方便调用方判断重试策略。
"""


class LLMCLIError(Exception):
    """LLM CLI 项目所有自定义异常的基类。"""


class ConfigError(LLMCLIError):
    """配置层异常——.env 文件缺失、必填项为空、格式错误等。

    使用示例：
        raise ConfigError(f"缺少必填环境变量: LLM_API_KEY")
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class LLMAPIError(LLMCLIError):
    """LLM API 调用层异常——HTTP 错误、超时、响应解析失败等。

    status_code 可选：当错误来自 HTTP 响应时传入，调用方可根据状态码
    判断是否需要重试（如 429/503 可重试，401 不可重试）。
    """

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code

    def __str__(self) -> str:
        """打印时带上状态码信息。"""
        base = super().__str__()
        if self.status_code:
            return f"[HTTP {self.status_code}] {base}"
        return base


class HistoryError(LLMCLIError):
    """历史持久化层异常——JSON 文件读写失败、格式损坏等。"""
    def __init__(self, message: str) -> None:
        super().__init__(message)
