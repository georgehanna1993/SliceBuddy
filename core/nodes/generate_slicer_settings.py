from typing import Any, Dict, List
from core.state import PlanState


def generate_slicer_settings_node(state: PlanState) -> PlanState:
    """
    Rule-based slicer settings generator.
    Uses material + orientation signals + normalized dimensions + STL signals when available.
    Writes state["slicer_settings"].
    """
    norm = state.get("input_norm", {})
    material_info = state.get("material", {})
    warnings: List[str] = state.get("warnings", [])
    assumptions: List[str] = state.get("assumptions", [])

    desc = (norm.get("description") or "").lower()
    h = float(norm.get("height_mm", 0) or 0)
    w = float(norm.get("width_mm", 0) or 0)
    aspect = (h / w) if (h > 0 and w > 0) else 0.0

    stl = state.get("stl_features", {}) or {}
    likely_supports = bool(stl.get("likely_supports", False))
    contact_ratio = float(stl.get("contact_ratio", 0.0) or 0.0)
    contact_area = float(stl.get("contact_area_mm2", 0.0) or 0.0)

    # STL signals (optional)
    stl = state.get("stl_features") or {}
    contact_area = float(stl.get("contact_area_mm2", 0) or 0)
    contact_ratio = float(stl.get("contact_ratio", 0) or 0)
    watertight = bool(stl.get("watertight", True)) if stl else True

    mat = (material_info.get("recommended") or "PLA").upper()

    # Base defaults (general purpose)
    settings: Dict[str, Any] = {
        "layer_height_mm": 0.2,
        "walls": 3,
        "top_bottom_layers": 4,
        "infill_percent": 15,
        "supports": "off (unknown geometry)",
        "brim_mm": 0,
        "notes": [],
    }

    # --- Material adjustments ---
    if mat == "PLA":
        settings["notes"].append("PLA: easy printing; good for prototypes/decor.")
        settings["supports"] = "auto (only if needed)"
    elif mat == "PETG":
        settings["top_bottom_layers"] = 5
        settings["infill_percent"] = 18
        settings["notes"].append("PETG: tougher than PLA; watch stringing.")
        settings["supports"] = "auto (only if needed)"
        assumptions.append("Assuming PETG benefits from extra top/bottom for stiffness.")
    elif mat in ("ABS", "ASA"):
        settings["walls"] = 4
        settings["top_bottom_layers"] = 5
        settings["infill_percent"] = 20
        settings["brim_mm"] = 6
        settings["supports"] = "auto (only if needed)"
        settings["notes"].append("ABS/ASA: brim helps; enclosure recommended.")
        warnings.append("ABS/ASA warping risk: consider enclosure and stable ambient temperature.")
    elif mat == "TPU":
        settings["layer_height_mm"] = 0.24
        settings["walls"] = 2
        settings["top_bottom_layers"] = 4
        settings["infill_percent"] = 12
        settings["supports"] = "off unless absolutely necessary"
        settings["notes"].append("TPU: print slowly; avoid aggressive retraction.")
        assumptions.append("Assuming TPU printed slowly with conservative retraction settings.")

    # --- STL quality warning ---
    if stl and not watertight:
        warnings.append("STL mesh may be non-watertight (open surface/holes). Slicing/volume may be unreliable.")
        settings["notes"].append("Mesh integrity warning: consider repairing the STL (Netfabb/Meshmixer/Orca repair).")

    # --- Geometry/stability adjustments ---
    if aspect >= 3.0:
        settings["brim_mm"] = max(settings["brim_mm"], 6)
        settings["walls"] = max(settings["walls"], 4)
        settings["notes"].append("Tall model: increased walls + brim for stability.")
        warnings.append("Tall aspect ratio: consider slowing down and using a brim.")

    # --- STL-based support detection (REAL geometry) ---
    if likely_supports and settings["supports"].startswith("auto"):
        settings["supports"] = "on (STL overhang detected)"
        warnings.append("STL overhang detected. Supports likely needed.")

    # --- STL-based adhesion tweaks ---
    # If contact is tiny (or ratio low), add brim even if bbox looks ok
    if 0 < contact_area < 350:  # mm^2 threshold, tweak later
        settings["brim_mm"] = max(settings["brim_mm"], 6)
        settings["notes"].append("Small real contact area: brim recommended.")
        warnings.append("Small real bed contact area detected. Brim recommended.")

    if 0 < contact_ratio < 0.25:
        settings["brim_mm"] = max(settings["brim_mm"], 8)
        settings["notes"].append("Low contact ratio: brim strongly recommended.")
        warnings.append("Low contact ratio detected. Brim strongly recommended.")

    # --- Real bed contact logic (better than width<=20) ---
    # Tiny contact area => high adhesion risk even if bbox is large (diamond tip case)
    if stl and contact_area > 0 and contact_area <= 500:
        settings["brim_mm"] = max(settings["brim_mm"], 8)
        settings["notes"].append("Very small bed contact: brim strongly recommended.")
        warnings.append("Very small bed contact area detected. High adhesion failure risk.")

    # Pointy contact (contact ratio low) => likely tip/edge touching
    if stl and contact_ratio > 0 and contact_ratio < 0.15:
        settings["brim_mm"] = max(settings["brim_mm"], 10)
        settings["notes"].append("Pointy base contact: consider re-orienting to increase contact area.")
        warnings.append("Pointy base contact detected. Consider changing orientation or adding a raft/brim.")

    # --- Keyword-based support hints (stop being generic) ---
    if any(k in desc for k in ["overhang", "bridge", "cantilever", "hanging"]):
        # Only force supports ON when user hints geometry risk
        settings["supports"] = "on (overhang hints detected)"
        settings["notes"].append("Overhang-related keywords: supports likely needed unless re-oriented.")
        warnings.append("Overhang hints detected. Supports may be needed.")

    # --- Strength hints ---
    if any(k in desc for k in ["functional", "bracket", "mount", "holder", "clip"]):
        settings["walls"] = max(settings["walls"], 4)
        settings["infill_percent"] = max(settings["infill_percent"], 20)
        settings["notes"].append("Functional part: increased walls/infill for strength.")

    if any(k in desc for k in ["figurine", "statue", "decor", "ornament"]):
        settings["infill_percent"] = min(settings["infill_percent"], 12)
        settings["notes"].append("Decorative part: lower infill usually fine.")

    state["slicer_settings"] = {
        "material": mat,
        "settings": settings,
        "signals": {
            "height_mm": round(h, 2),
            "width_mm": round(w, 2),
            "aspect_ratio": round(aspect, 2),
            "used_stl": bool(stl),
            "contact_area_mm2": round(contact_area, 2) if stl else None,
            "contact_ratio": round(contact_ratio, 3) if stl else None,
            "watertight": watertight if stl else None,
        },
    }

    state["warnings"] = warnings
    state["assumptions"] = assumptions
    return state