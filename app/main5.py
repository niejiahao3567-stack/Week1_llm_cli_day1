"""
main.py
LLM CLI 聊天工具入口。

用法：
    python main.py

启动后即可在终端中与 LLM 连续对话。
"""

from app.config import load_config, ConfigError
from app.cli import ChatCLI


def main() -> None:
    try:
        cfg = load_config()
    except ConfigError as exc:
        print(f"❌ 配置错误：{exc}")
        return

    cli = ChatCLI(api_key=cfg.llm_api_key, base_url=cfg.llm_base_url, model=cfg.llm_model, system_prompt="你是一个专业的 AI 编程助手，用中文回答。")
    cli.run()

if __name__ == "__main__":
    main()