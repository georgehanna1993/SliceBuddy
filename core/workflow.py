from langgraph.graph import StateGraph, START, END
from core.state import PlanState
from core.nodes.normalize_input import normalize_input_node


def dummy_plan_node(state: PlanState) -> PlanState:
    # Dummy logic for now (no LLM). We’ll replace this later with real nodes.
    desc = state.get("description", "")
    h = state.get("height_mm", 0)
    w = state.get("width_mm", 0)

    state["plan"] = {
        "summary": f"Draft plan for: {desc}",
        "recommended_material": "PLA",
        "recommended_orientation": "Lay flat on the largest face",
        "slicer_settings": {
            "layer_height_mm": 0.2,
            "walls": 3,
            "top_bottom_layers": 4,
            "infill_percent": 15,
            "supports": "off (draft)",
        },
        "notes": [
            f"Dimensions received: height={h}mm, width={w}mm",
            "This is a placeholder plan. Real logic will be added node-by-node.",
        ],
    }
    return state


def build_plan_app():
    graph = StateGraph(PlanState)

    graph.add_node("NORMALIZE_INPUT", normalize_input_node)
    graph.add_node("DUMMY_PLAN", dummy_plan_node)

    graph.add_edge(START, "NORMALIZE_INPUT")
    graph.add_edge("NORMALIZE_INPUT", "DUMMY_PLAN")
    graph.add_edge("DUMMY_PLAN", END)

    return graph.compile()