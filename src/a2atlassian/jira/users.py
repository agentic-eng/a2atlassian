"""Jira user operations — get user profile."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from a2atlassian.formatter import OperationResult

if TYPE_CHECKING:
    from a2atlassian.client import AtlassianClient


def _extract_user(raw: dict[str, Any]) -> dict[str, Any]:
    """Extract key fields from a raw user."""
    return {
        "account_id": raw.get("accountId", ""),
        "display_name": raw.get("displayName", ""),
        "email": raw.get("emailAddress", ""),
        "active": bool(raw.get("active", False)),
    }


async def get_user_profile(client: AtlassianClient, account_id: str) -> OperationResult:
    """Get a Jira user profile by account ID."""
    t0 = time.monotonic()
    data = await client._call(client._jira.user, account_id)
    elapsed = int((time.monotonic() - t0) * 1000)

    result_data: dict[str, Any]
    if isinstance(data, dict):
        result_data = _extract_user(data)
    else:
        result_data = {"account_id": account_id}

    return OperationResult(
        name="get_user_profile",
        data=result_data,
        count=1,
        truncated=False,
        time_ms=elapsed,
    )
