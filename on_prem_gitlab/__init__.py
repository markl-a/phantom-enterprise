"""On-prem GitLab / Gitea connector (validated against a live on-prem Gitea instance)."""

from .connector import (
    list_repos,
    list_repo_files,
    get_repo_file,
    GiteaUnreachable,
    DEFAULT_BASE_URL,
)
from .gitlab import (
    GITLAB_DEFAULT_BASE_URL,
    GitLabUnreachable,
    get_project_file,
    list_project_files,
    list_projects,
)

__all__ = [
    "list_repos",
    "list_repo_files",
    "get_repo_file",
    "GiteaUnreachable",
    "DEFAULT_BASE_URL",
    "GITLAB_DEFAULT_BASE_URL",
    "GitLabUnreachable",
    "list_projects",
    "list_project_files",
    "get_project_file",
]
