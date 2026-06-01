from typing import Any, Dict, List
from core.state import PlanState


def select_material_node(state: PlanState) -> PlanState:
    """
    Decide recommended filament material based on normalized input + description keywords.
    Rule-based (no LLM).
    """
    norm = state.get("input_norm", {})
    desc: str = (norm.get("description") or "").lower()
    context = norm.get("planning_context", {}) or {}
    environment = str(context.get("environment", "")).lower()
    purpose = str(context.get("purpose", "")).lower()
    load = str(context.get("load", "")).lower()

    warnings: List[str] = state.get("warnings", [])
    assumptions: List[str] = state.get("assumptions", [])

    height = float(norm.get("height_mm", 0) or 0)
    width = float(norm.get("width_mm", 0) or 0)

    # Helper: keyword detection
    def has_any(words: List[str]) -> bool:
        return any(w in desc for w in words)

    # Defaults
    material = "PLA"
    reason = "PLA is easy to print and suitable for most decorative or general-purpose models."
    alternatives = ["PETG"]

    # --- TPU (flexible) ---
    if purpose == "flexible" or has_any(["tpu", "flex", "flexible", "rubber", "gasket", "seal", "phone case", "bumper"]):
        material = "TPU"
        reason = "Description suggests flexibility/elasticity. TPU is the go-to flexible filament."
        alternatives = ["PETG (semi-flex depending on part)", "PLA (not flexible)"]
        assumptions.append("Assuming you want a flexible part based on description keywords.")

    # --- Outdoor / UV / weather resistance → ASA ---
    elif environment in {"outdoor", "car_interior", "car_or_engine"} or has_any(["outdoor", "sun", "uv", "weather", "rain", "garden", "car", "roof"]):
        material = "ASA"
        reason = "Sunlight, weather, or vehicle heat exposure is possible. ASA is preferred for UV and heat resistance."
        alternatives = ["PETG", "ABS"]
        warnings.append("ASA/ABS typically prints best with an enclosure and good ventilation.")

    # --- Heat resistance / functional part → ABS or ASA ---
    elif has_any(["heat", "hot", "engine", "motor", "high temp", "kitchen", "dishwasher"]):
        material = "ABS"
        reason = "Heat exposure suggested. ABS offers better temperature resistance than PLA/PETG."
        alternatives = ["ASA", "PETG"]
        warnings.append("ABS commonly needs an enclosure to avoid warping; ventilate due to fumes.")

    # --- Tall print strength / general functional part → PETG ---
    else:
        if purpose == "functional" or load in {"moderate", "high"}:
            material = "PETG"
            reason = "Functional use or regular load is expected. PETG is tougher than PLA and has better layer adhesion."
            alternatives = ["PLA", "ASA"]

        elif height >= 120:
            material = "PETG"
            reason = "Taller prints often benefit from PETG's improved toughness and layer adhesion."
            alternatives = ["PLA", "ASA"]
            warnings.append("Tall print detected. Consider a brim and slower speeds for stability.")

        # Small footprint adhesion note
        if width > 0 and width <= 20:
            assumptions.append("Small footprint detected. Bed adhesion may be critical; consider brim.")

    state["material"] = {
        "recommended": material,
        "reason": reason,
        "alternatives": alternatives,
        "signals": {
            "keyword_based": bool(desc),
            "height_mm": height,
            "width_mm": width,
            "environment": environment,
            "purpose": purpose,
            "load": load,
        },
    }

    state["warnings"] = warnings
    state["assumptions"] = assumptions
    return state
