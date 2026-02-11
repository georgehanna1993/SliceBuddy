from typing import Any, Dict, List
from core.state import PlanState


def analyze_risks_node(state: PlanState) -> PlanState:
    """
    Analyze the current plan for common print risks.
    No loops, no auto-fixes: only warnings + mitigations + structured risk list.
    """
    norm = state.get("input_norm", {})
    material = (state.get("material", {}).get("recommended") or "PLA").upper()
    orientation = state.get("orientation", {})
    slicer = state.get("slicer_settings", {}).get("settings", {})

    warnings: List[str] = state.get("warnings", [])
    assumptions: List[str] = state.get("assumptions", [])

    h = float(norm.get("height_mm", 0) or 0)
    w = float(norm.get("width_mm", 0) or 0)
    aspect = (h / w) if (h > 0 and w > 0) else 0.0

    brim_mm = float(slicer.get("brim_mm", 0) or 0)
    supports = str(slicer.get("supports", "")).lower()
    walls = int(slicer.get("walls", 0) or 0)

    risks: List[Dict[str, Any]] = []
    mitigations: List[str] = []

    def add_risk(risk_id: str, severity: str, why: str, fix: str | None = None):
        risks.append({"id": risk_id, "severity": severity, "why": why})
        if fix:
            mitigations.append(fix)

    # --- Stability risk (tall vs footprint) ---
    if aspect >= 3.0:
        add_risk(
            "stability_tall",
            "medium",
            f"High aspect ratio (≈{round(aspect, 2)}). Tall prints are more likely to wobble or fail.",
            "Use a brim (5–10mm), reduce speed, and ensure strong bed adhesion.",
        )
        if brim_mm < 5:
            warnings.append("Tall model detected but brim is small/zero. Consider adding a brim.")
        if walls < 3:
            warnings.append("Tall model detected but walls are low. Consider 3–4 walls.")

    # --- Small footprint adhesion risk ---
    if 0 < w <= 20:
        add_risk(
            "adhesion_small_footprint",
            "high",
            f"Small footprint (width≈{w}mm) can detach from bed easily.",
            "Add brim/mouse-ears, clean bed, and consider slower first layer.",
        )
        if brim_mm < 5:
            warnings.append("Small footprint detected but brim is small/zero. Brim is strongly recommended.")

    # --- Warping risk for ABS/ASA ---
    if material in ("ABS", "ASA"):
        add_risk(
            "warping_abs_asa",
            "high",
            f"{material} has higher warping risk without stable ambient temperature.",
            "Use an enclosure, avoid drafts, and use a brim. Consider ASA for outdoor UV needs.",
        )
        assumptions.append("Assuming enclosure/ventilation considerations for ABS/ASA.")

    # --- TPU general warning ---
    if material == "TPU":
        add_risk(
            "tpu_printing",
            "medium",
            "TPU is flexible and can be harder to feed; stringing and jams are more likely.",
            "Print slowly, minimize retractions, and ensure filament path is constrained.",
        )
        if "off" not in supports:
            warnings.append("TPU selected: supports can be messy; avoid supports unless necessary.")

    # --- Supports heuristic ---
    if "off" in supports:
        # We don't know geometry, so we only add a gentle warning when description hints overhangs
        desc = (norm.get("description") or "").lower()
        if any(k in desc for k in ["overhang", "bridge", "hanging", "cantilever"]):
            add_risk(
                "supports_maybe_needed",
                "medium",
                "Description suggests overhangs/bridges but supports are off.",
                "Enable supports (tree/organic if available) or re-orient to reduce overhangs.",
            )
            warnings.append("Overhang-related keywords detected. Supports might be needed.")

    state["risks"] = {
        "summary": {
            "count": len(risks),
            "highest_severity": "high" if any(r["severity"] == "high" for r in risks) else ("medium" if risks else "low"),
        },
        "items": risks,
        "mitigations": mitigations,
    }

    state["warnings"] = warnings
    state["assumptions"] = assumptions
    return state