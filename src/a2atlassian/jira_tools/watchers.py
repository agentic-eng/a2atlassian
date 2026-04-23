"""Jira watcher tools — get, add, remove watchers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from a2atlassian.client import AtlassianClient
from a2atlassian.decorators import mcp_tool
from a2atlassian.formatter import OperationResult  # noqa: TC001 — FastMCP needs runtime annotation
from a2atlassian.jira.watchers import add_watcher, get_watchers, remove_watcher

if TYPE_CHECKING:
    from collections.abc import Callable

    from mcp.server.fastmcp import FastMCP

    from a2atlassian.connections import ConnectionInfo
    from a2atlassian.errors import ErrorEnricher


def register_read(
    server: FastMCP,
    get_client: Callable[[str], AtlassianClient],
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
    async def jira_add_watcher(
        connection: str,
        issue_key: str,
        account_id: str,
        format: Literal["toon", "json"] = "json",  # noqa: A002
    ) -> OperationResult:
        """Add a watcher to a Jira issue."""
        conn = get_connection(connection)
        if conn.read_only:
            raise RuntimeError(f"Connection '{connection}' is read-only. Run: a2atlassian login -c {connection} --no-read-only")
        return await add_watcher(AtlassianClient(conn), issue_key, account_id)

    @server.tool()
    @mcp_tool(enricher)
    async def jira_remove_watcher(
        connection: str,
        issue_key: str,
        account_id: str,
        format: Literal["toon", "json"] = "json",  # noqa: A002
    ) -> OperationResult:
        """Remove a watcher from a Jira issue."""
        conn = get_connection(connection)
        if conn.read_only:
            raise RuntimeError(f"Connection '{connection}' is read-only. Run: a2atlassian login -c {connection} --no-read-only")
        return await remove_watcher(AtlassianClient(conn), issue_key, account_id)
