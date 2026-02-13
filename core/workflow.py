from langgraph.graph import StateGraph, START, END
import os
from dotenv import load_dotenv
load_dotenv()

from core.state import PlanState
from core.nodes.normalize_input import normalize_input_node
from core.nodes.select_material import select_material_node
from core.nodes.plan_orientation import plan_orientation_node
from core.nodes.generate_slicer_settings import generate_slicer_settings_node
from core.nodes.analyze_risks import analyze_risks_node
from core.nodes.explain_plan_llm import explain_plan_llm_node
from core.nodes.rag_retrieve import rag_retrieve_node


def dummy_plan_node(state: PlanState) -> PlanState:
    desc = state.get("description", "")
    h = state.get("height_mm", 0)
    w = state.get("width_mm", 0)

    state["plan"] = {
        "summary": f"Draft plan for: {desc}",
        "material": state.get("material", {}),
        "orientation": state.get("orientation", {}),
        "slicer_settings": state.get("slicer_settings", {}),
        "risks": state.get("risks", {}),
        "notes": [
            f"Dimensions received: height={h}mm, width={w}mm",
            "This is a placeholder plan. Real logic will be added node-by-node.",
        ],
    }

    return state


def build_plan_app():
    graph = StateGraph(PlanState)

    use_llm = os.getenv("USE_LLM_EXPLAINER", "true").lower() in ("1", "true", "yes")

    # Register core planning nodes
    graph.add_node("NORMALIZE_INPUT", normalize_input_node)
    graph.add_node("SELECT_MATERIAL", select_material_node)
    graph.add_node("PLAN_ORIENTATION", plan_orientation_node)
    graph.add_node("GENERATE_SLICER_SETTINGS", generate_slicer_settings_node)
    graph.add_node("ANALYZE_RISKS", analyze_risks_node)
    graph.add_node("DUMMY_PLAN", dummy_plan_node)

    # Register LLM-related nodes only if enabled
    if use_llm:
        graph.add_node("RAG_RETRIEVE", rag_retrieve_node)
        graph.add_node("EXPLAIN_PLAN", explain_plan_llm_node)

    # Main deterministic chain
    graph.add_edge(START, "NORMALIZE_INPUT")
    graph.add_edge("NORMALIZE_INPUT", "SELECT_MATERIAL")
    graph.add_edge("SELECT_MATERIAL", "PLAN_ORIENTATION")
    graph.add_edge("PLAN_ORIENTATION", "GENERATE_SLICER_SETTINGS")
    graph.add_edge("GENERATE_SLICER_SETTINGS", "ANALYZE_RISKS")
    graph.add_edge("ANALYZE_RISKS", "DUMMY_PLAN")

    # LLM path
    if use_llm:
        graph.add_edge("DUMMY_PLAN", "RAG_RETRIEVE")
        graph.add_edge("RAG_RETRIEVE", "EXPLAIN_PLAN")
        graph.add_edge("EXPLAIN_PLAN", END)
    else:
        graph.add_edge("DUMMY_PLAN", END)

    return graph.compile()