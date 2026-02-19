from core.state import PlanState
from core.stl import analyze_stl


def stl_analyze_node(state: PlanState) -> PlanState:
    """
    If stl_path exists, analyze STL and store stl_features.
    Also auto-fill height_mm and width_mm so the existing pipeline keeps working.
    """
    path = (state.get("stl_path") or "").strip()
    if not path:
        return state

    feats = analyze_stl(path)
    state["stl_features"] = feats

    # Backwards compatibility with existing logic:
    x, y, z = feats["bbox_mm"]
    state["height_mm"] = float(z)
    state["width_mm"] = float(max(x, y))

    return state