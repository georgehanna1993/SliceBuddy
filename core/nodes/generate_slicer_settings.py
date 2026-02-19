from typing import Any, Dict, List
from core.state import PlanState


def generate_slicer_settings_node(state: PlanState) -> PlanState:
    """
    Rule-based slicer settings generator.
    Uses material + normalized dimensions + STL signals (supports + contact area/ratio) when available.
    Writes state["slicer_settings"].

    IMPORTANT:
    - Mesh integrity warnings are handled in analyze_risks_node (single source of truth).
    - This node focuses on slicer knobs (supports, brim, walls, etc).
    """
    norm = state.get("input_norm", {})
    material_info = state.get("material", {})
    warnings: List[str] = state.get("warnings", [])
    assumptions: List[str] = state.get("assumptions", [])

    desc = (norm.get("description") or "").lower()
    h = float(norm.get("height_mm", 0) or 0)
    w = float(norm.get("width_mm", 0) or 0)
    aspect = (h / w) if (h > 0 and w > 0) else 0.0

    # --- STL signals (optional) ---
    stl = state.get("stl_features") or {}
    used_stl = bool(stl)
    likely_supports = bool(stl.get("likely_supports", False)) if used_stl else False
    contact_area = float(stl.get("contact_area_mm2", 0) or 0) if used_stl else 0.0
    contact_ratio = float(stl.get("contact_ratio", 0) or 0) if used_stl else 0.0
    watertight = bool(stl.get("watertight", True)) if used_stl else None

    mat = (material_info.get("recommended") or "PLA").upper()

    # Base defaults (general purpose)
    settings: Dict[str, Any] = {
        "layer_height_mm": 0.2,
        "walls": 3,
        "top_bottom_layers": 4,
        "infill_percent": 15,
        "infill_pattern": "gyroid",
        "infill_reason": "Good all-around strength and supports top layers well without harsh direction bias.",
        "supports": "off (unknown geometry)",
        "brim_mm": 0,
        "notes": [],
    }

    # --- Material adjustments ---
    if mat == "PLA":
        settings["notes"].append("PLA: easy printing; good for prototypes/decor.")
    elif mat == "PETG":
        settings["top_bottom_layers"] = 5
        settings["infill_percent"] = 18
        settings["notes"].append("PETG: tougher than PLA; watch stringing.")
        assumptions.append("Assuming PETG benefits from extra top/bottom for stiffness.")
    elif mat in ("ABS", "ASA"):
        settings["walls"] = 4
        settings["top_bottom_layers"] = 5
        settings["infill_percent"] = 20
        settings["brim_mm"] = 6
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

    # --- Infill pattern selection (beginner-friendly) ---
    # Functional / load parts
    if any(k in desc for k in ["functional", "bracket", "mount", "holder", "clip", "tool", "hinge"]):
        settings["infill_pattern"] = "gyroid"
        settings["infill_reason"] = "Balanced strength in all directions for functional parts."

    # Boxes / containers / organizers: fast, stable, clean walls
    elif any(k in desc for k in ["box", "container", "bin", "organizer", "tray"]):
        settings["infill_pattern"] = "grid"
        settings["infill_reason"] = "Fast, predictable, and plenty strong for simple containers."

    # Decorative / figurines: smooth + consistent, not overkill
    elif any(k in desc for k in ["figurine", "statue", "decor", "ornament", "model"]):
        settings["infill_pattern"] = "gyroid"
        settings["infill_reason"] = "Keeps strength consistent without needing high infill."

    # Tall skinny things: avoid wobble → use something stable
    if aspect >= 3.0:
        settings["infill_pattern"] = "gyroid"
        settings["infill_reason"] = "More uniform internal support can help tall parts behave better."

    # --- Stability adjustments (dimension-based fallback) ---
    if aspect >= 3.0:
        settings["brim_mm"] = max(settings["brim_mm"], 6)
        settings["walls"] = max(settings["walls"], 4)
        settings["notes"].append("Tall model: increased walls + brim for stability.")
        warnings.append("Tall aspect ratio: consider slowing down and using a brim.")

    # --- STL-based support detection (REAL geometry) ---
    # If the STL analyzer says supports likely needed, reflect that.
    if used_stl and likely_supports:
        settings["supports"] = "on (STL overhang detected)"
        warnings.append("STL overhang detected. Supports likely needed.")

    # --- Keyword-based support hints (user text) ---
    # If the user explicitly says overhang/cantilever/bridge, we force supports on.
    if any(k in desc for k in ["overhang", "bridge", "cantilever", "hanging"]):
        settings["supports"] = "on (overhang hints detected)"
        settings["notes"].append("Overhang-related keywords: supports likely needed unless re-oriented.")
        warnings.append("Overhang hints detected. Supports may be needed.")

    # --- STL-based adhesion tweaks (contact area > bbox-based) ---
    # 1) Very small real contact area (diamond tip case)
    if used_stl and 0 < contact_area <= 500:
        settings["brim_mm"] = max(settings["brim_mm"], 8)
        settings["notes"].append("Very small bed contact: brim strongly recommended.")
        warnings.append("Very small bed contact area detected. High adhesion failure risk.")

    # 2) Pointy base signal (low contact_ratio)
    if used_stl and 0 < contact_ratio < 0.15:
        settings["brim_mm"] = max(settings["brim_mm"], 10)
        settings["notes"].append("Pointy base contact: consider re-orienting or adding raft/brim.")
        warnings.append("Pointy base contact detected. Consider changing orientation or adding a raft/brim.")

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
            "used_stl": used_stl,
            "contact_area_mm2": round(contact_area, 2) if used_stl else None,
            "contact_ratio": round(contact_ratio, 3) if used_stl else None,
            "watertight": watertight,
            "likely_supports": likely_supports if used_stl else None,
        },
    }

    state["warnings"] = warnings
    state["assumptions"] = assumptions
    return state