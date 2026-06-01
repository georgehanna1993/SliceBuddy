from __future__ import annotations

import os
import json
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
import trimesh

from app.main import app


class APITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/health")

        self.assertEqual(200, response.status_code)
        self.assertEqual("ok", response.json()["status"])

    def test_rejects_non_stl_extension(self):
        response = self.client.post(
            "/plan",
            data={"use": "wall mount bracket"},
            files={"stl": ("notes.txt", b"hello", "text/plain")},
        )

        self.assertEqual(415, response.status_code)

    def test_rejects_empty_stl(self):
        response = self.client.post(
            "/plan",
            data={"use": "wall mount bracket"},
            files={"stl": ("empty.stl", b"", "application/octet-stream")},
        )

        self.assertEqual(422, response.status_code)

    def test_rejects_oversized_stl(self):
        with patch.dict(os.environ, {"MAX_STL_UPLOAD_MB": "1"}):
            response = self.client.post(
                "/plan",
                data={"use": "wall mount bracket"},
                files={"stl": ("large.stl", b"x" * (1024 * 1024 + 1), "application/octet-stream")},
            )

        self.assertEqual(413, response.status_code)

    def test_generates_plan_for_valid_stl(self):
        stl_bytes = trimesh.creation.box(extents=(10, 20, 30)).export(file_type="stl")

        response = self.client.post(
            "/plan",
            data={
                "use": "functional wall mount bracket",
                "planning_context": json.dumps({
                    "environment": "indoor",
                    "purpose": "functional",
                    "load": "moderate",
                }),
            },
            files={"stl": ("bracket.stl", stl_bytes, "application/octet-stream")},
        )

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertFalse(payload["stop"])
        self.assertIn("Print Plan", payload["plan_explanation"])
        self.assertEqual([10.0, 20.0, 30.0], payload["stl_features"]["bbox_mm"])

    def test_requests_clarification_before_generating_plan(self):
        stl_bytes = trimesh.creation.box(extents=(10, 20, 30)).export(file_type="stl")

        response = self.client.post(
            "/plan",
            data={"use": "functional wall mount bracket"},
            files={"stl": ("bracket.stl", stl_bytes, "application/octet-stream")},
        )

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertTrue(payload["needs_clarification"])
        self.assertEqual(
            ["environment", "purpose", "load"],
            [question["id"] for question in payload["clarification_questions"]],
        )


if __name__ == "__main__":
    unittest.main()
