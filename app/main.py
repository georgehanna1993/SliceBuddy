from pathlib import Path
import json
import os
import tempfile

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_cors_origins, get_max_stl_upload_bytes
from core.workflow import build_plan_app


app = FastAPI(
    title="SliceBuddy API",
    description="Deterministic 3D print planning with optional AI explanation.",
    version="2.0.0",
)
plan_app = build_plan_app()

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_endpoint():
    return {
        "status": "ok",
        "service": "slicebuddy-api",
        "version": app.version,
    }


@app.post("/plan")
async def plan_endpoint(
    use: str = Form(...),
    stl: UploadFile = File(...),
    planning_context: str = Form("{}"),
):
    if Path(stl.filename or "").suffix.lower() != ".stl":
        await stl.close()
        raise HTTPException(status_code=415, detail="Upload an STL file with a .stl extension.")

    max_upload_bytes = get_max_stl_upload_bytes()
    total_bytes = 0
    tmp_path: str | None = None

    try:
        try:
            parsed_context = json.loads(planning_context)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=422, detail="planning_context must be valid JSON.") from exc
        if not isinstance(parsed_context, dict):
            raise HTTPException(status_code=422, detail="planning_context must be a JSON object.")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".stl") as tmp:
            tmp_path = tmp.name
            while chunk := await stl.read(1024 * 1024):
                total_bytes += len(chunk)
                if total_bytes > max_upload_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"STL file exceeds the {max_upload_bytes // (1024 * 1024)} MB upload limit.",
                    )
                tmp.write(chunk)

        if total_bytes == 0:
            raise HTTPException(status_code=422, detail="The uploaded STL file is empty.")

        result = plan_app.invoke({
            "description": use,
            "stl_path": tmp_path,
            "planning_context": parsed_context,
        })

        return JSONResponse({
            "stop": bool(result.get("stop")),
            "model_overview": result.get("model_overview"),
            "plan": result.get("plan"),
            "warnings": result.get("warnings", []),
            "risks": result.get("risks", {}),
            "plan_explanation": result.get("plan_explanation", ""),
            "stl_features": result.get("stl_features", {}),
            "assumptions": result.get("assumptions", []),
            "input_norm": result.get("input_norm", {}),
            "needs_clarification": bool(result.get("needs_clarification")),
            "clarification_questions": result.get("clarification_questions", []),
        })
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Could not analyze STL: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not generate a print plan.") from exc
    finally:
        await stl.close()
        try:
            if tmp_path:
                os.remove(tmp_path)
        except OSError:
            pass
