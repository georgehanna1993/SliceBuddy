import json
from core.state import PlanState
from core.prompts import load_prompt
from langchain_openai import ChatOpenAI


def _render_stl_section(state: PlanState) -> str:
    stl = state.get("stl_features") or {}
    if not stl:
        return ""

    bbox = stl.get("bbox_mm")
    watertight = stl.get("watertight")
    contact_area = stl.get("contact_area_mm2")
    contact_ratio = stl.get("contact_ratio")
    aspect = stl.get("aspect_ratio")
    volume = stl.get("volume_mm3")
    surface = stl.get("surface_area_mm2")
    overhang_pct = stl.get("overhang_percent")
    max_overhang = stl.get("max_overhang_deg")
    likely_supports = stl.get("likely_supports")
    open_edges = stl.get("open_edges")
    likely_open_top = stl.get("likely_open_top")

    lines = []
    lines.append("\n### Model Checks (from STL)")

    if bbox:
        x, y, z = bbox
        lines.append(f"- **Dimensions (mm)**: {x:.2f} × {y:.2f} × {z:.2f}")
        lines.append(f"- **Height (mm)**: {z:.2f}")

    if watertight is not None:
        lines.append(f"- **Watertight**: {'Yes' if watertight else 'No'}")

    if likely_open_top is not None and not watertight:
        lines.append(f"- **Likely open-top (intentional)**: {'Yes' if likely_open_top else 'No'}")

    if open_edges is not None and not watertight:
        lines.append(f"- **Open edges (boundary edge count)**: {int(open_edges)}")

    if contact_area is not None:
        lines.append(f"- **Estimated bed contact area (mm²)**: {float(contact_area):.2f}")

    if contact_ratio is not None:
        lines.append(f"- **Contact ratio (contact / bbox footprint)**: {float(contact_ratio):.3f}")

    if aspect is not None:
        lines.append(f"- **Aspect ratio (height / max(x,y))**: {float(aspect):.3f}")

    if overhang_pct is not None:
        lines.append(f"- **Overhang faces ≥ threshold (%)**: {float(overhang_pct):.2f}%")

    if max_overhang is not None:
        lines.append(f"- **Max overhang angle (deg)**: {float(max_overhang):.1f}")

    if likely_supports is not None:
        lines.append(f"- **Supports likely needed**: {'Yes' if likely_supports else 'No'}")

    if volume is not None:
        lines.append(f"- **Volume (mm³)**: {float(volume):.2f}")

    if surface is not None:
        lines.append(f"- **Surface area (mm²)**: {float(surface):.2f}")

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

    # Always append deterministic STL section
    explanation += _render_stl_section(state)

    state["plan_explanation"] = explanation
    return state