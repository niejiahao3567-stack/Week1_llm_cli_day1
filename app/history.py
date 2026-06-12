"""对话历史持久化：把每次对话追加到 data/history.json。

新手注意：JSON 序列化要求所有 key 必须是字符串，
datetime 对象不能直接序列化，需要先转成 ISO 格式字符串。
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class HistoryError(Exception):
    """历史记录读写相关错误。"""
    pass


@dataclass
class Message:
    """单条对话消息。"""
    role: str  # "user" 或 "assistant"
    content: str  # 消息正文
    timestamp: str  # ISO 8601 格式时间戳，如 "2026-06-09T14:30:00+00:00"


def _get_data_dir() -> Path:  # _函数名 表示私有
    """获取 data 目录路径，不存在则自动创建。"""
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)  # 文件有就跳过，没有就创建
    return data_dir


def _get_history_path() -> Path:
    """获取历史文件完整路径。"""
    return _get_data_dir() / "history.json"


def save_message(role: str, content: str) -> None:
    """将一条消息追加保存到历史文件。

    Args:
        role: 消息角色，通常是 "user" 或 "assistant"。
        content: 消息正文。

    Raises:
        HistoryError: JSON 序列化失败或写入失败。
    """
    message = Message(
        role=role,
        content=content,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    history_path = _get_history_path()
    # 读取已有历史，文件不存在则初始化为空列表  loads()解析JSON为python对象
    if history_path.exists():
        try:
            existing: list[dict[str, Any]] = json.loads(history_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise HistoryError(
                f"历史文件已损坏，无法解析 JSON：{history_path}\n"
                f"原始错误：{exc}"
            ) from exc
    else:
        existing = []

    existing.append(asdict(message))

    try:  # dumps()将python转化为JSON格式
        # indent=2 让 JSON 文件人类可读；ensure_ascii=False 保留中文
        history_path.write_text(
            json.dumps(existing, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError as exc:
        raise HistoryError(f"写入历史文件失败：{history_path}\n原始错误：{exc}") from exc


def load_history() -> list[dict[str, Any]]:
    """读取全部历史消息。

    Returns:
        历史消息列表，如果文件不存在则返回空列表。

    Raises:
        HistoryError: 历史文件存在但 JSON 解析失败。
    """
    history_path = _get_history_path()
    if not history_path.exists():
        return []

    try:
        return json.loads(history_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HistoryError(
            f"历史文件已损坏，无法解析 JSON：{history_path}\n"
            f"原始错误：{exc}"
        ) from exc
