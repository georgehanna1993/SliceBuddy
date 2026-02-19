from __future__ import annotations

from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma



# Repo paths
REPO_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_DIR = REPO_ROOT / "knowledge"
CHROMA_DIR = REPO_ROOT / ".chroma"  # local persistent storage
COLLECTION_NAME = "slicebuddy_knowledge"


def load_markdown_knowledge() -> List[Document]:
    """Load all .md files under /knowledge into Documents."""
    docs: List[Document] = []
    for path in KNOWLEDGE_DIR.glob("**/*.md"):
        text = path.read_text(encoding="utf-8")
        docs.append(Document(page_content=text, metadata={"source": str(path)}))
    return docs


def build_or_update_index() -> None:
    """
    Build a persistent Chroma index from knowledge/*.md.
    Run this after adding/updating knowledge files.
    """
    docs = load_markdown_knowledge()
    if not docs:
        raise RuntimeError(f"No markdown files found under: {KNOWLEDGE_DIR}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=150,
        separators=["\n## ", "\n### ", "\n", " ", ""],
    )
    chunks = splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # This creates/overwrites the collection in a persistent local folder.
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
        collection_name=COLLECTION_NAME,
    )