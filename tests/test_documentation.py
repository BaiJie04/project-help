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


if __name__ == "__main__":
    unittest.main()
