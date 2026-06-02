
# 🧠 SliceBuddy

SliceBuddy is an agentic AI system for intelligent **3D print planning**.

It analyzes an STL or 3MF model file and usage description, then produces a structured, practical print plan — similar to how an experienced maker reasons before slicing a model.

SliceBuddy focuses on planning, not model generation.

Before generating recommendations, SliceBuddy asks a few quick deterministic
questions about environment, purpose, and expected load. These answers help it
avoid treating a decorative indoor print like an outdoor or automotive part.

---

## 🚀 Features

- STL and 3MF geometry analysis (bounding box, contact area, overhangs, mesh health)
- 3MF unit-aware dimensions, build items, and component transforms
- Material recommendation (PLA / PETG / ABS / ASA / TPU)
- Orientation planning
- Slicer settings generation (walls, infill, supports, brim, speeds, cooling guidance)
- Print risk detection with mitigations
- Guided clarification for environment, purpose, and expected load
- Optional RAG knowledge grounding (Chroma + Markdown KB)
- FastAPI backend
- CLI interface
- Structured JSON output + human-readable explanation

---

## 🚀 UI
![SliceBuddy UI](docs/images/u1.png)
![SliceBuddy UI](docs/images/u2.png)
---

## 🧠 How It Works

SliceBuddy uses a deterministic multi-step workflow built with **LangGraph**.
---

## 🗺️ Workflow

![SliceBuddy Workflow](docs/images/workflow.png)

Logic is rule-based where possible.  
The LLM is used only for explanation, not decision-making.

---

## 🏗 Architecture

### Core Stack

- Python 3.11+
- FastAPI
- LangGraph
- LangChain
- OpenAI
- ChromaDB (persistent local vector store)
- Trimesh (model analysis)

---

## 📦 Project Structure

```
app/
  main.py                # FastAPI entrypoint

core/
  nodes/                 # LangGraph workflow nodes
  rag/                   # RAG + Chroma integration
  stl/                   # STL and 3MF analysis engine

knowledge/
  3d_printing_knowledge_base.md

prompts/
  system/
  templates/

scripts/
  build_index.py
  stl_analyze.py
  stl_sanity.py

slicebuddy/
  cli.py

ui/
  # Next.js frontend
```

---

## 📊 Model Geometry Analysis

SliceBuddy extracts:

- Bounding box dimensions (X, Y, Z)
- Bed contact area
- Contact ratio (real vs bounding box)
- Aspect ratio
- Overhang percentage
- Maximum overhang angle
- Likely support requirement
- Mesh integrity:
  - Boundary edges
  - Non-manifold edges
  - Degenerate faces
  - Watertight check
  - Open-top detection

These signals drive planning decisions.

STL files do not contain a standard unit, so SliceBuddy assumes millimeters.
3MF files preserve their declared unit and SliceBuddy converts dimensions to
millimeters before generating recommendations.

---

## 🖥 CLI Usage

```bash
python -m slicebuddy --stl path/to/model.stl --use "functional wall mount bracket"
```

Outputs:

- Material recommendation
- Orientation suggestion
- Support & brim guidance
- Strength settings
- Conservative speed and process guidance
- Risk warnings

---

## 🌐 API Usage

Start the server:

```bash
uvicorn app.main:app --reload
```

Check that it is healthy:

```bash
curl http://127.0.0.1:8000/health
```

Send a POST request to `/plan` with:

- `use` (form field)
- `stl` (legacy form field name; accepts `.stl` or `.3mf` model uploads)

Example response:

```json
{
  "model_overview": "...",
  "plan": { ... },
  "warnings": [],
  "risks": { ... },
  "plan_explanation": "...",
  "stl_features": { ... }
}
```

---

## 🧠 RAG Knowledge System

Knowledge source:

```
knowledge/3d_printing_knowledge_base.md
```

The deterministic planner works without OpenAI or Chroma. To enable AI explanations,
set `USE_LLM_EXPLAINER=true`, add an OpenAI API key, and build the vector index:

```bash
python scripts/build_index.py
```

Chroma stores embeddings locally in:

```
.chroma/
```

---

## 🛠 Installation

### Docker Local Edition

The easiest local setup is Docker. It runs entirely on the user's computer and
does not require an API key or paid service.

```bash
docker compose up --build --detach
```

Open `http://127.0.0.1:3000`.

For beginner-friendly launch files and troubleshooting, see
[`START_HERE.md`](START_HERE.md).

### Manual Developer Setup

Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
.venv\Scripts\activate   # Windows
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your local environment file:

```bash
cp .env.example .env
```

The default configuration runs locally without an OpenAI key. Edit `.env` if you
want to enable optional AI explanations or change the upload limit and CORS origins.

Start the frontend:

```bash
cd ui
cp .env.example .env.local
npm install
npm run dev
```

Open `http://localhost:3000`.

---

## ✅ Verification

Run the backend test suite:

```bash
python -m unittest discover -s tests -v
```

Run the frontend checks:

```bash
cd ui
npm run lint
npm run build
```

---

## 🎯 Design Principles

- Deterministic logic first
- LLM only for explanation
- Geometry-driven decisions
- No invented printer temperatures
- Beginner-friendly output
- Transparent reasoning

---

## ⚠ Disclaimer

SliceBuddy provides best-practice recommendations.

3D printing results depend on:

- Printer calibration
- Filament quality
- Environment
- Hardware limits

Always test critical prints.

---

## 📈 Roadmap

- Printer profile support
- Automatic orientation optimization
- Slicer preset export
- UI graph visualization
- Multi-material planning
