from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from opspreflight.copilot import ReviewAgent
from opspreflight.models import AnalysisContext
from tests.helpers import plan


CASES = [
    (
        "public-port",
        plan(
            "aws_security_group",
            {},
            {"ingress": [{"from_port": 22, "to_port": 22, "cidr_blocks": ["0.0.0.0/0"]}]},
        ),
        "BLOCK",
        "RB-NETWORK-001",
    ),
    (
        "encryption",
        plan("aws_s3_bucket", {}, {"encrypted": False}),
        "BLOCK",
        "RB-DATA-001",
    ),
    (
        "iam",
        plan(
            "aws_iam_policy",
            {},
            {"policy": {"Statement": {"Effect": "Allow", "Action": "*", "Resource": "*"}}},
        ),
        "BLOCK",
        "RB-IAM-001",
    ),
    (
        "replicas",
        plan("service", {"replicas": 3}, {"replicas": 1}),
        "REVIEW",
        "RB-RELIABILITY-001",
    ),
    (
        "safe",
        plan("service", {}, {}),
        "PASS",
        "RB-CONTEXT-001",
    ),
]


def main() -> int:
    reviewer = ReviewAgent()
    rows = []
    for name, raw_plan, verdict, expected_doc in CASES:
        context = AnalysisContext(
            repository="synthetic/agent-eval",
            environment="production" if name != "safe" else "development",
            owners={"resource.test": "platform-team"},
        )
        review = reviewer.review(raw_plan, context)
        retrieval_hit = expected_doc in review.citations
        verdict_preserved = review.verdict == verdict == review.analysis["verdict"]
        citations_valid = all(
            citation in {item["doc_id"] for item in review.evidence}
            for citation in review.citations
        )
        rows.append(
            {
                "case": name,
                "retrieval_hit": retrieval_hit,
                "verdict_preserved": verdict_preserved,
                "citations_valid": citations_valid,
                "passed": retrieval_hit and verdict_preserved and citations_valid,
            }
        )
    summary = {
        "dataset": "controlled-synthetic-agent-eval-v1",
        "total": len(rows),
        "passed": sum(item["passed"] for item in rows),
        "retrieval_recall_at_3": round(
            sum(item["retrieval_hit"] for item in rows) / len(rows), 4
        ),
        "verdict_invariant_rate": round(
            sum(item["verdict_preserved"] for item in rows) / len(rows), 4
        ),
        "production_accuracy_claim": False,
        "cases": rows,
    }
    output = ROOT / "results" / "agent-eval-results.json"
    output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] == summary["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
