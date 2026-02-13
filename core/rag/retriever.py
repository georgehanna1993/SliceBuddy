from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from dotenv import load_dotenv
load_dotenv()


REPO_ROOT = Path(__file__).resolve().parents[2]
CHROMA_DIR = REPO_ROOT / ".chroma"
COLLECTION_NAME = "slicebuddy_knowledge"


def get_vectorstore() -> Chroma:
    """Load the persistent Chroma vector store from disk."""
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return Chroma(
        persist_directory=str(CHROMA_DIR),
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
    )


def retrieve(query: str, k: int = 3) -> List[Document]:
    """
    Retrieve top-k relevant chunks for a query.
    Returns LangChain Document objects with page_content + metadata.
    """
    vs = get_vectorstore()
    return vs.similarity_search(query, k=k)