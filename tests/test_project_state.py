import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import project_state


class StateFoundationTests(unittest.TestCase):
    def test_new_state_has_revision_one_and_required_sections(self):
        state = project_state.new_state(
            name="Demo",
            summary="Build a demo",
            success_criteria=["Runs"],
            constraints=["No network"],
            now="2026-09-20T00:00:00Z",
        )

        self.assertEqual(state["schema_version"], 1)
        self.assertEqual(state["revision"], 1)
        self.assertEqual(state["project"]["status"], "planning")
        self.assertEqual(state["milestones"], [])
        self.assertEqual(state["work_items"], [])

    def test_validate_state_rejects_missing_required_field(self):
        state = project_state.new_state(
            "Demo", "Build a demo", ["Runs"], [], now="2026-09-20T00:00:00Z"
        )
        del state["project"]["summary"]

        with self.assertRaisesRegex(project_state.ValidationError, "summary"):
            project_state.validate_state(state)

    def test_validate_state_rejects_invalid_project_status(self):
        state = project_state.new_state(
            "Demo", "Build a demo", ["Runs"], [], now="2026-09-20T00:00:00Z"
        )
        state["project"]["status"] = "unknown"

        with self.assertRaisesRegex(project_state.ValidationError, "project.status"):
            project_state.validate_state(state)

    def test_validate_state_rejects_non_utc_timestamp(self):
        state = project_state.new_state(
            "Demo", "Build a demo", ["Runs"], [], now="2026-09-20T00:00:00+08:00"
        )

        with self.assertRaisesRegex(project_state.ValidationError, "created_at"):
            project_state.validate_state(state)


if __name__ == "__main__":
    unittest.main()
