"""Jira transition operations — get available transitions and transition issues."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from a2atlassian.formatter import OperationResult

if TYPE_CHECKING:
    from a2atlassian.jira_client import JiraClient


def _extract_transition(raw: dict[str, Any]) -> dict[str, Any]:
    """Extract key fields from a raw transition."""
    to = raw.get("to", "")
    # atlassian-python-api returns "to" as a string (status name),
    # but the raw REST API returns it as a dict with a "name" key.
    if isinstance(to, dict):
        to_status = to.get("name", "")
    else:
        to_status = str(to)
    return {
        "id": str(raw.get("id", "")),
        "name": raw.get("name", ""),
        "to_status": to_status,
    }


async def get_transitions(client: JiraClient, issue_key: str) -> OperationResult:
    """Get available transitions for a Jira issue."""
    t0 = time.monotonic()
    transitions = await client._call(client._jira.get_issue_transitions, issue_key)
    elapsed = int((time.monotonic() - t0) * 1000)

    return OperationResult(
        name="get_transitions",
        data=[_extract_transition(t) for t in transitions],
        count=len(transitions),
        truncated=False,
        time_ms=elapsed,
    )


async def transition_issue(
    client: JiraClient,
    issue_key: str,
    transition_id: str,
) -> OperationResult:
    """Transition a Jira issue to a new status."""
    t0 = time.monotonic()
    await client._call(client._jira.issue_transition, issue_key, transition_id)
    elapsed = int((time.monotonic() - t0) * 1000)

    return OperationResult(
        name="transition_issue",
        data={"issue_key": issue_key, "transition_id": transition_id, "status": "transitioned"},
        count=1,
        truncated=False,
        time_ms=elapsed,
    )
