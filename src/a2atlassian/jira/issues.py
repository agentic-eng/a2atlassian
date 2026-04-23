"""Jira issue operations — get_issue and search."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from a2atlassian.formatter import OperationResult

if TYPE_CHECKING:
    from a2atlassian.client import AtlassianClient


DEFAULT_SEARCH_FIELDS: list[str] = ["summary", "status", "assignee", "priority", "issuetype", "parent", "updated"]


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
    fields: list[str] | None = None,
) -> OperationResult:
    """Search Jira issues by JQL query.

    fields:
      - None (default) → minimal field set (DEFAULT_SEARCH_FIELDS).
      - ["*all"] → omit fields kwarg; returns every field per issue (large).
      - explicit list → forwarded verbatim.
    """
    kwargs: dict[str, Any] = {"limit": limit, "start": offset}
    if fields is None:
        kwargs["fields"] = DEFAULT_SEARCH_FIELDS
    elif fields == ["*all"]:
        pass  # omit fields to get everything
    else:
        kwargs["fields"] = fields

    t0 = time.monotonic()
    response = await client._call(client._jira.jql, jql, **kwargs)
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


async def search_count(client: AtlassianClient, jql: str) -> OperationResult:
    """Return just the total count for a JQL — cheap pre-check before a broad search."""
    t0 = time.monotonic()
    response = await client._call(client._jira.jql, jql, limit=0, fields=[])
    elapsed = int((time.monotonic() - t0) * 1000)
    total = response.get("total", 0)
    return OperationResult(
        name="search_count",
        data={"jql": jql, "total": total},
        count=1,
        truncated=False,
        time_ms=elapsed,
    )


async def create_issue(
    client: AtlassianClient,
    project_key: str,
    summary: str,
    issue_type: str,
    description: str | None = None,
    extra_fields: dict[str, Any] | None = None,
) -> OperationResult:
    """Create a new Jira issue."""
    fields: dict[str, Any] = {
        "project": {"key": project_key},
        "summary": summary,
        "issuetype": {"name": issue_type},
    }
    if description:
        fields["description"] = description
    if extra_fields:
        fields.update(extra_fields)

    t0 = time.monotonic()
    data = await client._call(client._jira.create_issue, fields=fields)
    elapsed = int((time.monotonic() - t0) * 1000)

    # atlassian-python-api may return a dict with key/id or a full issue
    result_data: dict[str, Any] = {
        "key": data.get("key", ""),
        "id": str(data.get("id", "")),
        "self": data.get("self", ""),
        "status": "created",
    }

    return OperationResult(
        name="create_issue",
        data=result_data,
        count=1,
        truncated=False,
        time_ms=elapsed,
    )


async def update_issue(
    client: AtlassianClient,
    issue_key: str,
    fields: dict[str, Any],
) -> OperationResult:
    """Update fields on an existing Jira issue."""
    t0 = time.monotonic()
    await client._call(client._jira.update_issue_field, issue_key, fields)
    elapsed = int((time.monotonic() - t0) * 1000)

    return OperationResult(
        name="update_issue",
        data={"issue_key": issue_key, "status": "updated"},
        count=1,
        truncated=False,
        time_ms=elapsed,
    )


async def delete_issue(
    client: AtlassianClient,
    issue_key: str,
) -> OperationResult:
    """Delete a Jira issue."""
    t0 = time.monotonic()
    await client._call(client._jira.delete_issue, issue_key)
    elapsed = int((time.monotonic() - t0) * 1000)

    return OperationResult(
        name="delete_issue",
        data={"issue_key": issue_key, "status": "deleted"},
        count=1,
        truncated=False,
        time_ms=elapsed,
    )
