from __future__ import annotations

import unittest

from core.nodes.analyze_risks import analyze_risks_node
from core.nodes.generate_slicer_settings import generate_slicer_settings_node
from core.nodes.normalize_input import normalize_input_node
from core.nodes.plan_orientation import plan_orientation_node
from core.nodes.select_material import select_material_node


def run_rules(description: str, height_mm: float, width_mm: float, planning_context: dict | None = None) -> dict:
    state = {
        "description": description,
        "height_mm": height_mm,
        "width_mm": width_mm,
        "planning_context": planning_context or {},
    }
    for node in (
        normalize_input_node,
        select_material_node,
        plan_orientation_node,
        generate_slicer_settings_node,
        analyze_risks_node,
    ):
        state = node(state)
    return state


class PlanningRulesTests(unittest.TestCase):
    def test_functional_part_gets_stronger_defaults(self):
        state = run_rules("functional wall mount bracket", 20, 40)
        settings = state["slicer_settings"]["settings"]

        self.assertEqual("PLA", state["material"]["recommended"])
        self.assertGreaterEqual(settings["walls"], 4)
        self.assertGreaterEqual(settings["infill_percent"], 20)

    def test_outdoor_part_recommends_asa_and_warns_about_warping(self):
        state = run_rules("outdoor garden hook", 80, 30)

        self.assertEqual("ASA", state["material"]["recommended"])
        self.assertEqual("high", state["risks"]["summary"]["highest_severity"])
        self.assertIn("warping_abs_asa", [risk["id"] for risk in state["risks"]["items"]])

    def test_stl_contact_signals_add_adhesion_protection(self):
        state = {
            "description": "functional bracket",
            "height_mm": 30,
            "width_mm": 30,
            "stl_features": {
                "contact_area_mm2": 100,
                "contact_ratio": 0.1,
                "likely_supports": False,
                "watertight": True,
                "is_volume": True,
            },
        }
        for node in (
            normalize_input_node,
            select_material_node,
            plan_orientation_node,
            generate_slicer_settings_node,
            analyze_risks_node,
        ):
            state = node(state)

        self.assertGreaterEqual(state["slicer_settings"]["settings"]["brim_mm"], 10)
        self.assertIn("adhesion_low_contact", [risk["id"] for risk in state["risks"]["items"]])

    def test_vehicle_heat_and_high_load_get_conservative_plan(self):
        state = run_rules(
            "replacement mounting bracket",
            40,
            80,
            {
                "environment": "car_or_engine",
                "purpose": "functional",
                "load": "high",
            },
        )
        settings = state["slicer_settings"]["settings"]

        self.assertEqual("ASA", state["material"]["recommended"])
        self.assertGreaterEqual(settings["walls"], 5)
        self.assertGreaterEqual(settings["infill_percent"], 40)
        self.assertIn("validate_critical_part", [risk["id"] for risk in state["risks"]["items"]])


if __name__ == "__main__":
    unittest.main()
