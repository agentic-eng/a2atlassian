"""Jira project tools — list projects, versions, components."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from a2atlassian.client import AtlassianClient
from a2atlassian.decorators import mcp_tool
from a2atlassian.formatter import OperationResult  # noqa: TC001 — FastMCP needs runtime annotation
from a2atlassian.jira.projects import create_version, get_project_components, get_project_versions, get_projects

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
    async def jira_get_project_versions(
        connection: str,
        project_key: str,
        format: Literal["toon", "json"] = "toon",  # noqa: A002
    ) -> OperationResult:
        """Get versions for a Jira project.

        Returns TOON by default (compact); pass format='json' for standard JSON shape.
        """
        return await get_project_versions(get_client(connection), project_key)

    @server.tool()
    @mcp_tool(enricher)
    async def jira_get_project_components(
        connection: str,
        project_key: str,
        format: Literal["toon", "json"] = "toon",  # noqa: A002
    ) -> OperationResult:
        """Get components for a Jira project.

        Returns TOON by default (compact); pass format='json' for standard JSON shape.
        """
        return await get_project_components(get_client(connection), project_key)


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
        if conn.read_only:
            raise RuntimeError(f"Connection '{connection}' is read-only. Run: a2atlassian login -c {connection} --no-read-only")
        return await create_version(AtlassianClient(conn), project_key=project_key, name=name)
