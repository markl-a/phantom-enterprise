"""Glue: build context from a private repo and answer via a local phantom agent.

The LLM call goes through the ``phantom`` binary's ``exec`` subcommand, which
runs a single-turn agent **locally**. The repo bytes are read on this machine
and piped to that local process; they are never uploaded anywhere by this tool.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from typing import Optional

from .context import RepoContext, build_gitea_context, build_gitlab_context, build_local_context

PROMPT_TEMPLATE = """\
You are answering a question about a PRIVATE codebase. Use ONLY the file
contents provided below — do not invent files, functions, or behavior that is
not shown. If the answer is not present in the provided files, say so plainly.
Cite the relevant file path(s) in your answer.

QUESTION:
{question}

PROVIDED FILES (from {source}):
{blob}

Now answer the question, grounded strictly in the files above.
"""


@dataclass
class AskResult:
    question: str
    answer: str
    context: RepoContext
    prompt_chars: int


def answer_with_phantom(
    question: str,
    context: RepoContext,
    *,
    phantom_bin: str = "phantom",
    timeout: float = 300.0,
) -> str:
    """Run ``phantom exec`` locally with the grounding prompt; return its text."""
    prompt = PROMPT_TEMPLATE.format(
        question=question,
        source=context.source,
        blob=context.as_prompt_blob(),
    )
    cmd = [phantom_bin, "exec"]
    # Optional, env-driven provider passthrough. When PHANTOM_PROVIDER is set
    # and non-empty, forward it as ``--provider <value>`` right after ``exec``.
    # When unset/empty, the command is unchanged.
    provider = os.environ.get("PHANTOM_PROVIDER", "").strip()
    if provider:
        cmd += ["--provider", provider]
    cmd.append("--quiet")
    try:
        proc = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"'{phantom_bin}' not found on PATH — install the phantom binary"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"phantom exec timed out after {timeout}s") from exc
    if proc.returncode != 0:
        raise RuntimeError(
            f"phantom exec failed (exit {proc.returncode}): "
            f"{(proc.stderr or '').strip()[:500]}"
        )
    return proc.stdout.strip()


def ask(
    repo: str,
    question: str,
    *,
    token: Optional[str] = None,
    ref: Optional[str] = None,
    base_url: Optional[str] = None,
    phantom_bin: str = "phantom",
    is_gitea: Optional[bool] = None,
    is_gitlab: Optional[bool] = None,
) -> AskResult:
    """End-to-end: select files from ``repo`` and answer ``question``.

    ``repo`` is treated as a local path unless it looks like ``owner/repo``
    (and is not an existing local directory), or ``is_gitea`` is forced.
    """
    from pathlib import Path

    if not is_gitlab and is_gitea is None:
        looks_gitea = (
            "/" in repo
            and repo.count("/") == 1
            and not Path(repo).expanduser().exists()
        )
        is_gitea = looks_gitea

    if is_gitlab:
        context = build_gitlab_context(
            repo, question, token=token, ref=ref, base_url=base_url
        )
    elif is_gitea:
        owner, _, name = repo.partition("/")
        context = build_gitea_context(
            owner, name, question, token=token, ref=ref, base_url=base_url
        )
    else:
        context = build_local_context(repo, question)

    answer = answer_with_phantom(question, context, phantom_bin=phantom_bin)
    prompt_chars = context.total_chars
    return AskResult(
        question=question,
        answer=answer,
        context=context,
        prompt_chars=prompt_chars,
    )
