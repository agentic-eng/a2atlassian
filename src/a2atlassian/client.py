"""Shared Atlassian client base — retry, auth, rate limiting.

Service-specific subclasses (JiraClient, ConfluenceClient) own the lazy
`atlassian-python-api` instance. Keep this file free of service imports.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from requests.exceptions import HTTPError

from a2atlassian.errors import A2AtlassianError, AuthenticationError, RateLimitError, ServerError

if TYPE_CHECKING:
    from collections.abc import Callable

    from a2atlassian.connections import ConnectionInfo


class AtlassianClientBase:
    """Shared retry/auth wrapper. Subclasses provide a service instance."""

    MAX_RETRIES = 2
    RETRY_BACKOFF: list[float] = [1.0, 3.0]  # noqa: RUF012
    REQUEST_TIMEOUT = 30

    def __init__(self, connection: ConnectionInfo) -> None:
        self.connection = connection

    async def _call(self, fn: Callable, *args: Any, **kwargs: Any) -> Any:
        """Call a sync atlassian-python-api method with retry logic."""
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                return await asyncio.to_thread(fn, *args, **kwargs)
            except HTTPError as exc:
                status = getattr(exc.response, "status_code", None)

                if status in (401, 403):
                    msg = f"Authentication failed ({status}): {exc}"
                    raise AuthenticationError(msg) from exc

                if status == 429:
                    if attempt < self.MAX_RETRIES:
                        await asyncio.sleep(self.RETRY_BACKOFF[attempt])
                        continue
                    msg = f"Rate limited after {self.MAX_RETRIES + 1} attempts: {exc}"
                    raise RateLimitError(msg) from exc

                if status is not None and status >= 500:
                    if attempt < self.MAX_RETRIES:
                        await asyncio.sleep(self.RETRY_BACKOFF[attempt])
                        continue
                    msg = f"Server error after {self.MAX_RETRIES + 1} attempts: {exc}"
                    raise ServerError(msg) from exc

                raise

        msg = "Unexpected: retry loop exited without returning or raising"
        raise A2AtlassianError(msg)  # pragma: no cover


# Temporary shim — removed in Task 4 once every caller imports from jira_client.
from a2atlassian.jira_client import JiraClient as AtlassianClient  # noqa: E402, F401
