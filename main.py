#%%
from __future__ import annotations

from pathlib import Path

import dotenv
from langchain.agents import create_agent
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.agents.middleware import SummarizationMiddleware

import importlib
import tools
import utils
importlib.reload(tools)
importlib.reload(utils)
from tools import list_indexed_files, read_file, register_vector_store, search_all_files, search_file
from utils import _chunk_text, _make_file_id, pretty_print_event


# %%
dotenv.load_dotenv()
input_files = [
    "input_files/input_file_1.txt",
    "input_files/input_file_2.txt",
    "input_files/input_file_3.txt",
    "input_files/input_file_4.txt",
    "input_files/input_file_5.txt",
    "input_files/input_file_6.txt",
    "input_files/input_file_7.txt",
    "input_files/input_file_8.txt",
    "input_files/input_file_9.txt",
    "input_files/input_file_10.txt",
    "input_files/input_file_11.txt",
    "input_files/input_file_12.txt",
    "input_files/input_file_13.txt",
    "input_files/input_file_14.txt",
    "input_files/input_file_15.txt",
    "input_files/input_file_16.txt",
    "input_files/input_file_17.txt",
]

model = ChatOpenAI(model="gpt-5-mini")
embeddings = OpenAIEmbeddings()

used_ids: set[str] = set()

for file_str in input_files:
    path = Path(file_str)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

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

    register_vector_store(file_id=file_id, vector_store=store, source_path=str(path), chunks=chunks)

# %%
agent = create_agent(
    model=model,
    tools=[list_indexed_files, search_all_files, search_file, read_file],
    middleware=[
        SummarizationMiddleware(
            model=model,
            trigger=("tokens", 10000),
            keep=("messages", 10),
        ),
    ],
    system_prompt=(
        "あなたはRAGアシスタントです。\n"
        "- 回答する前に、必ず list_indexed_files または search_all_files / search_file を使って根拠を取得してください。\n"
        "- 回答では、根拠として file_id と chunk を必ず明示してください（例: [input_file_1.txt chunk=0]）。\n"
        "- 根拠にない断定は避け、不明な場合は不明と述べてください。\n"
    ),
)

prompt = "セキュリティについてのドキュメント間の不整合を検出してください。"

for event in agent.stream({"messages": [{"role": "user", "content": prompt}]}):
    pretty_print_event(event)


# %%
