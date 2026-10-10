# Resume wording and interview pitch

## Resume-ready wording

**OpsPreflight | Terraform Review Agent, FastAPI, Hybrid RAG, Agents SDK**

- Built an evidence-driven IaC review agent that combines eight deterministic
  Terraform risk policies, dependency blast-radius analysis and historical
  outcome signals into immutable `PASS / REVIEW / BLOCK` decisions.
- Added hybrid BM25+dense runbook RAG, source citations, embedded
  prompt-injection scanning and code-level invariants preventing an LLM from
  changing verdicts or inventing evidence.
- Delivered FastAPI/CLI interfaces, SQLite approval and Break-glass audit trails,
  Docker, GitHub Actions, 59 tests with 96% branch coverage, and separate
  controlled policy and Agent/RAG evaluations.

Keep **controlled synthetic evaluation** next to the 8/8 and 5/5 figures. They
are regression results rather than production accuracy.

## 90-second pitch

"OpsPreflight solves a release-review problem rather than adding chat to
Terraform. It parses and redacts a plan, then deterministic policy, dependency
blast radius and previous rollback or incident outcomes calculate the release
verdict. The review agent uses that immutable result to retrieve the relevant
operational runbooks through hybrid BM25 and dense search, and returns actions,
questions, citations and a machine-readable trace. IaC descriptions and tags are
untrusted, so I scan embedded prompt injection before any model-facing step.
Citation allow-listing and verdict equality are enforced in code. BLOCK can only
proceed through an explicit, reasoned Break-glass audit event. The complete
workflow, API and evaluations run without a paid model; an optional Agents SDK
example adds security and SRE specialist handoffs strictly as an explanation
layer. That separation makes the system testable and safe to degrade."

