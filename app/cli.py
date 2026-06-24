"""
app/cli.py
LLM CLI 交互核心 —— 命令行循环 + 历史管理 + 命令系统。

把 Day 1-4 写的 config、history、llm_client 拼起来，
变成一个可以在终端里连续对话的工具。

用法：
    from app.cli import ChatCLI
    cli = ChatCLI(api_key="...", base_url="...", model="...")
    cli.run()
"""

from __future__ import annotations

from app.llm_client import LLMClient, LLMError
from app.history import save_message, load_history, HistoryError

# Rich 是可选依赖，未安装时降级为普通 print
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown

    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    console = None  # type: ignore[assignment]
    RICH_AVAILABLE = False


def _print(text: str = "", style: str = "") -> None:
    """统一打印，有 Rich 就用 Rich，没有就降级 print。"""
    if RICH_AVAILABLE and console:
        if style:
            console.print(text, style=style)
        else:
            console.print(text)
    else:
        print(text)


def _print_markdown(content: str) -> None:
    """打印 Markdown 格式的内容。"""
    if RICH_AVAILABLE and console:
        console.print(Markdown(content))
    else:
        print(content)


class ChatCLI:
    """交互式 LLM 聊天命令行工具。

    功能：
    - 连续对话，模型记住上下文
    - 启动时加载历史记录
    - 每轮对话后自动保存到 JSON
    - 内置命令：/help /history /clear /model
    - Ctrl+C 优雅退出
    """

    # 最大保留的历史轮数（防止 messages 列表无限膨胀）
    MAX_HISTORY_ROUNDS = 50

    def __init__(
            self,
            api_key: str,
            base_url: str,
            model: str,
            system_prompt: str | None = None,
    ) -> None:
        self._client = LLMClient(
            api_key=api_key,
            base_url=base_url,
            model=model,
        )
        self._model = model
        self._system_prompt = system_prompt
        # messages 只保留 role 和 content 字段，给 LLMClient.chat() 当 history 用
        self._messages: list[dict[str, str]] = []

    def run(self) -> None:
        """启动命令行交互循环。"""
        self._print_welcome()

        try:
            self._load_history_into_context()
        except HistoryError as exc:
            _print(f"⚠️ 加载历史记录失败: {exc}", "yellow")
            _print("将以空白上下文启动。")

        # ── 主循环 ──
        while True:
            try:
                user_input = input("\n🧑 你: ").strip()
            except (EOFError, KeyboardInterrupt):
                _print("\n👋 再见！")
                break

            if not user_input:
                continue

            # 处理命令
            if user_input.startswith("/"):
                should_exit = self._handle_command(user_input)
                if should_exit:
                    break
                continue

            # 发送给 LLM
            self._chat_turn(user_input)

        # ── 退出时保存 ──
        self._save_context_to_history()
        self._client.close()

    # ── 对话核心 ──

    def _chat_turn(self, user_input: str) -> None:
        """一轮对话：发请求 → 打印回复（含耗时）→ 更新上下文 → 保存历史。"""
        from app.exceptions import LLMAPIError
        try:
            reply, elapsed = self._client.chat(
                prompt=user_input,
                system_prompt=self._system_prompt,
                history=self._messages if self._messages else None,
            )
        except LLMAPIError as exc:
            _print(f"❌ LLM 调用失败: {exc}", "red")
            # 根据状态码给出不同建议
            if exc.status_code == 401:
                _print("💡 请检查 .env 中的 LLM_API_KEY 是否正确。", "yellow")
            elif exc.status_code and exc.status_code >= 500:
                _print("💡 服务器错误，可稍后重试。", "yellow")
            return

        # 更新运行时上下文
        self._messages.append({"role": "user", "content": user_input})
        self._messages.append({"role": "assistant", "content": reply})

        # 限制上下文长度：只保留最近 N 轮
        max_messages = self.MAX_HISTORY_ROUNDS * 2  # user + assistant 各一条
        if len(self._messages) > max_messages:
            self._messages = self._messages[-max_messages:]

        # 打印回复 + 耗时
        _print(f"⏱️ [{elapsed * 1000:.0f}ms]", "dim")
        _print_markdown(reply)

        # 持久化保存
        try:
            save_message("user", user_input)
            save_message("assistant", reply)
        except HistoryError as exc:
            _print(f"⚠️ 保存历史失败: {exc}", "yellow")

    # ── 命令系统 ──

    def _handle_command(self, raw: str) -> bool:
        """处理 / 开头的命令。返回 True 表示要退出。"""
        cmd = raw.strip().lower()

        if cmd in ("/exit", "/quit"):
            _print("👋 再见！")
            return True

        if cmd == "/help":
            _print_markdown(
                """**可用命令：**
- `/help` — 显示此帮助
- `/history` — 显示最近 10 条对话记录
- `/clear` — 清空当前对话上下文（JSON 文件不丢）
- `/model` — 显示当前模型
- `/exit` 或 `/quit` — 退出"""
            )
            return False

        if cmd == "/history":
            self._show_history()
            return False

        if cmd == "/clear":
            self._messages.clear()
            _print("🧹 上下文已清空。下次对话 LLM 将不记得之前的内容。", "green")
            return False

        if cmd == "/model":
            _print(f"当前模型: {self._model}")
            return False

        _print(f"未知命令: {cmd}。输入 /help 查看可用命令。", "yellow")
        return False

    def _show_history(self) -> None:
        """显示 JSON 文件中持久化的历史记录。"""
        try:
            all_history = load_history()
        except HistoryError as exc:
            _print(f"❌ 读取历史失败: {exc}", "red")
            return

        if not all_history:
            _print("📭 暂无历史记录。")
            return

        recent = all_history[-10:]  # 最近 10 条
        _print(f"📜 最近 {len(recent)} 条记录（共 {len(all_history)} 条）：")
        for msg in recent:
            role_icon = "🧑" if msg["role"] == "user" else "🤖"
            ts = msg.get("timestamp", "?")[:19]  # ISO → 截到秒
            content_preview = str(msg.get("content", ""))[:60]
            _print(f"  [{ts}] {role_icon} {content_preview}...")

    # ── 历史持久化 ──

    def _load_history_into_context(self) -> None:
        """从 JSON 文件加载历史，重建 messages 上下文。"""
        all_history = load_history()
        if not all_history:
            return

        # 只加载最近 MAX_HISTORY_ROUNDS 轮的对话进入上下文
        recent = all_history[-(self.MAX_HISTORY_ROUNDS * 2):]
        for msg in recent:
            self._messages.append({
                "role": str(msg["role"]),
                "content": str(msg["content"]),
            })

        if recent:
            _print(f"📂 已加载最近 {len(recent)} 条历史记录。", "dim")

    def _save_context_to_history(self) -> None:
        """退出时把当前上下文中还没保存的轮次持久化。"""
        # 简化处理：聊天过程中已经逐条保存，
        # 这里只做一个标记性保存，防止最后一条丢失。
        pass  # 实际上 _chat_turn 里已经逐条保存了，这里不需要重复写。

    # ── 启动画面 ──

    def _print_welcome(self) -> None:
        """用 Rich 渲染启动画面。"""
        welcome_text = (
            f"🤖 LLM CLI 聊天工具\n"
            f"模型: {self._model}\n"
            f"输入消息开始对话，输入 /help 查看命令，输入 /exit 退出。"
        )
        if RICH_AVAILABLE:
            _print(
                Panel(welcome_text, title="欢迎", border_style="green"),
            )
        else:
            _print("=" * 50)
            _print(welcome_text)
            _print("=" * 50)
