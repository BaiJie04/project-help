# Project Workflow v0.1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a portable personal-development project workflow skill with revision-checked JSON state, deterministic Markdown rendering, optional standard-library tooling, and Git-aware prompts.

**Architecture:** `project.json` is the only state source. A standard-library Python module validates and atomically applies state changes, renders `PROJECT.md`, and exposes a small CLI. `SKILL.md` and plain-text references provide the cross-platform behavioral contract, while templates, an example, and scenario documents make the workflow testable without third-party dependencies.

**Tech Stack:** Markdown, JSON, Python 3.10+, `unittest`, standard library only, Git.

**Spec:** `docs/superpowers/specs/2026-09-20-project-workflow-design.md`

## Global Constraints

- Use Python 3.10 or newer and only the Python standard library.
- Keep `project.json` as the single source of truth and `PROJECT.md` as a generated view.
- Use Chinese natural-language prompts and English identifiers, filenames, enums, and Git commit types.
- Do not require Git, Python, platform-specific tools, network access, or third-party packages for core use.
- Write tests before production code and verify each test fails for the expected reason.
- Never infer permission to push Git changes.
- Keep the MIT License in the repository.
- Follow the exact state enums and rules in the approved design spec.

---

### Task 1: State Foundation and Basic Validation

**Files:**
- Create: `scripts/project_state.py`
- Create: `tests/test_project_state.py`
- Create: `tests/fixtures/__init__.py`

**Interfaces:**
- Produces: `ValidationError`
- Produces: `new_state(name: str, summary: str, success_criteria: list[str], constraints: list[str], status: str = "planning", now: str | None = None) -> dict`
- Produces: `validate_state(state: dict) -> None`
- Produces: constants `PROJECT_STATUSES`, `SCHEMA_VERSION`

- [ ] **Step 1: Write failing foundation tests**

```python
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
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `python -m unittest tests.test_project_state -v`  
Expected: import failure because `project_state` and `new_state` do not exist.

- [ ] **Step 3: Implement the minimal state foundation**

```python
SCHEMA_VERSION = 1
PROJECT_STATUSES = {"planning", "active", "paused", "completed", "archived"}


class ValidationError(ValueError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_state(name, summary, success_criteria, constraints, status="planning", now=None):
    timestamp = now or utc_now()
    return {
        "schema_version": SCHEMA_VERSION,
        "revision": 1,
        "project": {
            "id": "PRJ-001",
            "name": name,
            "summary": summary,
            "status": status,
            "constraints": list(constraints),
            "success_criteria": list(success_criteria),
            "created_at": timestamp,
            "updated_at": timestamp,
        },
        "milestones": [],
        "iterations": [],
        "work_items": [],
        "risks": [],
        "decisions": [],
    }


def validate_state(state):
    if not isinstance(state, dict):
        raise ValidationError("state must be an object")
    if state.get("schema_version") != SCHEMA_VERSION:
        raise ValidationError("schema_version must be 1")
    if not isinstance(state.get("revision"), int) or state["revision"] < 1:
        raise ValidationError("revision must be a positive integer")
    project = state.get("project")
    if not isinstance(project, dict):
        raise ValidationError("project must be an object")
    for field in ("id", "name", "summary", "status", "constraints", "success_criteria", "created_at", "updated_at"):
        if field not in project:
            raise ValidationError(f"project.{field} is required")
    if project["status"] not in PROJECT_STATUSES:
        raise ValidationError("project.status is invalid")
    for field in ("created_at", "updated_at"):
        _validate_utc_timestamp(project[field], f"project.{field}")
```

- [ ] **Step 4: Run the focused tests and verify they pass**

Run: `python -m unittest tests.test_project_state.StateFoundationTests -v`  
Expected: all foundation tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/project_state.py tests/test_project_state.py tests/fixtures/__init__.py
git commit -m "feat: add project state foundation"
```

### Task 2: Entity Integrity and Completion Rules

**Files:**
- Modify: `scripts/project_state.py`
- Modify: `tests/test_project_state.py`

**Interfaces:**
- Consumes: `ValidationError`, `new_state`, `validate_state`
- Produces: validation for IDs, references, dependency cycles, decisions, and completion rules

- [ ] **Step 1: Write failing integrity tests**

```python
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
        state["work_items"] = [self.work_item(
            "T-001",
            status="done",
            criteria=[{"id": "AC-001", "text": "Passes", "status": "pending"}],
        )]

        with self.assertRaisesRegex(project_state.ValidationError, "completion_exception"):
            project_state.validate_state(state)

        state["work_items"][0]["completion_exception"] = True
        state["work_items"][0]["completion_note"] = "User accepted the unmet criterion."
        state["work_items"][0]["completed_at"] = "2026-09-21T00:00:00Z"
        project_state.validate_state(state)
```

- [ ] **Step 2: Run the focused tests and verify they fail**

Run: `python -m unittest tests.test_project_state.StateIntegrityTests -v`  
Expected: the new integrity tests fail because entity validation is not implemented.

- [ ] **Step 3: Implement entity validation**

Use these rules and helpers:

```python
ID_PATTERNS = {
    "milestones": r"^M-\d{3,}$",
    "iterations": r"^I-\d{3,}$",
    "work_items": r"^T-\d{3,}$",
    "risks": r"^R-\d{3,}$",
    "decisions": r"^D-\d{3,}$",
}

WORK_ITEM_TYPES = {"epic", "story", "task", "bug", "spike"}
WORK_ITEM_STATUSES = {"backlog", "ready", "in_progress", "blocked", "review", "done", "cancelled"}
PRIORITIES = {"p0", "p1", "p2", "p3"}


def _validate_ids(items, pattern, collection):
    seen = set()
    for item in items:
        item_id = item.get("id")
        if not isinstance(item_id, str) or not re.fullmatch(pattern, item_id):
            raise ValidationError(f"{collection}.id is invalid")
        if item_id in seen:
            raise ValidationError(f"duplicate ID in {collection}: {item_id}")
        seen.add(item_id)


def _detect_work_item_cycle(work_items):
    graph = {item["id"]: item.get("depends_on", []) for item in work_items}
    visiting, visited = set(), set()

    def visit(node):
        if node in visiting:
            raise ValidationError("work item dependency cycle detected")
        if node in visited:
            return
        visiting.add(node)
        for dependency in graph[node]:
            if dependency not in graph:
                raise ValidationError(f"unknown work item dependency: {dependency}")
            visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)
```

Validate required work-item fields, enums, acceptance criteria IDs/statuses, references, self-dependencies, cycles, and the `done` rule. Apply analogous required-field and enum checks to milestones, iterations, risks, and decisions. Validate `supersedes` against decision IDs.

- [ ] **Step 4: Run all state tests and verify they pass**

Run: `python -m unittest tests.test_project_state -v`  
Expected: all state foundation and integrity tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/project_state.py tests/test_project_state.py
git commit -m "feat: validate project state integrity"
```

### Task 3: Deterministic Rendering and Atomic Apply

**Files:**
- Modify: `scripts/project_state.py`
- Modify: `tests/test_project_state.py`

**Interfaces:**
- Consumes: `ValidationError`, `validate_state`
- Produces: `render_project_md(state: dict) -> str`
- Produces: `load_state(path: Path) -> dict`
- Produces: `apply_candidate(project_dir: Path, candidate: dict, expected_revision: int) -> dict`

- [ ] **Step 1: Write failing rendering and apply tests**

```python
class StateRenderingAndApplyTests(unittest.TestCase):
    def test_render_project_md_contains_required_sections(self):
        state = project_state.new_state(
            "Demo", "Build a demo", ["Runs"], ["No network"], now="2026-09-20T00:00:00Z"
        )

        rendered = project_state.render_project_md(state)

        for heading in ("Project Summary", "Success Criteria", "Constraints", "Next Actions", "Risks", "Decisions"):
            self.assertIn(f"## {heading}", rendered)

    def test_apply_rejects_revision_mismatch_without_touching_files(self):
        with tempfile.TemporaryDirectory() as temp:
            project_dir = Path(temp) / ".project"
            state = project_state.new_state(
                "Demo", "Build a demo", ["Runs"], [], now="2026-09-20T00:00:00Z"
            )
            project_state.write_new_project(project_dir, state)
            before = (project_dir / "project.json").read_text(encoding="utf-8")
            candidate = dict(state)
            candidate["revision"] = 2

            with self.assertRaisesRegex(project_state.ValidationError, "revision"):
                project_state.apply_candidate(project_dir, candidate, expected_revision=99)

            self.assertEqual((project_dir / "project.json").read_text(encoding="utf-8"), before)

    def test_apply_writes_state_and_generated_view(self):
        with tempfile.TemporaryDirectory() as temp:
            project_dir = Path(temp) / ".project"
            state = project_state.new_state(
                "Demo", "Build a demo", ["Runs"], [], now="2026-09-20T00:00:00Z"
            )
            project_state.write_new_project(project_dir, state)
            candidate = copy.deepcopy(state)
            candidate["revision"] = 2
            candidate["project"]["summary"] = "Updated"

            applied = project_state.apply_candidate(project_dir, candidate, expected_revision=1)

            self.assertEqual(applied["revision"], 2)
            self.assertEqual(project_state.load_state(project_dir / "project.json")["project"]["summary"], "Updated")
            self.assertIn("Updated", (project_dir / "PROJECT.md").read_text(encoding="utf-8"))
```

- [ ] **Step 2: Run the focused tests and verify they fail**

Run: `python -m unittest tests.test_project_state.StateRenderingAndApplyTests -v`  
Expected: failures because rendering, project writes, and apply are not implemented.

- [ ] **Step 3: Implement rendering and atomic writes**

Use this behavior:

```python
def render_project_md(state):
    validate_state(state)
    project = state["project"]
    lines = [
        f"# {project['name']}",
        "",
        "## Project Summary",
        "",
        project["summary"],
        "",
        f"**Status:** `{project['status']}`",
        f"**Revision:** `{state['revision']}`",
        "",
        "## Success Criteria",
        "",
    ]
    lines.extend(_render_bullets(project["success_criteria"], "No success criteria recorded."))
    lines.extend(["", "## Constraints", ""])
    lines.extend(_render_bullets(project["constraints"], "No constraints recorded."))
    lines.extend(["", "## Next Actions", ""])
    lines.extend(_render_next_actions(state["work_items"]))
    lines.extend(["", "## Blocked Work", ""])
    lines.extend(_render_blocked_work(state["work_items"]))
    lines.extend(["", "## Milestones", ""])
    lines.extend(_render_entity_table(state["milestones"], ("ID", "Title", "Status", "Target")))
    lines.extend(["", "## Iterations", ""])
    lines.extend(_render_entity_table(state["iterations"], ("ID", "Title", "Status", "Goal")))
    lines.extend(["", "## Work Items", ""])
    lines.extend(_render_entity_table(state["work_items"], ("ID", "Priority", "Status", "Title")))
    lines.extend(["", "## Risks", ""])
    lines.extend(_render_entity_table(state["risks"], ("ID", "Probability", "Impact", "Status", "Title")))
    lines.extend(["", "## Decisions", ""])
    lines.extend(_render_entity_table(state["decisions"], ("ID", "Status", "Title")))
    return "\n".join(lines).rstrip() + "\n"


def write_new_project(project_dir, state):
    validate_state(state)
    project_dir.mkdir(parents=True, exist_ok=False)
    state_path = project_dir / "project.json"
    _write_text_atomic(state_path, json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    _write_text_atomic(project_dir / "PROJECT.md", render_project_md(state))


def apply_candidate(project_dir, candidate, expected_revision):
    current_path = project_dir / "project.json"
    current = load_state(current_path)
    if current["revision"] != expected_revision:
        raise ValidationError("revision mismatch")
    if candidate.get("revision") != expected_revision + 1:
        raise ValidationError("candidate revision must equal expected revision plus one")
    validate_state(candidate)
    _write_text_atomic(current_path, json.dumps(candidate, ensure_ascii=False, indent=2) + "\n")
    _write_text_atomic(project_dir / "PROJECT.md", render_project_md(candidate))
    return candidate
```

`_write_text_atomic` writes a temporary file in the same directory, flushes and closes it, then uses `os.replace`. On failure, remove the temporary file. Work items are ranked by priority order `p0`, `p1`, `p2`, `p3`, then by their JSON array order.

- [ ] **Step 4: Run all state tests and verify they pass**

Run: `python -m unittest tests.test_project_state -v`  
Expected: all state tests pass and no temporary files remain.

- [ ] **Step 5: Commit**

```bash
git add scripts/project_state.py tests/test_project_state.py
git commit -m "feat: render and atomically apply project state"
```

### Task 4: Standard-Library CLI

**Files:**
- Modify: `scripts/project_state.py`
- Modify: `tests/test_project_state.py`

**Interfaces:**
- Consumes: `new_state`, `validate_state`, `load_state`, `apply_candidate`, `render_project_md`, `write_new_project`
- Produces: `build_parser() -> argparse.ArgumentParser`
- Produces: `main(argv: list[str] | None = None) -> int`

- [ ] **Step 1: Write failing CLI tests**

```python
class ProjectStateCliTests(unittest.TestCase):
    def run_main(self, *args):
        return project_state.main([str(arg) for arg in args])

    def test_init_creates_project_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            result = self.run_main("init", "--root", root, "--name", "Demo", "--summary", "Build a demo", "--success", "Runs")

            self.assertEqual(result, 0)
            self.assertTrue((root / ".project" / "project.json").exists())

    def test_apply_returns_two_on_revision_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = project_state.new_state(
                "Demo", "Build a demo", ["Runs"], [], now="2026-09-20T00:00:00Z"
            )
            project_state.write_new_project(root / ".project", state)
            candidate = root / "candidate.json"
            state["revision"] = 2
            candidate.write_text(json.dumps(state), encoding="utf-8")

            result = self.run_main("apply", "--root", root, "--expected-revision", 99, "--file", candidate)

            self.assertEqual(result, 2)

    def test_validate_returns_zero_for_valid_state(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project_state.write_new_project(root / ".project", project_state.new_state(
                "Demo", "Build a demo", ["Runs"], [], now="2026-09-20T00:00:00Z"
            ))

            self.assertEqual(self.run_main("validate", "--root", root), 0)
```

- [ ] **Step 2: Run the focused tests and verify they fail**

Run: `python -m unittest tests.test_project_state.ProjectStateCliTests -v`  
Expected: failures because `main` and `build_parser` are not implemented.

- [ ] **Step 3: Implement the CLI**

Support the exact commands from the spec:

```text
project_state.py init --root ROOT --name NAME --summary SUMMARY --success VALUE [--success VALUE] [--constraint VALUE]
project_state.py validate --root ROOT
project_state.py apply --root ROOT --expected-revision N --file CANDIDATE.json
project_state.py render --root ROOT
project_state.py summary --root ROOT
```

`init` rejects an existing `.project/` without overwriting it. `validate` and `render` load `.project/project.json`. `summary` prints project name, status, revision, milestone count, work-item counts by status, active risk count, and the next three ready/in-progress work items. Validation and expected user errors return `2`; successful commands return `0`; unexpected programming errors propagate.

- [ ] **Step 4: Run the CLI and full state tests**

Run: `python -m unittest tests.test_project_state -v`  
Expected: all tests pass.

- [ ] **Step 5: Manually smoke-test the CLI**

Run:

```bash
python scripts/project_state.py init --root /tmp/project-workflow-smoke --name Demo --summary "Build a demo" --success Runs
python scripts/project_state.py validate --root /tmp/project-workflow-smoke
python scripts/project_state.py render --root /tmp/project-workflow-smoke
```

Expected: each command returns `0`, prints a useful result, and creates valid JSON and Markdown files.

- [ ] **Step 6: Commit**

```bash
git add scripts/project_state.py tests/test_project_state.py
git commit -m "feat: add project state cli"
```

### Task 5: Personal Project Example and Integration Flow

**Files:**
- Create: `examples/personal-project/.project/project.json`
- Create: `examples/personal-project/.project/PROJECT.md`
- Create: `tests/fixtures/personal-project.json`
- Modify: `tests/test_project_state.py`

**Interfaces:**
- Consumes: `validate_state`, `render_project_md`, `apply_candidate`
- Produces: a complete valid personal-project state used as an integration fixture

- [ ] **Step 1: Write the failing integration test**

```python
class PersonalProjectIntegrationTests(unittest.TestCase):
    def test_personal_project_fixture_validates_and_renders(self):
        fixture = ROOT / "tests" / "fixtures" / "personal-project.json"
        state = json.loads(fixture.read_text(encoding="utf-8"))

        project_state.validate_state(state)

        rendered = project_state.render_project_md(state)
        committed = (ROOT / "examples" / "personal-project" / ".project" / "PROJECT.md").read_text(encoding="utf-8")
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
            candidate["project"]["updated_at"] = "2026-09-21T00:00:00Z"

            changed = project_state.apply_candidate(project_dir, candidate, state["revision"])

            self.assertEqual(changed["revision"], state["revision"] + 1)
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `python -m unittest tests.test_project_state.PersonalProjectIntegrationTests -v`  
Expected: failure because the fixture and example files do not exist.

- [ ] **Step 3: Create the personal project fixture**

Create a `content-site` example with:

- Project ID `PRJ-001`, active status, revision `1`.
- Goal: publish a personal documentation site.
- Success criteria: responsive layout, search, deployment guide.
- Constraints: one maintainer, no paid services.
- Two milestones and two iterations.
- At least six work items covering `epic`, `story`, `task`, and `bug`.
- Dependencies with no cycles, one blocked item, and one completed item with all criteria met.
- One active risk and one accepted decision.

Use UTC timestamps beginning `2026-09-20T00:00:00Z` and increase them consistently.

- [ ] **Step 4: Generate and verify the example view**

Copy the validated fixture to `examples/personal-project/.project/project.json`, then run:

```bash
python -c "import json, pathlib, sys; sys.path.insert(0, 'scripts'); import project_state; p=pathlib.Path('examples/personal-project/.project/project.json'); s=json.loads(p.read_text(encoding='utf-8')); pathlib.Path('examples/personal-project/.project/PROJECT.md').write_text(project_state.render_project_md(s), encoding='utf-8')"
python -m unittest tests.test_project_state.PersonalProjectIntegrationTests -v
```

Expected: both integration tests pass and `PROJECT.md` matches the renderer exactly.

- [ ] **Step 5: Commit**

```bash
git add examples/personal-project tests/fixtures/personal-project.json tests/test_project_state.py
git commit -m "test: add personal project integration example"
```

### Task 6: Portable Skill Instructions, References, and Templates

**Files:**
- Create: `SKILL.md`
- Create: `agents/openai.yaml`
- Create: `references/method.md`
- Create: `references/state-model.md`
- Create: `references/portability.md`
- Create: `references/workflows/init.md`
- Create: `references/workflows/plan.md`
- Create: `references/workflows/update.md`
- Create: `references/workflows/review.md`
- Create: `references/workflows/close.md`
- Create: `templates/project.json`
- Create: `templates/PROJECT.md`
- Create: `tests/test_documentation.py`

**Interfaces:**
- Consumes: the CLI commands and state contract implemented in Tasks 1-5
- Produces: platform-neutral instructions that select Skill, File, or Chat mode and route to the correct workflow reference

- [ ] **Step 1: Write the failing documentation and template tests**

```python
class DocumentationTests(unittest.TestCase):
    def test_skill_links_resolve(self):
        for source in (ROOT / "SKILL.md", *sorted((ROOT / "references").rglob("*.md"))):
            text = source.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                if "://" not in target and not target.startswith("#"):
                    self.assertTrue((source.parent / target).resolve().exists(), f"{source}: {target}")

    def test_project_template_validates(self):
        state = json.loads((ROOT / "templates" / "project.json").read_text(encoding="utf-8"))
        project_state.validate_state(state)

    def test_openai_metadata_matches_skill_name(self):
        metadata = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn('display_name: "Project Workflow"', metadata)
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `python -m unittest tests.test_documentation -v`  
Expected: failures because the skill files, references, templates, and README do not exist.

- [ ] **Step 3: Write `SKILL.md` and platform metadata**

`SKILL.md` frontmatter:

```yaml
---
name: project-workflow
description: Use when managing a personal development project, including project initialization, backlog and iteration planning, task and risk updates, reviews, decisions, and closure.
---
```

The body must:

- Detect `project.json`, file writes, script execution, and Git availability before choosing a mode.
- Route `init`, `plan`, `update`, `review`, and `close` to the matching reference.
- State that `project.json` is authoritative and `PROJECT.md` is generated.
- Require confirmation before writes and commits.
- Require a complete candidate JSON for state changes.
- Direct the model to the CLI when Python is available.
- Forbid automatic pushes and unrelated file changes.

`agents/openai.yaml` provides only Codex UI metadata:

```yaml
interface:
  display_name: "Project Workflow"
  short_description: "Portable personal project workflow"
  default_prompt: "Manage this project using the project-workflow skill."
```

- [ ] **Step 4: Write method, state, portability, and workflow references**

`references/method.md` defines the development lifecycle, quality gates, task-completion evidence, review criteria, and closure rules.

`references/state-model.md` reproduces the complete schema, enums, ID rules, relationships, completion exception, revision protocol, and render sections from the approved spec.

`references/portability.md` defines Skill, File, and Chat modes and the unified response contract.

Each workflow reference contains:

- Preconditions and required inputs.
- Read-only analysis steps.
- Candidate-state construction rules.
- Validation and confirmation requirements.
- Git commit proposal.
- Chat-mode fallback.
- Concrete example request and expected state effects.

- [ ] **Step 5: Create templates**

Copy the personal-project fixture into `templates/project.json`, replace project-specific content with a minimal valid `planning` project, and generate `templates/PROJECT.md` through `render_project_md`. Templates must validate and must not retain the example project's work items or decisions.

- [ ] **Step 6: Run documentation and full tests**

Run: `python -m unittest discover -s tests -v`  
Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add SKILL.md agents references templates tests/test_documentation.py
git commit -m "feat: add portable project workflow skill"
```

### Task 7: Cross-Platform Prompt Scenarios

**Files:**
- Create: `tests/scenarios/init-project.md`
- Create: `tests/scenarios/blocked-work.md`
- Create: `tests/scenarios/overdue-review.md`
- Create: `tests/scenarios/acceptance-evidence.md`
- Create: `tests/scenarios/risk-escalation.md`
- Create: `tests/scenarios/project-retrospective.md`
- Create: `tests/scenarios/chat-only-fallback.md`
- Modify: `tests/test_documentation.py`

**Interfaces:**
- Consumes: the workflow references and unified output contract
- Produces: manually executable evaluation scenarios with observable state assertions

- [ ] **Step 1: Write the failing scenario-structure test**

```python
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
            for heading in ("## Runtime Capabilities", "## User Prompt", "## Expected Behavior", "## State Assertions", "## Failure Conditions"):
                self.assertIn(heading, text, name)
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `python -m unittest tests.test_documentation.PromptScenarioTests -v`  
Expected: failure because the scenario directory and files do not exist.

- [ ] **Step 3: Write the seven scenario documents**

Each scenario must include:

1. Runtime capabilities such as files, script, Git, or chat-only.
2. A realistic Chinese user prompt.
3. Expected behavioral decisions.
4. Exact state assertions such as revision increments, status transitions, required notes, or no-write behavior.
5. Failure conditions that indicate the skill did not follow its contract.

Cover these cases:

- Initialize a blank personal project and ask before enabling Git.
- Block a task with a missing dependency and require a `blocked_reason`.
- Review an overdue iteration without writing unless the user accepts proposed updates.
- Complete a task only after acceptance evidence is supplied.
- Escalate a risk from medium to high and record mitigation changes.
- Close a project after recording outcome, incomplete work, and lessons learned.
- Use Chat mode to return complete updated JSON when files, scripts, and Git are unavailable.

- [ ] **Step 4: Run documentation tests and manually inspect one scenario**

Run: `python -m unittest tests.test_documentation -v`  
Expected: all structural documentation tests pass.

Open `tests/scenarios/chat-only-fallback.md` and verify that it requires a complete JSON state, an explicit fallback statement, and no claim that files or Git were modified.

- [ ] **Step 5: Commit**

```bash
git add tests/scenarios tests/test_documentation.py
git commit -m "test: add portable prompt scenarios"
```

### Task 8: Packaging, Installation Guide, Verification, and Release Metadata

**Files:**
- Create: `README.md`
- Create: `LICENSE`
- Create: `CHANGELOG.md`
- Create: `pyproject.toml`
- Modify: `tests/test_documentation.py`

**Interfaces:**
- Consumes: the complete skill, CLI, templates, example, and tests
- Produces: user documentation and version metadata for `v0.1.0`

- [ ] **Step 1: Write failing packaging tests**

```python
class PackagingTests(unittest.TestCase):
    def test_readme_documents_three_portability_modes(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for heading in ("Skill Mode", "File Mode", "Chat Mode", "Installation", "GitHub Upload"):
            self.assertIn(f"## {heading}", readme)

    def test_release_metadata_uses_mit_and_v010(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn('version = "0.1.0"', pyproject)
        self.assertIn("MIT License", (ROOT / "LICENSE").read_text(encoding="utf-8"))
        self.assertIn("## [0.1.0]", changelog)
```

- [ ] **Step 2: Run the focused tests and verify they fail**

Run: `python -m unittest tests.test_documentation.PackagingTests -v`  
Expected: failure because README, license, changelog, and package metadata do not exist.

- [ ] **Step 3: Write README installation and usage instructions**

README sections must include:

- Purpose and v0.1.0 scope.
- Repository layout.
- Skill Mode installation for a skill-aware runtime.
- File Mode setup using `SKILL.md` as custom instructions and repository access.
- Chat Mode instructions for pasting the compact contract and complete state.
- CLI command examples.
- Managed project `.project/` layout.
- Git behavior and confirmation rules.
- Test command.
- GitHub Upload instructions using `git remote add`, `git push -u`, and optional `v0.1.0` tag commands.
- A clear statement that the skill does not push automatically.

- [ ] **Step 4: Add license, changelog, and package metadata**

- `LICENSE` contains the standard MIT License with year `2026` and copyright holder `yao-wen-yi`.
- `CHANGELOG.md` uses Keep a Changelog style and records `0.1.0` with the initial portable personal-project workflow.
- `pyproject.toml` declares project name `project-workflow-skill`, version `0.1.0`, Python `>=3.10`, MIT license, README, and no runtime dependencies.

- [ ] **Step 5: Run the complete verification suite**

Run:

```bash
python -m unittest discover -s tests -v
python scripts/project_state.py validate --root examples/personal-project
```

Expected: all automated tests pass and the personal-project example validates with revision `1`.

- [ ] **Step 6: Review the repository for portability**

Confirm:

- `SKILL.md` and workflow references do not require a specific AI product.
- Core behavior remains available without Python or Git.
- Script and Git usage are explicitly optional.
- No README or prompt instructs the agent to push automatically.
- `PROJECT.md` contains a generated-view notice and is reproducible from JSON.

- [ ] **Step 7: Commit and tag**

```bash
git add README.md LICENSE CHANGELOG.md pyproject.toml tests/test_documentation.py
git commit -m "docs: prepare project workflow v0.1.0 release"
git tag -a v0.1.0 -m "project-workflow v0.1.0"
```

## Spec Coverage Review

- Repository structure and MIT license: Tasks 6 and 8.
- Portable methodology and Chinese prompts: Tasks 6 and 7.
- JSON source of truth and Markdown view: Tasks 1, 3, and 5.
- Schema, enums, IDs, references, dependency cycles, and completion exceptions: Tasks 1 and 2.
- Revision checks and atomic writes: Task 3.
- CLI commands: Task 4.
- Personal project example: Task 5.
- Five workflows: Task 6.
- Skill, File, and Chat modes: Tasks 6 and 7.
- Git confirmation and no-push behavior: Tasks 6 and 8.
- Automated tests and scenario tests: Tasks 1-8.
- v0.1.0 release metadata and tag: Task 8.

## Execution Notes

- Keep each commit scoped to the files listed in that task.
- Run the focused test before every implementation step and run the full suite before every commit that changes production code.
- If a test reveals that the specified interface is wrong, stop and update the plan before implementation continues.
- GitHub pushing remains a user action after the local `v0.1.0` tag is verified.
