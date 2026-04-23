"""Confluence page tools — get, get_children, upsert."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from a2atlassian.confluence.pages import get_page, get_page_children, set_page_properties, upsert_pages
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

        `connection` is the saved a2atlassian connection name (e.g. "protea"), NOT a
        Jira/Confluence space or project key. Use `list_connections` to see names.

        Each page spec:
          space (str, required) — Confluence SPACE KEY (e.g. "TEAM"), not a connection name.
          title (str, required)
          content (str, optional) — markdown or storage. OMIT the key to preserve the
            existing page body on an update path (metadata-only write). An empty string
            is explicit and WILL wipe the body. Required when creating a new page.
          parent_id (str | None)
          page_id (str | None) — if set, always updates this id.
          content_format: "markdown" (default) | "storage"
          page_width: "full-width" | "fixed-width" | None (None preserves existing on update)
          emoji: str | None (None preserves existing on update)
          labels: list[str] | None

        Identity resolution per page (in order):
          1. page_id
          2. parent_id → title match under that parent only
          3. space root → title match at top level

        Returns {succeeded: [...], failed: [...], summary: {created, updated,
        metadata_updated, failed, total}}. Does NOT raise on partial failure —
        inspect `failed` for per-page errors with error_category (permission | format |
        conflict | other).
        """
        conn = get_connection(connection)
        check_writable(conn, connection)
        client = ConfluenceClient(conn)
        return await upsert_pages(client, pages)

    @server.tool()
    @mcp_tool(enricher)
    async def confluence_set_page_properties(
        connection: str,
        page_id: str,
        page_width: Literal["full-width", "fixed-width"] | None = None,
        emoji: str | None = None,
        labels: list[str] | None = None,
        format: Literal["toon", "json"] = "json",  # noqa: A002
    ) -> OperationResult:
        """Metadata-only write on a Confluence page — physically cannot touch body/title.

        Use this for safe width/emoji/label flips without any risk to page content.
        `connection` is the saved a2atlassian connection name (e.g. "protea"), NOT a
        Jira project key. Pass only the fields you want to change; omitted fields are
        left unchanged. All-None is a no-op that still verifies the page exists.

        Raises if `page_id` does not exist.
        """
        conn = get_connection(connection)
        check_writable(conn, connection)
        client = ConfluenceClient(conn)
        return await set_page_properties(
            client,
            page_id,
            page_width=page_width,
            emoji=emoji,
            labels=labels,
        )
