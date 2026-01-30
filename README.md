# 🧠 SliceBuddy

**SliceBuddy** is an agentic AI system designed to assist with **3D printing planning**.

Given a textual description of a 3D model and its dimensions, SliceBuddy analyzes the request and produces a structured, practical **print plan** — similar to how an experienced maker would reason through a print before opening a slicer.

---

## 🎯 Project Goals

SliceBuddy bridges the gap between:

> “I have a model idea”  
> “I know exactly how to print this successfully”

The project focuses on **reasoning and planning**, not generating 3D models.

---

## 🧩 What SliceBuddy Does

Given:
- A model description (free text)
- Model dimensions (height, width, optional depth)
- Optional constraints (e.g. *no supports*, *strong*, *outdoor use*)

SliceBuddy produces:
- Recommended **material / filament** (with alternatives)
- Best **print orientation** (with trade-offs)
- Practical **slicer settings** (walls, infill, layer height, etc.)
- Likely **print risks** and how to mitigate them
- Clear **assumptions** if information is missing

All decisions are made step-by-step through an agentic workflow.

---

## 🧠 Why Agentic AI?

Instead of a single large prompt, SliceBuddy is built as a **stateful decision pipeline** using **LangGraph**.

- Each node performs **one clear responsibility**
- Intermediate decisions are stored in shared state
- The reasoning process is transparent and debuggable
- The graph can branch based on print risks or constraints

This mirrors how a human reasons about 3D printing:

> classify → choose material → decide orientation → tune settings → assess risks

---

## 🗺️ High-Level Workflow

Future versions may add conditional branches  
(e.g. high overhangs with no supports, tall/thin stability issues).

---

## 🏗️ Architecture Overview

- **Language Model**: OpenAI (via LangChain)
- **Agent Framework**: LangGraph
- **State Management**: TypedDict-based shared state
- **Execution Model**: Deterministic multi-node graph
- **Output**: Human-readable plan + structured data

---

## 📦 Repository Structure (initial)

> Structure will evolve as the project grows.

---

## 🖥️ Future Plans

- Add a simple **web UI** for submitting print requests
- Visualize the LangGraph execution per request
- Add optional **STL analysis tools** (geometry, volume, bounding box)
- Support **printer profiles** (nozzle size, bed size, enclosure)
- Export slicer-ready presets (Bambu / Prusa / Orca)

---

## 🚧 Current Status

- [x] Project concept defined  
- [x] Agent workflow designed  
- [ ] Core LangGraph implementation  
- [ ] Risk-based branching logic  
- [ ] UI layer  

---

## ⚠️ Disclaimer

SliceBuddy provides **best-practice recommendations**, not guarantees.

3D printing depends on hardware, materials, environment, and calibration.  
Always validate critical prints with test runs.

