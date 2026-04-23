"""Confluence page operations — read, search, and batch upsert."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from a2atlassian.formatter import OperationResult

if TYPE_CHECKING:
    from a2atlassian.confluence_client import ConfluenceClient


DEFAULT_PAGE_EXPAND = "body.storage,version,space"


def _extract_page_detail(raw: dict[str, Any]) -> dict[str, Any]:
    """Flatten a Confluence page response into a single-entity shape."""
    space = raw.get("space") or {}
    version = raw.get("version") or {}
    body = (raw.get("body") or {}).get("storage") or {}
    links = raw.get("_links") or {}
    return {
        "id": raw.get("id", ""),
        "title": raw.get("title", ""),
        "space_key": space.get("key", ""),
        "space_name": space.get("name", ""),
        "version": version.get("number", 0),
        "updated": version.get("when", ""),
        "url": links.get("webui", ""),
        "body": body.get("value", ""),
    }


async def get_page(
    client: ConfluenceClient,
    page_id: str,
    expand: str | None = None,
) -> OperationResult:
    """Fetch a single Confluence page by id."""
    t0 = time.monotonic()
    raw = await client._call(
        client._confluence.get_page_by_id,
        page_id,
        expand=expand or DEFAULT_PAGE_EXPAND,
    )
    elapsed = int((time.monotonic() - t0) * 1000)

    return OperationResult(
        name="get_page",
        data=_extract_page_detail(raw),
        count=1,
        truncated=False,
        time_ms=elapsed,
    )


def _extract_child_summary(raw: dict[str, Any]) -> dict[str, Any]:
    version = raw.get("version") or {}
    links = raw.get("_links") or {}
    return {
        "id": raw.get("id", ""),
        "title": raw.get("title", ""),
        "version": version.get("number", 0),
        "url": links.get("webui", ""),
    }


async def get_page_children(
    client: ConfluenceClient,
    page_id: str,
    limit: int = 50,
    offset: int = 0,
) -> OperationResult:
    """List direct children of a Confluence page."""
    t0 = time.monotonic()
    raw = await client._call(
        client._confluence.get_page_child_by_type,
        page_id,
        type="page",
        start=offset,
        limit=limit,
    )
    elapsed = int((time.monotonic() - t0) * 1000)

    items = raw if isinstance(raw, list) else (raw or {}).get("results", [])
    return OperationResult(
        name="get_page_children",
        data=[_extract_child_summary(item) for item in items],
        count=len(items),
        truncated=len(items) >= limit,
        time_ms=elapsed,
    )


async def resolve_page_identity(
    client: ConfluenceClient,
    space: str,
    title: str,
    page_id: str | None,
    parent_id: str | None,
) -> str | None:
    """Resolve a page id for upsert. Returns the id if an existing page matches, None if not.

    Precedence:
      1. page_id given → must exist; raise if missing.
      2. parent_id given → search that parent's children for a title match (this parent only).
      3. Otherwise → search the space root by title.

    Per-parent scope is deliberate: same title under a different parent counts as a miss.
    """
    if page_id:
        existing = await client._call(client._confluence.get_page_by_id, page_id)
        if not existing:
            msg = f"page_id {page_id} not found"
            raise ValueError(msg)
        return page_id

    if parent_id:
        children = await client._call(client._confluence.get_page_child_by_type, parent_id, type="page", start=0, limit=200)
        items = children if isinstance(children, list) else (children or {}).get("results", [])
        for child in items:
            if child.get("title") == title:
                return str(child.get("id"))
        return None

    top = await client._call(client._confluence.get_page_by_title, space=space, title=title)
    if top:
        return str(top.get("id"))
    return None
