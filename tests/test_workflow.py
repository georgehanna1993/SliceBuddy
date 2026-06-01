from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import trimesh

from core.workflow import build_plan_app


class WorkflowTests(unittest.TestCase):
    def test_offline_workflow_generates_complete_plan(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "box.stl"
            trimesh.creation.box(extents=(20, 30, 10)).export(path)

            with patch.dict(os.environ, {"USE_LLM_EXPLAINER": "false"}):
                result = build_plan_app().invoke({
                    "description": "open-top box for screws",
                    "stl_path": str(path),
                    "planning_context": {
                        "environment": "indoor",
                        "purpose": "general",
                        "load": "light",
                    },
                })

        self.assertFalse(result["stop"])
        self.assertIn("Print Plan", result["plan_explanation"])
        self.assertNotIn("placeholder", str(result["plan"]).lower())
        self.assertNotIn("draft plan", str(result["plan"]).lower())
        self.assertEqual((20.0, 30.0, 10.0), result["stl_features"]["bbox_mm"])

    def test_workflow_pauses_for_missing_use_case_context(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "box.stl"
            trimesh.creation.box(extents=(20, 30, 10)).export(path)

            with patch.dict(os.environ, {"USE_LLM_EXPLAINER": "false"}):
                result = build_plan_app().invoke({
                    "description": "open-top box for screws",
                    "stl_path": str(path),
                })

        self.assertTrue(result["needs_clarification"])
        self.assertEqual(3, len(result["clarification_questions"]))
        self.assertNotIn("plan", result)


if __name__ == "__main__":
    unittest.main()
