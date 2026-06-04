"""Build a relevance-ranked context blob from a private repo.

Local mode walks the working tree; Gitea mode pulls file contents over the
on-prem connector. Both produce a :class:`RepoContext` (a list of selected
files + their contents), which the CLI turns into a single grounding prompt.
"""

from __future__ import annotations

import fnmatch
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

# --- tunables (caps keep the prompt inside the model context window) -------

#: Directories we never descend into.
SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", "env", "ENV",
    "dist", "build", ".tox", ".nox", ".mypy_cache", ".pytest_cache",
    ".idea", ".vscode", "target", ".cargo", "vendor", ".next", "coverage",
    "htmlcov", ".eggs",
}

#: Extensions we treat as "source / docs" (preferred for context).
SOURCE_EXTS = {
    ".py", ".rs", ".js", ".ts", ".tsx", ".jsx", ".go", ".java", ".kt",
    ".c", ".h", ".cpp", ".hpp", ".cc", ".cs", ".rb", ".php", ".swift",
    ".scala", ".sh", ".bash", ".zsh", ".sql", ".toml", ".yaml", ".yml",
    ".json", ".cfg", ".ini", ".md", ".rst", ".txt", ".proto", ".graphql",
}

#: Per-file char cap and total context char cap (rough proxy for tokens).
MAX_FILE_CHARS = 8_000
MAX_TOTAL_CHARS = 60_000
MAX_FILES = 25
#: Skip files larger than this on disk (bytes) before reading.
MAX_FILE_BYTES = 400_000

_WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")


@dataclass
class SelectedFile:
    path: str            # repo-relative path, posix style
    content: str         # (possibly truncated) text
    score: float
    truncated: bool = False


@dataclass
class RepoContext:
    source: str          # description of where files came from
    files: list[SelectedFile] = field(default_factory=list)
    total_chars: int = 0
    considered: int = 0  # how many candidate files were ranked

    def as_prompt_blob(self) -> str:
        parts = []
        for f in self.files:
            suffix = "\n... [truncated]" if f.truncated else ""
            parts.append(
                f"=== FILE: {f.path} ===\n{f.content}{suffix}\n"
            )
        return "\n".join(parts)


# --- relevance ranking -----------------------------------------------------

def _question_terms(question: str) -> set[str]:
    terms = {m.group(0).lower() for m in _WORD_RE.finditer(question)}
    # also split snake/camel-ish words a user might type as a path
    extra: set[str] = set()
    for t in list(terms):
        extra.update(p for p in re.split(r"[_\-./]", t) if len(p) > 2)
    return terms | extra


def _score(path: str, content: str, terms: set[str]) -> float:
    if not terms:
        return 0.0
    path_l = path.lower()
    content_l = content.lower()
    score = 0.0
    for t in terms:
        # path hits are strong relevance signals
        if t in path_l:
            score += 5.0
        # content hits, capped so one huge file doesn't dominate
        c = content_l.count(t)
        if c:
            score += min(c, 20) * 0.5
    return score


# --- local working-tree walk ----------------------------------------------

def _load_gitignore_globs(root: Path) -> list[str]:
    """Cheap .gitignore-ish: collect simple glob patterns (no negation/nesting)."""
    globs: list[str] = []
    gi = root / ".gitignore"
    if not gi.exists():
        return globs
    try:
        for line in gi.read_text(errors="ignore").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or s.startswith("!"):
                continue
            globs.append(s.rstrip("/"))
    except OSError:
        pass
    return globs


def _ignored(rel_posix: str, globs: Iterable[str]) -> bool:
    name = rel_posix.split("/")[-1]
    for g in globs:
        if fnmatch.fnmatch(rel_posix, g) or fnmatch.fnmatch(name, g):
            return True
        # directory-style pattern: foo matches foo/bar...
        if rel_posix == g or rel_posix.startswith(g + "/"):
            return True
    return False


def _iter_local_files(root: Path) -> Iterable[Path]:
    globs = _load_gitignore_globs(root)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            p = Path(dirpath) / fn
            rel = p.relative_to(root).as_posix()
            if _ignored(rel, globs):
                continue
            yield p


def _read_text(path: Path) -> Optional[str]:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return None
    except OSError:
        return None
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in data[:4096]:  # binary
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return data.decode("latin-1")
        except UnicodeDecodeError:
            return None


def build_local_context(repo_path: str, question: str) -> RepoContext:
    root = Path(repo_path).expanduser().resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"not a directory: {root}")
    terms = _question_terms(question)

    candidates: list[tuple[float, str, str]] = []  # (score, rel, content)
    considered = 0
    for p in _iter_local_files(root):
        rel = p.relative_to(root).as_posix()
        is_source = p.suffix.lower() in SOURCE_EXTS
        content = _read_text(p)
        if content is None:
            continue
        considered += 1
        s = _score(rel, content, terms)
        if is_source:
            s += 1.0  # mild preference for source/docs over data files
        candidates.append((s, rel, content))

    candidates.sort(key=lambda c: c[0], reverse=True)
    return _assemble(
        source=f"local working tree: {root}",
        ranked=candidates,
        considered=considered,
    )


# --- Gitea (on-prem) -------------------------------------------------------

def build_gitea_context(
    owner: str,
    repo: str,
    question: str,
    *,
    token: Optional[str] = None,
    ref: Optional[str] = None,
    base_url: Optional[str] = None,
) -> RepoContext:
    """Pull file contents over the existing on-prem Gitea connector.

    Raises :class:`on_prem_gitlab.GiteaUnreachable` if the host is down — the
    CLI catches it and points the user at the reliable local path.
    """
    from on_prem_gitlab import (
        DEFAULT_BASE_URL,
        get_repo_file,
        list_repo_files,
    )

    base = base_url or DEFAULT_BASE_URL
    entries = list_repo_files(
        owner, repo, token=token, ref=ref, base_url=base
    )
    terms = _question_terms(question)

    # Rank by path first (cheap), fetch contents only for the top slice to
    # avoid hammering the API with one request per file.
    blobs = [
        e for e in entries
        if e.get("type") == "blob"
        and (e.get("size") or 0) <= MAX_FILE_BYTES
    ]

    def path_pref(e: dict) -> float:
        path = e.get("path", "")
        s = _score(path, "", terms)
        if Path(path).suffix.lower() in SOURCE_EXTS:
            s += 1.0
        return s

    blobs.sort(key=path_pref, reverse=True)
    top = blobs[: MAX_FILES * 2]  # fetch a buffer, then re-rank with content

    ranked: list[tuple[float, str, str]] = []
    for e in top:
        path = e["path"]
        try:
            content = get_repo_file(
                owner, repo, path, token=token, ref=ref, base_url=base
            )
        except Exception:
            continue
        if "\x00" in content[:4096]:
            continue
        s = _score(path, content, terms)
        if Path(path).suffix.lower() in SOURCE_EXTS:
            s += 1.0
        ranked.append((s, path, content))

    ranked.sort(key=lambda c: c[0], reverse=True)
    return _assemble(
        source=f"on-prem Gitea: {owner}/{repo} @ {base}",
        ranked=ranked,
        considered=len(blobs),
    )


# --- shared assembly -------------------------------------------------------

def _assemble(
    source: str,
    ranked: list[tuple[float, str, str]],
    considered: int,
) -> RepoContext:
    ctx = RepoContext(source=source, considered=considered)
    for score, rel, content in ranked:
        if len(ctx.files) >= MAX_FILES:
            break
        if ctx.total_chars >= MAX_TOTAL_CHARS:
            break
        truncated = False
        body = content
        if len(body) > MAX_FILE_CHARS:
            body = body[:MAX_FILE_CHARS]
            truncated = True
        remaining = MAX_TOTAL_CHARS - ctx.total_chars
        if len(body) > remaining:
            body = body[:remaining]
            truncated = True
        ctx.files.append(
            SelectedFile(path=rel, content=body, score=score, truncated=truncated)
        )
        ctx.total_chars += len(body)
    return ctx
