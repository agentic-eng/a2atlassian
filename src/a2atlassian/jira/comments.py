"""Jira comment operations — get, add, edit comments (API v2, wiki markup)."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from a2atlassian.formatter import OperationResult

if TYPE_CHECKING:
    from a2atlassian.client import AtlassianClient


def _extract_comment(raw: dict[str, Any]) -> dict[str, Any]:
    """Extract key fields from a raw comment."""
    author = raw.get("author") or {}
    update_author = raw.get("updateAuthor") or {}
    # Body can be string (v2) or ADF dict (v3)
    body = raw.get("body", "")
    if isinstance(body, dict):
        # ADF — extract text content as fallback
        body = _adf_to_text(body)
    return {
        "id": raw.get("id", ""),
        "author": author.get("displayName", ""),
        "updated_by": update_author.get("displayName", ""),
        "body": body,
        "created": raw.get("created", ""),
        "updated": raw.get("updated", ""),
    }


def _adf_to_text(adf: dict[str, Any]) -> str:
    """Rough ADF-to-text extractor — pulls text nodes recursively."""
    parts: list[str] = []
    for node in adf.get("content", []):
        if node.get("type") == "text":
            parts.append(node.get("text", ""))
        elif "content" in node:
            parts.append(_adf_to_text(node))
    return "".join(parts)


async def get_comments(
    client: AtlassianClient,
    issue_key: str,
    limit: int = 50,
    offset: int = 0,
) -> OperationResult:
    """Get comments for a Jira issue."""
    t0 = time.monotonic()
    response = await client._call(client._jira.issue_get_comments, issue_key)
    elapsed = int((time.monotonic() - t0) * 1000)

    comments = response.get("comments", [])
    total = response.get("total", len(comments))

    return OperationResult(
        name="get_comments",
        data=[_extract_comment(c) for c in comments],
        count=len(comments),
        truncated=total > len(comments),
        time_ms=elapsed,
    )


async def add_comment(client: AtlassianClient, issue_key: str, body: str) -> OperationResult:
    """Add a comment to a Jira issue. Uses API v2 (wiki markup)."""
    t0 = time.monotonic()
    data = await client._call(client._jira.issue_add_comment, issue_key, body)
    elapsed = int((time.monotonic() - t0) * 1000)

    return OperationResult(
        name="add_comment",
        data=_extract_comment(data),
        count=1,
        truncated=False,
        time_ms=elapsed,
    )


async def edit_comment(
    client: AtlassianClient,
    issue_key: str,
    comment_id: str,
    body: str,
) -> OperationResult:
    """Edit an existing comment on a Jira issue. Uses API v2 (wiki markup)."""
    t0 = time.monotonic()
    data = await client._call(client._jira.issue_edit_comment, issue_key, comment_id, body)
    elapsed = int((time.monotonic() - t0) * 1000)

    return OperationResult(
        name="edit_comment",
        data=_extract_comment(data),
        count=1,
        truncated=False,
        time_ms=elapsed,
    )
