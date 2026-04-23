"""Jira watcher operations — get and set watchers."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from a2atlassian.formatter import OperationResult

if TYPE_CHECKING:
    from a2atlassian.jira_client import JiraClient


def _extract_watcher(raw: dict[str, Any]) -> dict[str, Any]:
    """Extract key fields from a raw watcher."""
    return {
        "account_id": str(raw.get("accountId", "")),
        "display_name": raw.get("displayName", ""),
    }


async def get_watchers(client: JiraClient, issue_key: str) -> OperationResult:
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


async def set_watchers(
    client: JiraClient,
    issue_key: str,
    add: list[str] | None = None,
    remove: list[str] | None = None,
) -> OperationResult:
    """Add and/or remove watchers on a Jira issue. Lists of account IDs."""
    t0 = time.monotonic()
    for account_id in add or []:
        await client._call(client._jira.issue_add_watcher, issue_key, account_id)
    for account_id in remove or []:
        await client._call(client._jira.issue_delete_watcher, issue_key, account_id)
    elapsed = int((time.monotonic() - t0) * 1000)
    return OperationResult(
        name="set_watchers",
        data={"issue_key": issue_key, "added": list(add or []), "removed": list(remove or []), "status": "ok"},
        count=1,
        truncated=False,
        time_ms=elapsed,
    )
