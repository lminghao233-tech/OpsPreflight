# Interview evidence and honest claim boundaries

## Reproducible claims

- The repository implements eight named deterministic risk policies.
- `python -m unittest discover -v` runs 47 core/API/CLI tests.
- `coverage report` currently reports 94% package branch coverage.
- `python scripts/run_eval.py` runs eight controlled synthetic regression cases.
- The risky plan returns BLOCK and can make CI exit with code 2.
- BLOCK approval requires an explicit Break-glass flag and is appended to the
  SQLite audit timeline.

## Claims that would be misleading

- Eight controlled cases do not imply 100% production accuracy.
- SQLite WAL is not an enterprise multi-region database.
- A shared API key is not enterprise identity or RBAC.
- The deterministic brief is not evidence of a live OpenAI model call.
- This public project does not prove that it processed a named company's plans.

## Honest project background

"I built OpsPreflight after identifying a common platform-engineering problem:
small teams often review Terraform output manually and lack a connected record
of ownership, approval and deployment outcome. The public project uses synthetic
plans and a local service catalog so the full decision path can be reproduced
without exposing any employer infrastructure. It is a portfolio MVP with an
explicit production-readiness document, not a claim of enterprise deployment."
