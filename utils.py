from pathlib import Path

import json
from typing import Any


def _chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be >= 0 and < chunk_size")

    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == n:
            break
        start = end - chunk_overlap
    return chunks


def _make_file_id(path: Path, used: set[str]) -> str:
    base = path.name
    if base not in used:
        used.add(base)
        return base
    i = 2
    while f"{base}#{i}" in used:
        i += 1
    fid = f"{base}#{i}"
    used.add(fid)
    return fid


def _truncate(text: str, max_chars: int) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def pretty_print_event(event: dict[str, Any], *, max_tool_chars: int = 900) -> None:
    """
    agent.stream() のイベントを、人が読みやすい形に整形して表示する。

    表示対象:
    - tool call（モデルが呼び出したツール名と引数）
    - tool result（ツールが返した内容）
    - model content（最終回答など、contentがあるもの）
    """

    def _print_tool_calls(msg: Any) -> None:
        tool_calls = getattr(msg, "tool_calls", None) or []
        for tc in tool_calls:
            name = tc.get("name", "?")
            args = tc.get("args", {})
            args_s = json.dumps(args, ensure_ascii=False, separators=(",", ":"))
            print(f"\n[TOOL CALL] {name} {args_s}")

    def _print_model_content(msg: Any) -> None:
        content = getattr(msg, "content", "") or ""
        content = content.strip()
        if content:
            print("\n[MODEL]\n" + content)

    def _print_tool_result(msg: Any) -> None:
        name = getattr(msg, "name", "") or "tool"
        content = getattr(msg, "content", "") or ""
        content = _truncate(str(content), max_tool_chars)
        print(f"\n[TOOL RESULT] {name}\n{content}")

    # event は {"model": {"messages": [...]}} / {"tools": {"messages": [...]}} のように来る
    if "model" in event and isinstance(event["model"], dict):
        for msg in event["model"].get("messages", []) or []:
            _print_tool_calls(msg)
            _print_model_content(msg)

    if "tools" in event and isinstance(event["tools"], dict):
        for msg in event["tools"].get("messages", []) or []:
            _print_tool_result(msg)