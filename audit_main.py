"""
Hypothesis-Driven Audit Agent - Main Entry Point

This module demonstrates the multi-agent architecture for hypothesis-driven audit tasks.
It uses a supervisor agent that orchestrates specialist agents (hypothesis generator and verifier)
along with parameterized tools and a domain knowledge base.

Usage:
    python audit_main.py

The system will:
1. Load input documents into vector stores
2. Initialize the domain knowledge base with sample data
3. Run a supervisor agent that coordinates hypothesis generation and verification
4. Output an audit report with findings
"""

from __future__ import annotations

import json
from pathlib import Path

import dotenv
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from agents.supervisor_agent import SupervisorAgent
from knowledge.knowledge_store import (
    KnowledgeCategory,
    load_sample_knowledge,
    lookup_knowledge,
    register_knowledge,
)
from tools import (
    _FILE_CHUNKS,
    aggregate_results,
    analyze_data,
    extract_data,
    list_indexed_files,
    read_file,
    register_vector_store,
    search_all_files,
    search_file,
)
from utils import _chunk_text, _make_file_id, pretty_print_event


def load_input_files(
    input_files: list[str], embeddings: OpenAIEmbeddings
) -> dict[str, list[str]]:
    """
    Load input files into vector stores.

    Args:
        input_files: List of file paths to load
        embeddings: Embeddings model for vector stores

    Returns:
        Dict mapping file_id to chunks
    """
    used_ids: set[str] = set()
    file_chunks: dict[str, list[str]] = {}

    for file_str in input_files:
        path = Path(file_str)
        if not path.exists():
            print(f"Warning: File not found: {path}")
            continue

        text = path.read_text(encoding="utf-8")
        file_id = _make_file_id(path, used_ids)

        chunks = _chunk_text(text, chunk_size=900, chunk_overlap=150)
        docs = [
            Document(
                page_content=chunk,
                metadata={"file_id": file_id, "path": str(path), "chunk": i},
            )
            for i, chunk in enumerate(chunks)
        ]

        store = InMemoryVectorStore(embeddings)
        store.add_documents(docs)

        register_vector_store(
            file_id=file_id, vector_store=store, source_path=str(path), chunks=chunks
        )
        file_chunks[file_id] = chunks

    return file_chunks


def create_extract_data_fn():
    """Create the extract_data function for the supervisor agent."""

    def extract_data_impl(source: str, extraction_type: str) -> str:
        # Use the tool's invoke method
        return extract_data.invoke({"source": source, "extraction_type": extraction_type})

    return extract_data_impl


def create_analyze_data_fn():
    """Create the analyze_data function for the supervisor agent."""

    def analyze_data_impl(data: str, analysis_type: str, parameters: str = "{}") -> str:
        return analyze_data.invoke({
            "data": data,
            "analysis_type": analysis_type,
            "parameters": parameters,
        })

    return analyze_data_impl


def create_knowledge_lookup_fn():
    """Create the knowledge lookup function for the supervisor agent."""

    def knowledge_lookup_impl(category: str, query: str) -> str:
        return lookup_knowledge(category, query)

    return knowledge_lookup_impl


def main():
    """Main entry point for the audit agent system."""
    # Load environment variables
    dotenv.load_dotenv()

    print("=" * 60)
    print("Hypothesis-Driven Audit Agent System")
    print("=" * 60)

    # Initialize models
    model = ChatOpenAI(model="gpt-4o-mini")
    embeddings = OpenAIEmbeddings()

    # Define input files
    input_files = [
        f"input_files/input_file_{i}.txt" for i in range(1, 18)
    ]

    # Load input files
    print("\n[1/4] Loading input documents...")
    file_chunks = load_input_files(input_files, embeddings)
    print(f"  Loaded {len(file_chunks)} documents")

    # Initialize knowledge base
    print("\n[2/4] Initializing domain knowledge base...")
    knowledge_store = load_sample_knowledge(embeddings)
    stats = knowledge_store.get_category_stats()
    print(f"  Knowledge base initialized with:")
    for category, count in stats.items():
        print(f"    - {category}: {count} entries")

    # Create the supervisor agent
    print("\n[3/4] Creating supervisor agent...")
    base_tools = [list_indexed_files, search_all_files, search_file, read_file]

    supervisor = SupervisorAgent(
        model=model,
        base_tools=base_tools,
        knowledge_lookup_fn=create_knowledge_lookup_fn(),
        extract_data_fn=create_extract_data_fn(),
        analyze_data_fn=create_analyze_data_fn(),
    )
    print("  Supervisor agent created with specialist agents:")
    print("    - hypothesis_generator: Generates hypotheses about discrepancies")
    print("    - hypothesis_verifier: Verifies hypotheses against evidence")

    # Run the audit task
    print("\n[4/4] Running audit task...")
    print("-" * 60)

    audit_prompt = """
以下の監査タスクを実行してください:

1. まず、list_indexed_files で利用可能なドキュメントを確認
2. search_all_files で「取引」「価格」「セキュリティ」に関連する情報を検索
3. lookup_knowledge で監査ルールと市場価格情報を参照
4. generate_hypotheses で潜在的な問題についての仮説を生成
5. verify_hypotheses で生成された仮説を検証

最終的に、発見された問題点、その根拠、推奨アクションをまとめてレポートしてください。
"""

    # Stream the agent's execution
    for event in supervisor.stream(audit_prompt):
        pretty_print_event(event)

    print("\n" + "=" * 60)
    print("Audit task completed")
    print("=" * 60)


if __name__ == "__main__":
    main()
