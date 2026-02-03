"""
Domain Knowledge Base Module

This module provides domain-specific vector stores for:
- Market pricing information
- Vendor profiles
- Audit rules and compliance requirements
"""

from knowledge.knowledge_store import (
    DomainKnowledgeStore,
    KnowledgeCategory,
    register_knowledge,
    lookup_knowledge,
    get_available_categories,
)

__all__ = [
    "DomainKnowledgeStore",
    "KnowledgeCategory",
    "register_knowledge",
    "lookup_knowledge",
    "get_available_categories",
]
