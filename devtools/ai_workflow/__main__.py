import argparse
import json
import subprocess
from pathlib import Path

from .workflow import Run, WorkflowError


def main():
    parser = argparse.ArgumentParser(
        description="Offline Notice Me AI review files; no model/browser transport"
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("init")
    create.add_argument("id")
    create.add_argument("--spec", type=Path, required=True)
    review = commands.add_parser("import-review")
    review.add_argument("id")
    review.add_argument("--role", choices=["gemini", "claude", "gpt"], required=True)
    review.add_argument("--file", type=Path, required=True)
    decision = commands.add_parser("decide")
    decision.add_argument("id")
    decision.add_argument("--file", type=Path, required=True)
    retry = commands.add_parser("retry")
    retry.add_argument("id")
    retry.add_argument("--extension", type=Path)
    retry.add_argument(
        "--context", action="append", help="Curated repo-relative files; refreshes context only"
    )
    check = commands.add_parser("verify")
    check.add_argument("id")
    check.add_argument("--profile", choices=["workflow", "server", "quality"], required=True)
    for name in ("status", "pause", "resume", "ready"):
        commands.add_parser(name).add_argument("id")
    args = parser.parse_args()
    try:
        run = Run(args.root, args.id)
        if args.command == "init":
            state = run.create(args.spec)
        elif args.command == "import-review":
            state = run.import_review(args.role, args.file)
        elif args.command == "decide":
            state = run.decide(args.file)
        elif args.command == "retry":
            state = run.retry(args.extension, args.context)
        elif args.command == "verify":
            state = run.verify(args.profile)
        elif args.command in {"pause", "resume"}:
            state = run.pause(resume=args.command == "resume")
        elif args.command == "ready":
            state = run.ready()
        else:
            state, _ = run.load()
        # Never print review bodies, prompts, external credentials or test logs.
        print(
            json.dumps(
                {
                    "status": state["status"],
                    "iteration": state["iteration"],
                    "iteration_limit": state["iteration_limit"],
                    "request_hash": state["request_hash"],
                    "request_file_hashes": state.get("request_file_hashes", {}),
                    "review_hashes": {r: x["sha256"] for r, x in state["reviews"].items()},
                    "review_verdicts": {r: x["data"]["verdict"] for r, x in state["reviews"].items()},
                    "comparison": run.compare(state),
                    "external_calls": state["external_calls"],
                    "browser_submissions": state["browser_submissions"],
                    "usage_unknown_imports": state["usage_unknown_imports"],
                    "reported_cost_usd": state["reported_cost_usd"],
                    "usage_note": "Manual reports only; zero external calls by this tool does not mean imported reviews cost zero",
                    "checks": state["checks"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1 if state["status"] in {"TEST_FAILED", "BUDGET_STOP", "ITERATION_STOP", "BLOCKED"} else 0
    except (WorkflowError, OSError, KeyError, TypeError, ValueError, subprocess.SubprocessError):
        # Error detail may contain sensitive file content. Emit only a safe code.
        import sys

        error = sys.exc_info()[1]
        print(
            json.dumps(
                {
                    "status": "ERROR",
                    "code": str(error) if isinstance(error, WorkflowError) else "INVALID_LOCAL_INPUT_OR_IO",
                }
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
