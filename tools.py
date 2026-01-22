from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain.tools import tool

# main.py 側で作った「ファイルごとのVectorStore」を、tool call から参照するための簡易レジストリ
_VECTOR_STORES: dict[str, Any] = {}
_SOURCES: dict[str, str] = {}
_FILE_CHUNKS: dict[str, list[str]] = {}


def register_vector_store(
    file_id: str, vector_store: Any, source_path: str, chunks: list[str] | None = None
) -> None:
    """main.py 側で作った VectorStore を tool から参照できるように登録する。"""
    _VECTOR_STORES[file_id] = vector_store
    _SOURCES[file_id] = source_path
    if chunks is not None:
        _FILE_CHUNKS[file_id] = list(chunks)


def _to_head(text: str, head_chars: int) -> str:
    # 改行やタブなどを畳んで「冒頭数文字」を取りやすくする
    normalized = " ".join((text or "").strip().split())
    if head_chars <= 0:
        return ""
    if len(normalized) <= head_chars:
        return normalized
    return normalized[: max(head_chars - 3, 0)] + "..."


def _search_file_impl(file_id: str, query: str, k: int = 4, *, head_chars: int = 80) -> str:
    """Tool本体ロジック（@toolでラップされたStructuredToolを内部呼び出ししないための実装関数）。"""
    if file_id not in _VECTOR_STORES:
        available = ", ".join(sorted(_VECTOR_STORES.keys())) or "(none)"
        return f"未知のfile_idです: {file_id}. 利用可能: {available}"

    store = _VECTOR_STORES[file_id]

    # InMemoryVectorStore は similarity_search / similarity_search_with_score を持つ
    try:
        results = store.similarity_search_with_score(query, k=k)
        scored = True
    except Exception:
        docs = store.similarity_search(query, k=k)
        results = [(d, None) for d in docs]
        scored = False

    if not results:
        return "該当なし"

    lines = [f"検索結果 file_id={file_id} query={query} (top {k})"]
    for doc, score in results:
        meta = dict(getattr(doc, "metadata", {}) or {})
        chunk = meta.get("chunk", "?")
        text = (getattr(doc, "page_content", "") or "").strip()
        head = _to_head(text, head_chars=head_chars)
        score_part = f" score={score:.4f}" if scored and score is not None else ""
        # 返却は「file_id(orファイル名) + chunk_id + 冒頭数文字」に限定してコンテキスト節約
        lines.append(f"- file_id={file_id} chunk={chunk}{score_part} head={head}")

    return "\n\n".join(lines)


@tool
def list_indexed_files() -> str:
    """
    登録済みのファイル一覧を返す（search_fileのfile_id指定に使う）。
    Returns:
        str: 登録済みファイル一覧
    """
    if not _SOURCES:
        return "登録済みファイルはありません。"

    lines = ["登録済みファイル:"]
    for file_id, path in sorted(_SOURCES.items()):
        lines.append(f"- file_id={file_id} path={path}")
    return "\n".join(lines)


@tool
def search_file(file_id: str, query: str, k: int = 4) -> str:
    """
    指定した file_id のVectorDBから query に近いチャンクを検索して返す。
    Args:
        file_id: ファイルID
        query: 検索クエリ
        k: 検索結果の数
    Returns:
        str: 検索結果
    """
    return _search_file_impl(file_id=file_id, query=query, k=k)


@tool
def search_all_files(query: str, k_per_file: int = 4) -> str:
    """
    登録済みの全ファイルを横断して検索する。
    Args:
        query: 検索クエリ
        k_per_file: 各ファイルから返す検索結果の数
    Returns:
        str: ファイルごとの検索結果をまとめた文字列
    """
    if not _VECTOR_STORES:
        return "登録済みファイルはありません。"

    blocks: list[str] = [f"横断検索 query={query} (k_per_file={k_per_file})"]
    for file_id in sorted(_VECTOR_STORES.keys()):
        blocks.append(_search_file_impl(file_id=file_id, query=query, k=k_per_file))
    return "\n\n---\n\n".join(blocks)


@tool
def read_file(file_id: str, chunk: int) -> str:
    """
    指定した file_id と chunk id から、該当チャンク全文を返す。
    （search_file/search_all_files は冒頭の短い抜粋しか返さないため、詳細確認用に使う）
    Args:
        file_id: ファイルID
        chunk: chunk id（0始まり）
    Returns:
        str: 該当チャンク全文（メタ情報付き）
    """
    if file_id not in _SOURCES:
        available = ", ".join(sorted(_SOURCES.keys())) or "(none)"
        return f"未知のfile_idです: {file_id}. 利用可能: {available}"

    if file_id not in _FILE_CHUNKS:
        return (
            f"チャンク本文が未登録です: file_id={file_id}\n"
            "（main.py 側で register_vector_store(..., chunks=...) を渡して登録してください）"
        )

    chunks = _FILE_CHUNKS[file_id]
    if chunk < 0 or chunk >= len(chunks):
        return f"chunk id が範囲外です: chunk={chunk}. 利用可能: 0..{len(chunks)-1}"

    path = _SOURCES.get(file_id, "")
    name = Path(path).name if path else file_id
    return f"[{name} file_id={file_id} chunk={chunk}]\n\n{chunks[chunk]}"
