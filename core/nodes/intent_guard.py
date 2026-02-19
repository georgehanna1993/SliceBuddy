from core.state import PlanState

def intent_guard_node(state: PlanState) -> PlanState:
    desc = (state.get("description") or "").strip()
    h = state.get("height_mm", None)
    w = state.get("width_mm", None)

    # NEW: allow STL instead of dims
    has_stl = bool((state.get("stl_path") or "").strip())

    # valid plan request = description + (positive height/width OR stl)
    desc_ok = len(desc) >= 3
    dims_ok = isinstance(h, (int, float)) and isinstance(w, (int, float)) and h > 0 and w > 0

    is_plan_request = desc_ok and (dims_ok or has_stl)
    state["stop"] = not is_plan_request

    if state["stop"]:
        state["plan"] = {"summary": "Not a print-plan request"}
        state["plan_explanation"] = (
            "I didn’t get that as a print-plan request. "
            "Send: description + STL file, OR description + height + width in mm "
            "(e.g. bracket mount, height 120, width 30)."
        )

    return state