"""Jira comment tools — get, add, edit."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from a2atlassian.decorators import check_writable, mcp_tool
from a2atlassian.formatter import OperationResult  # noqa: TC001 — FastMCP needs runtime annotation
from a2atlassian.jira.comments import add_comment, edit_comment, get_comments
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
    async def jira_get_comments(
        connection: str,
        issue_key: str,
        format: Literal["toon", "json"] = "toon",  # noqa: A002
    ) -> OperationResult:
        """Get all comments for a Jira issue.

        Returns TOON by default (compact); pass format='json' for standard JSON shape.
        """
        return await get_comments(get_client(connection), issue_key)


def register_write(
    server: FastMCP,
    get_connection: Callable[[str], ConnectionInfo],
    enricher: ErrorEnricher,
) -> None:
    @server.tool()
    @mcp_tool(enricher)
    async def jira_add_comment(
        connection: str,
        issue_key: str,
        body: str,
        format: Literal["toon", "json"] = "json",  # noqa: A002
    ) -> OperationResult:
        """Add a comment to a Jira issue. Uses wiki markup (API v2)."""
        conn = get_connection(connection)
        check_writable(conn, connection)
        return await add_comment(JiraClient(conn), issue_key, body)

    @server.tool()
    @mcp_tool(enricher)
    async def jira_edit_comment(
        connection: str,
        issue_key: str,
        comment_id: str,
        body: str,
        format: Literal["toon", "json"] = "json",  # noqa: A002
    ) -> OperationResult:
        """Edit an existing comment on a Jira issue. Uses wiki markup (API v2)."""
        conn = get_connection(connection)
        check_writable(conn, connection)
        return await edit_comment(JiraClient(conn), issue_key, comment_id, body)
