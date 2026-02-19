from core.state import PlanState


def model_overview_node(state: PlanState) -> PlanState:
    """
    Beginner-friendly, non-technical model overview.
    Goal: infer what the model probably is (based on user's 'use' + STL signals)
    without simply repeating the user's sentence.

    Produces: state["model_overview"]
    """
    desc = (state.get("description") or "").strip().lower()
    stl = state.get("stl_features") or {}

    bbox = stl.get("bbox_mm")  # (x,y,z)
    watertight = stl.get("watertight")
    likely_supports = stl.get("likely_supports")
    contact_area = float(stl.get("contact_area_mm2") or 0)
    contact_ratio = float(stl.get("contact_ratio") or 0)

    # --- Simple shape labels (no raw numbers) ---
    # Height vibe
    tall_skinny = False
    if bbox and len(bbox) == 3:
        x, y, z = bbox
        base = max(x, y) if max(x, y) > 0 else 1.0
        tall_skinny = (z / base) >= 1.8  # tune later if needed

    # Bed contact label
    if contact_area <= 0:
        bed_contact = "unknown bed contact"
    elif contact_area < 300 or contact_ratio < 0.15:
        bed_contact = "very small bed contact"
    elif contact_area < 600 or contact_ratio < 0.30:
        bed_contact = "small bed contact"
    else:
        bed_contact = "good bed contact"

    # Supports vibe
    supports_vibe = "supports probably not needed" if not likely_supports else "supports may be needed"

    # Mesh health vibe (beginner language)
    if watertight is False:
        mesh_vibe = "mesh has openings (repair recommended)"
    else:
        mesh_vibe = "mesh looks healthy"

    # --- Guess category from description keywords (WITHOUT repeating the sentence) ---
    # We try to infer a category and add "maybe"
    category = None
    if any(k in desc for k in ["box", "container", "bin", "tray", "organizer", "case"]):
        category = "a small container / organizer"
    elif any(k in desc for k in ["stand", "holder", "dock", "mount", "bracket"]):
        category = "a holder / mount type part"
    elif any(k in desc for k in ["toy", "figurine", "statue", "model"]):
        category = "a decorative model"
    elif any(k in desc for k in ["clip", "hook", "hanger"]):
        category = "a clip / hook style part"

    # If we couldn’t categorize, keep it neutral but still helpful
    if not category:
        category = "a general-purpose print"

    # --- Build overview (don’t echo the user text) ---
    lines = []
    lines.append(f"Looks like {category}.")
    lines.append(f"Shape check: {'tall & skinny' if tall_skinny else 'normal proportions'}, {bed_contact}, {supports_vibe}.")
    lines.append(f"Model health: {mesh_vibe}.")

    state["model_overview"] = " ".join(lines)
    return state