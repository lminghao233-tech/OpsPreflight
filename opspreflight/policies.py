"""Eight deterministic risk policies described by the portfolio project."""

from __future__ import annotations

import json
from typing import Any, Iterable

from .models import AnalysisContext, Finding, ResourceChange


MANAGEMENT_PORTS = {22, 3389, 3306, 5432, 6379}
STATEFUL_MARKERS = ("db", "rds", "sql", "disk", "volume", "bucket", "redis", "cache")


def _finding(
    rule_id: str,
    title: str,
    severity: str,
    score: int,
    change: ResourceChange,
    evidence: str,
    remediation: str,
) -> Finding:
    return Finding(rule_id, title, severity, score, change.address, evidence, remediation)


def _public_ingress(after: dict[str, Any]) -> bool:
    ingress = after.get("ingress") or after.get("ingress_rules") or []
    if isinstance(ingress, dict):
        ingress = [ingress]
    for rule in ingress if isinstance(ingress, list) else []:
        sources = rule.get("cidr_blocks") or rule.get("source_ranges") or []
        if isinstance(sources, str):
            sources = [sources]
        ipv6 = rule.get("ipv6_cidr_blocks") or []
        if isinstance(ipv6, str):
            ipv6 = [ipv6]
        public = "0.0.0.0/0" in sources or "::/0" in ipv6
        start = int(rule.get("from_port", rule.get("port", -1)))
        end = int(rule.get("to_port", start))
        if public and any(start <= port <= end for port in MANAGEMENT_PORTS):
            return True
    return False


def _is_database(change: ResourceChange) -> bool:
    lowered = change.resource_type.casefold()
    return any(marker in lowered for marker in ("db", "rds", "sql", "database"))


def _is_stateful(change: ResourceChange) -> bool:
    lowered = change.resource_type.casefold()
    return any(marker in lowered for marker in STATEFUL_MARKERS)


def _iam_double_wildcard(after: dict[str, Any]) -> bool:
    policy: Any = after.get("policy", after)
    if isinstance(policy, str):
        try:
            policy = json.loads(policy)
        except json.JSONDecodeError:
            return False
    statements = policy.get("Statement", []) if isinstance(policy, dict) else []
    if isinstance(statements, dict):
        statements = [statements]
    for statement in statements:
        if statement.get("Effect", "Allow") != "Allow":
            continue
        actions = statement.get("Action", [])
        resources = statement.get("Resource", [])
        actions = [actions] if isinstance(actions, str) else actions
        resources = [resources] if isinstance(resources, str) else resources
        if "*" in actions and "*" in resources:
            return True
    return False


def evaluate_change(change: ResourceChange, context: AnalysisContext) -> list[Finding]:
    findings: list[Finding] = []
    after, before = change.after, change.before
    production = context.environment.casefold() == "production"

    if _public_ingress(after):
        findings.append(_finding(
            "NETWORK-001", "Public management port", "BLOCK", 100, change,
            "A management/database port is reachable from a public CIDR.",
            "Restrict ingress to VPN, bastion or approved private CIDRs.",
        ))
    if _is_database(change) and after.get("publicly_accessible") is True:
        findings.append(_finding(
            "DATA-001", "Public database", "BLOCK", 100, change,
            "publicly_accessible changes to true.", "Place the database in private subnets.",
        ))
    encrypted = after.get("storage_encrypted", after.get("encrypted"))
    if encrypted is False:
        findings.append(_finding(
            "DATA-002", "Encryption disabled", "BLOCK", 100, change,
            "Encryption at rest is explicitly false.", "Enable provider-managed or customer-managed encryption.",
        ))
    if "iam" in change.resource_type.casefold() and _iam_double_wildcard(after):
        findings.append(_finding(
            "IAM-001", "IAM double wildcard", "BLOCK", 100, change,
            "An Allow statement contains Action=* and Resource=*.", "Apply least privilege to actions and resources.",
        ))
    if production and _is_stateful(change) and {"delete", "create"}.issubset(change.actions):
        findings.append(_finding(
            "CHANGE-002", "Stateful replacement", "BLOCK", 100, change,
            "A production stateful resource will be deleted and created.", "Use a migration, snapshot and reviewed cutover plan.",
        ))
    old_backup = before.get("backup_retention_period")
    new_backup = after.get("backup_retention_period")
    if isinstance(old_backup, (int, float)) and isinstance(new_backup, (int, float)) and new_backup < old_backup:
        findings.append(_finding(
            "DATA-003", "Backup retention reduced", "REVIEW", 60, change,
            f"Retention decreases from {old_backup} to {new_backup} days.", "Confirm recovery requirements and obtain approval.",
        ))
    old_replicas = before.get("replica_count", before.get("replicas"))
    new_replicas = after.get("replica_count", after.get("replicas"))
    if production and isinstance(new_replicas, int) and new_replicas <= 1 and new_replicas != old_replicas:
        findings.append(_finding(
            "RELIABILITY-001", "Production replicas reduced", "REVIEW", 60, change,
            f"Replica count changes from {old_replicas} to {new_replicas}.", "Confirm availability target and rollback plan.",
        ))
    if change.address not in context.owners:
        findings.append(_finding(
            "CONTEXT-001", "Missing resource ownership", "REVIEW", 40, change,
            "No owner is registered for the resource.", "Register a service and accountable owner.",
        ))
    return findings


def evaluate_all(changes: Iterable[ResourceChange], context: AnalysisContext) -> list[Finding]:
    findings: list[Finding] = []
    for change in changes:
        findings.extend(evaluate_change(change, context))
    return findings

