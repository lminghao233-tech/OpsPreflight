from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from opspreflight.analyzer import Analyzer
from opspreflight.models import AnalysisContext


def make_plan(resource_type, before, after, actions=None):
    return {
        "resource_changes": [{
            "address": "resource.test",
            "type": resource_type,
            "change": {
                "actions": actions or ["update"],
                "before": before,
                "after": after,
            },
        }]
    }


CASES = [
    ("safe-owned-change", "PASS", make_plan("service", {}, {}), "development"),
    ("public-management-port", "BLOCK", make_plan("aws_security_group", {}, {"ingress": [{"from_port": 22, "to_port": 22, "cidr_blocks": ["0.0.0.0/0"]}]}), "production"),
    ("public-database", "BLOCK", make_plan("aws_db_instance", {}, {"publicly_accessible": True}), "production"),
    ("encryption-disabled", "BLOCK", make_plan("aws_s3_bucket", {}, {"encrypted": False}), "production"),
    ("iam-double-wildcard", "BLOCK", make_plan("aws_iam_policy", {}, {"policy": {"Statement": {"Effect": "Allow", "Action": "*", "Resource": "*"}}}), "production"),
    ("stateful-replacement", "BLOCK", make_plan("aws_db_instance", {}, {}, ["delete", "create"]), "production"),
    ("backup-reduced", "REVIEW", make_plan("aws_db_instance", {"backup_retention_period": 14}, {"backup_retention_period": 1}), "production"),
    ("replicas-reduced", "REVIEW", make_plan("service", {"replicas": 3}, {"replicas": 1}), "production"),
]


def main() -> int:
    rows = []
    for name, expected, plan, environment in CASES:
        context = AnalysisContext(
            repository="synthetic/eval",
            environment=environment,
            owners={"resource.test": "platform-team"},
        )
        result = Analyzer().analyze(plan, context)
        rows.append({
            "case": name,
            "expected": expected,
            "actual": result.verdict,
            "passed": expected == result.verdict,
            "rules": [finding.rule_id for finding in result.findings],
        })
    summary = {
        "dataset": "controlled-synthetic-regression-v1",
        "total": len(rows),
        "passed": sum(row["passed"] for row in rows),
        "production_accuracy_claim": False,
        "cases": rows,
    }
    output = ROOT / "results" / "eval-results.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] == summary["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

