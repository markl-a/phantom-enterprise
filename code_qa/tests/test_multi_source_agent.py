from __future__ import annotations

from code_qa.multi_source_agent import MultiSourceAgent, ask_multi_source


class FakeConfluence:
    def __init__(self) -> None:
        self.searched: list[str] = []
        self.fetched: list[str] = []

    def search_pages(self, cql: str, *, limit: int = 25) -> list[dict]:
        self.searched.append(cql)
        assert limit == 5
        return [{"id": "123", "title": "Deploy runbook"}]

    def get_page(self, page_id: str, **kwargs) -> dict:
        self.fetched.append(page_id)
        return {
            "id": page_id,
            "title": "Deploy runbook",
            "body": {
                "storage": {
                    "value": "Retry the failed GitLab deploy job after checking secrets."
                }
            },
            "_links": {"webui": "/wiki/spaces/OPS/pages/123"},
        }


class FakeJira:
    def __init__(self) -> None:
        self.queried: list[str] = []

    def list_issues(self, jql: str, *, max_results: int = 50) -> list[dict]:
        self.queried.append(jql)
        assert max_results == 5
        return [
            {
                "key": "OPS-7",
                "fields": {
                    "summary": "Deploy job fails on missing secret",
                    "status": {"name": "Open"},
                    "description": "Known failure when DEPLOY_TOKEN is not present.",
                },
            }
        ]


def test_multi_source_agent_fans_out_merges_and_attributes_results():
    confluence = FakeConfluence()
    jira = FakeJira()

    result = MultiSourceAgent([confluence, jira], limit_per_source=5).ask(
        "Why did deploy fail?"
    )

    assert confluence.searched == ['text ~ "Why did deploy fail?"']
    assert confluence.fetched == ["123"]
    assert jira.queried == ['text ~ "Why did deploy fail?" ORDER BY updated DESC']

    assert result.query == "Why did deploy fail?"
    assert result.sources_queried == [
        "FakeConfluence.search_pages",
        "FakeJira.list_issues",
    ]
    assert [item["source_type"] for item in result.results] == ["confluence", "jira"]
    assert [item["source"] for item in result.results] == [
        "FakeConfluence.search_pages",
        "FakeJira.list_issues",
    ]
    assert [item["reference"] for item in result.results] == [
        "/wiki/spaces/OPS/pages/123",
        "OPS-7",
    ]
    assert "Deploy runbook" in result.answer
    assert "OPS-7" in result.answer
    assert "FakeConfluence.search_pages" in result.answer
    assert "FakeJira.list_issues" in result.answer


def test_ask_multi_source_requires_at_least_two_queryable_connectors():
    try:
        ask_multi_source("q", [FakeConfluence()])
    except ValueError as exc:
        assert "at least 2" in str(exc)
    else:
        raise AssertionError("expected ValueError")
