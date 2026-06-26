"""``phantom-enterprise`` command-line entrypoint.

Subcommands:
    ask    Answer a question about a private repo (local path or Gitea owner/repo).
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys
from typing import Optional, Sequence


def _pkg_version() -> str:
    try:
        return importlib.metadata.version("phantom-enterprise")
    except importlib.metadata.PackageNotFoundError:
        return "0.1.0"


def _cmd_ask(args: argparse.Namespace) -> int:
    from .ask import ask
    from on_prem_gitlab import GiteaUnreachable, GitLabUnreachable

    try:
        result = ask(
            args.repo,
            args.question,
            token=args.token,
            ref=args.ref,
            base_url=args.base_url,
            is_gitea=args.gitea or None,
            is_gitlab=args.gitlab or None,
        )
    except GitLabUnreachable as exc:
        print(
            f"error: on-prem GitLab unreachable: {exc}\n"
            f"hint: the reliable path is a LOCAL checkout — try:\n"
            f"      phantom-enterprise ask --repo /path/to/your/repo "
            f'"{args.question}"',
            file=sys.stderr,
        )
        return 2
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

    result = status.gather_status(
        base_url=args.base_url,
        backend=status.resolve_auth_backend(),
        ha_checks=status.gather_ha_checks(),
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for check in result["checks"]:
            marker = "[OK]" if check["ok"] else "[--]"
            print(f"{marker} {check['name']}: {check['detail']}")
        overall = "healthy" if result["healthy"] else "DEGRADED"
        print(f"overall: {overall}")

    return 0 if result["healthy"] else 1


def _cmd_demo_loop(args: argparse.Namespace) -> int:
    from .demo_loop import main as demo_loop_main

    return demo_loop_main(["--out", args.out])


def _cmd_connector_matrix(args: argparse.Namespace) -> int:
    from .connector_matrix import main as connector_matrix_main

    return connector_matrix_main(["--out", args.out])


def _cmd_knowledge_scenario(args: argparse.Namespace) -> int:
    from .knowledge_lookup_scenario import main as knowledge_scenario_main

    return knowledge_scenario_main(["--out", args.out])


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="phantom-enterprise",
        description="Enterprise connectors + AI for your PRIVATE code.",
    )
    p.add_argument(
        "--version",
        action="version",
        version=f"phantom-enterprise {_pkg_version()}",
    )
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser(
        "ask",
        help="Ask a question about a private repo; the code never leaves the machine.",
    )
    a.add_argument(
        "--repo",
        required=True,
        help=(
            "Local repo path (reliable default), Gitea 'owner/repo' (bonus), "
            "or GitLab project id."
        ),
    )
    a.add_argument("question", help="Natural-language question about the codebase.")
    a.add_argument(
        "--token",
        default=None,
        help="Personal access token (Gitea or GitLab mode).",
    )
    a.add_argument(
        "--ref",
        default=None,
        help="Git ref/branch for Gitea or GitLab mode (default HEAD).",
    )
    a.add_argument(
        "--base-url",
        default=None,
        help=(
            "Override Gitea/GitLab base URL (else "
            "GITEA_BASE_URL/GITLAB_BASE_URL / default)."
        ),
    )
    a.add_argument(
        "--gitea",
        action="store_true",
        help="Force Gitea mode even if --repo looks like a path.",
    )
    a.add_argument(
        "--gitlab",
        action="store_true",
        help=(
            "Force GitLab mode: treat --repo as a GitLab project id "
            "('group/name' or numeric)."
        ),
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

    d = sub.add_parser(
        "demo-loop",
        help=(
            "Write a deterministic synthetic local-code Q&A bundle with "
            "citations, evidence, and audit metadata."
        ),
    )
    d.add_argument("--out", required=True, help="directory to write the demo bundle")
    d.set_defaults(func=_cmd_demo_loop)

    m = sub.add_parser(
        "connector-matrix",
        help=(
            "Write a deterministic mock connector matrix with permission "
            "boundary and metadata-only audit artifacts."
        ),
    )
    m.add_argument("--out", required=True, help="directory to write the connector bundle")
    m.set_defaults(func=_cmd_connector_matrix)

    k = sub.add_parser(
        "knowledge-scenario",
        help=(
            "Write a deterministic enterprise knowledge lookup scenario with "
            "mock connectors, citations, permission review, and metadata audit."
        ),
    )
    k.add_argument("--out", required=True, help="directory to write the scenario bundle")
    k.set_defaults(func=_cmd_knowledge_scenario)
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        return args.func(args)
    except KeyboardInterrupt:
        print("aborted.", file=sys.stderr)
        return 130
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
