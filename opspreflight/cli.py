from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analyzer import Analyzer
from .copilot import ReviewAgent
from .models import AnalysisContext
from .storage import Store


def _add_common_arguments(command: argparse.ArgumentParser) -> None:
    command.add_argument("plan", type=Path)
    command.add_argument("--repository", default="local/demo")
    command.add_argument("--commit", default="working-tree")
    command.add_argument("--environment", default="development")
    command.add_argument("--database", default=":memory:")


def main() -> None:
    parser = argparse.ArgumentParser(prog="opspreflight")
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze")
    _add_common_arguments(analyze)
    analyze.add_argument("--fail-on", choices=("review", "block"))
    review = sub.add_parser("review")
    _add_common_arguments(review)
    review.add_argument(
        "--audience", choices=("developer", "approver", "manager"), default="approver"
    )
    args = parser.parse_args()

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    context = AnalysisContext(args.repository, args.commit, args.environment)
    if args.command == "review":
        result = ReviewAgent().review(plan, context, audience=args.audience)
        Store(args.database).save_analysis(
            Analyzer().analyze(plan, context)
        )
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return

    result = Analyzer().analyze(plan, context)
    Store(args.database).save_analysis(result)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    if args.fail_on == "block" and result.verdict == "BLOCK":
        raise SystemExit(2)
    if args.fail_on == "review" and result.verdict in {"REVIEW", "BLOCK"}:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

