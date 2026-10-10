# Production readiness boundary

Version 0.2.0 is a local or single-node portfolio system. It demonstrates the
architecture and controls but is not presented as an enterprise control plane.

## Implemented

- Terraform parsing and two-layer secret redaction.
- Eight deterministic findings and an immutable verdict.
- Dependency blast-radius and historical-outcome scoring.
- Hybrid runbook RAG with citations and score transparency.
- Recursive prompt-injection inspection for untrusted IaC text.
- Citation and verdict invariants around the review agent.
- Stable fingerprints, SQLite WAL, append-only audit events and Break-glass.
- FastAPI, CLI, Docker, GitHub Actions and controlled evaluations.
- Optional model handoffs that receive only the redacted evidence layer.

## Required before serious production use

- PostgreSQL, migrations, backups and multi-instance coordination.
- OIDC or GitHub App identity, fine-grained RBAC and tenant isolation.
- Signed/versioned policy and runbook bundles with review workflow.
- Tenant-scoped vector indexes and document access control.
- Real GitHub Check Run integration and verified webhook signatures.
- Durable queues, idempotent workers, retries and circuit breakers.
- OpenTelemetry traces/metrics/logs with sensitive-payload filtering.
- Prompt, model and embedding version registry with rollback.
- Authorized replay of real redacted plans, false-positive measurement,
  retrieval judgments and adversarial/red-team tests.
- Immutable or externally anchored audit storage.
- Automatic post-deployment health verification and feedback ingestion.

## Safe rollout sequence

1. Run in shadow mode and compare with human reviewers.
2. Curate organization-specific policies and runbook judgments.
3. Gate only BLOCK rules with low false-positive risk.
4. Add REVIEW workflows and service-owner feedback.
5. Measure deployment outcomes before tuning history-based risk.
6. Expand automation only after incident and rollback criteria are validated.

