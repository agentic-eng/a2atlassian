"""Jira watcher tools — get and set watchers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from a2atlassian.decorators import check_writable, mcp_tool
from a2atlassian.formatter import OperationResult  # noqa: TC001 — FastMCP needs runtime annotation
from a2atlassian.jira.watchers import get_watchers, set_watchers
from a2atlassian.jira_client import JiraClient

if TYPE_CHECKING:
    from collections.abc import Callable

    from mcp.server.fastmcp import FastMCP

    from a2atlassian.connections import ConnectionInfo
    from a2atlassian.errors import ErrorEnricher


def register_read(
    server: FastMCP,
    get_client: Callable[[str], JiraClient],
    enricher: ErrorEnricher,
) -> None:
    @server.tool()
    @mcp_tool(enricher)
    async def jira_get_watchers(
        connection: str,
        issue_key: str,
        format: Literal["toon", "json"] = "toon",  # noqa: A002
    ) -> OperationResult:
        """Get watchers for a Jira issue.

        Returns TOON by default (compact); pass format='json' for standard JSON shape.
        """
        return await get_watchers(get_client(connection), issue_key)


def register_write(
    server: FastMCP,
    get_connection: Callable[[str], ConnectionInfo],
    enricher: ErrorEnricher,
) -> None:
    @server.tool()
    @mcp_tool(enricher)
    async def jira_set_watchers(
        connection: str,
        issue_key: str,
        add: list[str] | None = None,
        remove: list[str] | None = None,
        format: Literal["toon", "json"] = "json",  # noqa: A002
    ) -> OperationResult:
        """Add and/or remove watchers on a Jira issue. Pass account IDs in 'add' and/or 'remove' lists."""
        conn = get_connection(connection)
        check_writable(conn, connection)
        return await set_watchers(JiraClient(conn), issue_key, add=add, remove=remove)
