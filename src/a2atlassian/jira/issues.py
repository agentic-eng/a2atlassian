"""Jira issue operations — get_issue and search."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from a2atlassian.formatter import OperationResult

if TYPE_CHECKING:
    from a2atlassian.client import AtlassianClient


def _extract_issue_summary(raw: dict[str, Any]) -> dict[str, Any]:
    """Extract key fields from a raw issue for list display."""
    fields = raw.get("fields", {})
    status = fields.get("status") or {}
    assignee = fields.get("assignee") or {}
    priority = fields.get("priority") or {}
    issuetype = fields.get("issuetype") or {}
    parent = fields.get("parent") or {}
    return {
        "key": raw.get("key", ""),
        "summary": fields.get("summary", ""),
        "status": status.get("name", ""),
        "assignee": assignee.get("displayName", ""),
        "priority": priority.get("name", ""),
        "type": issuetype.get("name", ""),
        "parent": parent.get("key", ""),
        "updated": fields.get("updated", ""),
    }


def _extract_issue_detail(raw: dict[str, Any]) -> dict[str, Any]:
    """Extract fields from a raw issue for single-entity display."""
    fields = raw.get("fields", {})
    status = fields.get("status") or {}
    status_cat = status.get("statusCategory") or {}
    assignee = fields.get("assignee") or {}
    reporter = fields.get("reporter") or {}
    priority = fields.get("priority") or {}
    issuetype = fields.get("issuetype") or {}
    parent = fields.get("parent") or {}
    labels = fields.get("labels") or []
    components = fields.get("components") or []
    fix_versions = fields.get("fixVersions") or []
    return {
        "key": raw.get("key", ""),
        "summary": fields.get("summary", ""),
        "status": status.get("name", ""),
        "status_category": status_cat.get("name", ""),
        "assignee": assignee.get("displayName", ""),
        "reporter": reporter.get("displayName", ""),
        "priority": priority.get("name", ""),
        "type": issuetype.get("name", ""),
        "parent": parent.get("key", ""),
        "labels": ", ".join(labels) if labels else "",
        "components": ", ".join(c.get("name", "") for c in components),
        "fix_versions": ", ".join(v.get("name", "") for v in fix_versions),
        "description": fields.get("description") or "",
        "created": fields.get("created", ""),
        "updated": fields.get("updated", ""),
    }


async def get_issue(client: AtlassianClient, issue_key: str) -> OperationResult:
    """Fetch a single Jira issue by key."""
    t0 = time.monotonic()
    data = await client._call(client._jira.issue, issue_key)
    elapsed = int((time.monotonic() - t0) * 1000)

    return OperationResult(
        name="get_issue",
        data=_extract_issue_detail(data),
        count=1,
        truncated=False,
        time_ms=elapsed,
    )


async def search(
    client: AtlassianClient,
    jql: str,
    limit: int = 50,
    offset: int = 0,
) -> OperationResult:
    """Search Jira issues by JQL query."""
    t0 = time.monotonic()
    response = await client._call(
        client._jira.jql,
        jql,
        limit=limit,
        start=offset,
    )
    elapsed = int((time.monotonic() - t0) * 1000)

    issues = response.get("issues", [])
    total = response.get("total", len(issues))
    truncated = total > offset + len(issues) or len(issues) >= limit

    return OperationResult(
        name="search",
        data=[_extract_issue_summary(i) for i in issues],
        count=len(issues),
        truncated=truncated,
        time_ms=elapsed,
    )
