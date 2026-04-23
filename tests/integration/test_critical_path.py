"""Live smoke tests for the critical Jira path."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from a2atlassian.formatter import OperationResult
    from a2atlassian.jira_client import JiraClient

from a2atlassian.jira.comments import add_comment, get_comments
from a2atlassian.jira.issues import get_issue, search
from a2atlassian.jira.transitions import get_transitions


@pytest.mark.integration
class TestCriticalPath:
    async def test_search_finds_issue(self, integration_client: JiraClient, test_issue: OperationResult):
        results = await search(integration_client, f"key = {test_issue.data['key']}")
        assert results.count == 1

    async def test_get_issue_returns_detail(self, integration_client: JiraClient, test_issue: OperationResult):
        issue = await get_issue(integration_client, test_issue.data["key"])
        assert issue.data["summary"].startswith("A2AT-")

    async def test_add_and_get_comment(self, integration_client: JiraClient, test_issue: OperationResult):
        comment = await add_comment(integration_client, test_issue.data["key"], "Integration test")
        assert comment.data["body"] == "Integration test"

        comments = await get_comments(integration_client, test_issue.data["key"])
        assert comments.count >= 1

    async def test_get_transitions(self, integration_client: JiraClient, test_issue: OperationResult):
        transitions = await get_transitions(integration_client, test_issue.data["key"])
        assert transitions.count > 0
