from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ResourceChange:
    address: str
    resource_type: str
    actions: tuple[str, ...]
    before: dict[str, Any]
    after: dict[str, Any]


@dataclass(frozen=True)
class Finding:
    rule_id: str
    title: str
    severity: str
    score: int
    resource: str
    evidence: str
    remediation: str


@dataclass(frozen=True)
class AnalysisContext:
    repository: str = "local/demo"
    commit: str = "working-tree"
    environment: str = "development"
    pull_request: int | None = None
    owners: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class AnalysisResult:
    analysis_id: str
    fingerprint: str
    verdict: str
    final_score: int
    policy_score: int
    blast_radius_points: int
    history_points: int
    affected_services: tuple[str, ...]
    findings: tuple[Finding, ...]
    context: AnalysisContext
    policy_version: str = "2026-10-v2"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

