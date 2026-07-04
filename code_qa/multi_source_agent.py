"""Bounded multi-source orchestration for existing enterprise connectors."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


@dataclass(frozen=True)
class MultiSourceAnswer:
    query: str
    answer: str
    results: list[dict[str, Any]]
    sources_queried: list[str]


class MultiSourceAgent:
    """Fan out a question over existing connector interfaces and merge evidence."""

    def __init__(
        self,
        connectors: Sequence[object],
        *,
        min_sources: int = 2,
        limit_per_source: int = 5,
    ) -> None:
        if min_sources < 1:
            raise ValueError("min_sources must be at least 1")
        if limit_per_source < 1:
            raise ValueError("limit_per_source must be at least 1")
        self.connectors = list(connectors)
        self.min_sources = min_sources
        self.limit_per_source = limit_per_source

    def ask(self, query: str) -> MultiSourceAnswer:
        clean_query = query.strip()
        if not clean_query:
            raise ValueError("query must not be empty")

        sources_queried: list[str] = []
        results: list[dict[str, Any]] = []

        for connector in self.connectors:
            for source_name, source_type, items in self._query_connector(
                connector,
                clean_query,
            ):
                sources_queried.append(source_name)
                for item in items:
                    enriched = dict(item)
                    enriched["source"] = source_name
                    enriched["source_type"] = source_type
                    results.append(enriched)

        if len(sources_queried) < self.min_sources:
            raise ValueError(
                f"MultiSourceAgent requires at least {self.min_sources} "
                f"queryable sources; queried {len(sources_queried)}"
            )

        return MultiSourceAnswer(
            query=clean_query,
            answer=_compose_answer(clean_query, results, sources_queried),
            results=results,
            sources_queried=sources_queried,
        )

    def _query_connector(
        self,
        connector: object,
        query: str,
    ) -> Iterable[tuple[str, str, list[dict[str, Any]]]]:
        if hasattr(connector, "search_pages"):
            source = _source_name(connector, "search_pages")
            pages = connector.search_pages(_confluence_cql(query), limit=self.limit_per_source)
            yield source, "confluence", [
                _normalize_confluence_page(connector, page)
                for page in list(pages or [])[: self.limit_per_source]
            ]

        if hasattr(connector, "list_issues"):
            source = _source_name(connector, "list_issues")
            issues = connector.list_issues(_jira_jql(query), max_results=self.limit_per_source)
            yield source, "jira", [
                _normalize_jira_issue(issue)
                for issue in list(issues or [])[: self.limit_per_source]
            ]

        if hasattr(connector, "list_project_files") and hasattr(connector, "get_project_file"):
            project_id = getattr(connector, "project_id", None)
            if project_id is not None:
                source = _source_name(connector, "list_project_files")
                yield source, "gitlab", _query_gitlab_files(
                    connector,
                    project_id,
                    query,
                    self.limit_per_source,
                )

        if hasattr(connector, "list_repo_files") and hasattr(connector, "get_repo_file"):
            owner = getattr(connector, "owner", None)
            repo = getattr(connector, "repo", None)
            if owner is not None and repo is not None:
                source = _source_name(connector, "list_repo_files")
                yield source, "gitea", _query_gitea_files(
                    connector,
                    owner,
                    repo,
                    query,
                    self.limit_per_source,
                )


def ask_multi_source(
    query: str,
    connectors: Sequence[object],
    *,
    min_sources: int = 2,
    limit_per_source: int = 5,
) -> MultiSourceAnswer:
    return MultiSourceAgent(
        connectors,
        min_sources=min_sources,
        limit_per_source=limit_per_source,
    ).ask(query)


def _query_gitlab_files(
    connector: object,
    project_id: object,
    query: str,
    limit: int,
) -> list[dict[str, Any]]:
    entries = connector.list_project_files(project_id)
    return [
        _normalize_file_result(
            path,
            connector.get_project_file(project_id, path),
            reference=f"{project_id}:{path}",
        )
        for path in _rank_file_paths(entries, query, limit)
    ]


def _query_gitea_files(
    connector: object,
    owner: object,
    repo: object,
    query: str,
    limit: int,
) -> list[dict[str, Any]]:
    entries = connector.list_repo_files(owner, repo)
    return [
        _normalize_file_result(
            path,
            connector.get_repo_file(owner, repo, path),
            reference=f"{owner}/{repo}:{path}",
        )
        for path in _rank_file_paths(entries, query, limit)
    ]


def _rank_file_paths(entries: object, query: str, limit: int) -> list[str]:
    ranked: list[tuple[int, str]] = []
    terms = _terms(query)
    for entry in entries or []:
        if not isinstance(entry, dict) or entry.get("type") != "blob":
            continue
        path = str(entry.get("path") or "")
        if not path:
            continue
        path_l = path.lower()
        score = sum(1 for term in terms if term in path_l)
        if Path(path).suffix.lower() in {".py", ".js", ".ts", ".md", ".txt", ".yml"}:
            score += 1
        ranked.append((score, path))
    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [path for _, path in ranked[:limit]]


def _normalize_confluence_page(connector: object, page: dict[str, Any]) -> dict[str, Any]:
    details = dict(page)
    page_id = page.get("id")
    if page_id is not None and hasattr(connector, "get_page"):
        fetched = connector.get_page(page_id)
        if isinstance(fetched, dict):
            details.update(fetched)

    title = str(details.get("title") or page_id or "Confluence page")
    text = _plain_text(
        details.get("body")
        or details.get("excerpt")
        or details.get("metadata")
        or details.get("title")
        or ""
    )
    return {
        "title": title,
        "reference": _confluence_reference(details, page_id),
        "text": text,
        "raw": details,
    }


def _normalize_jira_issue(issue: dict[str, Any]) -> dict[str, Any]:
    fields = issue.get("fields") if isinstance(issue.get("fields"), dict) else {}
    key = str(issue.get("key") or issue.get("id") or "Jira issue")
    summary = str(fields.get("summary") or issue.get("summary") or key)
    status = _plain_text(fields.get("status", {}).get("name", ""))
    description = _plain_text(fields.get("description", ""))
    text = " ".join(part for part in [summary, status, description] if part)
    return {
        "title": summary,
        "reference": key,
        "text": text,
        "raw": issue,
    }


def _normalize_file_result(path: str, content: str, *, reference: str) -> dict[str, Any]:
    return {
        "title": path,
        "reference": reference,
        "text": _plain_text(content)[:1000],
        "raw": {"path": path},
    }


def _compose_answer(
    query: str,
    results: list[dict[str, Any]],
    sources_queried: list[str],
) -> str:
    lines = [
        f"Found {len(results)} result(s) across {len(sources_queried)} source(s) for: {query}"
    ]
    for result in results:
        text = str(result.get("text") or "").strip()
        snippet = text[:220] + ("..." if len(text) > 220 else "")
        lines.append(
            "- "
            f"[{result['source']}] "
            f"{result.get('title', result.get('reference', 'result'))} "
            f"({result.get('reference', 'no reference')}): {snippet}"
        )
    if not results:
        lines.append("- No matching items were returned by the queried sources.")
    return "\n".join(lines)


def _source_name(connector: object, method: str) -> str:
    module_name = getattr(connector, "__name__", None)
    if isinstance(module_name, str) and module_name:
        return f"{module_name}.{method}"
    return f"{connector.__class__.__name__}.{method}"


def _confluence_cql(query: str) -> str:
    return f'text ~ "{_escape_query(query)}"'


def _jira_jql(query: str) -> str:
    return f'text ~ "{_escape_query(query)}" ORDER BY updated DESC'


def _escape_query(query: str) -> str:
    return query.replace("\\", "\\\\").replace('"', '\\"')


def _terms(query: str) -> set[str]:
    return {part.lower() for part in re.findall(r"[A-Za-z0-9_]{2,}", query)}


def _confluence_reference(details: dict[str, Any], page_id: object) -> str:
    links = details.get("_links") if isinstance(details.get("_links"), dict) else {}
    webui = links.get("webui")
    if webui:
        return str(webui)
    tinyui = links.get("tinyui")
    if tinyui:
        return str(tinyui)
    return str(page_id or details.get("id") or "confluence-page")


_TAG_RE = re.compile(r"<[^>]+>")


def _plain_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(_TAG_RE.sub(" ", value).split())
    if isinstance(value, dict):
        if "value" in value and isinstance(value["value"], str):
            return _plain_text(value["value"])
        return " ".join(_plain_text(item) for item in value.values()).strip()
    if isinstance(value, list):
        return " ".join(_plain_text(item) for item in value).strip()
    return str(value)
