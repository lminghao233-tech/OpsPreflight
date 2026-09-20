# Production readiness boundary

Version 0.1.0 is a local or single-node portfolio MVP. It is not presented as an
enterprise production control plane.

## Implemented

- Terraform plan JSON parsing and two-layer redaction.
- Eight deterministic findings and explainable scoring.
- Dependency blast-radius traversal with cycle protection.
- Stable fingerprints and idempotent analysis IDs.
- SQLite WAL persistence, append-only audit events and explicit Break-glass.
- FastAPI endpoints, CLI, Docker and GitHub Actions.
- Controlled regression evaluation and automated tests.

## Required before serious production use

- PostgreSQL, migrations, backups and multi-instance coordination.
- OIDC or GitHub App identity and fine-grained RBAC.
- Signed policy bundles, exceptions and organization-specific providers.
- Real GitHub Check Run integration and webhook verification.
- Metrics, tracing, alerting, capacity and disaster-recovery tests.
- Authorized replay of real, redacted plans and measured false-positive rates.
- Immutable or externally anchored audit storage.
- Automatic post-deployment health verification.

