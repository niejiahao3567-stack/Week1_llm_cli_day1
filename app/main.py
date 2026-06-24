"""
main.py
LLM CLI 聊天工具入口（Day 6 重构版）。

改动点：
  1. 使用 exceptions.py 中的 ConfigError 做精确错误处理。
  2. main() 中不包含业务逻辑，只负责初始化 + 启动。
"""

from app.config import load_config
from app.exceptions import ConfigError
from app.cli import ChatCLI


def main() -> None:
    """程序入口：加载配置 -> 创建 CLI -> 启动交互循环。"""
    try:
        cfg = load_config()
    except ConfigError as exc:
        print(f"❌ 配置错误：{exc}")
        print("请检查 .env 文件是否存在，以及 LLM_API_KEY、LLM_BASE_URL、LLM_MODEL 是否已填写。")
        return

    cli = ChatCLI(
        api_key=cfg.llm_api_key,
        base_url=cfg.llm_base_url,
        model=cfg.llm_model,
        system_prompt="你是一个专业的 AI 编程助手，用中文回答。"
    )
    cli.run()

if __name__ == "__main__":
    main()