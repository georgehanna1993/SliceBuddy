import json
from core.state import PlanState
from core.prompts import load_prompt
from langchain_openai import ChatOpenAI


def explain_plan_llm_node(state: PlanState) -> PlanState:
    """
    Uses an LLM to generate a human-readable explanation of the structured plan.
    Prompts are loaded from /prompts (no inline prompt strings).
    """
    system_prompt = load_prompt("system/base_system.txt")
    template = load_prompt("templates/explain_plan.txt")

    plan = state.get("plan", {})
    plan_json = json.dumps(plan, ensure_ascii=False, indent=2)

    user_prompt = template.format(
        plan_json=plan_json,
        rag_context=state.get("rag_context", "")
    )

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

    resp = llm.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )

    state["plan_explanation"] = resp.content.strip()
    return state