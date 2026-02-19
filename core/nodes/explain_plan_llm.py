import json
import os
from core.state import PlanState
from core.prompts import load_prompt
from langchain_openai import ChatOpenAI


def _render_model_checks_beginner(state: PlanState) -> str:
    """
    Beginner-friendly checks only:
    - dimensions
    - watertight status (simple)
    - supports likely (simple)
    - bed contact label (simple)
    """
    stl = state.get("stl_features") or {}
    if not stl:
        return ""

    bbox = stl.get("bbox_mm")
    watertight = stl.get("watertight")
    likely_supports = stl.get("likely_supports")

    contact_area = float(stl.get("contact_area_mm2") or 0)
    contact_ratio = float(stl.get("contact_ratio") or 0)

    # Simple bed-contact label
    if contact_area <= 0:
        contact_label = "Unknown"
    elif contact_area < 300 or contact_ratio < 0.15:
        contact_label = "Very Low"
    elif contact_area < 600 or contact_ratio < 0.30:
        contact_label = "Low"
    else:
        contact_label = "Good"

    lines = []
    lines.append("\n### Model Checks")
    if bbox:
        x, y, z = bbox
        lines.append(f"- **Size (mm)**: {x:.2f} × {y:.2f} × {z:.2f}")
    if watertight is not None:
        lines.append(f"- **Mesh health**: {'OK' if watertight else 'Needs repair (open mesh)'}")
    if likely_supports is not None:
        lines.append(f"- **Supports**: {'Likely needed' if likely_supports else 'Probably not needed'}")
    lines.append(f"- **Bed contact**: {contact_label}")

    return "\n".join(lines)


def _render_model_checks_tech(state: PlanState) -> str:
    """
    Optional: full technical dump (only when SHOW_TECH_DETAILS=true).
    """
    stl = state.get("stl_features") or {}
    if not stl:
        return ""

    lines = []
    lines.append("\n### Model Checks (technical)")
    for k in [
        "bbox_mm", "watertight", "is_volume",
        "contact_area_mm2", "contact_ratio",
        "aspect_ratio", "overhang_percent", "max_overhang_deg",
        "boundary_edges", "nonmanifold_edges", "degenerate_faces",
        "open_edges", "likely_open_top",
        "volume_mm3", "surface_area_mm2",
        "mesh_issue",
    ]:
        if k in stl:
            lines.append(f"- **{k}**: {stl.get(k)}")
    return "\n".join(lines)


def explain_plan_llm_node(state: PlanState) -> PlanState:
    system_prompt = load_prompt("system/base_system.txt")
    template = load_prompt("templates/explain_plan.txt")

    plan = state.get("plan", {}) or {}
    plan_json = json.dumps(plan, ensure_ascii=False, indent=2)

    warnings = state.get("warnings", []) or []
    risks = state.get("risks", {}) or {}

    user_prompt = template.format(
        plan_json=plan_json,
        warnings_text="\n".join(f"- {w}" for w in warnings) if warnings else "- (none)",
        risks_json=json.dumps(risks, ensure_ascii=False, indent=2),
        rag_context=state.get("rag_context", "") or "",
    )

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

    resp = llm.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )

    explanation = (resp.content or "").strip()

    # ✅ append beginner-friendly checks
    explanation += _render_model_checks_beginner(state)

    # ✅ optional technical dump
    show_tech = os.getenv("SHOW_TECH_DETAILS", "false").lower() in ("1", "true", "yes")
    if show_tech:
        explanation += _render_model_checks_tech(state)

    state["plan_explanation"] = explanation
    return state