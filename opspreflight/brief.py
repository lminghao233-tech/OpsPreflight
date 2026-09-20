from __future__ import annotations

from typing import Any


def deterministic_brief(analysis: dict[str, Any], audience: str = "approver") -> dict[str, Any]:
    findings = analysis.get("findings", [])
    rules = [item["rule_id"] for item in findings]
    actions = [item["remediation"] for item in findings]
    return {
        "audience": audience,
        "source": "deterministic-fallback",
        "verdict": analysis["verdict"],
        "score": analysis["final_score"],
        "summary": f"{analysis['verdict']} with {len(findings)} finding(s): {', '.join(rules) or 'none'}.",
        "required_actions": actions,
        "open_questions": ["Is the owner and rollback plan confirmed?"] if findings else [],
    }

