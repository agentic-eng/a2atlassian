"""Confluence page tools — get, get_children, upsert."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from a2atlassian.confluence.pages import get_page, get_page_children, upsert_pages
from a2atlassian.confluence_client import ConfluenceClient
from a2atlassian.decorators import check_writable, mcp_tool
from a2atlassian.formatter import OperationResult  # noqa: TC001 — FastMCP needs runtime annotation

if TYPE_CHECKING:
    from collections.abc import Callable

    from mcp.server.fastmcp import FastMCP

    from a2atlassian.connections import ConnectionInfo
    from a2atlassian.errors import ErrorEnricher


def register_read(
    server: FastMCP,
    get_client: Callable[[str], ConfluenceClient],
    enricher: ErrorEnricher,
) -> None:
    @server.tool()
    @mcp_tool(enricher)
    async def confluence_get_page(
        connection: str,
        page_id: str,
        expand: str | None = None,
        format: Literal["toon", "json"] = "json",  # noqa: A002
    ) -> OperationResult:
        """Get a Confluence page by id. Returns title, body (storage format), version, space, url."""
        return await get_page(get_client(connection), page_id, expand=expand)

    @server.tool()
    @mcp_tool(enricher)
    async def confluence_get_page_children(
        connection: str,
        page_id: str,
        limit: int = 50,
        offset: int = 0,
        format: Literal["toon", "json"] = "toon",  # noqa: A002
    ) -> OperationResult:
        """List direct children of a Confluence page. Paginated."""
        return await get_page_children(get_client(connection), page_id, limit=limit, offset=offset)


def register_write(
    server: FastMCP,
    get_connection: Callable[[str], ConnectionInfo],
    enricher: ErrorEnricher,
) -> None:
    @server.tool()
    @mcp_tool(enricher)
    async def confluence_upsert_pages(
        connection: str,
        pages: list[dict[str, Any]],
        format: Literal["toon", "json"] = "json",  # noqa: A002
    ) -> OperationResult:
        """Batch create-or-update Confluence pages.

        Each page spec:
          space (str, required)
          title (str, required)
          content (str, required)
          parent_id (str | None)
          page_id (str | None) — if set, always updates this id.
          content_format: "markdown" (default) | "storage"
          page_width: "full-width" | "fixed-width" | None (on update, None preserves existing)
          emoji: str | None
          labels: list[str] | None

        Identity resolution per page (in order):
          1. page_id
          2. parent_id → title match under that parent only
          3. space root → title match at top level

        Returns {succeeded: [...], failed: [...], summary: {...}}. Does NOT raise on
        partial failure — inspect `failed` to see per-page errors with error_category
        (permission | format | conflict | other).
        """
        conn = get_connection(connection)
        check_writable(conn, connection)
        client = ConfluenceClient(conn)
        return await upsert_pages(client, pages)
