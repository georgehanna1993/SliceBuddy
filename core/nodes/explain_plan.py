from __future__ import annotations

from core.state import PlanState


def explain_plan_node(state: PlanState) -> PlanState:
    """Build a useful explanation without requiring an external AI service."""
    plan = state.get("plan", {}) or {}
    material = plan.get("material", {}) or {}
    orientation = plan.get("orientation", {}) or {}
    slicer = (plan.get("slicer_settings", {}) or {}).get("settings", {}) or {}
    risks = plan.get("risks", {}) or {}

    lines = [
        "## Print Plan",
        f"- **Material:** {material.get('recommended', 'PLA')} - {material.get('reason', 'General-purpose default.')}",
        f"- **Orientation:** {orientation.get('recommended', 'Lay flat on the largest face')} - {orientation.get('reason', 'Improves stability.')}",
        f"- **Supports:** {slicer.get('supports', 'off (unknown geometry)')}",
        f"- **Brim:** {slicer.get('brim_mm', 0)} mm",
        f"- **Layer height:** {slicer.get('layer_height_mm', 0.2)} mm",
        f"- **Print speed:** {slicer.get('print_speed_mm_s', 60)} mm/s",
        f"- **Outer wall speed:** {slicer.get('outer_wall_speed_mm_s', 35)} mm/s",
        f"- **First layer speed:** {slicer.get('first_layer_speed_mm_s', 20)} mm/s",
        f"- **Walls:** {slicer.get('walls', 3)}",
        f"- **Infill:** {slicer.get('infill_percent', 15)}% {slicer.get('infill_pattern', 'gyroid')}",
    ]

    risk_items = risks.get("items", []) or []
    if risk_items:
        lines.append("")
        lines.append("## Risks")
        for risk in risk_items:
            lines.append(
                f"- **{str(risk.get('severity', 'low')).upper()}:** "
                f"{risk.get('why', 'Review this item before printing.')}"
            )

    mitigations = risks.get("mitigations", []) or []
    if mitigations:
        lines.append("")
        lines.append("## Mitigations")
        lines.extend(f"- {mitigation}" for mitigation in mitigations)

    state["plan_explanation"] = "\n".join(lines)
    return state
