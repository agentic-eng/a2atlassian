"""Tests for metadata-only page-property writes."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from a2atlassian.confluence.pages import set_page_properties
from a2atlassian.confluence_client import ConfluenceClient
from a2atlassian.connections import ConnectionInfo


@pytest.fixture
def mock_client() -> ConfluenceClient:
    conn = ConnectionInfo(
        connection="t",
        url="https://t.atlassian.net",
        email="t@t.com",
        token="tok",
        read_only=True,
    )
    client = ConfluenceClient(conn)
    client._confluence_instance = MagicMock()
    return client


class TestSetPageProperties:
    async def test_cannot_touch_body(self, mock_client: ConfluenceClient) -> None:
        from atlassian.errors import ApiError

        mock_client._confluence_instance.get_page_by_id.return_value = {"id": "9"}
        mock_client._confluence_instance.get_page_property.side_effect = ApiError("nf")
        result = await set_page_properties(
            mock_client,
            "9",
            page_width="full-width",
            emoji="📄",
            labels=["x"],
        )
        # Neither create_page nor update_page can be called
        mock_client._confluence_instance.create_page.assert_not_called()
        mock_client._confluence_instance.update_page.assert_not_called()
        assert set(result.data["applied"]) == {"page_width", "emoji", "labels"}

    async def test_raises_on_missing_page(self, mock_client: ConfluenceClient) -> None:
        mock_client._confluence_instance.get_page_by_id.return_value = None
        with pytest.raises(ValueError, match="not found"):
            await set_page_properties(mock_client, "404", page_width="full-width")

    async def test_noop_still_verifies_page_exists(self, mock_client: ConfluenceClient) -> None:
        mock_client._confluence_instance.get_page_by_id.return_value = {"id": "9"}
        result = await set_page_properties(mock_client, "9")
        assert result.data["applied"] == []
        assert result.data["page_id"] == "9"
