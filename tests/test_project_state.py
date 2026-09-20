import copy
import contextlib
import io
import json
import sys
import tempfile
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


class StateRenderingAndApplyTests(unittest.TestCase):
    def test_render_project_md_contains_required_sections(self):
        state = project_state.new_state(
            "Demo",
            "Build a demo",
            ["Runs"],
            ["No network"],
            now="2026-09-20T00:00:00Z",
        )

        rendered = project_state.render_project_md(state)

        for heading in (
            "Project Summary",
            "Success Criteria",
            "Constraints",
            "Next Actions",
            "Risks",
            "Decisions",
        ):
            self.assertIn(f"## {heading}", rendered)

    def test_apply_rejects_revision_mismatch_without_touching_files(self):
        with tempfile.TemporaryDirectory() as temp:
            project_dir = Path(temp) / ".project"
            state = project_state.new_state(
                "Demo",
                "Build a demo",
                ["Runs"],
                [],
                now="2026-09-20T00:00:00Z",
            )
            project_state.write_new_project(project_dir, state)
            before = (project_dir / "project.json").read_text(encoding="utf-8")
            candidate = copy.deepcopy(state)
            candidate["revision"] = 2

            with self.assertRaisesRegex(project_state.ValidationError, "revision"):
                project_state.apply_candidate(
                    project_dir, candidate, expected_revision=99
                )

            self.assertEqual(
                (project_dir / "project.json").read_text(encoding="utf-8"), before
            )

    def test_apply_writes_state_and_generated_view(self):
        with tempfile.TemporaryDirectory() as temp:
            project_dir = Path(temp) / ".project"
            state = project_state.new_state(
                "Demo",
                "Build a demo",
                ["Runs"],
                [],
                now="2026-09-20T00:00:00Z",
            )
            project_state.write_new_project(project_dir, state)
            candidate = copy.deepcopy(state)
            candidate["revision"] = 2
            candidate["project"]["summary"] = "Updated"

            applied = project_state.apply_candidate(
                project_dir, candidate, expected_revision=1
            )

            self.assertEqual(applied["revision"], 2)
            self.assertEqual(
                project_state.load_state(project_dir / "project.json")["project"][
                    "summary"
                ],
                "Updated",
            )
            self.assertIn(
                "Updated",
                (project_dir / "PROJECT.md").read_text(encoding="utf-8"),
            )


class ProjectStateCliTests(unittest.TestCase):
    def run_main(self, *args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            return project_state.main([str(arg) for arg in args])

    def test_init_creates_project_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            result = self.run_main(
                "init",
                "--root",
                root,
                "--name",
                "Demo",
                "--summary",
                "Build a demo",
                "--success",
                "Runs",
            )

            self.assertEqual(result, 0)
            self.assertTrue((root / ".project" / "project.json").exists())
            self.assertTrue((root / ".project" / "PROJECT.md").exists())

    def test_apply_returns_two_on_revision_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = project_state.new_state(
                "Demo",
                "Build a demo",
                ["Runs"],
                [],
                now="2026-09-20T00:00:00Z",
            )
            project_state.write_new_project(root / ".project", state)
            candidate = root / "candidate.json"
            state["revision"] = 2
            candidate.write_text(json.dumps(state), encoding="utf-8")

            result = self.run_main(
                "apply",
                "--root",
                root,
                "--expected-revision",
                99,
                "--file",
                candidate,
            )

            self.assertEqual(result, 2)

    def test_validate_returns_zero_for_valid_state(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project_state.write_new_project(
                root / ".project",
                project_state.new_state(
                    "Demo",
                    "Build a demo",
                    ["Runs"],
                    [],
                    now="2026-09-20T00:00:00Z",
                ),
            )

            self.assertEqual(self.run_main("validate", "--root", root), 0)


class PersonalProjectIntegrationTests(unittest.TestCase):
    def test_personal_project_fixture_validates_and_renders(self):
        fixture = ROOT / "tests" / "fixtures" / "personal-project.json"
        state = json.loads(fixture.read_text(encoding="utf-8"))

        project_state.validate_state(state)

        rendered = project_state.render_project_md(state)
        committed = (
            ROOT
            / "examples"
            / "personal-project"
            / ".project"
            / "PROJECT.md"
        ).read_text(encoding="utf-8")
        self.assertEqual(rendered, committed)

    def test_personal_project_update_bumps_revision(self):
        fixture = ROOT / "tests" / "fixtures" / "personal-project.json"
        state = json.loads(fixture.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp:
            project_dir = Path(temp) / ".project"
            project_state.write_new_project(project_dir, state)
            candidate = copy.deepcopy(state)
            candidate["revision"] += 1
            candidate["work_items"][0]["status"] = "in_progress"
            candidate["work_items"][0]["updated_at"] = "2026-09-21T00:00:00Z"
            candidate["project"]["updated_at"] = "2026-09-21T00:00:00Z"

            changed = project_state.apply_candidate(
                project_dir, candidate, state["revision"]
            )

            self.assertEqual(changed["revision"], state["revision"] + 1)


if __name__ == "__main__":
    unittest.main()
