from __future__ import annotations

from core.state import PlanState
from core.rag.retriever import retrieve


def rag_retrieve_node(state: PlanState) -> PlanState:
    desc = (state.get("description") or "").strip()
    h = state.get("height_mm")
    w = state.get("width_mm")

    # Keep query simple & aligned with knowledge headings
    query = f"{desc}. height {h}mm width {w}mm. brim supports tall print walls infill bed adhesion materials PLA PETG ABS ASA TPU."

    try:
        docs = retrieve(query, k=3)
    except Exception:
        warnings = state.get("warnings", []) or []
        warning = "Knowledge retrieval is unavailable. Continuing with the deterministic print plan."
        if warning not in warnings:
            warnings.append(warning)
        state["warnings"] = warnings
        state["rag_context"] = ""
        state["rag_sources"] = []
        return state

    snippets = []
    sources = []

    for d in docs:
        src = d.metadata.get("source", "unknown")
        text = (d.page_content or "").strip()
        if not text:
            continue

        sources.append(src)
        snippets.append(f"SOURCE: {src}\n{text}")

    state["rag_context"] = "\n\n---\n\n".join(snippets)
    state["rag_sources"] = list(dict.fromkeys(sources))  # unique, keep order
    MAX_RAG_CHARS = 1800
    state["rag_context"] = state["rag_context"][:MAX_RAG_CHARS]

    return state
