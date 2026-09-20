from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceNode:
    name: str
    tier: int = 3


class DependencyGraph:
    """Reverse dependency graph: a node maps to services that consume it."""

    def __init__(self, consumers: dict[str, list[str]] | None = None, tiers: dict[str, int] | None = None) -> None:
        self.consumers = consumers or {}
        self.tiers = tiers or {}

    def blast_radius(self, starts: list[str]) -> tuple[tuple[str, ...], int]:
        queue = deque(starts)
        visited = set(starts)
        affected: list[str] = []
        points = 0
        while queue:
            current = queue.popleft()
            for consumer in self.consumers.get(current, []):
                if consumer in visited:
                    continue
                visited.add(consumer)
                affected.append(consumer)
                points += 15 if self.tiers.get(consumer, 3) <= 1 else 5
                queue.append(consumer)
        return tuple(affected), min(points, 40)

