from fastapi import FastAPI
from pydantic import BaseModel
from core.workflow import build_plan_app
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="SliceBuddy", version="0.1.0")

plan_app = build_plan_app()


class PlanRequest(BaseModel):
    description: str
    height_mm: float
    width_mm: float


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/plan")
def plan(req: PlanRequest):
    initial_state = {
        "description": req.description,
        "height_mm": req.height_mm,
        "width_mm": req.width_mm,
    }
    result = plan_app.invoke(initial_state)

    return {
        "plan": result.get("plan", {}),
        "plan_explanation": result.get("plan_explanation", ""),
        "assumptions": result.get("assumptions", []),
        "warnings": result.get("warnings", []),

    }