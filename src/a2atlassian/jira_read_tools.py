"""Jira read-only tool registrations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from a2atlassian.formatter import format_result
from a2atlassian.jira.boards import get_board_issues, get_boards
from a2atlassian.jira.comments import get_comments
from a2atlassian.jira.fields import get_field_options, search_fields
from a2atlassian.jira.issues import get_issue, search
from a2atlassian.jira.links import get_link_types
from a2atlassian.jira.projects import get_project_components, get_project_versions, get_projects
from a2atlassian.jira.sprints import get_sprint_issues, get_sprints
from a2atlassian.jira.transitions import get_transitions
from a2atlassian.jira.users import get_user_profile
from a2atlassian.jira.watchers import get_watchers
from a2atlassian.jira.worklogs import get_worklogs

if TYPE_CHECKING:
    from collections.abc import Callable

    from mcp.server.fastmcp import FastMCP

    from a2atlassian.client import AtlassianClient
    from a2atlassian.errors import ErrorEnricher


def register_jira_read_tools(
    server: FastMCP,
    get_client: Callable[[str], AtlassianClient],
    enricher: ErrorEnricher,
) -> None:
    """Register all Jira read-only tools on the MCP server."""

    @server.tool()
    async def jira_get_issue(project: str, issue_key: str, format: str = "json") -> str:  # noqa: A002
        """Get a Jira issue by key. Returns full issue data including fields and status."""
        client = get_client(project)
        try:
            result = await get_issue(client, issue_key)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_search(project: str, jql: str, limit: int = 50, offset: int = 0, format: str = "toon") -> str:  # noqa: A002
        """Search Jira issues using JQL. Returns list of matching issues."""
        client = get_client(project)
        try:
            result = await search(client, jql, limit=limit, offset=offset)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_get_comments(project: str, issue_key: str, format: str = "toon") -> str:  # noqa: A002
        """Get all comments for a Jira issue."""
        client = get_client(project)
        try:
            result = await get_comments(client, issue_key)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_get_transitions(project: str, issue_key: str, format: str = "toon") -> str:  # noqa: A002
        """Get available transitions for a Jira issue."""
        client = get_client(project)
        try:
            result = await get_transitions(client, issue_key)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_get_projects(project: str, format: str = "toon") -> str:  # noqa: A002
        """List all Jira projects."""
        client = get_client(project)
        try:
            result = await get_projects(client)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_get_project_versions(project: str, project_key: str, format: str = "toon") -> str:  # noqa: A002
        """Get versions for a Jira project."""
        client = get_client(project)
        try:
            result = await get_project_versions(client, project_key)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_get_project_components(project: str, project_key: str, format: str = "toon") -> str:  # noqa: A002
        """Get components for a Jira project."""
        client = get_client(project)
        try:
            result = await get_project_components(client, project_key)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_search_fields(project: str, format: str = "toon") -> str:  # noqa: A002
        """Search all Jira fields. Returns field id, name, custom flag, and schema type."""
        client = get_client(project)
        try:
            result = await search_fields(client)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_get_field_options(project: str, field_id: str, format: str = "toon") -> str:  # noqa: A002
        """Get allowed values for a Jira field."""
        client = get_client(project)
        try:
            result = await get_field_options(client, field_id)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_get_user_profile(project: str, account_id: str, format: str = "json") -> str:  # noqa: A002
        """Get a Jira user profile by account ID."""
        client = get_client(project)
        try:
            result = await get_user_profile(client, account_id)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_get_boards(project: str, format: str = "toon") -> str:  # noqa: A002
        """List all Jira boards visible to the authenticated user."""
        client = get_client(project)
        try:
            result = await get_boards(client)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_get_board_issues(project: str, board_id: int, limit: int = 50, offset: int = 0, format: str = "toon") -> str:  # noqa: A002
        """Get issues for a specific Jira board."""
        client = get_client(project)
        try:
            result = await get_board_issues(client, board_id, limit=limit, offset=offset)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_get_sprints(project: str, board_id: int, format: str = "toon") -> str:  # noqa: A002
        """Get all sprints for a Jira board."""
        client = get_client(project)
        try:
            result = await get_sprints(client, board_id)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_get_sprint_issues(project: str, sprint_id: int, limit: int = 50, offset: int = 0, format: str = "toon") -> str:  # noqa: A002
        """Get issues in a specific sprint."""
        client = get_client(project)
        try:
            result = await get_sprint_issues(client, sprint_id, limit=limit, offset=offset)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_get_link_types(project: str, format: str = "toon") -> str:  # noqa: A002
        """Get all available issue link types (e.g. Blocks, Duplicate, Relates)."""
        client = get_client(project)
        try:
            result = await get_link_types(client)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_get_watchers(project: str, issue_key: str, format: str = "toon") -> str:  # noqa: A002
        """Get watchers for a Jira issue."""
        client = get_client(project)
        try:
            result = await get_watchers(client, issue_key)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_get_worklogs(project: str, issue_key: str, format: str = "toon") -> str:  # noqa: A002
        """Get worklogs for a Jira issue."""
        client = get_client(project)
        try:
            result = await get_worklogs(client, issue_key)
        except Exception as exc:  # noqa: BLE001
            return enricher.enrich(str(exc), {"project": project})
        return format_result(result, fmt=format)

    @server.tool()
    async def jira_get_issue_dev_info(project: str, issue_key: str) -> str:
        """Get development info (branches, commits, PRs) for a Jira issue.

        Note: Dev info requires the Jira Software dev-status API which is not yet
        supported by atlassian-python-api. This is a placeholder.
        """
        return (
            f"Dev info for {issue_key}: dev info requires Jira Software API — not yet supported. "
            "Use the Jira UI or the /rest/dev-status/latest/issue/detail REST endpoint directly."
        )
