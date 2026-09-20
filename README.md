# Project Workflow Skill

[English](README.md) | [Simplified Chinese](README.zh-CN.md)

`project-workflow` is a portable project-management skill for personal development projects. It stores goals, milestones, iterations, work items, dependencies, risks, decisions, and completion evidence as structured JSON while generating a human-readable Markdown view.

The same methodology, state format, and core prompts can be used with skill-aware AI software, file-aware assistants, and chat-only models. Python, Git, and platform-specific tools are optional enhancements rather than core requirements.

This repository provides the reusable workflow. Each managed project keeps its own state under `.project/`.

## Version Scope

Version 0.1.0 supports:

- Initializing personal project state.
- Planning milestones, iterations, backlogs, dependencies, and acceptance criteria.
- Updating work items, blockers, risks, decisions, and completion evidence.
- Reviewing progress and producing next actions.
- Closing milestones or projects with retrospectives.
- Revision-conflict protection, atomic writes, and deterministic Markdown rendering.
- Git-aware workflows with confirmation before commits and no automatic pushes.

Team permissions, enterprise budgets, multi-project portfolio dashboards, and bidirectional external integrations are outside v0.1.0.

## Repository Layout

```text
project-help/
|-- SKILL.md
|-- agents/openai.yaml
|-- references/
|-- templates/
|-- examples/personal-project/
|-- scripts/project_state.py
`-- tests/
```

`SKILL.md` is the portable entry point. `references/` contains the methodology, state contract, and workflow instructions loaded as needed. `scripts/project_state.py` is an optional standard-library tool.

## Installation

### Skill Mode

Place the repository in the skill directory of a skill-aware AI application, or copy its contents into that application's local skill storage. The platform should discover `SKILL.md` and read the relevant references when needed.

After installation, requests such as these can invoke the workflow:

```text
Initialize project-management state for this repository.
Break the next phase into milestones, iterations, and work items.
Review the current iteration for blockers and risks.
```

Explicit invocation is also supported when the runtime provides it:

```text
Use $project-workflow to update T-003.
```

### File Mode

If the platform cannot discover skills but can read repository files:

1. Supply `SKILL.md` as a system prompt, custom instruction, or project instruction.
2. Allow the model to read `references/`, `templates/`, and the target project's `.project/` directory.
3. Follow the workflow routing in `SKILL.md`.

### Chat Mode

If the platform cannot access files:

1. Paste the core contract from `SKILL.md`.
2. Paste the complete current `project.json`.
3. Specify the requested `init`, `plan`, `update`, `review`, or `close` operation.
4. The model must return a complete candidate JSON object and explicitly state that it did not write files or modify Git.

## Managed Project Layout

```text
<project-root>/
`-- .project/
    |-- project.json
    `-- PROJECT.md
```

`project.json` is the single source of truth. `PROJECT.md` is a generated view and should not be edited manually.

## CLI Usage

Python 3.10 or newer is required. On Windows, `py` can be used instead of `python`.

```bash
python scripts/project_state.py init --root /path/to/project --name "Project" --summary "Outcome" --success "Observable result"
python scripts/project_state.py validate --root /path/to/project
python scripts/project_state.py apply --root /path/to/project --expected-revision 1 --file candidate.json
python scripts/project_state.py render --root /path/to/project
python scripts/project_state.py summary --root /path/to/project
```

`apply` requires the candidate revision to equal `expected-revision + 1`. A validation failure leaves the existing state unchanged.

## Git Behavior

- Show the intended state effects and obtain confirmation before writing files.
- Obtain separate confirmation before committing.
- By default, commit only `.project/project.json` and `.project/PROJECT.md`.
- Do not modify unrelated working-tree files.
- Use commit subjects such as `project(init|plan|update|review|close): <summary>`.
- Never push automatically.

## Testing

```bash
python -m unittest discover -s tests -v
python scripts/project_state.py validate --root examples/personal-project
```

The tests use no third-party packages. On Windows, run `py -m unittest discover -s tests -v`.

## GitHub Upload

After local verification, create an empty GitHub repository and run:

```bash
git remote add origin https://github.com/<your-account>/<repository>.git
git push -u origin main
git push origin v0.1.0
```

To upload a feature branch first, replace `main` with the feature branch name. Pushing is always performed by the user or an explicitly authorized agent; this project never pushes automatically.

## Design Documents

- Design specification: `docs/superpowers/specs/2026-09-20-project-workflow-design.md`
- Implementation plan: `docs/superpowers/plans/2026-09-20-project-workflow-v0.1.0.md`

## License

MIT License. See `LICENSE` for details.
