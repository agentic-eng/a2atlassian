"""Assert the Confluence code path does not transitively import Jira modules."""

from __future__ import annotations

import subprocess
import sys

import pytest


def test_confluence_client_does_not_import_jira() -> None:
    code = (
        "import sys\n"
        "from a2atlassian.confluence_client import ConfluenceClient\n"
        "from a2atlassian.connections import ConnectionInfo\n"
        "c = ConfluenceClient(ConnectionInfo(connection='x', url='https://x', email='a@b', token='t', read_only=True))\n"
        "assert c is not None\n"
        "loaded_jira = [m for m in sys.modules if m.startswith('a2atlassian.jira') or m.startswith('a2atlassian.jira_client')]\n"
        "assert loaded_jira == [], f'unexpected jira imports: {loaded_jira}'\n"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)  # noqa: S603
    if result.returncode != 0:
        pytest.fail(f"stdout={result.stdout!r} stderr={result.stderr!r}")


def test_all_four_confluence_tools_registered() -> None:
    import contextlib

    import a2atlassian.mcp_server as ms

    # Register — idempotency varies; suppress if already registered in a previous test module.
    with contextlib.suppress(Exception):
        ms._register_confluence_tools(None)

    tool_names = {t.name for t in ms.server._tool_manager.list_tools()}
    assert "confluence_get_page" in tool_names
    assert "confluence_get_page_children" in tool_names
    assert "confluence_search" in tool_names
    assert "confluence_upsert_pages" in tool_names
