"""Jira write tool registrations — all tools that modify data."""

from __future__ import annotations

from typing import TYPE_CHECKING

from a2atlassian.client import AtlassianClient
from a2atlassian.formatter import format_result
from a2atlassian.jira.comments import add_comment, edit_comment
from a2atlassian.jira.issues import create_issue, delete_issue, update_issue
from a2atlassian.jira.links import create_issue_link, link_to_epic, remove_issue_link
from a2atlassian.jira.projects import create_version
from a2atlassian.jira.sprints import add_issues_to_sprint, create_sprint, update_sprint
from a2atlassian.jira.transitions import transition_issue
from a2atlassian.jira.watchers import add_watcher, remove_watcher
from a2atlassian.jira.worklogs import add_worklog

if TYPE_CHECKING:
    from collections.abc import Callable

    from mcp.server.fastmcp import FastMCP

    from a2atlassian.connections import ConnectionInfo
    from a2atlassian.errors import ErrorEnricher


def register_jira_write_tools(
    server: FastMCP,
    get_connection: Callable[[str], ConnectionInfo],
    enricher: ErrorEnricher,
) -> None:
    """Register all Jira write tools on the MCP server."""

    @server.tool()
    async def jira_add_comment(project: str, issue_key: str, body: str, format: str = "json") -> str:  # noqa: A002
        """Add a comment to a Jira issue. Uses wiki markup (API v2)."""
        conn = get_connection(project)
        if conn.read_only:
            return enricher.enrich(f"Connection '{project}' is read-only.", {"project": project})
        client = AtlassianClient(conn)
        try:
            result = await add_comment(client, issue_key, body)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_edit_comment(project: str, issue_key: str, comment_id: str, body: str, format: str = "json") -> str:  # noqa: A002
        """Edit an existing comment on a Jira issue. Uses wiki markup (API v2)."""
        conn = get_connection(project)
        if conn.read_only:
            return enricher.enrich(f"Connection '{project}' is read-only.", {"project": project})
        client = AtlassianClient(conn)
        try:
            result = await edit_comment(client, issue_key, comment_id, body)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_transition_issue(project: str, issue_key: str, transition_id: str, format: str = "json") -> str:  # noqa: A002
        """Transition a Jira issue to a new status. Use jira_get_transitions to discover available transitions."""
        conn = get_connection(project)
        if conn.read_only:
            return enricher.enrich(f"Connection '{project}' is read-only.", {"project": project})
        client = AtlassianClient(conn)
        try:
            result = await transition_issue(client, issue_key, transition_id)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_create_sprint(
        project: str,
        name: str,
        board_id: int,
        start_date: str | None = None,
        end_date: str | None = None,
        format: str = "json",  # noqa: A002
    ) -> str:
        """Create a new sprint on a Jira board."""
        conn = get_connection(project)
        if conn.read_only:
            return enricher.enrich(f"Connection '{project}' is read-only.", {"project": project})
        client = AtlassianClient(conn)
        try:
            result = await create_sprint(client, name, board_id, start_date=start_date, end_date=end_date)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_update_sprint(
        project: str,
        sprint_id: int,
        name: str | None = None,
        state: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        format: str = "json",  # noqa: A002
    ) -> str:
        """Update an existing sprint (name, state, dates)."""
        conn = get_connection(project)
        if conn.read_only:
            return enricher.enrich(f"Connection '{project}' is read-only.", {"project": project})
        client = AtlassianClient(conn)
        try:
            kwargs = {
                k: v for k, v in {"name": name, "state": state, "start_date": start_date, "end_date": end_date}.items() if v is not None
            }
            result = await update_sprint(client, sprint_id, **kwargs)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_add_issues_to_sprint(project: str, sprint_id: int, issue_keys: list[str], format: str = "json") -> str:  # noqa: A002
        """Move issues into a sprint."""
        conn = get_connection(project)
        if conn.read_only:
            return enricher.enrich(f"Connection '{project}' is read-only.", {"project": project})
        client = AtlassianClient(conn)
        try:
            result = await add_issues_to_sprint(client, sprint_id, issue_keys)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_create_issue(
        project: str,
        project_key: str,
        summary: str,
        issue_type: str,
        description: str | None = None,
        extra_fields: dict | None = None,
        format: str = "json",  # noqa: A002
    ) -> str:
        """Create a new Jira issue. Accepts project_key, summary, issue_type, optional description and extra_fields dict."""
        conn = get_connection(project)
        if conn.read_only:
            return enricher.enrich(f"Connection '{project}' is read-only.", {"project": project})
        client = AtlassianClient(conn)
        try:
            result = await create_issue(client, project_key, summary, issue_type, description=description, extra_fields=extra_fields)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_update_issue(project: str, issue_key: str, fields: dict, format: str = "json") -> str:  # noqa: A002
        """Update fields on an existing Jira issue. Pass a dict of field names to values."""
        conn = get_connection(project)
        if conn.read_only:
            return enricher.enrich(f"Connection '{project}' is read-only.", {"project": project})
        client = AtlassianClient(conn)
        try:
            result = await update_issue(client, issue_key, fields)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_delete_issue(project: str, issue_key: str, format: str = "json") -> str:  # noqa: A002
        """Delete a Jira issue by key."""
        conn = get_connection(project)
        if conn.read_only:
            return enricher.enrich(f"Connection '{project}' is read-only.", {"project": project})
        client = AtlassianClient(conn)
        try:
            result = await delete_issue(client, issue_key)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_create_version(project: str, project_key: str, name: str, format: str = "json") -> str:  # noqa: A002
        """Create a new version in a Jira project."""
        conn = get_connection(project)
        if conn.read_only:
            return enricher.enrich(f"Connection '{project}' is read-only.", {"project": project})
        client = AtlassianClient(conn)
        try:
            result = await create_version(client, project_key=project_key, name=name)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_create_issue_link(
        project: str,
        link_type: str,
        inward_key: str,
        outward_key: str,
        format: str = "json",  # noqa: A002
    ) -> str:
        """Create a link between two Jira issues. Use jira_get_link_types to discover available types."""
        conn = get_connection(project)
        if conn.read_only:
            return enricher.enrich(f"Connection '{project}' is read-only.", {"project": project})
        client = AtlassianClient(conn)
        try:
            result = await create_issue_link(client, link_type, inward_key, outward_key)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_remove_issue_link(project: str, link_id: str, format: str = "json") -> str:  # noqa: A002
        """Remove an issue link by its ID."""
        conn = get_connection(project)
        if conn.read_only:
            return enricher.enrich(f"Connection '{project}' is read-only.", {"project": project})
        client = AtlassianClient(conn)
        try:
            result = await remove_issue_link(client, link_id)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_link_to_epic(project: str, issue_key: str, epic_key: str, format: str = "json") -> str:  # noqa: A002
        """Set the parent (epic) of an issue. Uses the parent field."""
        conn = get_connection(project)
        if conn.read_only:
            return enricher.enrich(f"Connection '{project}' is read-only.", {"project": project})
        client = AtlassianClient(conn)
        try:
            result = await link_to_epic(client, issue_key, epic_key)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_add_watcher(project: str, issue_key: str, account_id: str, format: str = "json") -> str:  # noqa: A002
        """Add a watcher to a Jira issue."""
        conn = get_connection(project)
        if conn.read_only:
            return enricher.enrich(f"Connection '{project}' is read-only.", {"project": project})
        client = AtlassianClient(conn)
        try:
            result = await add_watcher(client, issue_key, account_id)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_remove_watcher(project: str, issue_key: str, account_id: str, format: str = "json") -> str:  # noqa: A002
        """Remove a watcher from a Jira issue."""
        conn = get_connection(project)
        if conn.read_only:
            return enricher.enrich(f"Connection '{project}' is read-only.", {"project": project})
        client = AtlassianClient(conn)
        try:
            result = await remove_watcher(client, issue_key, account_id)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_add_worklog(
        project: str,
        issue_key: str,
        time_spent: str,
        comment: str = "",
        format: str = "json",  # noqa: A002
    ) -> str:
        """Add a worklog entry to a Jira issue. time_spent is a string like '2h 30m'."""
        conn = get_connection(project)
        if conn.read_only:
            return enricher.enrich(f"Connection '{project}' is read-only.", {"project": project})
        client = AtlassianClient(conn)
        try:
            result = await add_worklog(client, issue_key, time_spent, comment=comment)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)
