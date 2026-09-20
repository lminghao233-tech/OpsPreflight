from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from .graph import DependencyGraph
from .models import AnalysisContext, AnalysisResult
from .parser import parse_plan
from .policies import evaluate_all


class Analyzer:
    def __init__(
        self,
        graph: DependencyGraph | None = None,
        history: list[dict[str, Any]] | None = None,
    ) -> None:
        self.graph = graph or DependencyGraph()
        self.history = history or []

    @staticmethod
    def fingerprint(plan: dict[str, Any], context: AnalysisContext) -> str:
        canonical = json.dumps(
            {
                "plan": plan,
                "repository": context.repository,
                "commit": context.commit,
                "environment": context.environment,
                "policy_version": "2026-09-portfolio-v1",
            },
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _history_points(self, context: AnalysisContext, resource_types: set[str]) -> int:
        points = 0
        for item in self.history:
            if item.get("repository") != context.repository:
                continue
            if item.get("resource_type") not in resource_types:
                continue
            if item.get("outcome") == "incident":
                points = max(points, 25)
            elif item.get("outcome") == "rollback":
                points = max(points, 15)
        return points

    def analyze(self, plan: dict[str, Any], context: AnalysisContext | None = None) -> AnalysisResult:
        context = context or AnalysisContext()
        changes = parse_plan(plan)
        findings = evaluate_all(changes, context)
        policy_score = max((finding.score for finding in findings), default=0)

        starts = [change.address for change in changes]
        affected, blast_points = self.graph.blast_radius(starts)
        history_points = self._history_points(context, {c.resource_type for c in changes})
        final_score = min(100, policy_score + blast_points + history_points)

        if any(finding.severity == "BLOCK" for finding in findings):
            verdict = "BLOCK"
        elif findings or final_score >= 40 or context.environment == "production" and not changes:
            verdict = "REVIEW"
        else:
            verdict = "PASS"

        fingerprint = self.fingerprint(plan, context)
        analysis_id = str(uuid.uuid5(uuid.NAMESPACE_URL, fingerprint))
        return AnalysisResult(
            analysis_id=analysis_id,
            fingerprint=fingerprint,
            verdict=verdict,
            final_score=final_score,
            policy_score=policy_score,
            blast_radius_points=blast_points,
            history_points=history_points,
            affected_services=affected,
            findings=tuple(findings),
            context=context,
        )

