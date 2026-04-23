"""Confluence CQL search."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from a2atlassian.formatter import OperationResult

if TYPE_CHECKING:
    from a2atlassian.confluence_client import ConfluenceClient


def _extract_search_row(raw: dict[str, Any]) -> dict[str, Any]:
    """Unified minimal row that works across pages / blogposts / comments / attachments."""
    content = raw.get("content") or {}
    links = content.get("_links") or {}
    return {
        "id": content.get("id", ""),
        "type": content.get("type", ""),
        "title": raw.get("title") or content.get("title", ""),
        "excerpt": raw.get("excerpt", ""),
        "url": links.get("webui", ""),
        "last_modified": raw.get("lastModified", ""),
    }


async def search(
    client: ConfluenceClient,
    cql: str,
    limit: int = 25,
    offset: int = 0,
) -> OperationResult:
    """Run a CQL query against Confluence. Returns a minimal row per match."""
    t0 = time.monotonic()
    raw = await client._call(client._confluence.cql, cql, start=offset, limit=limit)
    elapsed = int((time.monotonic() - t0) * 1000)

    results = (raw or {}).get("results", []) if isinstance(raw, dict) else (raw or [])
    rows = [_extract_search_row(r) for r in results]
    return OperationResult(
        name="search",
        data=rows,
        count=len(rows),
        truncated=len(rows) >= limit,
        time_ms=elapsed,
    )
