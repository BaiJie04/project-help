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


class StateIntegrityTests(unittest.TestCase):
    def base_state(self):
        return project_state.new_state(
            "Demo", "Build a demo", ["Runs"], [], now="2026-09-20T00:00:00Z"
        )

    def work_item(self, item_id, depends_on=None, status="ready", criteria=None):
        return {
            "id": item_id,
            "type": "task",
            "title": item_id,
            "description": "Do work",
            "status": status,
            "priority": "p1",
            "acceptance_criteria": criteria or [],
            "depends_on": depends_on or [],
            "created_at": "2026-09-20T00:00:00Z",
            "updated_at": "2026-09-20T00:00:00Z",
        }

    def test_validate_state_rejects_duplicate_work_item_ids(self):
        state = self.base_state()
        state["work_items"] = [self.work_item("T-001"), self.work_item("T-001")]

        with self.assertRaisesRegex(project_state.ValidationError, "duplicate"):
            project_state.validate_state(state)

    def test_validate_state_rejects_dangling_dependency(self):
        state = self.base_state()
        state["work_items"] = [self.work_item("T-001", depends_on=["T-999"])]

        with self.assertRaisesRegex(project_state.ValidationError, "T-999"):
            project_state.validate_state(state)

    def test_validate_state_rejects_dependency_cycle(self):
        state = self.base_state()
        state["work_items"] = [
            self.work_item("T-001", depends_on=["T-002"]),
            self.work_item("T-002", depends_on=["T-001"]),
        ]

        with self.assertRaisesRegex(project_state.ValidationError, "cycle"):
            project_state.validate_state(state)

    def test_done_requires_met_criteria_or_documented_exception(self):
        state = self.base_state()
        state["work_items"] = [
            self.work_item(
                "T-001",
                status="done",
                criteria=[
                    {"id": "AC-001", "text": "Passes", "status": "pending"}
                ],
            )
        ]
        state["work_items"][0]["completion_note"] = (
            "User accepted the unmet criterion."
        )
        state["work_items"][0]["completed_at"] = "2026-09-21T00:00:00Z"

        with self.assertRaisesRegex(project_state.ValidationError, "completion_exception"):
            project_state.validate_state(state)

        state["work_items"][0]["completion_exception"] = True
        project_state.validate_state(state)


if __name__ == "__main__":
    unittest.main()
