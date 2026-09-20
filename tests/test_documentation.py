import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import project_state


class DocumentationTests(unittest.TestCase):
    def test_skill_links_resolve(self):
        for source in (
            ROOT / "SKILL.md",
            *sorted((ROOT / "references").rglob("*.md")),
        ):
            text = source.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                if "://" not in target and not target.startswith("#"):
                    self.assertTrue(
                        (source.parent / target).resolve().exists(),
                        f"{source}: {target}",
                    )

    def test_project_template_validates(self):
        state = json.loads(
            (ROOT / "templates" / "project.json").read_text(encoding="utf-8")
        )
        project_state.validate_state(state)

    def test_openai_metadata_matches_skill_name(self):
        metadata = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn('display_name: "Project Workflow"', metadata)


class PromptScenarioTests(unittest.TestCase):
    def test_required_scenarios_have_contract_sections(self):
        expected = {
            "init-project.md",
            "blocked-work.md",
            "overdue-review.md",
            "acceptance-evidence.md",
            "risk-escalation.md",
            "project-retrospective.md",
            "chat-only-fallback.md",
        }
        scenario_dir = ROOT / "tests" / "scenarios"
        self.assertEqual(expected, {path.name for path in scenario_dir.glob("*.md")})
        for name in expected:
            text = (scenario_dir / name).read_text(encoding="utf-8")
            for heading in (
                "## Runtime Capabilities",
                "## User Prompt",
                "## Expected Behavior",
                "## State Assertions",
                "## Failure Conditions",
            ):
                self.assertIn(heading, text, name)


if __name__ == "__main__":
    unittest.main()
