from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
import tempfile
import os

from core.workflow import build_plan_app

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
plan_app = build_plan_app()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/plan")
async def plan_endpoint(
    use: str = Form(...),
    stl: UploadFile = File(...)
):
    # Save uploaded STL to a temp file
    suffix = ".stl"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        contents = await stl.read()
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        result = plan_app.invoke({
            "description": use,
            "stl_path": tmp_path,
        })

        # Return only what UI needs (keep it simple)
        return JSONResponse({
            "stop": bool(result.get("stop")),
            "model_overview": result.get("model_overview"),
            "plan": result.get("plan"),
            "warnings": result.get("warnings", []),
            "risks": result.get("risks", {}),
            "plan_explanation": result.get("plan_explanation", ""),
            "stl_features": result.get("stl_features", {}),
        })
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass