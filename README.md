# OpsPreflight

Evidence-driven Terraform change risk gate for platform, SRE and small IT teams.

OpsPreflight turns Terraform plan JSON into an explainable `PASS / REVIEW /
BLOCK` decision, then preserves approval, Break-glass and deployment outcome as
an audit timeline. The public repository is a runnable portfolio MVP using
synthetic plans. It does not contain or claim access to employer infrastructure.

## Why this project exists

Manual review of large Terraform plans can miss public databases, exposed
management ports, disabled encryption, broad IAM grants, reduced backups or
stateful replacement. A chat model may explain these risks, but a release gate
needs deterministic, reproducible rules. OpsPreflight therefore keeps the
verdict local and uses briefing only as a presentation layer.

## Implemented capabilities

- Terraform plan JSON parsing and normalization.
- Redaction from Terraform sensitive masks plus sensitive field names.
- Eight deterministic risk policies.
- `PASS / REVIEW / BLOCK` with explainable score components.
- Dependency graph traversal with cycle protection.
- Stable SHA-256 fingerprint and idempotent analysis ID.
- Historical rollback/incident risk points.
- SQLite WAL persistence and append-only audit events.
- Explicit Break-glass requirement for BLOCK approvals.
- Deterministic briefing fallback that cannot alter the verdict.
- FastAPI, CLI, Docker, GitHub Actions and controlled regression evaluation.
- 47 automated core/API/CLI tests with 94% package branch coverage.

## Policy set

| Rule | Evidence | Default result |
|---|---|---|
| `NETWORK-001` | Public management/database port | BLOCK |
| `DATA-001` | Database becomes publicly accessible | BLOCK |
| `DATA-002` | Encryption at rest explicitly disabled | BLOCK |
| `IAM-001` | Allow statement with Action and Resource `*` | BLOCK |
| `CHANGE-002` | Production stateful delete/create replacement | BLOCK |
| `DATA-003` | Backup retention reduced | REVIEW |
| `RELIABILITY-001` | Production replicas reduced to 1 or 0 | REVIEW |
| `CONTEXT-001` | Resource has no registered owner | REVIEW |

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run tests and controlled evaluation:

```bash
coverage run -m unittest discover -v
coverage report
python scripts/run_eval.py
```

Analyze the included risky plan:

```bash
opspreflight analyze examples/risky-plan.json \
  --repository acme/platform \
  --commit abc123 \
  --environment production \
  --fail-on block
```

The risky example returns `BLOCK (100/100)`. With `--fail-on block`, exit code 2
is an expected policy result suitable for a CI gate, not a crash.

Start the API:

```bash
uvicorn opspreflight.api:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` for the generated API schema.

## Controlled regression result

`python scripts/run_eval.py` executes eight synthetic cases covering safe
change, public port, public database, encryption, IAM, stateful replacement,
backup reduction and replica reduction. The committed result is in
`results/eval-results.json`.

An `8/8` result means the current implementation matches these eight expected
cases. It **does not** mean 100% production accuracy. Real adoption requires an
authorized replay set of redacted plans, false-positive review and shadow mode.

The current coverage result is 94% with branch coverage enabled. Coverage is a
regression signal, not proof that the policy set is complete or production-safe.

## API surface

- `POST /v1/analyses`
- `GET /v1/analyses/{id}`
- `POST /v1/analyses/{id}/approvals`
- `POST /v1/analyses/{id}/outcomes`
- `POST /v1/analyses/{id}/brief`
- `GET /v1/analyses/{id}/timeline`

Set `OPSPREFLIGHT_API_KEY` to require `X-API-Key`. The shared key is a local MVP
mechanism, not a substitute for OIDC, GitHub App identity or RBAC.

## Repository layout

```text
opspreflight/parser.py       Plan parsing and redaction
opspreflight/policies.py     Eight deterministic policies
opspreflight/graph.py        Blast-radius traversal
opspreflight/analyzer.py     Fingerprint, scoring and verdict
opspreflight/storage.py      SQLite WAL audit timeline
opspreflight/brief.py        Deterministic explanation fallback
opspreflight/api.py          FastAPI endpoints
opspreflight/cli.py          CI-friendly CLI
tests/                       Core unit and regression tests
scripts/run_eval.py          Eight-case controlled evaluation
examples/                    Safe and risky synthetic plans
docs/                        Architecture, evidence and production boundary
```

## Documentation

- [Architecture](docs/architecture.md)
- [Production-readiness boundary](docs/production-readiness.md)
- [Interview evidence and honest claim boundaries](docs/interview-evidence.md)
- [Resume wording and 90-second pitch](docs/resume-and-interview.md)

## Security and production boundary

Version 0.1.0 is a local or single-node portfolio MVP. Production use still
requires PostgreSQL, migrations, organization-specific policies, OIDC/GitHub
App identity, RBAC, signed integrations, monitoring, backup/restore and real
authorized evaluation. See the production-readiness document before making any
deployment claim.

## Author

Liu Minghao - AI application and solution engineering portfolio
GitHub: [@lminghao233-tech](https://github.com/lminghao233-tech)

## License

MIT
