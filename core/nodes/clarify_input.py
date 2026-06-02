from __future__ import annotations

from typing import Any

from core.state import PlanState


QUESTION_DEFINITIONS: list[dict[str, Any]] = [
    {
        "id": "environment",
        "question": "Where will the printed part be used?",
        "options": [
            {"value": "indoor", "label": "Indoors"},
            {"value": "outdoor", "label": "Outdoors / sunlight"},
            {"value": "car_interior", "label": "Inside a car"},
            {"value": "car_or_engine", "label": "Car or engine area"},
        ],
    },
    {
        "id": "purpose",
        "question": "What matters most for this part?",
        "options": [
            {"value": "decorative", "label": "Looks / home decor"},
            {"value": "general", "label": "General everyday use"},
            {"value": "functional", "label": "Strength / functional use"},
            {"value": "flexible", "label": "Flexibility"},
        ],
    },
    {
        "id": "load",
        "question": "Will it hold weight or experience force?",
        "options": [
            {"value": "none", "label": "No meaningful load"},
            {"value": "light", "label": "Light load"},
            {"value": "moderate", "label": "Regular functional load"},
            {"value": "high", "label": "High or safety-critical load"},
        ],
    },
]


def clarify_input_node(state: PlanState) -> PlanState:
    """Ask for product context before making recommendations."""
    context = state.get("planning_context", {}) or {}
    valid_values = {
        question["id"]: {option["value"] for option in question["options"]}
        for question in QUESTION_DEFINITIONS
    }
    context = {
        key: str(value).strip()
        for key, value in context.items()
        if key in valid_values and str(value).strip() in valid_values[key]
    }
    state["planning_context"] = context
    input_norm = state.get("input_norm", {}) or {}
    input_norm["planning_context"] = context
    state["input_norm"] = input_norm
    missing_questions = [
        question for question in QUESTION_DEFINITIONS
        if not str(context.get(question["id"], "")).strip()
    ]

    state["needs_clarification"] = bool(missing_questions)
    state["clarification_questions"] = missing_questions

    if missing_questions:
        state["plan_explanation"] = (
            "I analyzed the model file. Before I recommend material and slicer settings, "
            "answer a few quick questions so the plan matches the real use case."
        )

    return state
