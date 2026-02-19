from typing import Any, Dict, List
from core.state import PlanState


def plan_orientation_node(state: PlanState) -> PlanState:
    """
    Rule-based orientation planning.
    If STL features exist, prefer them (bbox/footprint/aspect).
    Falls back to normalized height/width if STL is not present.
    """
    norm = state.get("input_norm", {})
    desc = (norm.get("description") or "").lower()

    warnings: List[str] = state.get("warnings", [])
    assumptions: List[str] = state.get("assumptions", [])

    # --- Prefer STL signals when available ---
    stl = state.get("stl_features") or {}
    if stl and "bbox_mm" in stl:
        x, y, z = stl["bbox_mm"]
        h = float(z)
        w = float(max(x, y))
        footprint_mm2 = float(stl.get("footprint_mm2", x * y))
        aspect = float(stl.get("aspect_ratio", (h / w) if (h > 0 and w > 0) else 0.0))
        used_stl = True
    else:
        h = float(norm.get("height_mm", 0) or 0)
        w = float(norm.get("width_mm", 0) or 0)
        footprint_mm2 = float(w * w) if w > 0 else 0.0  # weak fallback
        aspect = (h / w) if (h > 0 and w > 0) else 0.0
        used_stl = False

    # Defaults
    recommended = "Lay flat on the largest face"
    reason = "Maximizes bed contact and reduces the chance of tipping."
    tradeoffs = [
        "May change which surfaces look best (aesthetic trade-off).",
        "May increase support needs depending on overhangs.",
    ]
    bed_adhesion_tips = ["Clean bed and use appropriate bed temp for your material."]

    # --- Stability heuristics (now more reliable with STL) ---
    if aspect >= 3.0:
        recommended = "Lay flat (prioritize the widest footprint)"
        reason = "Tall geometry (high aspect ratio) suggests instability if printed upright."
        tradeoffs = [
            "Better stability and lower failure risk.",
            "May require more supports depending on shape.",
        ]
        bed_adhesion_tips.append("Use a brim (5–10mm) for extra stability.")
        warnings.append("Orientation chosen to reduce tipping risk (tall vs. wide).")

    # --- Small footprint heuristics (use footprint if we have it) ---
    # Rough threshold: < 500 mm² is tiny (e.g., ~22mm x 22mm)
    if footprint_mm2 > 0 and footprint_mm2 <= 500:
        bed_adhesion_tips.append("Small footprint: consider brim or mouse-ears for adhesion.")
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
            "height_mm": round(h, 2),
            "width_mm": round(w, 2),
            "aspect_ratio": round(aspect, 2),
            "footprint_mm2": round(footprint_mm2, 2),
            "used_stl": used_stl,
        },
        "tradeoffs": tradeoffs,
        "bed_adhesion_tips": bed_adhesion_tips,
    }

    state["warnings"] = warnings
    state["assumptions"] = assumptions
    return state