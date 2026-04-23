"""Tests for Confluence CQL search."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from a2atlassian.confluence.search import search
from a2atlassian.confluence_client import ConfluenceClient
from a2atlassian.connections import ConnectionInfo
from a2atlassian.formatter import OperationResult

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def mock_client() -> ConfluenceClient:
    conn = ConnectionInfo(connection="t", url="https://t.atlassian.net", email="t@t.com", token="tok", read_only=True)
    client = ConfluenceClient(conn)
    client._confluence_instance = MagicMock()
    return client


class TestSearch:
    async def test_returns_operation_result(self, mock_client: ConfluenceClient) -> None:
        mock_client._confluence_instance.cql.return_value = json.loads((FIXTURES / "confluence_cql_search.json").read_text())
        result = await search(mock_client, "type = page AND space = TEAM", limit=25, offset=0)
        assert isinstance(result, OperationResult)
        assert result.count == 1
        row = result.data[0]
        assert row["id"] == "300"
        assert row["title"] == "Spec"
        assert row["excerpt"] == "First paragraph snippet"
        assert row["url"].endswith("/pages/300")

    async def test_passes_cql_and_pagination(self, mock_client: ConfluenceClient) -> None:
        mock_client._confluence_instance.cql.return_value = {"results": []}
        await search(mock_client, "text ~ foo", limit=10, offset=5)
        call = mock_client._confluence_instance.cql.call_args
        assert call.args[0] == "text ~ foo"
        assert call.kwargs.get("start") == 5
        assert call.kwargs.get("limit") == 10
