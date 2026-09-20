from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analyzer import Analyzer
from .models import AnalysisContext
from .storage import Store


def main() -> None:
    parser = argparse.ArgumentParser(prog="opspreflight")
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze")
    analyze.add_argument("plan", type=Path)
    analyze.add_argument("--repository", default="local/demo")
    analyze.add_argument("--commit", default="working-tree")
    analyze.add_argument("--environment", default="development")
    analyze.add_argument("--database", default=":memory:")
    analyze.add_argument("--fail-on", choices=("review", "block"))
    args = parser.parse_args()

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    context = AnalysisContext(args.repository, args.commit, args.environment)
    result = Analyzer().analyze(plan, context)
    Store(args.database).save_analysis(result)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    if args.fail_on == "block" and result.verdict == "BLOCK":
        raise SystemExit(2)
    if args.fail_on == "review" and result.verdict in {"REVIEW", "BLOCK"}:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

