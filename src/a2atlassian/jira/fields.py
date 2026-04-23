"""Jira field operations — list fields and field options."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from a2atlassian.formatter import OperationResult

if TYPE_CHECKING:
    from a2atlassian.jira_client import JiraClient


def _extract_field(raw: dict[str, Any]) -> dict[str, Any]:
    """Extract key fields from a raw field definition."""
    schema = raw.get("schema") or {}
    # schema may be a string or a dict
    if isinstance(schema, str):
        schema_type = schema
    else:
        schema_type = schema.get("type", "")
    return {
        "id": raw.get("id", ""),
        "name": raw.get("name", ""),
        "custom": bool(raw.get("custom", False)),
        "schema_type": schema_type,
    }


def _extract_option(raw: dict[str, Any]) -> dict[str, Any]:
    """Extract key fields from a field option."""
    return {
        "id": str(raw.get("id", "")),
        "value": raw.get("value", ""),
    }


async def search_fields(client: JiraClient) -> OperationResult:
    """List all Jira fields (system and custom)."""
    t0 = time.monotonic()
    data = await client._call(client._jira.get_all_fields)
    elapsed = int((time.monotonic() - t0) * 1000)

    fields = data if isinstance(data, list) else []

    return OperationResult(
        name="search_fields",
        data=[_extract_field(f) for f in fields],
        count=len(fields),
        truncated=False,
        time_ms=elapsed,
    )


async def get_field_options(client: JiraClient, field_id: str) -> OperationResult:
    """Get options for a custom field."""
    t0 = time.monotonic()
    data = await client._call(client._jira.get_custom_field_option, field_id)
    elapsed = int((time.monotonic() - t0) * 1000)

    # Response may be a list of dicts, a dict with "values" key, or a single dict
    options: list[dict[str, Any]]
    if isinstance(data, list):
        options = data
    elif isinstance(data, dict):
        if "values" in data:
            options = data["values"] if isinstance(data["values"], list) else []
        else:
            # Single option dict
            options = [data]
    else:
        options = []

    return OperationResult(
        name="get_field_options",
        data=[_extract_option(o) for o in options],
        count=len(options),
        truncated=False,
        time_ms=elapsed,
    )
