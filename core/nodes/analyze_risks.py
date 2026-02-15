from typing import Any, Dict, List
from core.state import PlanState


def analyze_risks_node(state: PlanState) -> PlanState:
    """
    Analyze the current plan for common print risks.
    Uses STL signals when available (contact area/ratio, watertight, open-top heuristic, overhang heuristic).
    No loops, no auto-fixes: only warnings + mitigations + structured risk list.
    """
    norm = state.get("input_norm", {})
    material = (state.get("material", {}).get("recommended") or "PLA").upper()
    slicer = state.get("slicer_settings", {}).get("settings", {}) or {}

    warnings: List[str] = state.get("warnings", []) or []
    assumptions: List[str] = state.get("assumptions", []) or []

    desc = (norm.get("description") or "").lower()
    h = float(norm.get("height_mm", 0) or 0)
    w = float(norm.get("width_mm", 0) or 0)
    aspect = (h / w) if (h > 0 and w > 0) else 0.0

    brim_mm = float(slicer.get("brim_mm", 0) or 0)
    supports = str(slicer.get("supports", "")).lower()
    walls = int(slicer.get("walls", 0) or 0)

    # STL signals (optional)
    stl = state.get("stl_features") or {}
    used_stl = bool(stl)

    contact_area = float(stl.get("contact_area_mm2", 0) or 0)
    contact_ratio = float(stl.get("contact_ratio", 0) or 0)

    watertight = bool(stl.get("watertight", True)) if used_stl else True
    is_volume = bool(stl.get("is_volume", True)) if used_stl else True

    open_edges = int(stl.get("open_edges", 0) or 0)
    likely_open_top = bool(stl.get("likely_open_top", False))

    likely_supports = bool(stl.get("likely_supports", False))
    overhang_pct = float(stl.get("overhang_percent", 0) or 0)
    max_overhang_deg = float(stl.get("max_overhang_deg", 0) or 0)

    risks: List[Dict[str, Any]] = []
    mitigations: List[str] = []

    def add_warning_once(msg: str):
        if msg not in warnings:
            warnings.append(msg)

    def add_risk(risk_id: str, severity: str, why: str, fix: str | None = None):
        risks.append({"id": risk_id, "severity": severity, "why": why})
        if fix:
            mitigations.append(fix)

    # ------------------------------------------------------------
    # 1) Mesh integrity risk (SMART)
    # ------------------------------------------------------------
    if used_stl and not watertight:
        # Intentionally open-top container → not "high risk", just informational
        if likely_open_top:
            add_risk(
                "mesh_open_top",
                "low",
                "STL is not watertight, but it looks like an intentionally open-top shape (boundary edges mostly at the top).",
                "This is usually fine. If slicing looks weird, run a quick repair; otherwise print normally.",
            )
            add_warning_once("STL is not watertight, but likely intentional (open-top).")
        else:
            # Truly broken mesh (random holes/seams)
            add_risk(
                "mesh_not_watertight",
                "high",
                f"STL mesh is not watertight (open edges/holes). Boundary edges detected: {open_edges}. Slicing/volume can be unreliable.",
                "Repair the STL (Orca/PrusaSlicer repair, Netfabb, Meshmixer) before printing.",
            )
            add_warning_once("Mesh integrity issue: STL is not watertight. Consider repairing before printing.")

    # If not a closed volume, volume-based estimates are unreliable
    if used_stl and not is_volume:
        add_warning_once("STL is not a closed volume (is_volume=false). Volume-based metrics may be unreliable.")

    # ------------------------------------------------------------
    # 2) Adhesion risk (STL-based) — BEST SIGNALS
    # ------------------------------------------------------------
    # Small real contact area
    if used_stl and contact_area > 0 and contact_area <= 500:
        add_risk(
            "adhesion_low_contact",
            "high",
            f"Very small contact area with the bed (≈{round(contact_area, 1)} mm²). Detachment risk is high.",
            "Add brim/raft, slow first layer, clean bed, and consider re-orienting to increase contact area.",
        )
        if brim_mm < 6:
            add_warning_once("Low contact area detected but brim is small/zero. Brim is strongly recommended.")

    # Pointy / edge contact (ratio)
    if used_stl and contact_ratio > 0 and contact_ratio < 0.15:
        add_risk(
            "pointy_base_contact",
            "medium",
            f"Pointy/edge contact with the bed (contact ratio ≈{round(contact_ratio, 3)}). May wobble or detach.",
            "Re-orient to a flatter face, or use a raft/brim and slower speeds.",
        )

    # ------------------------------------------------------------
    # 3) Stability risk (tall)
    # ------------------------------------------------------------
    if aspect >= 3.0:
        severity = "medium"
        if used_stl and contact_area > 0 and contact_area <= 500:
            severity = "high"

        add_risk(
            "stability_tall",
            severity,
            f"High aspect ratio (≈{round(aspect, 2)}). Tall prints are more likely to wobble or fail.",
            "Use brim (5–10mm), reduce speed, and ensure strong bed adhesion.",
        )

        if brim_mm < 5:
            add_warning_once("Tall model detected but brim is small/zero. Consider adding a brim.")
        if walls < 3:
            add_warning_once("Tall model detected but walls are low. Consider 3–4 walls.")

    # ------------------------------------------------------------
    # 4) Fallback adhesion risk when STL not available
    # ------------------------------------------------------------
    if (not used_stl) and (0 < w <= 20):
        add_risk(
            "adhesion_small_footprint",
            "high",
            f"Small footprint (width≈{w}mm) can detach from bed easily.",
            "Add brim/mouse-ears, clean bed, and consider slower first layer.",
        )
        if brim_mm < 5:
            add_warning_once("Small footprint detected but brim is small/zero. Brim is strongly recommended.")

    # ------------------------------------------------------------
    # 5) Overhang/support risks
    # ------------------------------------------------------------
    # Geometry-based supports signal
    if used_stl and likely_supports:
        add_risk(
            "supports_likely_needed",
            "medium",
            f"STL geometry suggests overhangs (overhang_faces≈{overhang_pct}%, max_overhang≈{max_overhang_deg}°). Supports likely needed.",
            "Enable supports (tree/organic if available) or re-orient to reduce overhangs.",
        )
        # If slicer is still 'auto', we don’t warn; if it’s off, we do.
        if "off" in supports:
            add_warning_once("STL overhang detected but supports are OFF. This may fail without supports.")

    # Text-based hint (backup)
    if "off" in supports:
        if any(k in desc for k in ["overhang", "bridge", "hanging", "cantilever"]):
            add_risk(
                "supports_maybe_needed",
                "medium",
                "Description suggests overhangs/bridges but supports are off.",
                "Enable supports (tree/organic if available) or re-orient to reduce overhangs.",
            )
            add_warning_once("Overhang-related keywords detected. Supports might be needed.")

    # ------------------------------------------------------------
    # 6) Material risks
    # ------------------------------------------------------------
    if material in ("ABS", "ASA"):
        add_risk(
            "warping_abs_asa",
            "high",
            f"{material} has higher warping risk without stable ambient temperature.",
            "Use an enclosure, avoid drafts, and use a brim. Consider ASA for outdoor UV needs.",
        )
        if "Assuming enclosure/ventilation considerations for ABS/ASA." not in assumptions:
            assumptions.append("Assuming enclosure/ventilation considerations for ABS/ASA.")

    if material == "TPU":
        add_risk(
            "tpu_printing",
            "medium",
            "TPU is flexible and can be harder to feed; stringing and jams are more likely.",
            "Print slowly, minimize retractions, and ensure filament path is constrained.",
        )
        if "off" not in supports:
            add_warning_once("TPU selected: supports can be messy; avoid supports unless necessary.")

    # ------------------------------------------------------------
    # Summary severity
    # ------------------------------------------------------------
    highest = "low"
    if any(r["severity"] == "high" for r in risks):
        highest = "high"
    elif any(r["severity"] == "medium" for r in risks):
        highest = "medium"

    state["risks"] = {
        "summary": {"count": len(risks), "highest_severity": highest},
        "items": risks,
        "mitigations": mitigations,
    }

    state["warnings"] = warnings
    state["assumptions"] = assumptions
    return state