"""Jira project tools — list projects, versions, components."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from a2atlassian.decorators import check_writable, mcp_tool
from a2atlassian.formatter import OperationResult  # noqa: TC001 — FastMCP needs runtime annotation
from a2atlassian.jira.projects import create_version, get_project_metadata, get_projects
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
    async def jira_get_projects(
        connection: str,
        format: Literal["toon", "json"] = "toon",  # noqa: A002
    ) -> OperationResult:
        """List all Jira projects.

        Returns TOON by default (compact); pass format='json' for standard JSON shape.
        """
        return await get_projects(get_client(connection))

    @server.tool()
    @mcp_tool(enricher)
    async def jira_get_project_metadata(
        connection: str,
        project_key: str,
        include: list[str] | None = None,
        format: Literal["toon", "json"] = "json",  # noqa: A002
    ) -> OperationResult:
        """Get project metadata (components, versions). include=['components'], ['versions'], ['all'], or omit for all."""
        return await get_project_metadata(get_client(connection), project_key, include=include)


def register_write(
    server: FastMCP,
    get_connection: Callable[[str], ConnectionInfo],
    enricher: ErrorEnricher,
) -> None:
    @server.tool()
    @mcp_tool(enricher)
    async def jira_create_version(
        connection: str,
        project_key: str,
        name: str,
        format: Literal["toon", "json"] = "json",  # noqa: A002
    ) -> OperationResult:
        """Create a new version in a Jira project."""
        conn = get_connection(connection)
        check_writable(conn, connection)
        return await create_version(JiraClient(conn), project_key=project_key, name=name)
