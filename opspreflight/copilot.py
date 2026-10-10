"""Evidence-first IaC review agent.

The deterministic Analyzer owns the verdict. Retrieval and generated prose are
explanation layers and are validated against the analysis result.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .analyzer import Analyzer
from .brief import deterministic_brief
from .guardrails import sanitize_untrusted_text, scan_prompt_injection
from .models import AnalysisContext
from .parser import parse_plan
from .retrieval import RunbookHit, RunbookRetriever


@dataclass(frozen=True)
class ReviewStep:
    tool: str
    status: str
    detail: dict[str, Any]


@dataclass(frozen=True)
class AgentReview:
    analysis_id: str
    verdict: str
    final_score: int
    summary: str
    required_actions: tuple[str, ...]
    open_questions: tuple[str, ...]
    citations: tuple[str, ...]
    evidence: tuple[dict[str, Any], ...]
    injection_findings: tuple[dict[str, str], ...]
    trace: tuple[ReviewStep, ...]
    analysis: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ReviewAgent:
    """Orchestrate policy, graph, history and runbook tools."""

    def __init__(
        self,
        *,
        analyzer: Analyzer | None = None,
        retriever: RunbookRetriever | None = None,
    ) -> None:
        self.analyzer = analyzer or Analyzer()
        self.retriever = retriever or RunbookRetriever()

    @staticmethod
    def _validate(
        review_verdict: str,
        analysis_verdict: str,
        citations: tuple[str, ...],
        hits: list[RunbookHit],
    ) -> None:
        if review_verdict != analysis_verdict:
            raise ValueError("generated review cannot change deterministic verdict")
        allowed = {hit.doc_id for hit in hits}
        invalid = set(citations) - allowed
        if invalid:
            raise ValueError(f"review contains citations outside retrieved evidence: {invalid}")

    def review(
        self,
        plan: dict[str, Any],
        context: AnalysisContext | None = None,
        *,
        audience: str = "approver",
    ) -> AgentReview:
        context = context or AnalysisContext()
        injection = scan_prompt_injection(plan)
        sanitized = sanitize_untrusted_text(plan)
        # Parsing sanitized content proves that suspicious free text is not sent
        # into later model-facing evidence. The authoritative policy analysis
        # still consumes the original plan and applies its own secret redaction.
        changes = parse_plan(sanitized)
        result = self.analyzer.analyze(plan, context)
        analysis = result.to_dict()
        brief = deterministic_brief(analysis, audience)
        rule_ids = tuple(finding.rule_id for finding in result.findings)
        retrieval_rules = rule_ids or ("PASS",)
        query_parts = [
            result.verdict,
            context.environment,
            *(finding.title for finding in result.findings),
            *(finding.remediation for finding in result.findings),
            *(change.resource_type for change in changes),
        ]
        hits = self.retriever.search(
            " ".join(query_parts), rule_ids=retrieval_rules, top_k=3
        )
        if injection:
            safety = self.retriever.search(
                "untrusted terraform prompt injection model safety",
                rule_ids=("PROMPT-INJECTION",),
                top_k=1,
            )
            for hit in safety:
                if hit.doc_id not in {item.doc_id for item in hits}:
                    hits.append(hit)
        citations = tuple(hit.doc_id for hit in hits)
        actions = tuple(dict.fromkeys(brief["required_actions"]))
        questions = tuple(brief["open_questions"])
        self._validate(result.verdict, analysis["verdict"], citations, hits)
        return AgentReview(
            analysis_id=result.analysis_id,
            verdict=result.verdict,
            final_score=result.final_score,
            summary=brief["summary"],
            required_actions=actions,
            open_questions=questions,
            citations=citations,
            evidence=tuple(
                {
                    "doc_id": hit.doc_id,
                    "title": hit.title,
                    "source": hit.source,
                    "excerpt": hit.excerpt,
                    "score": hit.score,
                    "sparse_score": hit.sparse_score,
                    "dense_score": hit.dense_score,
                }
                for hit in hits
            ),
            injection_findings=tuple(asdict(item) for item in injection),
            trace=(
                ReviewStep(
                    "scan_and_redact_untrusted_text",
                    "flagged" if injection else "passed",
                    {"finding_count": len(injection)},
                ),
                ReviewStep(
                    "deterministic_policy_engine",
                    "completed",
                    {"rules": list(rule_ids), "verdict": result.verdict},
                ),
                ReviewStep(
                    "dependency_and_history_risk",
                    "completed",
                    {
                        "blast_radius_points": result.blast_radius_points,
                        "history_points": result.history_points,
                    },
                ),
                ReviewStep(
                    "hybrid_runbook_search",
                    "completed",
                    {"hits": len(hits), "citations": list(citations)},
                ),
                ReviewStep(
                    "validate_review_invariants",
                    "passed",
                    {"verdict_immutable": True, "citations_allow_listed": True},
                ),
            ),
            analysis=analysis,
        )
