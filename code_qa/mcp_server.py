"""MCP tools for phantom-enterprise."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from code_qa.ask import ask as _ask
from code_qa.status import gather_status

mcp = FastMCP("phantom-enterprise")


@mcp.tool()
def enterprise_code_ask(repo: str, question: str) -> dict:
    result = _ask(repo, question)
    return {
        "answer": result.answer,
        "files": [file.path for file in result.context.files],
        "prompt_chars": result.prompt_chars,
    }


@mcp.tool()
def enterprise_status(
    *,
    base_url=None,
    backend=None,
    ha_checks=None,
    router=None,
    lister=None,
) -> dict:
    return gather_status(
        base_url=base_url,
        backend=backend,
        ha_checks=ha_checks,
        router=router,
        lister=lister,
    )


def main():
    mcp.run()


if __name__ == "__main__":
    main()
