"""Jira link tools — get link types, create/remove links."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from a2atlassian.decorators import check_writable, mcp_tool
from a2atlassian.formatter import OperationResult  # noqa: TC001 — FastMCP needs runtime annotation
from a2atlassian.jira.links import create_issue_link, get_link_types, remove_issue_link
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
    async def jira_get_link_types(
        connection: str,
        format: Literal["toon", "json"] = "toon",  # noqa: A002
    ) -> OperationResult:
        """Get all available issue link types (e.g. Blocks, Duplicate, Relates).

        Returns TOON by default (compact); pass format='json' for standard JSON shape.
        """
        return await get_link_types(get_client(connection))


def register_write(
    server: FastMCP,
    get_connection: Callable[[str], ConnectionInfo],
    enricher: ErrorEnricher,
) -> None:
    @server.tool()
    @mcp_tool(enricher)
    async def jira_create_issue_link(
        connection: str,
        link_type: str,
        inward_key: str,
        outward_key: str,
        format: Literal["toon", "json"] = "json",  # noqa: A002
    ) -> OperationResult:
        """Create a link between two Jira issues. Use jira_get_link_types to discover available types.

        To set an issue's parent (Epic), pass link_type='Epic' with inward_key=<child> and outward_key=<epic>.
        """
        conn = get_connection(connection)
        check_writable(conn, connection)
        return await create_issue_link(JiraClient(conn), link_type, inward_key, outward_key)

    @server.tool()
    @mcp_tool(enricher)
    async def jira_remove_issue_link(
        connection: str,
        link_id: str,
        format: Literal["toon", "json"] = "json",  # noqa: A002
    ) -> OperationResult:
        """Remove an issue link by its ID."""
        conn = get_connection(connection)
        check_writable(conn, connection)
        return await remove_issue_link(JiraClient(conn), link_id)
