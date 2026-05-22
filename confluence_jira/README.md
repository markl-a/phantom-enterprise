# confluence_jira

**Status:** placeholder — no code.

Target: corporate Atlassian Confluence + Jira (Cloud or Data Center).
This is the easiest connector to validate because Atlassian has public,
stable REST APIs and most target employers run it.

Planned shape: ``search_pages(cql)``, ``get_page(page_id)``,
``list_issues(jql)``, ``add_comment(issue_key, body)``.

Activates: first hour at any employer running Atlassian — straightforward
``requests`` wrapper around documented endpoints.
