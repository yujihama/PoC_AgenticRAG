"""Domain knowledge store for audit-specific information."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore


class KnowledgeCategory(str, Enum):
    """Categories of domain knowledge."""

    MARKET_PRICING = "market_pricing"
    VENDOR_PROFILES = "vendor_profiles"
    AUDIT_RULES = "audit_rules"
    COMPLIANCE = "compliance"


@dataclass
class KnowledgeEntry:
    """A single entry in the knowledge base."""

    id: str
    content: str
    category: KnowledgeCategory
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_document(self) -> Document:
        return Document(
            page_content=self.content,
            metadata={
                "id": self.id,
                "category": self.category.value,
                **self.metadata,
            },
        )


class DomainKnowledgeStore:
    """
    A registry of domain-specific vector stores for audit knowledge.

    This implements the internal knowledge base pattern where agents can
    query pre-built stores containing market pricing, vendor profiles,
    audit rules, and compliance requirements.
    """

    def __init__(self, embeddings: Embeddings):
        """
        Initialize the knowledge store.

        Args:
            embeddings: The embedding model to use for vector stores
        """
        self.embeddings = embeddings
        self._stores: dict[KnowledgeCategory, InMemoryVectorStore] = {}
        self._entries: dict[KnowledgeCategory, list[KnowledgeEntry]] = {}

        # Initialize stores for each category
        for category in KnowledgeCategory:
            self._stores[category] = InMemoryVectorStore(embeddings)
            self._entries[category] = []

    def add_entry(self, entry: KnowledgeEntry) -> None:
        """
        Add a knowledge entry to the appropriate category store.

        Args:
            entry: The knowledge entry to add
        """
        store = self._stores[entry.category]
        store.add_documents([entry.to_document()])
        self._entries[entry.category].append(entry)

    def add_entries(self, entries: list[KnowledgeEntry]) -> None:
        """Add multiple knowledge entries."""
        for entry in entries:
            self.add_entry(entry)

    def lookup(
        self, category: KnowledgeCategory | str, query: str, k: int = 3
    ) -> list[dict[str, Any]]:
        """
        Search the knowledge base for relevant information.

        Args:
            category: The category to search in
            query: The search query
            k: Number of results to return

        Returns:
            List of relevant knowledge entries with scores
        """
        if isinstance(category, str):
            try:
                category = KnowledgeCategory(category)
            except ValueError:
                return [{"error": f"Unknown category: {category}"}]

        store = self._stores.get(category)
        if not store:
            return [{"error": f"No store for category: {category}"}]

        try:
            results = store.similarity_search_with_score(query, k=k)
        except Exception:
            # Fallback if similarity_search_with_score is not available
            docs = store.similarity_search(query, k=k)
            results = [(doc, None) for doc in docs]

        if not results:
            return [{"message": "該当する知識が見つかりませんでした"}]

        return [
            {
                "content": doc.page_content,
                "score": score,
                "metadata": doc.metadata,
            }
            for doc, score in results
        ]

    def lookup_all_categories(self, query: str, k_per_category: int = 2) -> dict[str, list[dict]]:
        """
        Search across all knowledge categories.

        Args:
            query: The search query
            k_per_category: Number of results per category

        Returns:
            Dict mapping category names to results
        """
        results = {}
        for category in KnowledgeCategory:
            results[category.value] = self.lookup(category, query, k=k_per_category)
        return results

    def get_category_stats(self) -> dict[str, int]:
        """Get the number of entries in each category."""
        return {cat.value: len(entries) for cat, entries in self._entries.items()}


# Global knowledge store instance (to be initialized with embeddings)
_KNOWLEDGE_STORE: DomainKnowledgeStore | None = None


def init_knowledge_store(embeddings: Embeddings) -> DomainKnowledgeStore:
    """Initialize the global knowledge store."""
    global _KNOWLEDGE_STORE
    _KNOWLEDGE_STORE = DomainKnowledgeStore(embeddings)
    return _KNOWLEDGE_STORE


def get_knowledge_store() -> DomainKnowledgeStore | None:
    """Get the global knowledge store."""
    return _KNOWLEDGE_STORE


def register_knowledge(
    id: str,
    content: str,
    category: KnowledgeCategory | str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """
    Register a knowledge entry in the global store.

    Args:
        id: Unique identifier for the entry
        content: The knowledge content
        category: The category (as enum or string)
        metadata: Optional metadata
    """
    if _KNOWLEDGE_STORE is None:
        raise RuntimeError("Knowledge store not initialized. Call init_knowledge_store first.")

    if isinstance(category, str):
        category = KnowledgeCategory(category)

    entry = KnowledgeEntry(
        id=id,
        content=content,
        category=category,
        metadata=metadata or {},
    )
    _KNOWLEDGE_STORE.add_entry(entry)


def lookup_knowledge(category: str, query: str, k: int = 3) -> str:
    """
    Lookup knowledge from the global store.

    This is the function to be used as a tool.

    Args:
        category: The category to search
        query: The search query
        k: Number of results

    Returns:
        Formatted string of results
    """
    if _KNOWLEDGE_STORE is None:
        return "知識ベースが初期化されていません。"

    results = _KNOWLEDGE_STORE.lookup(category, query, k=k)

    if not results:
        return f"カテゴリ '{category}' で '{query}' に関する知識が見つかりませんでした。"

    lines = [f"知識ベース検索結果 (category={category}, query={query}):"]
    for i, r in enumerate(results, 1):
        if "error" in r:
            lines.append(f"  エラー: {r['error']}")
        elif "message" in r:
            lines.append(f"  {r['message']}")
        else:
            score_str = f" (score={r['score']:.4f})" if r.get("score") is not None else ""
            lines.append(f"  [{i}]{score_str}: {r['content'][:200]}...")

    return "\n".join(lines)


def get_available_categories() -> list[str]:
    """Get list of available knowledge categories."""
    return [cat.value for cat in KnowledgeCategory]


# Sample knowledge data for demonstration
SAMPLE_MARKET_PRICING = [
    KnowledgeEntry(
        id="MP001",
        content="デジタル広告の市場価格: ディスプレイ広告のCPMは業界平均で$2-$10。プレミアム枠は$15-$30。",
        category=KnowledgeCategory.MARKET_PRICING,
        metadata={"type": "advertising", "updated": "2024-01"},
    ),
    KnowledgeEntry(
        id="MP002",
        content="IT機器の標準価格帯: エンタープライズサーバー $5,000-$50,000、ネットワーク機器 $500-$10,000。",
        category=KnowledgeCategory.MARKET_PRICING,
        metadata={"type": "hardware", "updated": "2024-01"},
    ),
    KnowledgeEntry(
        id="MP003",
        content="コンサルティングサービスの時間単価: ジュニア $100-$200/時、シニア $250-$500/時、パートナー $500-$1000/時。",
        category=KnowledgeCategory.MARKET_PRICING,
        metadata={"type": "services", "updated": "2024-01"},
    ),
]

SAMPLE_VENDOR_PROFILES = [
    KnowledgeEntry(
        id="VP001",
        content="ABC Technologies: IT機器サプライヤー。信頼度: 高。過去3年の取引実績あり。支払条件: Net 30。",
        category=KnowledgeCategory.VENDOR_PROFILES,
        metadata={"vendor_id": "V001", "risk_level": "low"},
    ),
    KnowledgeEntry(
        id="VP002",
        content="XYZ Media Agency: 広告代理店。信頼度: 中。新規取引先。支払条件: 前払い50%。",
        category=KnowledgeCategory.VENDOR_PROFILES,
        metadata={"vendor_id": "V002", "risk_level": "medium"},
    ),
]

SAMPLE_AUDIT_RULES = [
    KnowledgeEntry(
        id="AR001",
        content="価格逸脱ルール: 市場価格から20%以上の逸脱がある場合は追加承認が必要。",
        category=KnowledgeCategory.AUDIT_RULES,
        metadata={"rule_type": "pricing", "severity": "high"},
    ),
    KnowledgeEntry(
        id="AR002",
        content="分割発注ルール: 同一ベンダーへの発注が連続3回以上で合計が承認限度を超える場合は要調査。",
        category=KnowledgeCategory.AUDIT_RULES,
        metadata={"rule_type": "procurement", "severity": "medium"},
    ),
    KnowledgeEntry(
        id="AR003",
        content="タイミング異常ルール: 月末・四半期末の3日以内に集中する発注は要注意。",
        category=KnowledgeCategory.AUDIT_RULES,
        metadata={"rule_type": "timing", "severity": "medium"},
    ),
]

SAMPLE_COMPLIANCE = [
    KnowledgeEntry(
        id="CP001",
        content="内部統制基準: 10万円以上の発注には部長承認、100万円以上は役員承認が必要。",
        category=KnowledgeCategory.COMPLIANCE,
        metadata={"regulation": "internal_control"},
    ),
    KnowledgeEntry(
        id="CP002",
        content="関連当事者取引: 役員・従業員の関係者との取引は事前開示と取締役会承認が必要。",
        category=KnowledgeCategory.COMPLIANCE,
        metadata={"regulation": "related_party"},
    ),
]


def load_sample_knowledge(embeddings: Embeddings) -> DomainKnowledgeStore:
    """
    Load sample knowledge data for demonstration.

    Args:
        embeddings: The embedding model to use

    Returns:
        Initialized knowledge store with sample data
    """
    store = init_knowledge_store(embeddings)

    all_samples = (
        SAMPLE_MARKET_PRICING
        + SAMPLE_VENDOR_PROFILES
        + SAMPLE_AUDIT_RULES
        + SAMPLE_COMPLIANCE
    )

    store.add_entries(all_samples)

    return store
