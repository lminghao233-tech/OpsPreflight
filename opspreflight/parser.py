"""Terraform plan parsing, normalization and defensive redaction."""

from __future__ import annotations

import copy
import re
from typing import Any

from .models import ResourceChange


SENSITIVE_NAME = re.compile(
    r"(?i)(password|passwd|secret|token|private[_-]?key|access[_-]?key|client[_-]?secret)"
)
REDACTED = "[REDACTED]"


def _redact_by_name(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: REDACTED if SENSITIVE_NAME.search(str(key)) else _redact_by_name(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_by_name(item) for item in value]
    return value


def _apply_sensitive_mask(value: Any, mask: Any) -> Any:
    if mask is True:
        return REDACTED
    if isinstance(value, dict) and isinstance(mask, dict):
        return {
            key: _apply_sensitive_mask(item, mask.get(key, False))
            for key, item in value.items()
        }
    if isinstance(value, list) and isinstance(mask, list):
        return [
            _apply_sensitive_mask(item, mask[index] if index < len(mask) else False)
            for index, item in enumerate(value)
        ]
    return value


def redact(value: Any, sensitive_mask: Any = None) -> Any:
    copied = copy.deepcopy(value)
    masked = _apply_sensitive_mask(copied, sensitive_mask or {})
    return _redact_by_name(masked)


def parse_plan(plan: dict[str, Any]) -> list[ResourceChange]:
    if not isinstance(plan, dict):
        raise ValueError("plan must be a JSON object")
    raw_changes = plan.get("resource_changes")
    if not isinstance(raw_changes, list):
        raise ValueError("plan.resource_changes must be a list")

    changes: list[ResourceChange] = []
    for raw in raw_changes:
        change = raw.get("change", {})
        actions = change.get("actions", [])
        if not isinstance(actions, list):
            raise ValueError("change.actions must be a list")
        before = redact(change.get("before") or {}, change.get("before_sensitive") or {})
        after = redact(change.get("after") or {}, change.get("after_sensitive") or {})
        changes.append(
            ResourceChange(
                address=str(raw.get("address", "unknown")),
                resource_type=str(raw.get("type", "unknown")),
                actions=tuple(str(action) for action in actions),
                before=before,
                after=after,
            )
        )
    return changes

