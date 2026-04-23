"""Jira-specific Atlassian client — lazy atlassian.Jira wrapper."""

from __future__ import annotations

from typing import Any

from a2atlassian.client import AtlassianClientBase


def _lazy_jira() -> Any:
    """Lazy import to avoid loading atlassian module at import time."""
    from atlassian import Jira  # noqa: PLC0415

    return Jira


class JiraClient(AtlassianClientBase):
    """Async wrapper around atlassian-python-api Jira client."""

    def __init__(self, connection: Any) -> None:
        super().__init__(connection)
        self._jira_instance: Any | None = None

    @property
    def _jira(self) -> Any:
        """Lazily create the Jira client."""
        if self._jira_instance is None:
            jira_cls = _lazy_jira()
            self._jira_instance = jira_cls(
                url=self.connection.url,
                username=self.connection.email,
                password=self.connection.resolved_token,
                cloud=True,
            )
        return self._jira_instance

    async def validate(self) -> dict:
        """Validate the connection by calling /myself. Returns Jira user info."""
        return await self._call(self._jira.myself)
