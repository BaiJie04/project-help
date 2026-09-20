# Project Workflow Skill v0.1.0 Design

## Status

Approved design for implementation planning. User review of this written specification is pending.

## Goal

Build a portable project-management skill for personal software and development projects. The same methodology, state format, and core prompts must work across different models and AI software. The first release targets personal projects, while keeping the state model extensible to small-team and multi-project use later.

The repository contains the reusable skill. Each managed project contains its own `.project/` state directory.

## Scope

Version 0.1.0 supports:

- Project initialization with goals, constraints, success criteria, and status.
- Milestones, iterations, backlog items, dependencies, priorities, and acceptance criteria.
- Task, risk, decision, blocker, and progress updates.
- Project review and reporting.
- Milestone and project closure with retrospectives.
- Git-aware operation with user-confirmed commits and no automatic pushes.
- Native skill, file-aware, and chat-only usage modes.

Version 0.1.0 does not include:

- Team roles or permissions.
- Enterprise budgets, procurement, or portfolio management.
- Bidirectional integrations with GitHub Issues, Jira, calendars, or other external systems.
- Automatic Git pushes.
- Any mandatory third-party Python package or platform-specific tool.

## Core Principles

1. `project.json` is the single source of truth. `PROJECT.md` is a generated human-readable view and must not drift from it.
2. The portable core uses plain Markdown, JSON, and Git concepts. Platform-specific capabilities are optional enhancements.
3. Chinese is the default language for natural-language prompts. Fields, enums, IDs, paths, and Git commit types use English.
4. State changes are explicit, revision-checked, validated, and written atomically.
5. Git operations require confirmation and affect only the selected `.project/` files unless the user explicitly requests otherwise.
6. Unsupported platform capabilities trigger a documented fallback instead of a false claim that an operation occurred.

## Repository Structure

```text
project-help/
|-- SKILL.md
|-- README.md
|-- LICENSE
|-- CHANGELOG.md
|-- pyproject.toml
|-- agents/
|   `-- openai.yaml
|-- references/
|   |-- method.md
|   |-- state-model.md
|   |-- portability.md
|   `-- workflows/
|       |-- init.md
|       |-- plan.md
|       |-- update.md
|       |-- review.md
|       `-- close.md
|-- templates/
|   |-- project.json
|   `-- PROJECT.md
|-- examples/
|   `-- personal-project/
|       |-- project.json
|       `-- PROJECT.md
|-- scripts/
|   `-- project_state.py
`-- tests/
    |-- fixtures/
    |-- scenarios/
    `-- test_project_state.py
```

The repository uses the MIT License.

## Managed Project Layout

```text
<project-root>/
`-- .project/
    |-- project.json
    `-- PROJECT.md
```

`project.json` stores current state only. Git stores historical changes. The state file does not duplicate a full chronological event log.

## State Model

Every state document includes `schema_version` and a positive integer `revision`. The initial revision is `1`. A valid update increments it by exactly one.

```json
{
  "schema_version": 1,
  "revision": 1,
  "project": {
    "id": "PRJ-001",
    "name": "Project name",
    "summary": "Project objective",
    "status": "planning",
    "constraints": [],
    "success_criteria": [],
    "created_at": "2026-09-20T00:00:00Z",
    "updated_at": "2026-09-20T00:00:00Z"
  },
  "milestones": [],
  "iterations": [],
  "work_items": [],
  "risks": [],
  "decisions": []
}
```

### IDs

IDs remain stable for the lifetime of an entity:

- Project: `PRJ-001`
- Milestone: `M-001`
- Iteration: `I-001`
- Work item: `T-001`
- Risk: `R-001`
- Decision: `D-001`

Each entity collection enforces uniqueness within its own ID namespace.
IDs are never reused. The next ID is the highest existing numeric suffix in that namespace plus one.

### Project

Required fields:

- `id`: valid project ID.
- `name`: non-empty string.
- `summary`: non-empty string.
- `status`: `planning`, `active`, `paused`, `completed`, or `archived`.
- `constraints`: array of strings.
- `success_criteria`: array of strings.
- `created_at` and `updated_at`: ISO 8601 timestamps in UTC.

### Milestones

Required fields:

- `id`, `title`, `description`, and `status`.
- `status`: `planned`, `active`, `completed`, or `cancelled`.
- `created_at` and `updated_at`.

Optional fields:

- `target_date`, `completed_at`, and `completion_note`.

### Iterations

Required fields:

- `id`, `title`, `goal`, `status`, `created_at`, and `updated_at`.
- `status`: `planned`, `active`, `completed`, or `cancelled`.

Optional fields:

- `start_date`, `end_date`, `completed_at`, and `completion_note`.

### Work Items

Required fields:

- `id`, `type`, `title`, `description`, `status`, `priority`, `created_at`, and `updated_at`.
- `type`: `epic`, `story`, `task`, `bug`, or `spike`.
- `status`: `backlog`, `ready`, `in_progress`, `blocked`, `review`, `done`, or `cancelled`.
- `priority`: `p0`, `p1`, `p2`, `p3`.
- `acceptance_criteria`: array of objects with unique `id`, `text`, and `status`.
- Acceptance-criteria status is `pending` or `met`.

Optional fields:

- `milestone_id`, `iteration_id`, `parent_id`, `depends_on`, `due_date`, `blocked_reason`, `completed_at`, `completion_note`, and `completion_exception`.

Rules:

- `depends_on` contains work-item IDs and must not contain self-references or cycles.
- `milestone_id`, `iteration_id`, and `parent_id` must reference existing entities of the correct type.
- A work item can be marked `done` when all acceptance criteria are `met`.
- If the user explicitly accepts incomplete criteria, set `completion_exception` to `true`, document every incomplete criterion in `completion_note`, and pass all mandatory automated checks.

### Risks

Required fields:

- `id`, `title`, `description`, `probability`, `impact`, `status`, `mitigation`, `created_at`, and `updated_at`.
- `probability`: `low`, `medium`, or `high`.
- `impact`: `low`, `medium`, or `high`.
- `status`: `open`, `mitigated`, `accepted`, or `closed`.

### Decisions

Required fields:

- `id`, `title`, `context`, `decision`, `rationale`, `consequences`, `status`, `created_at`, and `updated_at`.
- `status`: `proposed`, `accepted`, `rejected`, or `superseded`.

Optional fields:

- `supersedes`: an existing decision ID.

## Human-Readable View

`PROJECT.md` is deterministic and regenerated from `project.json`. Its sections are:

1. Project summary and status.
2. Success criteria and constraints.
3. Current milestone and iteration.
4. Next actions derived from ready and in-progress work items.
5. Blocked work and active risks.
6. Milestone and iteration summaries.
7. Work-item overview ordered by priority and planning order.
8. Recent accepted decisions.

Manual edits to `PROJECT.md` are treated as disposable. The next valid state update regenerates the file.

## Workflows

Every workflow follows this sequence:

1. Read the skill instructions and current `.project/project.json`.
2. Inspect Git availability and repository status.
3. Explain the intended state change and its impact.
4. Obtain user confirmation before writing.
5. Validate and atomically apply the candidate state.
6. Regenerate `PROJECT.md`.
7. Show a concise change summary and propose a Git commit.
8. Commit only after confirmation and never push automatically.

### `init`

- Collect the project name, summary, success criteria, constraints, and initial status.
- Create `.project/project.json` and `.project/PROJECT.md`.
- If Git is absent, ask whether to run `git init` instead of initializing it silently.

### `plan`

- Create or update milestones and iterations.
- Create work items with priorities, dependencies, and acceptance criteria.
- Detect duplicate IDs, dangling references, and dependency cycles before writing.

### `update`

- Update project, milestone, iteration, work-item, risk, or decision state.
- Require a completion note for work marked `done`.
- Require an explicit reason for a blocked item.
- Record risk changes and accepted decisions without deleting their original context.

### `review`

- Analyze overdue work, stale in-progress items, blockers, dependency conflicts, risk changes, and missing next actions.
- Default to read-only analysis.
- Apply proposed state changes only after confirmation.

### `close`

- Complete or cancel a milestone or project.
- Record outcome, incomplete work, lessons learned, and follow-up suggestions.
- Set the appropriate terminal state only after recording the retrospective information.

## Git Behavior

- Commits require explicit confirmation.
- A default commit includes only validated `.project/` changes.
- Unrelated working-tree changes remain untouched.
- Commit subjects use `project(init|plan|update|review|close): <summary>`.
- If Git is unavailable, the workflow still updates files but reports that no version record was created.
- Pushes are always left to the user.

## Validation Script

`scripts/project_state.py` uses only the Python standard library and provides:

```text
project_state.py init
project_state.py validate
project_state.py apply --expected-revision N --file candidate.json
project_state.py render
project_state.py summary
```

`apply` rules:

- Read the current state and candidate state.
- Require candidate `revision` to equal `expected_revision + 1`.
- Validate schema shape, enums, timestamps, IDs, references, dependencies, and completion rules.
- Write the candidate to a temporary file in `.project/`, flush it, and atomically replace `project.json`.
- Regenerate `PROJECT.md` only after the state write succeeds.
- Leave both files unchanged when validation fails.

The script is optional. Skill-capable and file-aware models can perform the same contract manually, and chat-only models exchange complete JSON states.

## Portability Model

The portable core is `SKILL.md` plus plain-text references, templates, and examples. No core instruction hard-codes a platform tool or executable path.

Three usage levels are supported:

### Skill Mode

The platform discovers and loads `SKILL.md`, then reads only the referenced workflow files needed for the current operation.

### File Mode

The platform cannot discover skills but can read the repository and managed-project files. `SKILL.md` is supplied as a system prompt or custom instruction, and the model reads the relevant references directly.

### Chat Mode

The platform cannot read files. The user supplies the compact skill instructions and the complete current `project.json`. The model returns an updated complete JSON object, a human-readable summary, and any suggested Git commands.

### Unified Output Contract

Workflow responses include:

1. Operation result.
2. State-change summary.
3. Complete candidate `project.json` when state changed.
4. Git commit suggestion or an explanation of the fallback.
5. Next action.

The implementation detects capabilities before using them. If file writes, scripts, or Git are unavailable, it states the limitation and selects the next supported fallback.

## Testing

### Automated State Tests

- Valid initialization produces a complete state and generated view.
- Required fields, enums, timestamps, and ID formats are enforced.
- Duplicate IDs and invalid references are rejected.
- Dependency cycles are rejected.
- Revision mismatches and failed validations leave existing files unchanged.
- Successful updates are written atomically and render deterministically.
- Work items cannot be completed with unmet acceptance criteria unless the documented exception path is valid.

### Integration Tests

- Execute `init -> plan -> update -> review -> close` against fixtures.
- Validate the personal-project example after each transition.
- Confirm that `PROJECT.md` can be regenerated without changing semantics.

### Prompt Scenarios

Scenario documents cover:

- New project initialization.
- Task blocked by a dependency.
- Overdue iteration review.
- Work-item completion with acceptance evidence.
- Risk escalation.
- Project retrospective and closure.
- Chat-only fallback when no filesystem or Git is available.

Scenario tests verify decisions and state changes rather than exact wording.

## Acceptance Criteria

- The portable core works without Git, Python, or platform-specific tools.
- The Python validation script works with no third-party dependencies.
- `python -m unittest discover -s tests -v` passes.
- The personal-project example validates and renders correctly.
- `README.md` documents Skill, File, and Chat modes.
- Git behavior follows the confirmation and path-scope rules.
- No workflow automatically pushes or modifies unrelated files.
- The first release is tagged `v0.1.0` after all checks pass.

## Future Extensions

The schema version allows later additions without breaking personal-project state:

- Team members and ownership.
- Multiple projects under one workspace.
- Portfolio views and cross-project dependencies.
- Scope, schedule, cost, and stakeholder governance.
- Controlled change requests and baselines.
- Optional integrations with Git hosting, issue trackers, and calendars.

These extensions are outside the v0.1.0 implementation.
