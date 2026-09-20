"""Validate and maintain portable project state files."""

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = 1
PROJECT_STATUSES = {"planning", "active", "paused", "completed", "archived"}
MILESTONE_STATUSES = {"planned", "active", "completed", "cancelled"}
ITERATION_STATUSES = {"planned", "active", "completed", "cancelled"}
WORK_ITEM_TYPES = {"epic", "story", "task", "bug", "spike"}
WORK_ITEM_STATUSES = {
    "backlog",
    "ready",
    "in_progress",
    "blocked",
    "review",
    "done",
    "cancelled",
}
PRIORITIES = {"p0", "p1", "p2", "p3"}
ACCEPTANCE_STATUSES = {"pending", "met"}
RISK_LEVELS = {"low", "medium", "high"}
RISK_STATUSES = {"open", "mitigated", "accepted", "closed"}
DECISION_STATUSES = {"proposed", "accepted", "rejected", "superseded"}

PROJECT_ID_PATTERN = r"^PRJ-\d{3,}$"
ENTITY_PATTERNS = {
    "milestones": r"^M-\d{3,}$",
    "iterations": r"^I-\d{3,}$",
    "work_items": r"^T-\d{3,}$",
    "risks": r"^R-\d{3,}$",
    "decisions": r"^D-\d{3,}$",
}


class ValidationError(ValueError):
    """Raised when a project state violates the portable state contract."""


def utc_now():
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


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
    revision = state.get("revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        raise ValidationError("revision must be a positive integer")

    project = state.get("project")
    if not isinstance(project, dict):
        raise ValidationError("project must be an object")

    required = (
        "id",
        "name",
        "summary",
        "status",
        "constraints",
        "success_criteria",
        "created_at",
        "updated_at",
    )
    for field in required:
        if field not in project:
            raise ValidationError(f"project.{field} is required")

    for field in ("id", "name", "summary", "status", "created_at", "updated_at"):
        if not isinstance(project[field], str) or not project[field].strip():
            raise ValidationError(f"project.{field} must be a non-empty string")
    if project["status"] not in PROJECT_STATUSES:
        raise ValidationError("project.status is invalid")
    if not re.fullmatch(PROJECT_ID_PATTERN, project["id"]):
        raise ValidationError("project.id is invalid")

    for field in ("constraints", "success_criteria"):
        if not isinstance(project[field], list) or not all(
            isinstance(value, str) for value in project[field]
        ):
            raise ValidationError(f"project.{field} must be an array of strings")

    for field in ("created_at", "updated_at"):
        _validate_utc_timestamp(project[field], f"project.{field}")

    for collection in ("milestones", "iterations", "work_items", "risks", "decisions"):
        if not isinstance(state.get(collection), list):
            raise ValidationError(f"{collection} must be an array")

    milestone_ids = _validate_entity_ids(
        state["milestones"], ENTITY_PATTERNS["milestones"], "milestones"
    )
    iteration_ids = _validate_entity_ids(
        state["iterations"], ENTITY_PATTERNS["iterations"], "iterations"
    )
    work_item_ids = _validate_entity_ids(
        state["work_items"], ENTITY_PATTERNS["work_items"], "work_items"
    )
    risk_ids = _validate_entity_ids(
        state["risks"], ENTITY_PATTERNS["risks"], "risks"
    )
    decision_ids = _validate_entity_ids(
        state["decisions"], ENTITY_PATTERNS["decisions"], "decisions"
    )

    _validate_milestones(state["milestones"])
    _validate_iterations(state["iterations"])
    _validate_work_items(
        state["work_items"], milestone_ids, iteration_ids, work_item_ids
    )
    _validate_risks(state["risks"])
    _validate_decisions(state["decisions"], decision_ids)
    _detect_work_item_cycle(state["work_items"])


def _validate_utc_timestamp(value, label):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValidationError(f"{label} must be a UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValidationError(f"{label} must be a valid ISO 8601 timestamp") from exc
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValidationError(f"{label} must use UTC")


def _require_fields(item, fields, label):
    if not isinstance(item, dict):
        raise ValidationError(f"{label} must be an object")
    for field in fields:
        if field not in item:
            raise ValidationError(f"{label}.{field} is required")


def _require_string(item, field, label):
    value = item[field]
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{label}.{field} must be a non-empty string")


def _validate_optional_timestamp(item, field, label):
    if field in item:
        _validate_utc_timestamp(item[field], f"{label}.{field}")


def _validate_entity_ids(items, pattern, collection):
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValidationError(f"{collection} items must be objects")
        item_id = item.get("id")
        if not isinstance(item_id, str) or not re.fullmatch(pattern, item_id):
            raise ValidationError(f"{collection}.id is invalid")
        if item_id in seen:
            raise ValidationError(f"duplicate ID in {collection}: {item_id}")
        seen.add(item_id)
    return seen


def _validate_milestones(milestones):
    required = ("id", "title", "description", "status", "created_at", "updated_at")
    for milestone in milestones:
        label = f"milestones[{milestone.get('id', '?')}]"
        _require_fields(milestone, required, label)
        for field in ("title", "description", "status", "created_at", "updated_at"):
            _require_string(milestone, field, label)
        if milestone["status"] not in MILESTONE_STATUSES:
            raise ValidationError(f"{label}.status is invalid")
        _validate_utc_timestamp(milestone["created_at"], f"{label}.created_at")
        _validate_utc_timestamp(milestone["updated_at"], f"{label}.updated_at")
        for field in ("target_date", "completed_at"):
            _validate_optional_timestamp(milestone, field, label)


def _validate_iterations(iterations):
    required = ("id", "title", "goal", "status", "created_at", "updated_at")
    for iteration in iterations:
        label = f"iterations[{iteration.get('id', '?')}]"
        _require_fields(iteration, required, label)
        for field in ("title", "goal", "status", "created_at", "updated_at"):
            _require_string(iteration, field, label)
        if iteration["status"] not in ITERATION_STATUSES:
            raise ValidationError(f"{label}.status is invalid")
        _validate_utc_timestamp(iteration["created_at"], f"{label}.created_at")
        _validate_utc_timestamp(iteration["updated_at"], f"{label}.updated_at")
        for field in ("start_date", "end_date", "completed_at"):
            _validate_optional_timestamp(iteration, field, label)


def _validate_work_items(work_items, milestone_ids, iteration_ids, work_item_ids):
    required = (
        "id",
        "type",
        "title",
        "description",
        "status",
        "priority",
        "acceptance_criteria",
        "created_at",
        "updated_at",
    )
    for item in work_items:
        label = f"work_items[{item.get('id', '?')}]"
        _require_fields(item, required, label)
        for field in (
            "type",
            "title",
            "description",
            "status",
            "priority",
            "created_at",
            "updated_at",
        ):
            _require_string(item, field, label)
        if item["type"] not in WORK_ITEM_TYPES:
            raise ValidationError(f"{label}.type is invalid")
        if item["status"] not in WORK_ITEM_STATUSES:
            raise ValidationError(f"{label}.status is invalid")
        if item["priority"] not in PRIORITIES:
            raise ValidationError(f"{label}.priority is invalid")
        _validate_utc_timestamp(item["created_at"], f"{label}.created_at")
        _validate_utc_timestamp(item["updated_at"], f"{label}.updated_at")
        _validate_optional_timestamp(item, "due_date", label)
        _validate_optional_timestamp(item, "completed_at", label)

        if item.get("milestone_id") is not None and item["milestone_id"] not in milestone_ids:
            raise ValidationError(f"{label}.milestone_id references an unknown milestone")
        if item.get("iteration_id") is not None and item["iteration_id"] not in iteration_ids:
            raise ValidationError(f"{label}.iteration_id references an unknown iteration")
        if item.get("parent_id") is not None and item["parent_id"] not in work_item_ids:
            raise ValidationError(f"{label}.parent_id references an unknown work item")

        depends_on = item.get("depends_on", [])
        if not isinstance(depends_on, list) or not all(
            isinstance(value, str) for value in depends_on
        ):
            raise ValidationError(f"{label}.depends_on must be an array of IDs")
        if item["id"] in depends_on:
            raise ValidationError(f"{label}.depends_on contains a self-reference")
        for dependency in depends_on:
            if dependency not in work_item_ids:
                raise ValidationError(f"{label}.depends_on references {dependency}")

        criteria = item["acceptance_criteria"]
        if not isinstance(criteria, list):
            raise ValidationError(f"{label}.acceptance_criteria must be an array")
        criterion_ids = set()
        for criterion in criteria:
            criterion_label = f"{label}.acceptance_criteria"
            _require_fields(criterion, ("id", "text", "status"), criterion_label)
            _require_string(criterion, "id", criterion_label)
            _require_string(criterion, "text", criterion_label)
            if not re.fullmatch(r"^AC-\d{3,}$", criterion["id"]):
                raise ValidationError(f"{criterion_label}.id is invalid")
            if criterion["id"] in criterion_ids:
                raise ValidationError(f"duplicate acceptance criterion ID: {criterion['id']}")
            criterion_ids.add(criterion["id"])
            if criterion["status"] not in ACCEPTANCE_STATUSES:
                raise ValidationError(f"{criterion_label}.status is invalid")

        if item["status"] == "blocked" and not item.get("blocked_reason"):
            raise ValidationError(f"{label}.blocked_reason is required when blocked")

        if item["status"] == "done":
            if "completed_at" not in item:
                raise ValidationError(f"{label}.completed_at is required when done")
            if not item.get("completion_note"):
                raise ValidationError(f"{label}.completion_note is required when done")
            pending = [
                criterion
                for criterion in criteria
                if criterion["status"] == "pending"
            ]
            if pending and item.get("completion_exception") is not True:
                raise ValidationError(
                    f"{label}.completion_exception is required for unmet criteria"
                )
        elif item.get("completion_exception") is True:
            raise ValidationError(
                f"{label}.completion_exception is only valid when done"
            )


def _validate_risks(risks):
    required = (
        "id",
        "title",
        "description",
        "probability",
        "impact",
        "status",
        "mitigation",
        "created_at",
        "updated_at",
    )
    for risk in risks:
        label = f"risks[{risk.get('id', '?')}]"
        _require_fields(risk, required, label)
        for field in required[1:]:
            _require_string(risk, field, label)
        if risk["probability"] not in RISK_LEVELS:
            raise ValidationError(f"{label}.probability is invalid")
        if risk["impact"] not in RISK_LEVELS:
            raise ValidationError(f"{label}.impact is invalid")
        if risk["status"] not in RISK_STATUSES:
            raise ValidationError(f"{label}.status is invalid")
        _validate_utc_timestamp(risk["created_at"], f"{label}.created_at")
        _validate_utc_timestamp(risk["updated_at"], f"{label}.updated_at")


def _validate_decisions(decisions, decision_ids):
    required = (
        "id",
        "title",
        "context",
        "decision",
        "rationale",
        "consequences",
        "status",
        "created_at",
        "updated_at",
    )
    for decision in decisions:
        label = f"decisions[{decision.get('id', '?')}]"
        _require_fields(decision, required, label)
        for field in required[1:]:
            _require_string(decision, field, label)
        if decision["status"] not in DECISION_STATUSES:
            raise ValidationError(f"{label}.status is invalid")
        _validate_utc_timestamp(decision["created_at"], f"{label}.created_at")
        _validate_utc_timestamp(decision["updated_at"], f"{label}.updated_at")
        if decision.get("supersedes") is not None:
            if decision["supersedes"] not in decision_ids:
                raise ValidationError(f"{label}.supersedes references an unknown decision")


def _detect_work_item_cycle(work_items):
    graph = {item["id"]: item.get("depends_on", []) for item in work_items}
    visiting = set()
    visited = set()

    def visit(node):
        if node in visiting:
            raise ValidationError("work item dependency cycle detected")
        if node in visited:
            return
        visiting.add(node)
        for dependency in graph[node]:
            visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)


def render_project_md(state):
    validate_state(state)
    project = state["project"]
    lines = [
        f"# {project['name']}",
        "",
        "> Generated from `project.json`. Do not edit this file directly.",
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
    lines.extend(
        _render_entity_table(
            state["milestones"],
            (("id", "ID"), ("title", "Title"), ("status", "Status"), ("target_date", "Target")),
            "No milestones recorded.",
        )
    )
    lines.extend(["", "## Iterations", ""])
    lines.extend(
        _render_entity_table(
            state["iterations"],
            (("id", "ID"), ("title", "Title"), ("status", "Status"), ("goal", "Goal")),
            "No iterations recorded.",
        )
    )
    lines.extend(["", "## Work Items", ""])
    ordered_items = sorted(
        enumerate(state["work_items"]),
        key=lambda pair: (("p0", "p1", "p2", "p3").index(pair[1]["priority"]), pair[0]),
    )
    lines.extend(
        _render_entity_table(
            [item for _, item in ordered_items],
            (
                ("id", "ID"),
                ("priority", "Priority"),
                ("status", "Status"),
                ("title", "Title"),
            ),
            "No work items recorded.",
        )
    )
    lines.extend(["", "## Risks", ""])
    lines.extend(
        _render_entity_table(
            state["risks"],
            (
                ("id", "ID"),
                ("probability", "Probability"),
                ("impact", "Impact"),
                ("status", "Status"),
                ("title", "Title"),
            ),
            "No risks recorded.",
        )
    )
    lines.extend(["", "## Decisions", ""])
    lines.extend(
        _render_entity_table(
            state["decisions"],
            (("id", "ID"), ("status", "Status"), ("title", "Title")),
            "No decisions recorded.",
        )
    )
    return "\n".join(lines).rstrip() + "\n"


def _render_bullets(values, empty_message):
    if not values:
        return [f"- {empty_message}"]
    return [f"- {value}" for value in values]


def _render_next_actions(work_items):
    candidates = [
        item
        for item in work_items
        if item["status"] in {"ready", "in_progress"}
    ]
    candidates.sort(key=lambda item: ("p0", "p1", "p2", "p3").index(item["priority"]))
    if not candidates:
        return ["- No next actions recorded."]
    return [
        f"- `{item['id']}` [{item['priority']}/{item['status']}] {item['title']}"
        for item in candidates[:3]
    ]


def _render_blocked_work(work_items):
    blocked = [item for item in work_items if item["status"] == "blocked"]
    if not blocked:
        return ["- No blocked work recorded."]
    return [
        f"- `{item['id']}` {item['title']}: {item['blocked_reason']}"
        for item in blocked
    ]


def _render_entity_table(items, columns, empty_message):
    if not items:
        return [f"- {empty_message}"]
    headers = [label for _, label in columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for item in items:
        values = [str(item.get(key, "")) for key, _ in columns]
        lines.append("| " + " | ".join(values) + " |")
    return lines


def load_state(path):
    path = Path(path)
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"unable to read project state: {path}") from exc
    validate_state(state)
    return state


def write_new_project(project_dir, state):
    validate_state(state)
    project_dir = Path(project_dir)
    project_dir.mkdir(parents=True, exist_ok=False)
    _write_text_atomic(
        project_dir / "project.json",
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
    )
    _write_text_atomic(project_dir / "PROJECT.md", render_project_md(state))


def apply_candidate(project_dir, candidate, expected_revision):
    project_dir = Path(project_dir)
    current_path = project_dir / "project.json"
    current = load_state(current_path)
    if current["revision"] != expected_revision:
        raise ValidationError("revision mismatch")
    if not isinstance(candidate, dict):
        raise ValidationError("candidate must be an object")
    if candidate.get("revision") != expected_revision + 1:
        raise ValidationError(
            "candidate revision must equal expected revision plus one"
        )
    validate_state(candidate)
    _write_text_atomic(
        current_path,
        json.dumps(candidate, ensure_ascii=False, indent=2) + "\n",
    )
    _write_text_atomic(project_dir / "PROJECT.md", render_project_md(candidate))
    return candidate


def _write_text_atomic(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


if __name__ == "__main__":
    raise SystemExit("CLI is not implemented yet")
