from typing import TypedDict, List, Dict, Any


class PlanState(TypedDict, total=False):
    # --- Raw inputs (as received) ---
    description: str
    height_mm: float
    width_mm: float

    # STL input (optional)
    stl_path: str
    stl_features: Dict[str, Any]

    # --- Control flags ---
    stop: bool

    # --- Normalized/validated inputs ---
    input_raw: Dict[str, Any]
    input_norm: Dict[str, Any]

    # --- Diagnostics for transparency ---
    assumptions: List[str]
    warnings: List[str]

    # --- Final output ---
    plan: Dict[str, Any]
    model_overview: str
    beginner_labels: Dict[str, Any]
    material: Dict[str, Any]
    orientation: Dict[str, Any]
    slicer_settings: Dict[str, Any]
    risks: Dict[str, Any]
    plan_explanation: str

    # --- RAG ---
    rag_context: str
    rag_sources: List[str]