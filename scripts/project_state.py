"""Validate and maintain portable project state files."""

from datetime import datetime, timezone


SCHEMA_VERSION = 1
PROJECT_STATUSES = {"planning", "active", "paused", "completed", "archived"}


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


def _validate_utc_timestamp(value, label):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValidationError(f"{label} must be a UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValidationError(f"{label} must be a valid ISO 8601 timestamp") from exc
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValidationError(f"{label} must use UTC")


if __name__ == "__main__":
    raise SystemExit("CLI is not implemented yet")
