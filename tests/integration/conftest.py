"""Fixtures for integration tests that hit a real Jira instance."""

from __future__ import annotations

import contextlib
import os
import uuid

import pytest

from a2atlassian.client import AtlassianClient
from a2atlassian.connections import ConnectionInfo
from a2atlassian.jira.issues import create_issue, delete_issue


def _require_env(name: str) -> str:
    """Return env var value or skip the test if missing."""
    val = os.environ.get(name)
    if not val:
        pytest.skip(f"missing env var {name}")
    return val


@pytest.fixture
def test_prefix() -> str:
    return f"A2AT-{uuid.uuid4().hex[:6]}"


@pytest.fixture
async def integration_client() -> AtlassianClient:
    conn = ConnectionInfo(
        project="test",
        url=_require_env("A2ATLASSIAN_TEST_URL"),
        email=_require_env("A2ATLASSIAN_TEST_EMAIL"),
        token=_require_env("A2ATLASSIAN_TEST_TOKEN"),
        read_only=False,
    )
    return AtlassianClient(conn)


@pytest.fixture
def test_project_key() -> str:
    return _require_env("A2ATLASSIAN_TEST_PROJECT")


@pytest.fixture
async def test_issue(integration_client: AtlassianClient, test_prefix: str, test_project_key: str):
    result = await create_issue(
        integration_client,
        test_project_key,
        f"{test_prefix} integration test issue",
        "Task",
    )
    yield result
    with contextlib.suppress(Exception):
        await delete_issue(integration_client, result.data["key"])
