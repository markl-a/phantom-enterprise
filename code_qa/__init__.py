"""AI for your PRIVATE code.

Point phantom at a private repository, ask a question in natural language, and
get an answer grounded in the actual file contents — **the code is read locally
and handed to a local phantom agent; nothing leaves the machine**.

Two source modes:

* ``--repo <local-path>``  (reliable default): walk the working tree, pick the
  files most relevant to the question, build a context blob, and answer via
  ``phantom exec``.
* ``--repo <owner/repo>`` (Gitea bonus): fetch file contents over the existing
  on-prem Gitea connector. Fails gracefully with a clear message if the host
  is unreachable.
"""

from .context import RepoContext, build_local_context, build_gitea_context
from .ask import ask, answer_with_phantom

__all__ = [
    "RepoContext",
    "build_local_context",
    "build_gitea_context",
    "ask",
    "answer_with_phantom",
]
