"""从 .env 文件读取 LLM 配置，返回类型安全的配置对象。

新手注意：dotenv_values 会把所有值当字符串读进来，
所以 LLM_TEMPERATURE 需要手动转 float。
"""

from dataclasses import dataclass
from pathlib import Path  # 代替os模块处理路径的
from dotenv import dotenv_values


class ConfigError(Exception):
    """配置相关错误，例如 .env 文件缺失或必填字段为空。"""
    pass


@dataclass
class LLMConfig:
    """大模型连接配置，所有字段来自 .env 文件。
       llm_temperature的含义：大模型“创造力”的调节旋钮
    """
    llm_api_key: str
    llm_base_url: str
    llm_model: str
    llm_temperature: float = 0.7


def load_config(env_path: str | None = None) -> LLMConfig:
    """从 .env 文件加载 LLM 配置。

    Args:
        env_path: .env 文件的路径。不传则从项目根目录自动查找。

    Returns:
        LLMConfig: 包含 api_key、base_url、model、temperature 的配置对象。

    Raises:
        ConfigError: .env 文件不存在，或必填字段为空。
    """
    # 定位项目根目录：config.py 的父目录的父目录 resolve()保证能稳定获取的是绝对路径
    project_root = Path(__file__).resolve().parent.parent
    env_file = Path(env_path) if env_path else project_root / ".env"
    if not env_file.exists():
        raise ConfigError(
            f".env 文件不存在：{env_file}\n"
            f"请在项目根目录创建 .env 文件，参考 .env.example。"
        )

    values = dotenv_values(env_file)  # 读取env_file文件，返回值为字典

    # 校验必填字段
    missing = []  # 准备一个空列表，用来收集缺失的字段
    for key in ("LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"):
        if not values.get(key):
            missing.append(key)
    if missing:
        raise ConfigError(
            f".env 文件中以下必填字段为空：{', '.join(missing)}\n"
            f"文件位置：{env_file}"
        )

    return LLMConfig(
        llm_api_key=values["LLM_API_KEY"],
        llm_base_url=values["LLM_BASE_URL"],
        llm_model=values["LLM_MODEL"],
        llm_temperature=float(values.get("LLM_TEMPERATURE", "0.7")),
    )
