"""
main.py
Day 3 验证入口 —— 加载配置、创建 LLMClient、发一次对话。
"""


from app.config import load_config, ConfigError
from app.llm_client import LLMClient, LLMError


def main() -> None:
    # 1. 加载配置（和你 Day 1 的 config.py 对接）
    try:
        cfg = load_config()
    except ConfigError as exc:
        print(f"❌ 配置错误：{exc}")
        return

    print(f"✅ 配置加载成功，模型：{cfg.llm_model}")

    # 2. 创建 LLM 客户端
    client = LLMClient(
        api_key=cfg.llm_api_key,
        base_url=cfg.llm_base_url,
        model=cfg.llm_model,
        temperature=cfg.llm_temperature,
    )

    try:
        # 3. 单轮对话
        prompt = input("请输入您要问的问题：").strip()
        reply = client.chat(prompt)
        print(f"\n🤖 模型回复：\n{reply}")


        # 4. 多轮对话：把上一轮的问答作为 history 传入
        print("\n--- 多轮对话---")
        reply2 = client.chat(
            "刚才你提到的是什么模型？请用中文回答。",
            history=[
                {"role": "user", "content": "你好，请用一句话介绍你自己"},
                {"role": "assistant", "content": reply},
            ],
        )
        print(f"🤖 模型回复：\n{reply2}")

    except LLMError as exc:
        print(f"❌ LLM 调用失败：{exc}")
        if exc.status_code:
            print(f"HTTP 状态码: {exc.status_code}")
    finally:
        client.close()


if __name__ == "__main__":
    main()