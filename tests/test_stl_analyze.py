from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import trimesh

from core.stl import analyze_stl


class STLAnalyzeTests(unittest.TestCase):
    def test_box_mesh_has_expected_dimensions(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "box.stl"
            trimesh.creation.box(extents=(10, 20, 30)).export(path)

            features = analyze_stl(str(path))

        self.assertEqual((10.0, 20.0, 30.0), features["bbox_mm"])
        self.assertTrue(features["watertight"])
        self.assertTrue(features["is_volume"])
        self.assertGreater(features["contact_area_mm2"], 0)

    def test_invalid_mesh_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "invalid.stl"
            path.write_text("not an stl", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "STL"):
                analyze_stl(str(path))


if __name__ == "__main__":
    unittest.main()
