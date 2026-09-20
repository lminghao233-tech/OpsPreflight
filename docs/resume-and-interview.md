# Resume wording and interview pitch

## Resume-ready wording

**OpsPreflight - Terraform change risk and release approval portfolio MVP**

- Implemented Terraform plan JSON parsing, two-layer sensitive-data redaction
  and eight deterministic policies that produce explainable PASS/REVIEW/BLOCK
  decisions before release.
- Added dependency blast-radius traversal, stable SHA-256 fingerprints,
  historical outcome points, SQLite WAL audit events and explicit Break-glass
  approval for BLOCK findings.
- Delivered FastAPI and CLI interfaces, Docker and GitHub Actions, with 47
  automated tests, 94% package branch coverage and 8/8 controlled synthetic
  regression cases.

The phrase **controlled synthetic regression cases** must remain. `8/8` is not
a production accuracy claim.

## 90-second pitch

"Small teams often review Terraform plans manually, so risky changes and the
reason behind approvals are easy to miss. OpsPreflight parses plan JSON, redacts
sensitive fields and evaluates eight deterministic policies. It then combines
the highest policy score with dependency blast radius and relevant historical
outcomes. Strong findings force BLOCK; a normal approval cannot erase that fact,
so continuing requires an explicit audited Break-glass. I kept AI outside the
safety decision: briefing can explain evidence, but it cannot change the
verdict. The public repository uses synthetic plans and now has 47 tests, 94%
branch coverage and an eight-case reproducible evaluation. It is a local
portfolio MVP; PostgreSQL, OIDC, real GitHub App integration and authorized
production replay remain future work."

