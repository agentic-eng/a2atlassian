"""Tests for Jira watcher operations."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from a2atlassian.client import AtlassianClient
from a2atlassian.connections import ConnectionInfo
from a2atlassian.formatter import OperationResult
from a2atlassian.jira.watchers import get_watchers, set_watchers


@pytest.fixture
def mock_client() -> AtlassianClient:
    conn = ConnectionInfo(
        connection="test",
        url="https://test.atlassian.net",
        email="t@t.com",
        token="tok",
        read_only=False,
    )
    client = AtlassianClient(conn)
    client._jira_instance = MagicMock()
    return client


class TestGetWatchers:
    async def test_returns_watchers_from_dict(self, mock_client: AtlassianClient) -> None:
        mock_client._jira_instance.issue_get_watchers.return_value = {
            "watchers": [
                {"accountId": "abc123", "displayName": "Alice"},
                {"accountId": "def456", "displayName": "Bob"},
            ]
        }
        result = await get_watchers(mock_client, "PROJ-1")
        assert isinstance(result, OperationResult)
        assert result.count == 2
        assert result.data[0]["account_id"] == "abc123"
        assert result.data[0]["display_name"] == "Alice"
        assert result.data[1]["account_id"] == "def456"

    async def test_returns_watchers_from_list(self, mock_client: AtlassianClient) -> None:
        mock_client._jira_instance.issue_get_watchers.return_value = [
            {"accountId": "abc123", "displayName": "Alice"},
        ]
        result = await get_watchers(mock_client, "PROJ-1")
        assert result.count == 1
        assert result.data[0]["display_name"] == "Alice"

    async def test_handles_int_account_id(self, mock_client: AtlassianClient) -> None:
        mock_client._jira_instance.issue_get_watchers.return_value = {"watchers": [{"accountId": 12345, "displayName": "Alice"}]}
        result = await get_watchers(mock_client, "PROJ-1")
        assert result.data[0]["account_id"] == "12345"

    async def test_empty_watchers(self, mock_client: AtlassianClient) -> None:
        mock_client._jira_instance.issue_get_watchers.return_value = {"watchers": []}
        result = await get_watchers(mock_client, "PROJ-1")
        assert result.count == 0
        assert result.data == []


class TestSetWatchers:
    async def test_adds_and_removes(self, mock_client: AtlassianClient) -> None:
        await set_watchers(mock_client, "PROJ-1", add=["a1", "a2"], remove=["r1"])
        calls = mock_client._jira_instance.mock_calls
        # Expect issue_add_watcher called for 'a1', 'a2'
        # Expect issue_delete_watcher called for 'r1'
        added = [c for c in calls if c[0] == "issue_add_watcher"]
        removed = [c for c in calls if c[0] == "issue_delete_watcher"]
        assert len(added) == 2
        assert len(removed) == 1

    async def test_empty_lists_no_calls(self, mock_client: AtlassianClient) -> None:
        await set_watchers(mock_client, "PROJ-1", add=[], remove=[])
        # No watcher-mutation calls made
        names = [c[0] for c in mock_client._jira_instance.mock_calls]
        assert "issue_add_watcher" not in names
        assert "issue_delete_watcher" not in names
