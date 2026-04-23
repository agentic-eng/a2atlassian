"""Jira worklog operations — get and add worklogs."""

from __future__ import annotations

import time
from datetime import date as date_cls
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal
from zoneinfo import ZoneInfo

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


def _parse_started(started: str) -> datetime:
    """Parse Jira's '2026-04-22T10:00:00.000+0300' into a timezone-aware datetime.

    Jira uses e.g. '+0300' rather than '+03:00'; normalize to ISO 8601.
    """
    s = started
    if len(s) >= 5 and s[-5] in "+-" and s[-3] != ":":
        s = s[:-2] + ":" + s[-2:]
    return datetime.fromisoformat(s)


def _extract_assignee(issue: dict[str, Any]) -> dict[str, str]:
    """Return {'name': ..., 'email': ...} from a raw Jira issue dict."""
    fields = issue.get("fields", {}) or {}
    assignee = fields.get("assignee") or {}
    if isinstance(assignee, dict):
        return {"name": assignee.get("displayName", ""), "email": assignee.get("emailAddress", "")}
    return {"name": "", "email": ""}


def _attribute_worklog(
    wl: dict[str, Any],
    asn: dict[str, str],
    admins: tuple[str, ...],
) -> tuple[str, str] | None:
    """Return (person, source) for one worklog entry, or None if author data is absent."""
    author = wl.get("author") or {}
    if isinstance(author, dict):
        logger_email = author.get("emailAddress", "")
        logger_name = author.get("displayName", "")
    else:
        logger_email = ""
        logger_name = str(author)

    assignee_name = asn["name"]
    assignee_email = asn["email"]

    if logger_email and assignee_email and logger_email == assignee_email:
        return assignee_name or logger_name, "self"
    if logger_email in admins:
        return assignee_name or logger_name, f"proxy:{logger_name}"
    return logger_name, "non-admin-other"


def _aggregate_rows(
    rows: list[dict[str, Any]],
    detail: Literal["total", "by_day", "by_ticket"],
) -> list[dict[str, Any]]:
    """Reduce flat worklog rows into the requested detail level."""
    if detail == "by_ticket":
        return rows
    if detail == "by_day":
        agg: dict[tuple[str, str], float] = {}
        for r in rows:
            k = (r["person"], r["date"])
            agg[k] = agg.get(k, 0.0) + r["hours"]
        return [{"person": p, "date": d, "hours": h} for (p, d), h in sorted(agg.items())]
    # total
    totals: dict[str, float] = {}
    for r in rows:
        totals[r["person"]] = totals.get(r["person"], 0.0) + r["hours"]
    return [{"person": p, "total_hours": h} for p, h in sorted(totals.items())]


async def _fetch_issue_worklogs(
    client: AtlassianClient,
    key: str,
    asn: dict[str, str],
    admins: tuple[str, ...],
    tz: Any,
    dfrom: date_cls,
    dto: date_cls,
) -> list[dict[str, Any]]:
    """Fetch and attribute worklogs for a single issue."""
    raw = await client._call(client._jira.issue_get_worklog, key)
    worklogs_raw: list[dict[str, Any]]
    if isinstance(raw, dict):
        worklogs_raw = raw.get("worklogs", [])
    elif isinstance(raw, list):
        worklogs_raw = raw
    else:
        worklogs_raw = []

    rows: list[dict[str, Any]] = []
    for wl in worklogs_raw:
        started = wl.get("started", "")
        if not started:
            continue
        wl_date = _parse_started(started).astimezone(tz).date()
        if wl_date < dfrom or wl_date > dto:
            continue
        attribution = _attribute_worklog(wl, asn, admins)
        if attribution is None:
            continue
        person, source = attribution
        rows.append(
            {
                "person": person,
                "date": wl_date.isoformat(),
                "key": key,
                "hours": wl.get("timeSpentSeconds", 0) / 3600.0,
                "source": source,
            }
        )
    return rows


async def get_worklogs_summary(
    client: AtlassianClient,
    date_from: str,
    date_to: str | None = None,
    people: list[str] | None = None,
    jql_scope: str | None = None,
    detail: Literal["total", "by_day", "by_ticket"] = "by_day",
) -> OperationResult:
    """Aggregate worklogs across a date range per attribution rules.

    date_from / date_to: ISO dates. Day boundaries evaluated in the connection's timezone.
    jql_scope: optional JQL narrowing the ticket set (default: 'project is not empty').
    people: optional filter on the *attributed* person display name.
    detail: 'total' | 'by_day' (default) | 'by_ticket'.

    Attribution rules (first match wins):
      1. logger_email == assignee_email -> assignee ('self')
      2. logger_email in worklog_admins  -> assignee ('proxy:<logger_name>')
      3. otherwise                       -> logger ('non-admin-other')
    """
    tz = ZoneInfo(client.connection.timezone)
    dfrom = date_cls.fromisoformat(date_from)
    dto = date_cls.fromisoformat(date_to) if date_to else dfrom
    admins = client.connection.worklog_admins

    scope = jql_scope or "project is not empty"
    jql = f"{scope} AND worklogDate >= '{dfrom.isoformat()}' AND worklogDate <= '{dto.isoformat()}'"

    t0 = time.monotonic()

    response = await client._call(
        client._jira.jql,
        jql,
        limit=500,
        start=0,
        fields=["summary", "assignee"],
    )
    candidate_issues = response.get("issues", []) if isinstance(response, dict) else []
    per_issue_assignee = {iss.get("key", ""): _extract_assignee(iss) for iss in candidate_issues}

    rows: list[dict[str, Any]] = []
    for key, asn in per_issue_assignee.items():
        rows.extend(await _fetch_issue_worklogs(client, key, asn, admins, tz, dfrom, dto))

    if people:
        rows = [r for r in rows if r["person"] in people]

    data = _aggregate_rows(rows, detail)
    elapsed = int((time.monotonic() - t0) * 1000)
    return OperationResult(
        name="get_worklogs_summary",
        data=data,
        count=len(data),
        truncated=False,
        time_ms=elapsed,
    )
