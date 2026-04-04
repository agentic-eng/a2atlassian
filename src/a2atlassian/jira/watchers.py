"""Jira watcher operations — get, add, remove watchers."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from a2atlassian.formatter import OperationResult

if TYPE_CHECKING:
    from a2atlassian.client import AtlassianClient


def _extract_watcher(raw: dict[str, Any]) -> dict[str, Any]:
    """Extract key fields from a raw watcher."""
    return {
        "account_id": str(raw.get("accountId", "")),
        "display_name": raw.get("displayName", ""),
    }


async def get_watchers(client: AtlassianClient, issue_key: str) -> OperationResult:
    """Get watchers for a Jira issue."""
    t0 = time.monotonic()
    data = await client._call(client._jira.issue_get_watchers, issue_key)
    elapsed = int((time.monotonic() - t0) * 1000)

    # Response may have "watchers" key or be a list directly
    if isinstance(data, dict):
        watchers = data.get("watchers", [])
    elif isinstance(data, list):
        watchers = data
    else:
        watchers = []

    return OperationResult(
        name="get_watchers",
        data=[_extract_watcher(w) for w in watchers],
        count=len(watchers),
        truncated=False,
        time_ms=elapsed,
    )


async def add_watcher(
    client: AtlassianClient,
    issue_key: str,
    account_id: str,
) -> OperationResult:
    """Add a watcher to a Jira issue."""
    t0 = time.monotonic()
    await client._call(client._jira.issue_add_watcher, issue_key, account_id)
    elapsed = int((time.monotonic() - t0) * 1000)

    return OperationResult(
        name="add_watcher",
        data={
            "issue_key": issue_key,
            "account_id": account_id,
            "status": "added",
        },
        count=1,
        truncated=False,
        time_ms=elapsed,
    )


async def remove_watcher(
    client: AtlassianClient,
    issue_key: str,
    account_id: str,
) -> OperationResult:
    """Remove a watcher from a Jira issue."""
    t0 = time.monotonic()
    await client._call(client._jira.issue_remove_watcher, issue_key, account_id)
    elapsed = int((time.monotonic() - t0) * 1000)

    return OperationResult(
        name="remove_watcher",
        data={
            "issue_key": issue_key,
            "account_id": account_id,
            "status": "removed",
        },
        count=1,
        truncated=False,
        time_ms=elapsed,
    )
