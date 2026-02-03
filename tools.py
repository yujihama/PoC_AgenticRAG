from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

from langchain.tools import tool

# main.py 側で作った「ファイルごとのVectorStore」を、tool call から参照するための簡易レジストリ
_VECTOR_STORES: dict[str, Any] = {}
_SOURCES: dict[str, str] = {}
_FILE_CHUNKS: dict[str, list[str]] = {}

# Extraction type definitions
ExtractionType = Literal["transaction_details", "amounts", "dates", "parties", "all"]
AnalysisType = Literal["compare_values", "validate_sequence", "detect_anomalies", "calculate_variance"]


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


# ==============================================================================
# Parameterized Tools for Hypothesis-Driven Audit Agent Architecture
# ==============================================================================


@tool
def extract_data(source: str, extraction_type: str) -> str:
    """
    文書やデータソースから情報を抽出します。

    Args:
        source: 抽出元のデータ（文書内容またはファイルID）
        extraction_type: 抽出タイプ
            - "transaction_details": 取引の詳細情報（ID、日付、金額、当事者など）
            - "amounts": 金額関連の情報のみ
            - "dates": 日付関連の情報のみ
            - "parties": 取引当事者の情報のみ
            - "all": すべての情報

    Returns:
        抽出されたデータ（JSON形式）
    """
    valid_types = ["transaction_details", "amounts", "dates", "parties", "all"]
    if extraction_type not in valid_types:
        return json.dumps({
            "error": f"無効な抽出タイプ: {extraction_type}",
            "valid_types": valid_types
        }, ensure_ascii=False)

    # If source is a file_id, get the content
    content = source
    if source in _SOURCES:
        chunks = _FILE_CHUNKS.get(source, [])
        content = "\n".join(chunks) if chunks else source

    result = {"extraction_type": extraction_type, "source_length": len(content)}

    # Pattern-based extraction
    if extraction_type in ["amounts", "all"]:
        # Extract monetary amounts
        amount_patterns = [
            r'[\$¥€£]\s*[\d,]+(?:\.\d{2})?',
            r'[\d,]+(?:\.\d{2})?\s*(?:円|ドル|USD|JPY|EUR)',
            r'(?:金額|合計|単価|総額)[：:]\s*[\d,]+',
        ]
        amounts = []
        for pattern in amount_patterns:
            amounts.extend(re.findall(pattern, content))
        result["amounts"] = list(set(amounts))[:20]  # Limit results

    if extraction_type in ["dates", "all"]:
        # Extract dates
        date_patterns = [
            r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?',
            r'\d{1,2}[-/]\d{1,2}[-/]\d{4}',
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}',
        ]
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, content, re.IGNORECASE))
        result["dates"] = list(set(dates))[:20]

    if extraction_type in ["parties", "all"]:
        # Extract party names (simplified)
        party_patterns = [
            r'(?:株式会社|有限会社|合同会社)[\w]+',
            r'[\w]+(?:株式会社|有限会社|Inc\.|Corp\.|Ltd\.)',
            r'(?:発注者|受注者|取引先|顧客|ベンダー)[：:]\s*([^\n]+)',
        ]
        parties = []
        for pattern in party_patterns:
            matches = re.findall(pattern, content)
            if isinstance(matches, list) and matches:
                if isinstance(matches[0], tuple):
                    parties.extend([m[0] for m in matches if m[0]])
                else:
                    parties.extend(matches)
        result["parties"] = list(set(parties))[:20]

    if extraction_type in ["transaction_details", "all"]:
        # Extract transaction IDs
        tx_patterns = [
            r'(?:取引ID|Transaction ID|TX|PO)[#：:\-]?\s*([A-Z0-9\-]+)',
            r'(?:注文番号|Order No\.?)[：:\-]?\s*([A-Z0-9\-]+)',
        ]
        tx_ids = []
        for pattern in tx_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            tx_ids.extend(matches)
        result["transaction_ids"] = list(set(tx_ids))[:10]

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def analyze_data(data: str, analysis_type: str, parameters: str = "{}") -> str:
    """
    データを分析して結果を返します。

    Args:
        data: 分析対象のデータ（JSON形式または自然言語）
        analysis_type: 分析タイプ
            - "compare_values": 複数の値を比較して差異を検出
            - "validate_sequence": 一連のイベントの順序や整合性を検証
            - "detect_anomalies": 異常値や外れ値を検出
            - "calculate_variance": 基準値からの乖離率を計算
        parameters: 追加パラメータ（JSON形式）
            - threshold: 異常検出の閾値（デフォルト: 0.2 = 20%）
            - baseline: 比較基準値

    Returns:
        分析結果（JSON形式）
    """
    valid_types = ["compare_values", "validate_sequence", "detect_anomalies", "calculate_variance"]
    if analysis_type not in valid_types:
        return json.dumps({
            "error": f"無効な分析タイプ: {analysis_type}",
            "valid_types": valid_types
        }, ensure_ascii=False)

    # Parse parameters
    try:
        params = json.loads(parameters) if parameters else {}
    except json.JSONDecodeError:
        params = {}

    threshold = params.get("threshold", 0.2)
    baseline = params.get("baseline")

    result = {
        "analysis_type": analysis_type,
        "parameters": params,
        "findings": [],
    }

    # Try to parse data as JSON
    try:
        parsed_data = json.loads(data)
    except json.JSONDecodeError:
        parsed_data = None

    # Extract numbers from data
    numbers = re.findall(r'[\d,]+(?:\.\d+)?', data)
    numeric_values = []
    for n in numbers:
        try:
            numeric_values.append(float(n.replace(',', '')))
        except ValueError:
            pass

    if analysis_type == "compare_values":
        if len(numeric_values) >= 2:
            max_val = max(numeric_values)
            min_val = min(numeric_values)
            if min_val > 0:
                variance = (max_val - min_val) / min_val
                result["findings"].append({
                    "type": "value_comparison",
                    "min": min_val,
                    "max": max_val,
                    "variance_ratio": round(variance, 4),
                    "significant": variance > threshold,
                })

    elif analysis_type == "validate_sequence":
        # Check for date sequence validity
        date_pattern = r'\d{4}[-/]\d{1,2}[-/]\d{1,2}'
        dates = re.findall(date_pattern, data)
        if dates:
            result["findings"].append({
                "type": "date_sequence",
                "dates_found": dates,
                "count": len(dates),
                "note": "日付の順序検証が必要です",
            })

    elif analysis_type == "detect_anomalies":
        if len(numeric_values) >= 3:
            avg = sum(numeric_values) / len(numeric_values)
            anomalies = []
            for i, val in enumerate(numeric_values):
                if avg > 0:
                    deviation = abs(val - avg) / avg
                    if deviation > threshold:
                        anomalies.append({
                            "index": i,
                            "value": val,
                            "deviation": round(deviation, 4),
                        })
            result["findings"].append({
                "type": "anomaly_detection",
                "average": round(avg, 2),
                "threshold": threshold,
                "anomalies": anomalies,
                "anomaly_count": len(anomalies),
            })

    elif analysis_type == "calculate_variance":
        if baseline is not None and numeric_values:
            variances = []
            for val in numeric_values:
                if baseline > 0:
                    variance = (val - baseline) / baseline
                    variances.append({
                        "value": val,
                        "baseline": baseline,
                        "variance": round(variance, 4),
                        "exceeds_threshold": abs(variance) > threshold,
                    })
            result["findings"].append({
                "type": "variance_calculation",
                "baseline": baseline,
                "variances": variances,
            })
        else:
            result["findings"].append({
                "type": "variance_calculation",
                "error": "基準値（baseline）が指定されていません",
            })

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def aggregate_results(results: str, aggregation_method: str = "weighted_average") -> str:
    """
    複数のエージェントや分析結果を集約します。

    Args:
        results: 集約対象の結果（JSON配列形式）
        aggregation_method: 集約方法
            - "weighted_average": 信頼度による加重平均
            - "majority_vote": 多数決
            - "conservative": 最も保守的な結果を採用

    Returns:
        集約された結果（JSON形式）
    """
    try:
        parsed_results = json.loads(results)
        if not isinstance(parsed_results, list):
            parsed_results = [parsed_results]
    except json.JSONDecodeError:
        return json.dumps({
            "error": "結果のJSON解析に失敗しました",
            "raw_input": results[:200]
        }, ensure_ascii=False)

    aggregated = {
        "method": aggregation_method,
        "input_count": len(parsed_results),
        "aggregated_confidence": 0.0,
        "summary": "",
    }

    # Extract confidence scores
    confidences = []
    for r in parsed_results:
        if isinstance(r, dict):
            conf = r.get("confidence", r.get("score", 0.5))
            if isinstance(conf, (int, float)):
                confidences.append(conf)

    if confidences:
        if aggregation_method == "weighted_average":
            aggregated["aggregated_confidence"] = round(sum(confidences) / len(confidences), 4)
        elif aggregation_method == "conservative":
            aggregated["aggregated_confidence"] = round(min(confidences), 4)
        elif aggregation_method == "majority_vote":
            # For majority vote, we consider confidence > 0.5 as positive
            positive_count = sum(1 for c in confidences if c > 0.5)
            aggregated["aggregated_confidence"] = round(positive_count / len(confidences), 4)

    aggregated["individual_confidences"] = confidences
    aggregated["summary"] = f"{len(parsed_results)}件の結果を'{aggregation_method}'方式で集約"

    return json.dumps(aggregated, ensure_ascii=False, indent=2)
