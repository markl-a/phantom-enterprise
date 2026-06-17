"""``phantom-enterprise`` command-line entrypoint.

Subcommands:
    ask    Answer a question about a private repo (local path or Gitea owner/repo).
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional, Sequence


def _cmd_ask(args: argparse.Namespace) -> int:
    from .ask import ask
    from on_prem_gitlab import GiteaUnreachable

    try:
        result = ask(
            args.repo,
            args.question,
            token=args.token,
            ref=args.ref,
            base_url=args.base_url,
            is_gitea=args.gitea or None,
        )
    except GiteaUnreachable as exc:
        print(
            f"error: on-prem Gitea unreachable: {exc}\n"
            f"hint: the reliable path is a LOCAL checkout — try:\n"
            f"      phantom-enterprise ask --repo /path/to/your/repo "
            f'"{args.question}"',
            file=sys.stderr,
        )
        return 2
    except NotADirectoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    ctx = result.context
    if not ctx.files:
        print(
            "error: no readable/relevant files found in repo for this question.",
            file=sys.stderr,
        )
        return 3

    used = ", ".join(f.path for f in ctx.files)
    print("=" * 70)
    print("phantom-enterprise ask  —  AI for your PRIVATE code")
    print("code read locally; nothing left the machine.")
    print("=" * 70)
    print(f"source       : {ctx.source}")
    print(
        f"files used   : {len(ctx.files)} of {ctx.considered} considered "
        f"({ctx.total_chars} chars of context)"
    )
    print(f"             : {used}")
    print(f"question     : {result.question}")
    print("-" * 70)
    print(result.answer)
    print("-" * 70)
    print("(answer grounded in the files above; context may be truncated to fit.)")
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    """Run HA-readiness checks and print a CLI-friendly summary."""

    from . import status

    result = status.gather_status(base_url=args.base_url)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for check in result["checks"]:
            marker = "[OK]" if check["ok"] else "[--]"
            print(f"{marker} {check['name']}: {check['detail']}")
        overall = "healthy" if result["healthy"] else "DEGRADED"
        print(f"overall: {overall}")

    return 0 if result["healthy"] else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="phantom-enterprise",
        description="Enterprise connectors + AI for your PRIVATE code.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser(
        "ask",
        help="Ask a question about a private repo; the code never leaves the machine.",
    )
    a.add_argument(
        "--repo",
        required=True,
        help="Local repo path (reliable default) OR Gitea 'owner/repo' (bonus).",
    )
    a.add_argument("question", help="Natural-language question about the codebase.")
    a.add_argument(
        "--token",
        default=None,
        help="Gitea/GitLab personal access token (Gitea mode only).",
    )
    a.add_argument(
        "--ref", default=None, help="Git ref/branch for Gitea mode (default HEAD)."
    )
    a.add_argument(
        "--base-url",
        default=None,
        help="Override Gitea base URL (else GITEA_BASE_URL / default).",
    )
    a.add_argument(
        "--gitea",
        action="store_true",
        help="Force Gitea mode even if --repo looks like a path.",
    )
    a.set_defaults(func=_cmd_ask)

    s = sub.add_parser(
        "status",
        help="Run HA-readiness checks for enterprise dependencies.",
    )
    s.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable status JSON.",
    )
    s.add_argument(
        "--base-url",
        default=None,
        help="Override Gitea base URL for the Git readiness check.",
    )
    s.set_defaults(func=_cmd_status)
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
