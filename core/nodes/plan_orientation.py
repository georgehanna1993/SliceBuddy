from typing import Any, Dict, List
from core.state import PlanState


def plan_orientation_node(state: PlanState) -> PlanState:
    """
    Rule-based orientation planning using normalized dimensions (height_mm, width_mm).
    Writes state["orientation"] with recommendation + reasoning.
    """
    norm = state.get("input_norm", {})
    desc = (norm.get("description") or "").lower()

    warnings: List[str] = state.get("warnings", [])
    assumptions: List[str] = state.get("assumptions", [])

    h = float(norm.get("height_mm", 0) or 0)
    w = float(norm.get("width_mm", 0) or 0)

    # Basic derived signals
    aspect = (h / w) if (h > 0 and w > 0) else 0.0

    # Default orientation
    recommended = "Lay flat on the largest face"
    reason = "Maximizes bed contact and reduces the chance of tipping."
    tradeoffs = [
        "May show the best surface on the top face depending on geometry.",
        "May increase support needs if the model has overhangs.",
    ]
    bed_adhesion_tips = ["Clean bed and use appropriate bed temp for your material."]

    # Heuristics: tall / thin → stability focus
    if aspect >= 3.0:
        recommended = "Lay flat (prioritize the widest footprint)"
        reason = "High aspect ratio suggests instability if printed upright."
        tradeoffs = [
            "Better stability and lower failure risk.",
            "May change which surfaces look best (aesthetic trade-off).",
        ]
        bed_adhesion_tips.append("Use a brim (5–10mm) for extra stability.")
        warnings.append("Orientation chosen to reduce tipping risk (tall vs. wide).")

    # Heuristics: very small footprint → adhesion risk
    if w > 0 and w <= 20:
        bed_adhesion_tips.append("Consider brim or mouse-ears due to small footprint.")
        warnings.append("Small footprint detected. Bed adhesion may be critical.")

    # Keyword hinting (light touch)
    if any(k in desc for k in ["logo", "text", "engrave", "face", "front"]):
        assumptions.append(
            "Description suggests a visible 'face' (logo/text). Consider orienting to keep that face clean and support-free."
        )

    state["orientation"] = {
        "recommended": recommended,
        "reason": reason,
        "signals": {
            "height_mm": h,
            "width_mm": w,
            "aspect_ratio": round(aspect, 2),
        },
        "tradeoffs": tradeoffs,
        "bed_adhesion_tips": bed_adhesion_tips,
    }

    state["warnings"] = warnings
    state["assumptions"] = assumptions
    return state