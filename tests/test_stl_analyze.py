from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import trimesh

from core.stl import analyze_model, analyze_stl
from tests.three_mf_fixture import box_3mf_bytes, translated_box_3mf_bytes


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

            with self.assertRaisesRegex(ValueError, "model|STL"):
                analyze_stl(str(path))

    def test_3mf_unit_metadata_is_converted_to_millimeters(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "inch-box.3mf"
            path.write_bytes(box_3mf_bytes(unit="inch", x=1, y=2, z=3))

            features = analyze_model(str(path))

        self.assertEqual("3mf", features["source_format"])
        self.assertEqual("inch", features["source_unit"])
        self.assertEqual(1, features["object_count"])
        self.assertEqual((25.4, 50.8, 76.19999999999999), features["bbox_mm"])

    def test_invalid_3mf_archive_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "invalid.3mf"
            path.write_bytes(b"not a zip archive")

            with self.assertRaisesRegex(ValueError, "3MF"):
                analyze_model(str(path))

    def test_3mf_transform_translation_uses_declared_unit(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "translated-boxes.3mf"
            path.write_bytes(translated_box_3mf_bytes())

            features = analyze_model(str(path))

        self.assertEqual(2, features["build_item_count"])
        self.assertAlmostEqual(76.2, features["bbox_mm"][0])


if __name__ == "__main__":
    unittest.main()
