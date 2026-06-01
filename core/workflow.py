from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv

load_dotenv()

from core.config import get_bool_env
from core.state import PlanState

from core.nodes.intent_guard import intent_guard_node
from core.nodes.normalize_input import normalize_input_node
from core.nodes.select_material import select_material_node
from core.nodes.plan_orientation import plan_orientation_node
from core.nodes.generate_slicer_settings import generate_slicer_settings_node
from core.nodes.analyze_risks import analyze_risks_node
from core.nodes.stl_analyze import stl_analyze_node
from core.nodes.model_overview import model_overview_node
from core.nodes.explain_plan import explain_plan_node
from core.nodes.clarify_input import clarify_input_node

def ASSEMBLE_PLAN_node(state: PlanState) -> PlanState:
    desc = state.get("description", "")
    h = state.get("height_mm", 0)
    w = state.get("width_mm", 0)

    state["plan"] = {
        "summary": f"Print plan for: {desc}",
        "material": state.get("material", {}),
        "orientation": state.get("orientation", {}),
        "slicer_settings": state.get("slicer_settings", {}),
        "risks": state.get("risks", {}),
        "notes": [f"Analyzed dimensions: height={h}mm, width={w}mm"],
        "assumptions": state.get("assumptions", []),
    }
    return state


def build_plan_app():
    graph = StateGraph(PlanState)

    use_llm = get_bool_env("USE_LLM_EXPLAINER", default=False)

    # ----------------------------
    # 1) Register nodes
    # ----------------------------
    graph.add_node("INTENT_GUARD", intent_guard_node)
    graph.add_node("STL_ANALYZE", stl_analyze_node)
    graph.add_node("NORMALIZE_INPUT", normalize_input_node)
    graph.add_node("SELECT_MATERIAL", select_material_node)
    graph.add_node("PLAN_ORIENTATION", plan_orientation_node)
    graph.add_node("GENERATE_SLICER_SETTINGS", generate_slicer_settings_node)
    graph.add_node("ANALYZE_RISKS", analyze_risks_node)
    graph.add_node("ASSEMBLE_PLAN", ASSEMBLE_PLAN_node)
    graph.add_node("MODEL_OVERVIEW", model_overview_node)
    graph.add_node("CLARIFY_INPUT", clarify_input_node)
    graph.add_node("EXPLAIN_PLAN_LOCAL", explain_plan_node)

    if use_llm:
        from core.nodes.explain_plan_llm import explain_plan_llm_node
        from core.nodes.rag_retrieve import rag_retrieve_node

        graph.add_node("RAG_RETRIEVE", rag_retrieve_node)
        graph.add_node("EXPLAIN_PLAN", explain_plan_llm_node)

    # ----------------------------
    # 2) Wire edges (WITH guard)
    # ----------------------------
    graph.add_edge(START, "INTENT_GUARD")

    # If guard says "stop", end immediately.
    # Otherwise continue to planning nodes.
    graph.add_conditional_edges(
        "INTENT_GUARD",
        lambda s: "STOP" if s.get("stop") else "CONTINUE",
        {
            "STOP": END,
            "CONTINUE": "STL_ANALYZE",
        },
    )

    # Main deterministic chain
    graph.add_edge("STL_ANALYZE", "MODEL_OVERVIEW")
    graph.add_edge("MODEL_OVERVIEW", "NORMALIZE_INPUT")
    graph.add_edge("NORMALIZE_INPUT", "CLARIFY_INPUT")
    graph.add_conditional_edges(
        "CLARIFY_INPUT",
        lambda s: "ASK" if s.get("needs_clarification") else "CONTINUE",
        {
            "ASK": END,
            "CONTINUE": "SELECT_MATERIAL",
        },
    )
    graph.add_edge("SELECT_MATERIAL", "PLAN_ORIENTATION")
    graph.add_edge("PLAN_ORIENTATION", "GENERATE_SLICER_SETTINGS")
    graph.add_edge("GENERATE_SLICER_SETTINGS", "ANALYZE_RISKS")
    graph.add_edge("ANALYZE_RISKS", "ASSEMBLE_PLAN")

    # LLM path
    if use_llm:
        graph.add_edge("ASSEMBLE_PLAN", "RAG_RETRIEVE")
        graph.add_edge("RAG_RETRIEVE", "EXPLAIN_PLAN")
        graph.add_edge("EXPLAIN_PLAN", END)
    else:
        graph.add_edge("ASSEMBLE_PLAN", "EXPLAIN_PLAN_LOCAL")
        graph.add_edge("EXPLAIN_PLAN_LOCAL", END)

    return graph.compile()
