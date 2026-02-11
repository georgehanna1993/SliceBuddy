from typing import Any, Dict, List
from core.state import PlanState


def generate_slicer_settings_node(state: PlanState) -> PlanState:
    """
    Rule-based slicer settings generator.
    Uses material + orientation signals + normalized dimensions.
    Writes state["slicer_settings"].
    """
    norm = state.get("input_norm", {})
    material_info = state.get("material", {})
    orientation_info = state.get("orientation", {})

    warnings: List[str] = state.get("warnings", [])
    assumptions: List[str] = state.get("assumptions", [])

    desc = (norm.get("description") or "").lower()
    h = float(norm.get("height_mm", 0) or 0)
    w = float(norm.get("width_mm", 0) or 0)

    mat = (material_info.get("recommended") or "PLA").upper()
    aspect = (h / w) if (h > 0 and w > 0) else 0.0

    # Base defaults (good "general purpose" profile)
    settings: Dict[str, Any] = {
        "layer_height_mm": 0.2,
        "walls": 3,
        "top_bottom_layers": 4,
        "infill_percent": 15,
        "supports": "auto (only if needed)",
        "brim_mm": 0,
        "notes": [],
    }

    # --- Material adjustments ---
    if mat == "PLA":
        settings["notes"].append("PLA: keep cooling on; easy printing profile.")
    elif mat == "PETG":
        settings["walls"] = 3
        settings["top_bottom_layers"] = 5
        settings["infill_percent"] = 18
        settings["notes"].append("PETG: reduce fan vs PLA; watch stringing.")
        assumptions.append("Assuming PETG needs slightly more top/bottom for stiffness.")
    elif mat in ("ABS", "ASA"):
        settings["walls"] = 4
        settings["top_bottom_layers"] = 5
        settings["infill_percent"] = 20
        settings["brim_mm"] = 6
        settings["notes"].append("ABS/ASA: enclosure recommended; brim helps prevent warping.")
        warnings.append("ABS/ASA warping risk: consider enclosure and stable ambient temperature.")
    elif mat == "TPU":
        settings["layer_height_mm"] = 0.24
        settings["walls"] = 2
        settings["top_bottom_layers"] = 4
        settings["infill_percent"] = 12
        settings["supports"] = "off unless absolutely necessary"
        settings["notes"].append("TPU: slow printing recommended; avoid aggressive retraction.")
        assumptions.append("Assuming TPU printed slowly with conservative retraction settings.")

    # --- Geometry / stability adjustments ---
    if aspect >= 3.0:
        settings["brim_mm"] = max(settings["brim_mm"], 6)
        settings["walls"] = max(settings["walls"], 4)
        settings["notes"].append("Tall model: increased walls + brim for stability.")
        warnings.append("Tall aspect ratio: consider slowing down and using brim.")

    if w > 0 and w <= 20:
        settings["brim_mm"] = max(settings["brim_mm"], 6)
        settings["notes"].append("Small footprint: brim recommended for adhesion.")
        warnings.append("Small footprint: bed adhesion is critical; brim recommended.")

    # --- Keyword hints (light, explainable) ---
    if any(k in desc for k in ["functional", "bracket", "mount", "holder", "clip"]):
        settings["walls"] = max(settings["walls"], 4)
        settings["infill_percent"] = max(settings["infill_percent"], 20)
        settings["notes"].append("Functional part keywords: increased walls/infill for strength.")

    if any(k in desc for k in ["figurine", "statue", "decor", "ornament"]):
        settings["infill_percent"] = min(settings["infill_percent"], 12)
        settings["notes"].append("Decorative part keywords: lower infill is usually fine.")

    state["slicer_settings"] = {
        "material": mat,
        "settings": settings,
        "signals": {
            "height_mm": h,
            "width_mm": w,
            "aspect_ratio": round(aspect, 2),
        },
    }

    state["warnings"] = warnings
    state["assumptions"] = assumptions
    return state