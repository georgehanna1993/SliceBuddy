from typing import TypedDict, List, Dict, Any


class PlanState(TypedDict, total=False):
    # --- Raw inputs (as received) ---
    description: str
    height_mm: float
    width_mm: float

    # --- Normalized/validated inputs ---
    input_raw: Dict[str, Any]
    input_norm: Dict[str, Any]

    # --- Diagnostics for transparency ---
    assumptions: List[str]
    warnings: List[str]

    # --- Final output ---
    plan: Dict[str, Any]