from __future__ import annotations

from typing import Any


def plan(resource_type: str, before: dict[str, Any] | None, after: dict[str, Any] | None, actions=None, address="resource.test"):
    return {
        "resource_changes": [
            {
                "address": address,
                "type": resource_type,
                "change": {
                    "actions": actions or ["update"],
                    "before": before,
                    "after": after,
                },
            }
        ]
    }

