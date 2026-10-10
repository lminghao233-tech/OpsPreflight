# Architecture and trust boundary

## End-to-end flow

```text
Terraform plan JSON
  -> parser
       Terraform sensitive masks
       + sensitive-name redaction
  -> untrusted-text guardrail
       scan names/tags/descriptions
       replace detected instructions in model-facing evidence
  -> deterministic tools
       policy engine
       dependency blast radius
       repository outcome history
  -> immutable PASS / REVIEW / BLOCK
  -> hybrid runbook RAG
       BM25 + dense vector score
       rule-ID metadata filter
  -> review packet
       actions + questions + citations + tool trace
  -> citation/verdict invariant validation
  -> audit, approval, break-glass and deployment outcome
```

## Why the model is not the judge

A release gate must be reproducible and fail safely. `Analyzer` calculates the
verdict from named rules, graph facts and recorded history. `ReviewAgent`
retrieves operational guidance and packages the evidence, but validates that its
verdict still equals the analyzer result. Any BLOCK finding therefore remains a
BLOCK regardless of generated prose or retrieval quality.

The optional Agents SDK example runs only after the local review exists. It
receives redacted evidence and cannot execute deployment actions.

## Hybrid runbook retrieval

`RunbookRetriever` combines BM25 sparse relevance with a deterministic
hashing-vector cosine score. Rule IDs act as metadata filters, so an IAM finding
does not retrieve unrelated reliability guidance merely because words overlap.
Every hit exposes source, excerpt, combined score and component scores.

The hashing vector is an offline test baseline, not a trained semantic model.
The interface can be replaced with managed embeddings/vector storage while
keeping policy and evaluation unchanged.

## Prompt-injection boundary

Terraform strings are attacker-controlled data. Resource descriptions and tags
can contain text that looks like model instructions. The guardrail recursively
records JSON paths for suspicious patterns and replaces those strings in the
model-facing plan. The policy engine still evaluates the original plan through
its separate secret-redacting parser.

## Audit model

Analyses have deterministic fingerprints and IDs. SQLite stores the immutable
analysis and append-only events for approvals, explicit Break-glass and
deployment outcomes. Historical rollback/incident evidence can raise later
scores for the same repository and resource type.

## Failure behavior

- Retrieval failure must not weaken the verdict.
- Model absence must not prevent deterministic analysis.
- Unknown ownership produces REVIEW.
- Any BLOCK policy forces BLOCK independently of numeric score.
- A BLOCK approval requires explicit Break-glass and a reason.
- Citations not present in retrieved evidence are rejected.

