"""Deterministic synthetic local-code Q&A demo bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .context import RepoContext, SelectedFile, build_local_context


QUESTION = "How does authentication work?"

PUBLIC_ARTIFACTS = [
    "manifest.json",
    "answer.json",
    "evidence.json",
    "audit-log.jsonl",
    "summary.md",
]

_SYNTHETIC_AUTH = """\
def authenticate(token):
    if not token:
        raise ValueError("token required")
    return {"Authorization": f"Bearer {token}"}
"""


@dataclass(frozen=True)
class DemoBundle:
    out_dir: Path
    artifacts: list[str]


def _dump_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_synthetic_repo(repo_dir: Path) -> None:
    src = repo_dir / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "auth.py").write_text(_SYNTHETIC_AUTH, encoding="utf-8")
    (repo_dir / "README.md").write_text(
        "# Synthetic Enterprise Demo\n\nAuthentication helper lives in `src/auth.py`.\n",
        encoding="utf-8",
    )
    (repo_dir / ".gitignore").write_text("*.log\nsecrets.txt\n", encoding="utf-8")
    (repo_dir / "debug.log").write_text("synthetic ignored log\n", encoding="utf-8")
    (repo_dir / "secrets.txt").write_text("synthetic ignored secret\n", encoding="utf-8")


def _line_span_for_auth(file: SelectedFile) -> tuple[int, int, str]:
    lines = file.content.splitlines()
    for index, line in enumerate(lines, start=1):
        if line.startswith("def authenticate"):
            end = min(index + 3, len(lines))
            return index, end, line
    return 1, min(1, len(lines)), lines[0] if lines else ""


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _selected_auth_file(ctx: RepoContext) -> SelectedFile:
    for file in ctx.files:
        if file.path == "src/auth.py":
            return file
    if not ctx.files:
        raise RuntimeError("synthetic demo produced no readable context files")
    return ctx.files[0]


def _answer_artifact(ctx: RepoContext) -> dict:
    auth_file = _selected_auth_file(ctx)
    line_start, line_end, snippet = _line_span_for_auth(auth_file)
    return {
        "question": QUESTION,
        "answer": (
            "Authentication is implemented in src/auth.py. The authenticate "
            "function requires a token and returns an Authorization header "
            "using the Bearer scheme."
        ),
        "citations": [
            {
                "path": auth_file.path,
                "line_start": line_start,
                "line_end": line_end,
                "snippet": snippet,
            }
        ],
        "model": "deterministic-local-extractor",
    }


def _evidence_artifact(ctx: RepoContext) -> dict:
    files = []
    ranked_files = sorted(
        ctx.files,
        key=lambda file: (file.path != "src/auth.py", file.path),
    )
    for file in ranked_files:
        line_start, line_end, snippet = _line_span_for_auth(file)
        files.append(
            {
                "path": file.path,
                "score": file.score,
                "truncated": file.truncated,
                "sha256": _sha256(file.content),
                "snippet_line_start": line_start,
                "snippet_line_end": line_end,
                "snippet": snippet,
            }
        )
    return {
        "source": "local working tree: synthetic-repo",
        "considered": ctx.considered,
        "selected_count": len(ctx.files),
        "total_chars": ctx.total_chars,
        "files": files,
    }


def _audit_events(ctx: RepoContext, answer: dict, artifacts: list[str]) -> list[dict]:
    selected_paths = [file.path for file in ctx.files]
    return [
        {
            "schema_version": 1,
            "event": "demo_started",
            "mode": "synthetic_local_code_qa",
            "live_connectors": False,
            "external_network": False,
        },
        {
            "schema_version": 1,
            "event": "context_built",
            "source": "synthetic-repo",
            "considered": ctx.considered,
            "selected_count": len(ctx.files),
            "selected_paths": selected_paths,
        },
        {
            "schema_version": 1,
            "event": "answer_generated",
            "model": answer["model"],
            "citation_count": len(answer["citations"]),
        },
        {
            "schema_version": 1,
            "event": "artifact_written",
            "artifacts": artifacts,
        },
    ]


def _write_audit_log(path: Path, events: list[dict]) -> None:
    lines = [json.dumps(event, ensure_ascii=False, sort_keys=True) for event in events]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_synthetic_code_qa_demo(out_dir: str | Path) -> DemoBundle:
    """Write a deterministic public local-code Q&A bundle."""
    out_path = Path(out_dir)
    repo_dir = out_path / "synthetic-repo"
    out_path.mkdir(parents=True, exist_ok=True)
    _write_synthetic_repo(repo_dir)

    ctx = build_local_context(str(repo_dir), QUESTION)
    answer = _answer_artifact(ctx)
    evidence = _evidence_artifact(ctx)

    manifest = {
        "schema_version": 1,
        "mode": "synthetic_local_code_qa",
        "synthetic_only": True,
        "live_connectors": False,
        "external_network": False,
        "local_llm_required": False,
        "question": QUESTION,
        "artifacts": ["synthetic-repo/src/auth.py", *PUBLIC_ARTIFACTS],
    }

    _dump_json(out_path / "manifest.json", manifest)
    _dump_json(out_path / "answer.json", answer)
    _dump_json(out_path / "evidence.json", evidence)
    _write_audit_log(
        out_path / "audit-log.jsonl",
        _audit_events(ctx, answer, manifest["artifacts"]),
    )
    (out_path / "summary.md").write_text(
        "\n".join(
            [
                "# Synthetic Local Code-QA Demo",
                "",
                "This bundle uses a tiny synthetic repo and a deterministic local extractor.",
                "It does not require live enterprise connectors, network access, or a local LLM.",
                "",
                f"- Question: {QUESTION}",
                "- Primary citation: src/auth.py:1-4",
                "- Audit log stores metadata, paths, counts, and artifact names only.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return DemoBundle(out_dir=out_path, artifacts=list(manifest["artifacts"]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="code_qa.demo_loop")
    parser.add_argument("--out", required=True, help="directory to write the demo bundle")
    args = parser.parse_args(argv)

    try:
        bundle = write_synthetic_code_qa_demo(args.out)
    except (OSError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    sys.stdout.write(
        json.dumps(
            {"out_dir": str(bundle.out_dir), "artifacts": bundle.artifacts},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
