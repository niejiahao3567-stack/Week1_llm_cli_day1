"""Day 1 最小验证脚本：加载配置 + 保存/读取历史。

运行方式：在项目根目录执行 `python main.py`。
你需要观察：
  - 终端是否打印了模型名（不是 API Key 明文）
  - data/history.json 是否被创建
  - 重复运行时历史是否追加而非覆盖

可扩展任务：
  - 给 load_config 加上 LLM_TEMPERATURE 的合法性校验（0.0 ~ 2.0）
  - 让 save_message 支持可选 metadata 字典参数
"""

from app.config import load_config, ConfigError
from app.history import load_history, save_message, HistoryError


def main() -> None:
    # 1.尝试加载配置
    try:
        cfg = load_config()
    except ConfigError as e:
        print(f"❌ 配置错误{e}")
        return

    print(f"✅ 配置加载成功")
    print(f"   模型：{cfg.llm_model}")
    print(f"   接口：{cfg.llm_base_url}")

    # 2.尝试保存消息
    try:
        save_message("你好", "你好，这是我在Python保存的第一条消息。")
        print("✅ 测试消息已保存")
    except HistoryError as e:
        print(f"❌ 保存失败：{e}")
        return

    # 3.读取打印历史
    try:
        history = load_history()
        print(f"✅ 当前历史共 {len(history)} 条消息：")
        for msg in history:
            print(f"[{msg['timestamp'][:19]}] {msg['role']}: {msg['content'][:40]}...")
    except HistoryError as e:
        print(f"❌ 读取失败：{e}")


if __name__ == "__main__":
    main()
