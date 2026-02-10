from __future__ import annotations

from typing import Any, Dict, List
from core.state import PlanState


def normalize_input_node(state: PlanState) -> PlanState:
    """
    Normalize + validate raw user input into a predictable shape.

    Writes:
      - state["input_raw"]   : snapshot of what we received
      - state["input_norm"]  : cleaned values the workflow should use
      - state["assumptions"] : human-readable assumptions
      - state["warnings"]    : human-readable warnings
    """
    assumptions: List[str] = state.get("assumptions", [])
    warnings: List[str] = state.get("warnings", [])

    # Snapshot the raw input (useful for debugging & presentation)
    input_raw: Dict[str, Any] = {
        "description": state.get("description"),
        "height_mm": state.get("height_mm"),
        "width_mm": state.get("width_mm"),
    }

    # ---- Normalize description ----
    desc = (state.get("description") or "").strip()
    if not desc:
        desc = "Unknown model"
        assumptions.append("No description provided. Using 'Unknown model'.")

    # ---- Normalize dimensions (mm) ----
    def to_float(x: Any) -> float | None:
        try:
            if x is None:
                return None
            return float(x)
        except (TypeError, ValueError):
            return None

    h = to_float(state.get("height_mm"))
    w = to_float(state.get("width_mm"))

    if h is None:
        h = 0.0
        assumptions.append("Height not provided or invalid. Using 0.0mm.")
    if w is None:
        w = 0.0
        assumptions.append("Width not provided or invalid. Using 0.0mm.")

    # Basic sanity checks
    if h < 0:
        warnings.append(f"Height was negative ({h}mm). Converting to absolute value.")
        h = abs(h)
    if w < 0:
        warnings.append(f"Width was negative ({w}mm). Converting to absolute value.")
        w = abs(w)

    # Heuristic warnings (not errors)
    if h > 250:
        warnings.append(
            "Height is over ~250mm. Make sure your printer's Z height can handle it."
        )
    if w > 250:
        warnings.append(
            "Width is over ~250mm. Make sure your printer's bed size can handle it."
        )
    if h > 0 and w > 0:
        aspect = h / w if w != 0 else 0
        if aspect >= 4:
            warnings.append(
                "Model looks tall vs. wide (high aspect ratio). Stability risk; consider brim/supports."
            )

    input_norm: Dict[str, Any] = {
        "description": desc,
        "height_mm": round(h, 2),
        "width_mm": round(w, 2),
    }

    state["input_raw"] = input_raw
    state["input_norm"] = input_norm
    state["assumptions"] = assumptions
    state["warnings"] = warnings

    return state