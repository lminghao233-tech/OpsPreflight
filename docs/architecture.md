# Architecture

```text
terraform plan -> terraform show -json
                         |
                         v
                  parse + redact
                         |
             +-----------+-----------+
             |                       |
       8 deterministic          dependency graph
          policies              + history facts
             |                       |
             +-----------+-----------+
                         v
              score + PASS/REVIEW/BLOCK
                         |
              audit / approval / outcome
                         |
              deterministic briefing
```

## Trust boundary

The verdict is calculated locally from deterministic evidence. Briefing output
does not modify the verdict or findings. The current public implementation uses
a deterministic fallback and does not require an LLM API key.

## Scoring

```text
final_score = max(policy finding score) + blast radius points + history points
```

The final score is capped at 100. Any BLOCK finding forces the BLOCK verdict,
regardless of arithmetic. This prevents a scoring threshold from weakening a
hard safety rule.

