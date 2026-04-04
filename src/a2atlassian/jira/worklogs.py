"""Jira worklog operations — get and add worklogs."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from a2atlassian.formatter import OperationResult

if TYPE_CHECKING:
    from a2atlassian.client import AtlassianClient


def _adf_to_text(adf: dict[str, Any]) -> str:
    """Rough ADF-to-text extractor — pulls text nodes recursively."""
    parts: list[str] = []
    for node in adf.get("content", []):
        if node.get("type") == "text":
            parts.append(node.get("text", ""))
        elif "content" in node:
            parts.append(_adf_to_text(node))
    return "".join(parts)


def _extract_worklog(raw: dict[str, Any]) -> dict[str, Any]:
    """Extract key fields from a raw worklog."""
    author = raw.get("author") or {}
    if isinstance(author, str):
        author_name = author
    else:
        author_name = author.get("displayName", "")

    comment = raw.get("comment", "")
    if isinstance(comment, dict):
        comment = _adf_to_text(comment)

    return {
        "id": str(raw.get("id", "")),
        "author": author_name,
        "time_spent": raw.get("timeSpent", ""),
        "started": raw.get("started", ""),
        "comment": comment,
    }


async def get_worklogs(client: AtlassianClient, issue_key: str) -> OperationResult:
    """Get worklogs for a Jira issue."""
    t0 = time.monotonic()
    data = await client._call(client._jira.issue_get_worklog, issue_key)
    elapsed = int((time.monotonic() - t0) * 1000)

    # Response may have "worklogs" key or be a list directly
    if isinstance(data, dict):
        worklogs = data.get("worklogs", [])
    elif isinstance(data, list):
        worklogs = data
    else:
        worklogs = []

    return OperationResult(
        name="get_worklogs",
        data=[_extract_worklog(w) for w in worklogs],
        count=len(worklogs),
        truncated=False,
        time_ms=elapsed,
    )


async def add_worklog(
    client: AtlassianClient,
    issue_key: str,
    time_spent: str,
    comment: str | None = None,
) -> OperationResult:
    """Add a worklog entry to a Jira issue."""
    t0 = time.monotonic()
    data = await client._call(client._jira.issue_worklog, issue_key, timeSpent=time_spent, comment=comment)
    elapsed = int((time.monotonic() - t0) * 1000)

    result_data: dict[str, Any]
    if isinstance(data, dict):
        result_data = _extract_worklog(data)
        result_data["status"] = "added"
    else:
        result_data = {"issue_key": issue_key, "time_spent": time_spent, "status": "added"}

    return OperationResult(
        name="add_worklog",
        data=result_data,
        count=1,
        truncated=False,
        time_ms=elapsed,
    )
