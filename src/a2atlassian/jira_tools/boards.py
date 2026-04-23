"""Jira board tools — list boards, get board issues."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from a2atlassian.decorators import mcp_tool
from a2atlassian.formatter import OperationResult  # noqa: TC001 — FastMCP needs runtime annotation
from a2atlassian.jira.boards import get_board_issues, get_boards

if TYPE_CHECKING:
    from collections.abc import Callable

    from mcp.server.fastmcp import FastMCP

    from a2atlassian.client import AtlassianClient
    from a2atlassian.errors import ErrorEnricher


def register_read(
    server: FastMCP,
    get_client: Callable[[str], AtlassianClient],
    enricher: ErrorEnricher,
) -> None:
    @server.tool()
    @mcp_tool(enricher)
    async def jira_get_boards(
        connection: str,
        format: Literal["toon", "json"] = "toon",  # noqa: A002
    ) -> OperationResult:
        """List all Jira boards visible to the authenticated user.

        Returns TOON by default (compact); pass format='json' for standard JSON shape.
        """
        return await get_boards(get_client(connection))

    @server.tool()
    @mcp_tool(enricher)
    async def jira_get_board_issues(
        connection: str,
        board_id: int,
        limit: int = 50,
        offset: int = 0,
        format: Literal["toon", "json"] = "toon",  # noqa: A002
    ) -> OperationResult:
        """Get issues for a specific Jira board.

        Returns TOON by default (compact); pass format='json' for standard JSON shape.
        """
        return await get_board_issues(get_client(connection), board_id, limit=limit, offset=offset)
