# Interview evidence and honest claim boundaries

## Reproducible claims

- Eight named deterministic Terraform risk policies and explainable score
  components.
- An IaC Review Agent that orchestrates policy, graph, history and hybrid runbook
  retrieval tools.
- Prompt-injection inspection for embedded IaC text plus existing secret
  redaction.
- Verdict immutability and citation allow-listing as code-level invariants.
- SQLite WAL audit events and explicit Break-glass for BLOCK approval.
- FastAPI, CLI, Docker and an optional OpenAI Agents SDK specialist example.
- 59 automated tests with 96% branch coverage in the current controlled run.
- 8/8 policy cases and 5/5 Agent/RAG cases in synthetic regression suites.

## Claims that would be misleading

- Controlled cases do not imply 100% production detection or retrieval accuracy.
- The hashing-vector baseline is not a trained semantic embedding model.
- The optional Agents SDK example is not proof of a hosted production service.
- SQLite and a shared API key are not enterprise persistence, identity or RBAC.
- This repository does not claim access to any employer's infrastructure.

## Interview demonstration

1. Run the risky example through `analyze` and show the BLOCK rule.
2. Run it through `review` and show the matching runbook citation and scores.
3. Put an injection phrase in a tag and show its JSON path plus safety citation.
4. Attempt a normal approval of BLOCK, then show the required Break-glass event.
5. Run both evaluation scripts and explain why their metrics are scoped.

The important design discussion is why deterministic release control and
generative explanation are separate, and how feedback outcomes could later
improve policy thresholds without handing authority to the model.
