from __future__ import annotations

import argparse
import json
from pathlib import Path

from core.workflow import build_plan_app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a SliceBuddy 3D print plan from an STL file.",
    )
    parser.add_argument("--stl", required=True, help="Path to the STL file to analyze.")
    parser.add_argument("--use", required=True, help="Short description of the model's intended use.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    stl_path = Path(args.stl)
    if stl_path.suffix.lower() != ".stl":
        raise SystemExit("Error: --stl must point to a file ending in .stl.")
    if not stl_path.is_file():
        raise SystemExit(f"Error: STL file not found: {stl_path}")

    result = build_plan_app().invoke({
        "description": args.use,
        "stl_path": str(stl_path),
    })
    print(json.dumps(result, indent=2, ensure_ascii=False))
