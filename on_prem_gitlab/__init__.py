"""On-prem GitLab / Gitea connector (validated against live Gitea on z13)."""

from .connector import list_repos, GiteaUnreachable, DEFAULT_BASE_URL

__all__ = ["list_repos", "GiteaUnreachable", "DEFAULT_BASE_URL"]
