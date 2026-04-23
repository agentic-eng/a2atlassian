# a2atlassian v0.4.0 — Confluence Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended, with sonnet — NOT haiku) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship Confluence parity in the a2atlassian MCP server — four Confluence tools (`confluence_get_page`, `confluence_get_page_children`, `confluence_search`, `confluence_upsert_pages`) backed by a split client (`AtlassianClientBase` + `JiraClient` + `ConfluenceClient`) and a markdown→storage translator that recursively handles `<details>`.

**Architecture:** Refactor the single `AtlassianClient` into a base + per-service subclasses so Jira and Confluence live in separate modules and test boundaries. Add a `confluence/` operations package (pages, search, content format translator) and a `confluence_tools/` tool-registration package that mirrors the existing `jira_tools/` pattern. Wire the new domain into `mcp_server.py` through `_get_confluence_client` and extend `--enable` to recognize `confluence`. The upsert tool is batch-only, returns per-page `{succeeded, failed, summary}` rather than raising on partial failure, and uses a strictly-per-parent identity resolution to avoid cross-space false matches.

**Tech Stack:** Python 3.12, `atlassian-python-api>=4,<5` (the `Confluence` class), `mcp[cli]>=1.9`, pytest with `asyncio_mode=auto`, `ruff` + `agent-harness` as quality gate, `toon-format` for list output.

**Spec:** `docs/superpowers/specs/2026-04-23-a2atlassian-confluence-design.md`

**Repo path note:** The canonical working copy is `/Users/iorlas/Workspaces/a2atlassian`. Shell cwd resets to a stale `agentic-eng/a2atlassian` copy between tool calls — **always prefix Bash commands with `cd /Users/iorlas/Workspaces/a2atlassian`**, or use absolute paths in Read/Edit/Write.

**Branching:** Work happens on `feat/v0.4.0-confluence` off `main` (currently at tag `v0.3.1`, commit `25b4fa9`). No PR; merge fast-forward directly to main at the end.

**Quality gate:** After every task, run `cd /Users/iorlas/Workspaces/a2atlassian && make lint && make test`. Run `make check` before each commit at a task boundary. Intermediate commits are allowed to dip below the 95% coverage-diff threshold while boilerplate lands; the **final** `make check` at the end of the plan must pass clean.

---

## File Structure

**New files:**

```
src/a2atlassian/
  client.py                         # AtlassianClientBase (refactored)
  jira_client.py                    # JiraClient — lazy _jira
  confluence_client.py              # ConfluenceClient — lazy _confluence
  confluence/
    __init__.py
    pages.py                        # get_page, get_page_children, upsert_pages (batch)
    search.py                       # cql search
    content_format.py               # markdown_to_storage(), rule helpers
  confluence_tools/
    __init__.py                     # FEATURES mapping
    pages.py                        # register_read/register_write for page tools
    search.py                       # register_read for search tool

tests/
  confluence/
    __init__.py
    test_pages.py                   # get, children, upsert (identity + batch)
    test_search.py                  # CQL
    test_content_format.py          # translator round-trip rules
  confluence_tools/
    __init__.py
    test_registration.py            # module-boundary fixture + feature matrix
  fixtures/
    confluence_page.json
    confluence_page_children.json
    confluence_cql_search.json
    confluence_create_page_response.json
    confluence_update_page_response.json

docs/spikes/
  2026-04-23-confluence-api-surface.md  # dir(Confluence) output + method-name decisions
```

**Modified files:**

```
src/a2atlassian/
  mcp_server.py                     # _get_confluence_client, --enable confluence, instructions
  jira_tools/<all files>            # AtlassianClient → JiraClient import rename
scripts/
  record_fixtures.py                # extend with Confluence recordings
tests/
  conftest.py                       # add confluence fixture helpers (if needed)
  test_client.py                    # rename tests target AtlassianClientBase / JiraClient
  test_mcp_server.py                # new tests for confluence wiring
pyproject.toml                      # version 0.3.1 → 0.4.0
README.md                           # Confluence scope update, tool table entries
CHANGELOG.md                        # v0.4.0 entry (create if absent)
```

---

## Task Summary

| # | Task | Scope |
|---|---|---|
| 0 | Branch + empty-commit anchor | repo |
| 1 | Spike: record `dir(Confluence)` API surface | docs/spikes/ |
| 2 | Refactor — introduce `AtlassianClientBase`; retain backward-compat alias | client.py |
| 3 | Add `JiraClient` subclass; migrate `_jira` lazy property | jira_client.py |
| 4 | Migrate all Jira callers to `JiraClient` import | jira/, jira_tools/ |
| 5 | Add `ConfluenceClient` subclass with lazy `_confluence` | confluence_client.py |
| 6 | Confluence ops — `get_page` | confluence/pages.py |
| 7 | Confluence ops — `get_page_children` | confluence/pages.py |
| 8 | Confluence ops — `search` (CQL) | confluence/search.py |
| 9 | Translator rules — headings, HTML passthrough, code fences, mentions | confluence/content_format.py |
| 10 | Translator rules — pipe tables | confluence/content_format.py |
| 11 | Translator rules — recursive `<details>` → expand macro | confluence/content_format.py |
| 12 | Upsert — identity resolution (3-path) helper | confluence/pages.py |
| 13 | Upsert — single-page create/update | confluence/pages.py |
| 14 | Upsert — batch with structured succeeded/failed/summary | confluence/pages.py |
| 15 | Upsert — labels, emoji, page_width knobs | confluence/pages.py |
| 16 | MCP tools — register `confluence_get_page`, `confluence_get_page_children` | confluence_tools/pages.py |
| 17 | MCP tools — register `confluence_search` | confluence_tools/search.py |
| 18 | MCP tools — register `confluence_upsert_pages` | confluence_tools/pages.py |
| 19 | MCP server wiring — `_get_confluence_client`, `--enable confluence`, instructions | mcp_server.py |
| 20 | Client module-boundary test | tests/confluence_tools/test_registration.py |
| 21 | Fixture recording — extend `scripts/record_fixtures.py` | scripts/ |
| 22 | README + CHANGELOG + version bump | root |
| 23 | Final `make check` + merge to main + tag v0.4.0 | repo |

---

## Task 0 — Branch anchor

**Files:** *(no file edits)*

- [ ] **Step 1: Verify you're on the correct repo and clean tree**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
git status
git rev-parse HEAD
git tag --points-at HEAD
```

Expected: `nothing to commit, working tree clean`; HEAD `25b4fa9` tagged `v0.3.1`.

- [ ] **Step 2: Create and switch to the feature branch**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
git switch -c feat/v0.4.0-confluence
```

Expected: `Switched to a new branch 'feat/v0.4.0-confluence'`.

---

## Task 1 — Spike: record `dir(Confluence)` API surface

**Why:** `atlassian-python-api` method names diverge from older code assumptions. Record the real surface before writing client or ops code so later tasks reference real symbols.

**Files:**
- Create: `docs/spikes/2026-04-23-confluence-api-surface.md`

- [ ] **Step 1: Run the spike script**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run python -c "
from atlassian import Confluence
methods = [m for m in dir(Confluence) if not m.startswith('_')]
for m in methods:
    print(m)
"
```

Expected: a printed list of public methods. **Do not proceed** until the output is captured.

- [ ] **Step 2: Record results and lock method names**

Create `docs/spikes/2026-04-23-confluence-api-surface.md` with:

```markdown
# Confluence API surface spike — 2026-04-23

Ran against `atlassian-python-api` (version from `uv pip show atlassian-python-api`).

## Full `dir(Confluence)` output
<paste the full list here>

## Method names we will use in v0.4.0

| Purpose                 | atlassian-python-api method (verified)            |
|-------------------------|---------------------------------------------------|
| get page by id          | `get_page_by_id(page_id, expand=...)`             |
| list children of page   | `get_page_child_by_type(page_id, type='page', start, limit)` |
| CQL search              | `cql(cql, expand=None, start, limit)`             |
| create page             | `create_page(space, title, body, parent_id=..., type='page', representation='storage')` |
| update page             | `update_page(page_id, title, body, parent_id=..., representation='storage')` |
| find page by title      | `get_page_by_title(space, title, expand=None)`    |
| add labels to page      | `set_page_label(page_id, label)`                  |
| set page properties     | (use `set_page_property` or fall back to REST raw for emoji/page_width) |

Notes:
- If any of the above method names differ in the installed version, update this table and every downstream reference.
- Emoji / page_width may require raw REST calls via `self._confluence.put('rest/api/content/{id}/property/...')`. Confirm during Task 15.
```

- [ ] **Step 3: Commit the spike doc**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
git add docs/spikes/2026-04-23-confluence-api-surface.md
git commit -m "docs(spike): Confluence API surface for v0.4.0"
```

---

## Task 2 — Refactor `AtlassianClient` into `AtlassianClientBase`

**Files:**
- Modify: `src/a2atlassian/client.py`
- Modify: `tests/test_client.py`

- [ ] **Step 1: Write the failing tests**

Overwrite or extend `tests/test_client.py` so it imports `AtlassianClientBase` from `a2atlassian.client` and exercises `_call` retry behavior using a fake `fn` — not the Jira client. Example additions (append to the file, do not replace existing tests yet; existing tests still pass because Step 2 keeps a back-compat alias):

```python
"""Tests for AtlassianClientBase retry/auth behavior."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock
from requests.exceptions import HTTPError
from requests.models import Response

from a2atlassian.client import AtlassianClientBase
from a2atlassian.connections import ConnectionInfo
from a2atlassian.errors import AuthenticationError, RateLimitError, ServerError


def _make_http_error(status: int) -> HTTPError:
    resp = Response()
    resp.status_code = status
    return HTTPError(response=resp)


@pytest.fixture
def base_client() -> AtlassianClientBase:
    conn = ConnectionInfo(
        connection="t",
        url="https://t.atlassian.net",
        email="t@t.com",
        token="tok",
        read_only=True,
    )
    return AtlassianClientBase(conn)


class TestBaseRetry:
    async def test_401_raises_authentication_error(self, base_client: AtlassianClientBase) -> None:
        def boom() -> None:
            raise _make_http_error(401)

        with pytest.raises(AuthenticationError):
            await base_client._call(boom)

    async def test_429_retries_then_raises_rate_limit(self, base_client: AtlassianClientBase) -> None:
        calls = 0

        def boom() -> None:
            nonlocal calls
            calls += 1
            raise _make_http_error(429)

        base_client.RETRY_BACKOFF = [0.0, 0.0]
        with pytest.raises(RateLimitError):
            await base_client._call(boom)
        assert calls == base_client.MAX_RETRIES + 1

    async def test_500_retries_then_raises_server_error(self, base_client: AtlassianClientBase) -> None:
        def boom() -> None:
            raise _make_http_error(503)

        base_client.RETRY_BACKOFF = [0.0, 0.0]
        with pytest.raises(ServerError):
            await base_client._call(boom)

    async def test_success_returns_value(self, base_client: AtlassianClientBase) -> None:
        def ok() -> str:
            return "hello"

        result = await base_client._call(ok)
        assert result == "hello"
```

- [ ] **Step 2: Refactor `client.py`**

Replace `src/a2atlassian/client.py` with:

```python
"""Shared Atlassian client base — retry, auth, rate limiting.

Service-specific subclasses (JiraClient, ConfluenceClient) own the lazy
`atlassian-python-api` instance. Keep this file free of service imports.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from requests.exceptions import HTTPError

from a2atlassian.errors import A2AtlassianError, AuthenticationError, RateLimitError, ServerError

if TYPE_CHECKING:
    from collections.abc import Callable

    from a2atlassian.connections import ConnectionInfo


class AtlassianClientBase:
    """Shared retry/auth wrapper. Subclasses provide a service instance."""

    MAX_RETRIES = 2
    RETRY_BACKOFF: list[float] = [1.0, 3.0]  # noqa: RUF012
    REQUEST_TIMEOUT = 30

    def __init__(self, connection: ConnectionInfo) -> None:
        self.connection = connection

    async def _call(self, fn: Callable, *args: Any, **kwargs: Any) -> Any:
        """Call a sync atlassian-python-api method with retry logic."""
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                return await asyncio.to_thread(fn, *args, **kwargs)
            except HTTPError as exc:
                status = getattr(exc.response, "status_code", None)

                if status in (401, 403):
                    msg = f"Authentication failed ({status}): {exc}"
                    raise AuthenticationError(msg) from exc

                if status == 429:
                    if attempt < self.MAX_RETRIES:
                        await asyncio.sleep(self.RETRY_BACKOFF[attempt])
                        continue
                    msg = f"Rate limited after {self.MAX_RETRIES + 1} attempts: {exc}"
                    raise RateLimitError(msg) from exc

                if status is not None and status >= 500:
                    if attempt < self.MAX_RETRIES:
                        await asyncio.sleep(self.RETRY_BACKOFF[attempt])
                        continue
                    msg = f"Server error after {self.MAX_RETRIES + 1} attempts: {exc}"
                    raise ServerError(msg) from exc

                raise

        msg = "Unexpected: retry loop exited without returning or raising"
        raise A2AtlassianError(msg)
```

**Do NOT yet delete** `AtlassianClient`, `_lazy_jira`, or the `_jira` property — those move to `jira_client.py` in Task 3. Until then, keep a temporary re-export stub at the end of `client.py` so existing Jira code still imports cleanly:

```python
# Temporary shim — removed in Task 4 once every caller imports from jira_client.
from a2atlassian.jira_client import JiraClient as AtlassianClient  # noqa: E402, F401
```

This line will fail to import until Task 3 creates `jira_client.py`. **Do not run tests yet.** Continue to Task 3 without committing; the shim keeps the import graph valid once Task 3 lands.

- [ ] **Step 3: (no run, no commit — Task 3 completes this pair)**

---

## Task 3 — Add `JiraClient` subclass

**Files:**
- Create: `src/a2atlassian/jira_client.py`

- [ ] **Step 1: Write the file**

Create `src/a2atlassian/jira_client.py`:

```python
"""Jira-specific Atlassian client — lazy atlassian.Jira wrapper."""

from __future__ import annotations

from typing import Any

from a2atlassian.client import AtlassianClientBase


def _lazy_jira() -> Any:
    """Lazy import to avoid loading atlassian module at import time."""
    from atlassian import Jira  # noqa: PLC0415

    return Jira


class JiraClient(AtlassianClientBase):
    """Async wrapper around atlassian-python-api Jira client."""

    def __init__(self, connection: Any) -> None:
        super().__init__(connection)
        self._jira_instance: Any | None = None

    @property
    def _jira(self) -> Any:
        """Lazily create the Jira client."""
        if self._jira_instance is None:
            jira_cls = _lazy_jira()
            self._jira_instance = jira_cls(
                url=self.connection.url,
                username=self.connection.email,
                password=self.connection.resolved_token,
                cloud=True,
            )
        return self._jira_instance

    async def validate(self) -> dict:
        """Validate the connection by calling /myself. Returns Jira user info."""
        return await self._call(self._jira.myself)
```

- [ ] **Step 2: Run tests**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run pytest tests/test_client.py tests/jira/ -x -q
```

Expected: PASS (the shim in `client.py` re-exports `JiraClient` as `AtlassianClient`, so every existing `from a2atlassian.client import AtlassianClient` still resolves).

- [ ] **Step 3: Commit Tasks 2+3 together**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
git add src/a2atlassian/client.py src/a2atlassian/jira_client.py tests/test_client.py
git commit -m "refactor(client): split AtlassianClient into Base + JiraClient"
```

---

## Task 4 — Migrate all Jira callers to `JiraClient` import

**Files:**
- Modify: `src/a2atlassian/jira_tools/*.py` (all 11 modules)
- Modify: `src/a2atlassian/jira/*.py` (TYPE_CHECKING blocks only)
- Modify: `src/a2atlassian/mcp_server.py`
- Modify: `scripts/record_fixtures.py`
- Modify: `tests/jira/test_*.py` (all 11 test modules)
- Modify: `tests/test_client.py`
- Modify: `src/a2atlassian/client.py` (remove shim)

- [ ] **Step 1: Find every usage**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && grep -rn "AtlassianClient" src/ tests/ scripts/
```

Expected: a list covering the files above. Use the output as your migration checklist.

- [ ] **Step 2: Rewrite each import**

In every hit, replace:

```python
from a2atlassian.client import AtlassianClient
```

with:

```python
from a2atlassian.jira_client import JiraClient
```

…and every reference to the name `AtlassianClient` with `JiraClient`. This includes:

- type annotations (`AtlassianClient` → `JiraClient`)
- `Callable[[str], AtlassianClient]` → `Callable[[str], JiraClient]`
- `isinstance(..., AtlassianClient)` if any
- mock fixtures (`client = AtlassianClient(conn)` → `client = JiraClient(conn)`)
- `client._jira_instance = MagicMock()` — unchanged, lives on `JiraClient` now

In `src/a2atlassian/mcp_server.py`:

```python
# old
from a2atlassian.client import AtlassianClient
...
def _get_client(connection: str) -> AtlassianClient:
    return AtlassianClient(_get_connection(connection))
```

becomes:

```python
from a2atlassian.jira_client import JiraClient
...
def _get_jira_client(connection: str) -> JiraClient:
    return JiraClient(_get_connection(connection))
```

and the call site `_get_client` → `_get_jira_client`. (Confluence gets its own accessor in Task 19.) Also update the `client = AtlassianClient(info)` line inside `login()` to `JiraClient(info)` — the `validate()` still exists on `JiraClient`.

- [ ] **Step 3: Remove the shim**

Edit `src/a2atlassian/client.py` and delete the three-line `# Temporary shim` block at the bottom (along with the preceding blank line and the `# noqa: E402, F401` import). `client.py` should now end at `raise A2AtlassianError(msg)`.

- [ ] **Step 4: Run the full test suite**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && make test
```

Expected: all existing tests pass. If any fail because a `AtlassianClient` reference was missed, grep again and fix.

- [ ] **Step 5: Commit**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
git add -A
git commit -m "refactor(client): migrate Jira callers to JiraClient"
```

---

## Task 5 — Add `ConfluenceClient`

**Files:**
- Create: `src/a2atlassian/confluence_client.py`
- Create: `tests/confluence/__init__.py` (empty)
- Create: `tests/confluence/test_client.py`

- [ ] **Step 1: Write the failing test**

`tests/confluence/test_client.py`:

```python
"""Tests for ConfluenceClient lazy construction."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from a2atlassian.confluence_client import ConfluenceClient
from a2atlassian.connections import ConnectionInfo


@pytest.fixture
def conn() -> ConnectionInfo:
    return ConnectionInfo(
        connection="t",
        url="https://t.atlassian.net",
        email="t@t.com",
        token="tok",
        read_only=True,
    )


class TestConfluenceClient:
    def test_does_not_import_atlassian_at_construction(self, conn: ConnectionInfo) -> None:
        # Constructing the client must not access the _confluence property.
        client = ConfluenceClient(conn)
        assert client._confluence_instance is None

    def test_lazy_confluence_instantiation(self, conn: ConnectionInfo) -> None:
        with patch("a2atlassian.confluence_client._lazy_confluence") as loader:
            loader.return_value = MagicMock(return_value="CONFLUENCE_OBJ")
            client = ConfluenceClient(conn)
            first = client._confluence
            second = client._confluence
        assert first == "CONFLUENCE_OBJ"
        assert first is second  # cached after first access
        loader.assert_called_once()

    async def test_validate_calls_myself(self, conn: ConnectionInfo) -> None:
        client = ConfluenceClient(conn)
        client._confluence_instance = MagicMock()
        client._confluence_instance.get_user_details_by_username.return_value = {"displayName": "X"}
        # validate() delegates to /myself or equivalent — see implementation for actual call.
        result = await client.validate()
        assert "displayName" in result or "accountId" in result or "email" in result
```

Note: the third test is loose on purpose — the exact `/myself` method name depends on the spike results from Task 1. Adjust both test and implementation together.

- [ ] **Step 2: Run — expect failure**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run pytest tests/confluence/test_client.py -x -q
```

Expected: `ModuleNotFoundError: No module named 'a2atlassian.confluence_client'`.

- [ ] **Step 3: Write implementation**

`src/a2atlassian/confluence_client.py`:

```python
"""Confluence-specific Atlassian client — lazy atlassian.Confluence wrapper."""

from __future__ import annotations

from typing import Any

from a2atlassian.client import AtlassianClientBase


def _lazy_confluence() -> Any:
    """Lazy import to avoid loading atlassian module at import time."""
    from atlassian import Confluence  # noqa: PLC0415

    return Confluence


class ConfluenceClient(AtlassianClientBase):
    """Async wrapper around atlassian-python-api Confluence client."""

    def __init__(self, connection: Any) -> None:
        super().__init__(connection)
        self._confluence_instance: Any | None = None

    @property
    def _confluence(self) -> Any:
        """Lazily create the Confluence client."""
        if self._confluence_instance is None:
            confluence_cls = _lazy_confluence()
            self._confluence_instance = confluence_cls(
                url=self.connection.url,
                username=self.connection.email,
                password=self.connection.resolved_token,
                cloud=True,
            )
        return self._confluence_instance

    async def validate(self) -> dict:
        """Validate the connection by calling the Confluence current-user endpoint.

        Uses the raw REST path because atlassian-python-api's Confluence class
        does not always expose a `myself` helper. The endpoint returns
        {accountId, displayName, ...}.
        """
        return await self._call(self._confluence.get, "rest/api/user/current")
```

If the spike showed a first-class method (e.g., `get_current_user()`), prefer it — update this method to call `self._confluence.get_current_user()` instead. Adjust the test accordingly.

- [ ] **Step 4: Run tests — expect pass**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run pytest tests/confluence/test_client.py -x -q
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
git add src/a2atlassian/confluence_client.py tests/confluence/__init__.py tests/confluence/test_client.py
git commit -m "feat(confluence): add ConfluenceClient with lazy wrapper"
```

---

## Task 6 — `confluence.pages.get_page`

**Files:**
- Create: `src/a2atlassian/confluence/__init__.py` (empty)
- Create: `src/a2atlassian/confluence/pages.py`
- Create: `tests/confluence/test_pages.py`
- Create: `tests/fixtures/confluence_page.json`

- [ ] **Step 1: Write a minimal recorded fixture**

Create `tests/fixtures/confluence_page.json` with a shape matching a real `get_page_by_id` response (an anonymized representative example):

```json
{
  "id": "123456789",
  "type": "page",
  "status": "current",
  "title": "Example page",
  "space": {"key": "TEAM", "name": "Team space"},
  "version": {"number": 3, "when": "2026-04-23T10:00:00.000Z"},
  "body": {"storage": {"value": "<p>Hello</p>", "representation": "storage"}},
  "_links": {"webui": "/spaces/TEAM/pages/123456789/Example+page"}
}
```

- [ ] **Step 2: Write the failing test**

`tests/confluence/test_pages.py`:

```python
"""Tests for Confluence page operations."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from a2atlassian.confluence.pages import get_page
from a2atlassian.confluence_client import ConfluenceClient
from a2atlassian.connections import ConnectionInfo
from a2atlassian.formatter import OperationResult


FIXTURES = Path(__file__).parent.parent / "fixtures"


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


class TestGetPage:
    async def test_returns_operation_result(self, mock_client: ConfluenceClient) -> None:
        mock_client._confluence_instance.get_page_by_id.return_value = json.loads(
            (FIXTURES / "confluence_page.json").read_text()
        )
        result = await get_page(mock_client, "123456789")
        assert isinstance(result, OperationResult)
        assert result.data["id"] == "123456789"
        assert result.data["title"] == "Example page"
        assert result.data["space_key"] == "TEAM"
        assert result.data["version"] == 3
        assert "body" in result.data
        assert result.count == 1
        assert result.truncated is False

    async def test_passes_expand_default(self, mock_client: ConfluenceClient) -> None:
        mock_client._confluence_instance.get_page_by_id.return_value = {
            "id": "1", "title": "", "space": {}, "version": {}, "body": {"storage": {"value": ""}}
        }
        await get_page(mock_client, "1")
        call = mock_client._confluence_instance.get_page_by_id.call_args
        assert call.kwargs.get("expand") == "body.storage,version,space"
```

- [ ] **Step 3: Run — expect failure**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run pytest tests/confluence/test_pages.py -x -q
```

Expected: `ModuleNotFoundError: No module named 'a2atlassian.confluence'`.

- [ ] **Step 4: Write the implementation**

`src/a2atlassian/confluence/__init__.py` — empty file.

`src/a2atlassian/confluence/pages.py`:

```python
"""Confluence page operations — read, search, and batch upsert."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from a2atlassian.formatter import OperationResult

if TYPE_CHECKING:
    from a2atlassian.confluence_client import ConfluenceClient


DEFAULT_PAGE_EXPAND = "body.storage,version,space"


def _extract_page_detail(raw: dict[str, Any]) -> dict[str, Any]:
    """Flatten a Confluence page response into a single-entity shape."""
    space = raw.get("space") or {}
    version = raw.get("version") or {}
    body = (raw.get("body") or {}).get("storage") or {}
    links = raw.get("_links") or {}
    return {
        "id": raw.get("id", ""),
        "title": raw.get("title", ""),
        "space_key": space.get("key", ""),
        "space_name": space.get("name", ""),
        "version": version.get("number", 0),
        "updated": version.get("when", ""),
        "url": links.get("webui", ""),
        "body": body.get("value", ""),
    }


async def get_page(
    client: ConfluenceClient,
    page_id: str,
    expand: str | None = None,
) -> OperationResult:
    """Fetch a single Confluence page by id."""
    t0 = time.monotonic()
    raw = await client._call(
        client._confluence.get_page_by_id,
        page_id,
        expand=expand or DEFAULT_PAGE_EXPAND,
    )
    elapsed = int((time.monotonic() - t0) * 1000)

    return OperationResult(
        name="get_page",
        data=_extract_page_detail(raw),
        count=1,
        truncated=False,
        time_ms=elapsed,
    )
```

- [ ] **Step 5: Run tests — expect pass**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run pytest tests/confluence/test_pages.py -x -q
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
git add src/a2atlassian/confluence/ tests/confluence/test_pages.py tests/fixtures/confluence_page.json
git commit -m "feat(confluence): get_page operation"
```

---

## Task 7 — `confluence.pages.get_page_children`

**Files:**
- Modify: `src/a2atlassian/confluence/pages.py`
- Modify: `tests/confluence/test_pages.py`
- Create: `tests/fixtures/confluence_page_children.json`

- [ ] **Step 1: Fixture**

`tests/fixtures/confluence_page_children.json`:

```json
{
  "results": [
    {"id": "200", "type": "page", "title": "Child A", "version": {"number": 1}, "_links": {"webui": "/pages/200"}},
    {"id": "201", "type": "page", "title": "Child B", "version": {"number": 4}, "_links": {"webui": "/pages/201"}}
  ],
  "start": 0, "limit": 50, "size": 2
}
```

- [ ] **Step 2: Append test class**

Append to `tests/confluence/test_pages.py`:

```python
from a2atlassian.confluence.pages import get_page_children


class TestGetPageChildren:
    async def test_returns_list_result(self, mock_client: ConfluenceClient) -> None:
        import json as _json
        mock_client._confluence_instance.get_page_child_by_type.return_value = _json.loads(
            (FIXTURES / "confluence_page_children.json").read_text()
        )["results"]
        result = await get_page_children(mock_client, "100", limit=50, offset=0)
        assert isinstance(result, OperationResult)
        assert result.count == 2
        assert result.data[0]["id"] == "200"
        assert result.data[0]["title"] == "Child A"
        assert result.data[0]["version"] == 1
        assert result.data[0]["url"].endswith("/pages/200")

    async def test_passes_pagination_params(self, mock_client: ConfluenceClient) -> None:
        mock_client._confluence_instance.get_page_child_by_type.return_value = []
        await get_page_children(mock_client, "100", limit=10, offset=20)
        call = mock_client._confluence_instance.get_page_child_by_type.call_args
        assert call.kwargs.get("start") == 20
        assert call.kwargs.get("limit") == 10
        assert call.kwargs.get("type") == "page"
```

- [ ] **Step 3: Run — expect failure**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run pytest tests/confluence/test_pages.py -x -q
```

Expected: `ImportError: cannot import name 'get_page_children'`.

- [ ] **Step 4: Append implementation**

Append to `src/a2atlassian/confluence/pages.py`:

```python
def _extract_child_summary(raw: dict[str, Any]) -> dict[str, Any]:
    version = raw.get("version") or {}
    links = raw.get("_links") or {}
    return {
        "id": raw.get("id", ""),
        "title": raw.get("title", ""),
        "version": version.get("number", 0),
        "url": links.get("webui", ""),
    }


async def get_page_children(
    client: ConfluenceClient,
    page_id: str,
    limit: int = 50,
    offset: int = 0,
) -> OperationResult:
    """List direct children of a Confluence page."""
    t0 = time.monotonic()
    raw = await client._call(
        client._confluence.get_page_child_by_type,
        page_id,
        type="page",
        start=offset,
        limit=limit,
    )
    elapsed = int((time.monotonic() - t0) * 1000)

    items = raw if isinstance(raw, list) else (raw or {}).get("results", [])
    return OperationResult(
        name="get_page_children",
        data=[_extract_child_summary(item) for item in items],
        count=len(items),
        truncated=len(items) >= limit,
        time_ms=elapsed,
    )
```

- [ ] **Step 5: Run tests — expect pass**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run pytest tests/confluence/test_pages.py -x -q
```

Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
git add src/a2atlassian/confluence/pages.py tests/confluence/test_pages.py tests/fixtures/confluence_page_children.json
git commit -m "feat(confluence): get_page_children operation"
```

---

## Task 8 — `confluence.search.search` (CQL)

**Files:**
- Create: `src/a2atlassian/confluence/search.py`
- Create: `tests/confluence/test_search.py`
- Create: `tests/fixtures/confluence_cql_search.json`

- [ ] **Step 1: Fixture**

`tests/fixtures/confluence_cql_search.json`:

```json
{
  "results": [
    {
      "content": {"id": "300", "type": "page", "title": "Spec", "_links": {"webui": "/pages/300"}},
      "title": "Spec",
      "excerpt": "First paragraph snippet",
      "lastModified": "2026-04-20T12:00:00.000Z",
      "friendlyLastModified": "3 days ago"
    }
  ],
  "start": 0, "limit": 25, "size": 1, "totalSize": 1
}
```

- [ ] **Step 2: Write the failing test**

`tests/confluence/test_search.py`:

```python
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
        mock_client._confluence_instance.cql.return_value = json.loads(
            (FIXTURES / "confluence_cql_search.json").read_text()
        )
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
```

- [ ] **Step 3: Run — expect failure**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run pytest tests/confluence/test_search.py -x -q
```

- [ ] **Step 4: Write implementation**

`src/a2atlassian/confluence/search.py`:

```python
"""Confluence CQL search."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from a2atlassian.formatter import OperationResult

if TYPE_CHECKING:
    from a2atlassian.confluence_client import ConfluenceClient


def _extract_search_row(raw: dict[str, Any]) -> dict[str, Any]:
    """Unified minimal row that works across pages / blogposts / comments / attachments."""
    content = raw.get("content") or {}
    links = content.get("_links") or {}
    return {
        "id": content.get("id", ""),
        "type": content.get("type", ""),
        "title": raw.get("title") or content.get("title", ""),
        "excerpt": raw.get("excerpt", ""),
        "url": links.get("webui", ""),
        "last_modified": raw.get("lastModified", ""),
    }


async def search(
    client: ConfluenceClient,
    cql: str,
    limit: int = 25,
    offset: int = 0,
) -> OperationResult:
    """Run a CQL query against Confluence. Returns a minimal row per match."""
    t0 = time.monotonic()
    raw = await client._call(client._confluence.cql, cql, start=offset, limit=limit)
    elapsed = int((time.monotonic() - t0) * 1000)

    results = (raw or {}).get("results", []) if isinstance(raw, dict) else (raw or [])
    rows = [_extract_search_row(r) for r in results]
    return OperationResult(
        name="search",
        data=rows,
        count=len(rows),
        truncated=len(rows) >= limit,
        time_ms=elapsed,
    )
```

- [ ] **Step 5: Run — expect pass**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run pytest tests/confluence/test_search.py -x -q
```

- [ ] **Step 6: Commit**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
git add src/a2atlassian/confluence/search.py tests/confluence/test_search.py tests/fixtures/confluence_cql_search.json
git commit -m "feat(confluence): CQL search operation"
```

---

## Task 9 — Translator: headings, HTML passthrough, code fences, mentions

**Files:**
- Create: `src/a2atlassian/confluence/content_format.py`
- Create: `tests/confluence/test_content_format.py`

- [ ] **Step 1: Write the failing tests**

`tests/confluence/test_content_format.py`:

```python
"""Tests for markdown → Confluence storage translator."""

from __future__ import annotations

import pytest

from a2atlassian.confluence.content_format import markdown_to_storage


class TestHeadings:
    def test_h1(self) -> None:
        assert markdown_to_storage("# Title") == "<h1>Title</h1>"

    def test_h2(self) -> None:
        assert markdown_to_storage("## Section") == "<h2>Section</h2>"

    def test_h3(self) -> None:
        assert markdown_to_storage("### Subsection") == "<h3>Subsection</h3>"

    def test_mixed_with_paragraphs(self) -> None:
        out = markdown_to_storage("# A\n\nbody text\n\n## B")
        assert out == "<h1>A</h1><p>body text</p><h2>B</h2>"


class TestHtmlPassthrough:
    def test_raw_html_preserved(self) -> None:
        html = '<ac:structured-macro ac:name="info"><ac:rich-text-body><p>x</p></ac:rich-text-body></ac:structured-macro>'
        assert markdown_to_storage(html) == html


class TestCodeFences:
    def test_fenced_with_language(self) -> None:
        src = "```python\nprint(1)\n```"
        out = markdown_to_storage(src)
        assert '<ac:structured-macro ac:name="code">' in out
        assert '<ac:parameter ac:name="language">python</ac:parameter>' in out
        assert "<ac:plain-text-body><![CDATA[print(1)]]></ac:plain-text-body>" in out

    def test_fenced_without_language(self) -> None:
        src = "```\nhello\n```"
        out = markdown_to_storage(src)
        assert '<ac:structured-macro ac:name="code">' in out
        assert "<ac:plain-text-body><![CDATA[hello]]></ac:plain-text-body>" in out


class TestMentions:
    def test_user_mention(self) -> None:
        out = markdown_to_storage("hi @user:712020:abc123")
        assert '<ac:link><ri:user ri:account-id="712020:abc123"/></ac:link>' in out


class TestParagraphs:
    def test_plain_paragraph(self) -> None:
        assert markdown_to_storage("hello world") == "<p>hello world</p>"
```

- [ ] **Step 2: Run — expect failure**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run pytest tests/confluence/test_content_format.py -x -q
```

- [ ] **Step 3: Write implementation (block-by-block, regex-free)**

`src/a2atlassian/confluence/content_format.py`:

```python
"""Markdown → Confluence storage-format translator.

Block-oriented translator. Splits input on blank lines into blocks, then
translates each block independently. HTML blocks (starting with ``<``) pass
through unchanged — this is the hook that lets callers mix raw Confluence
storage (e.g. macros) with markdown.

Recursive `<details>` → ``expand`` macro handling lives in this module too,
but is implemented in a later task (Task 11).
"""

from __future__ import annotations

import re

_MENTION_RE = re.compile(r"@user:([A-Za-z0-9:_-]+)")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
_FENCE_OPEN_RE = re.compile(r"^```(\w+)?\s*$")


def markdown_to_storage(text: str) -> str:
    """Translate markdown source to Confluence storage format XHTML."""
    if not text:
        return ""
    blocks = _split_blocks(text)
    return "".join(_translate_block(b) for b in blocks)


def _split_blocks(text: str) -> list[str]:
    """Split on blank lines, preserving fenced code blocks as single blocks."""
    lines = text.splitlines()
    blocks: list[str] = []
    buf: list[str] = []
    in_fence = False
    for line in lines:
        if _FENCE_OPEN_RE.match(line.strip()):
            buf.append(line)
            if in_fence:
                blocks.append("\n".join(buf))
                buf = []
                in_fence = False
            else:
                in_fence = True
            continue
        if in_fence:
            buf.append(line)
            continue
        if line.strip() == "":
            if buf:
                blocks.append("\n".join(buf))
                buf = []
            continue
        buf.append(line)
    if buf:
        blocks.append("\n".join(buf))
    return blocks


def _translate_block(block: str) -> str:
    stripped = block.strip()
    if not stripped:
        return ""

    # HTML passthrough — tables/details/macros handled in later tasks will
    # intercept before this fallback via explicit checks.
    if stripped.startswith("<"):
        return stripped

    # Fenced code block
    first = stripped.splitlines()[0]
    m = _FENCE_OPEN_RE.match(first)
    if m:
        lang = m.group(1) or ""
        body_lines = stripped.splitlines()[1:]
        if body_lines and _FENCE_OPEN_RE.match(body_lines[-1].strip()):
            body_lines = body_lines[:-1]
        body = "\n".join(body_lines)
        lang_param = f'<ac:parameter ac:name="language">{lang}</ac:parameter>' if lang else ""
        return (
            '<ac:structured-macro ac:name="code">'
            f"{lang_param}"
            f"<ac:plain-text-body><![CDATA[{body}]]></ac:plain-text-body>"
            "</ac:structured-macro>"
        )

    # Heading
    m = _HEADING_RE.match(stripped)
    if m:
        level = len(m.group(1))
        return f"<h{level}>{_inline(m.group(2))}</h{level}>"

    # Paragraph
    return f"<p>{_inline(stripped)}</p>"


def _inline(text: str) -> str:
    """Apply inline transforms: user mentions."""
    def _mention(match: re.Match[str]) -> str:
        account_id = match.group(1)
        return f'<ac:link><ri:user ri:account-id="{account_id}"/></ac:link>'

    return _MENTION_RE.sub(_mention, text)
```

- [ ] **Step 4: Run tests — expect pass**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run pytest tests/confluence/test_content_format.py -x -q
```

Expected: all tests in Task 9's test classes pass.

- [ ] **Step 5: Commit**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
git add src/a2atlassian/confluence/content_format.py tests/confluence/test_content_format.py
git commit -m "feat(confluence): content translator — headings, code, mentions"
```

---

## Task 10 — Translator: pipe-syntax tables

**Files:**
- Modify: `src/a2atlassian/confluence/content_format.py`
- Modify: `tests/confluence/test_content_format.py`

- [ ] **Step 1: Append test class**

Append to `tests/confluence/test_content_format.py`:

```python
class TestTables:
    def test_basic_table(self) -> None:
        src = "| A | B |\n| --- | --- |\n| 1 | 2 |\n| 3 | 4 |"
        out = markdown_to_storage(src)
        assert out == (
            "<table><tbody>"
            "<tr><th>A</th><th>B</th></tr>"
            "<tr><td>1</td><td>2</td></tr>"
            "<tr><td>3</td><td>4</td></tr>"
            "</tbody></table>"
        )

    def test_table_with_inline_mention(self) -> None:
        src = "| Who |\n| --- |\n| @user:abc |"
        out = markdown_to_storage(src)
        assert '<ri:user ri:account-id="abc"/>' in out
```

- [ ] **Step 2: Run — expect failure**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run pytest tests/confluence/test_content_format.py::TestTables -x -q
```

- [ ] **Step 3: Add table handling**

Insert a table-detection branch in `_translate_block` in `src/a2atlassian/confluence/content_format.py` **before** the heading check, and add the `_translate_table` helper:

```python
def _translate_block(block: str) -> str:
    stripped = block.strip()
    if not stripped:
        return ""

    if stripped.startswith("<"):
        return stripped

    first = stripped.splitlines()[0]
    m = _FENCE_OPEN_RE.match(first)
    if m:
        # ...existing fenced-code branch unchanged...

    if _looks_like_table(stripped):
        return _translate_table(stripped)

    # ...existing heading + paragraph branches unchanged...
```

Add helpers at module scope:

```python
def _looks_like_table(block: str) -> bool:
    lines = block.splitlines()
    if len(lines) < 2:
        return False
    if "|" not in lines[0]:
        return False
    sep = lines[1].strip()
    cells = [c.strip() for c in sep.strip("|").split("|") if c.strip()]
    return bool(cells) and all(set(c) <= set("-:") for c in cells)


def _split_row(row: str) -> list[str]:
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]
    return [cell.strip() for cell in row.split("|")]


def _translate_table(block: str) -> str:
    lines = block.splitlines()
    header_cells = _split_row(lines[0])
    data_rows = [_split_row(line) for line in lines[2:] if line.strip()]
    head = "".join(f"<th>{_inline(c)}</th>" for c in header_cells)
    rows = ["<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>" for r in data_rows]
    return f"<table><tbody><tr>{head}</tr>{''.join(rows)}</tbody></table>"
```

- [ ] **Step 4: Run — expect pass**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run pytest tests/confluence/test_content_format.py -x -q
```

- [ ] **Step 5: Commit**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
git add src/a2atlassian/confluence/content_format.py tests/confluence/test_content_format.py
git commit -m "feat(confluence): translator pipe-table rule"
```

---

## Task 11 — Translator: recursive `<details>` → expand macro

**Why critical:** This is the signal-S11 regression. `<details>` bodies must be re-parsed through the full rule set (including nested tables) so that markdown *inside* `<details>` gets translated, not passed through literally.

**Files:**
- Modify: `src/a2atlassian/confluence/content_format.py`
- Modify: `tests/confluence/test_content_format.py`

- [ ] **Step 1: Append tests**

Append to `tests/confluence/test_content_format.py`:

```python
class TestDetailsExpand:
    def test_simple_details(self) -> None:
        src = "<details><summary>More</summary>\n\nhello\n\n</details>"
        out = markdown_to_storage(src)
        assert out.startswith('<ac:structured-macro ac:name="expand">')
        assert '<ac:parameter ac:name="title">More</ac:parameter>' in out
        assert "<ac:rich-text-body><p>hello</p></ac:rich-text-body>" in out
        assert out.endswith("</ac:structured-macro>")

    def test_details_contains_translated_table(self) -> None:
        src = (
            "<details><summary>Stats</summary>\n\n"
            "| A | B |\n| --- | --- |\n| 1 | 2 |\n\n"
            "</details>"
        )
        out = markdown_to_storage(src)
        assert "<table><tbody>" in out
        assert "<th>A</th><th>B</th>" in out
        assert "<td>1</td><td>2</td>" in out

    def test_nested_details(self) -> None:
        src = (
            "<details><summary>Outer</summary>\n\n"
            "<details><summary>Inner</summary>\n\n"
            "body\n\n"
            "</details>\n\n"
            "</details>"
        )
        out = markdown_to_storage(src)
        # Two expand macros, inner nested inside outer's rich-text-body.
        assert out.count('<ac:structured-macro ac:name="expand">') == 2
        assert '<ac:parameter ac:name="title">Outer</ac:parameter>' in out
        assert '<ac:parameter ac:name="title">Inner</ac:parameter>' in out
```

- [ ] **Step 2: Run — expect failure**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run pytest tests/confluence/test_content_format.py::TestDetailsExpand -x -q
```

- [ ] **Step 3: Add recursive `<details>` handling**

In `src/a2atlassian/confluence/content_format.py`, replace the top of `markdown_to_storage` so that, *before* the block split, we extract `<details>` blocks recursively. Use a two-pass: detect outermost `<details>` regions with a balanced-tag scan (regex can't do this), recurse on the body, then wrap.

Add at module scope:

```python
_DETAILS_OPEN = "<details>"
_DETAILS_CLOSE = "</details>"
_SUMMARY_OPEN = "<summary>"
_SUMMARY_CLOSE = "</summary>"


def _extract_outermost_details(text: str) -> list[tuple[int, int, str, str]]:
    """Return list of (start, end, title, body) for outermost <details> regions."""
    out: list[tuple[int, int, str, str]] = []
    i = 0
    while i < len(text):
        open_at = text.find(_DETAILS_OPEN, i)
        if open_at == -1:
            break
        depth = 1
        scan = open_at + len(_DETAILS_OPEN)
        close_at = -1
        while scan < len(text):
            next_open = text.find(_DETAILS_OPEN, scan)
            next_close = text.find(_DETAILS_CLOSE, scan)
            if next_close == -1:
                break
            if next_open != -1 and next_open < next_close:
                depth += 1
                scan = next_open + len(_DETAILS_OPEN)
            else:
                depth -= 1
                if depth == 0:
                    close_at = next_close
                    break
                scan = next_close + len(_DETAILS_CLOSE)
        if close_at == -1:
            break  # unbalanced — leave the rest to HTML passthrough
        inner = text[open_at + len(_DETAILS_OPEN) : close_at]
        s_open = inner.find(_SUMMARY_OPEN)
        s_close = inner.find(_SUMMARY_CLOSE)
        if s_open == -1 or s_close == -1 or s_close < s_open:
            title = ""
            body = inner
        else:
            title = inner[s_open + len(_SUMMARY_OPEN) : s_close].strip()
            body = inner[s_close + len(_SUMMARY_CLOSE) :]
        out.append((open_at, close_at + len(_DETAILS_CLOSE), title, body))
        i = close_at + len(_DETAILS_CLOSE)
    return out


def _apply_details(text: str) -> str:
    """Replace every outermost <details> region with an expand macro whose body is recursively translated."""
    regions = _extract_outermost_details(text)
    if not regions:
        return text
    pieces: list[str] = []
    cursor = 0
    for start, end, title, body in regions:
        pieces.append(text[cursor:start])
        inner_html = markdown_to_storage(body.strip())
        pieces.append(
            '<ac:structured-macro ac:name="expand">'
            f'<ac:parameter ac:name="title">{title}</ac:parameter>'
            f"<ac:rich-text-body>{inner_html}</ac:rich-text-body>"
            "</ac:structured-macro>"
        )
        cursor = end
    pieces.append(text[cursor:])
    return "".join(pieces)
```

Then change the top of `markdown_to_storage`:

```python
def markdown_to_storage(text: str) -> str:
    if not text:
        return ""
    # Recursive details → expand; body gets re-parsed by this same function.
    text = _apply_details(text)
    blocks = _split_blocks(text)
    return "".join(_translate_block(b) for b in blocks)
```

Because `_apply_details` replaces `<details>` with `<ac:structured-macro ...>`, the surviving block-splitter will pass the whole macro through the HTML-passthrough branch unchanged. Verify that path by hand: a paragraph after `</details>` should still be processed (blank-line separated).

- [ ] **Step 4: Run — expect pass**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run pytest tests/confluence/test_content_format.py -x -q
```

- [ ] **Step 5: Commit**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
git add src/a2atlassian/confluence/content_format.py tests/confluence/test_content_format.py
git commit -m "feat(confluence): recursive <details> → expand macro translator"
```

---

## Task 12 — Upsert identity resolution helper

**Files:**
- Modify: `src/a2atlassian/confluence/pages.py`
- Modify: `tests/confluence/test_pages.py`

Per spec §Design — Tool 4 Identity resolution:

1. `page_id` given → update that page (error if missing).
2. Else `parent_id` given → search title match under that parent only.
3. Else → search space root (top-level) for matching title.

- [ ] **Step 1: Append tests**

Append to `tests/confluence/test_pages.py`:

```python
from a2atlassian.confluence.pages import resolve_page_identity


class TestResolveIdentity:
    async def test_page_id_wins(self, mock_client: ConfluenceClient) -> None:
        mock_client._confluence_instance.get_page_by_id.return_value = {"id": "42", "title": "X"}
        resolved = await resolve_page_identity(mock_client, space="SP", title="ignored", page_id="42", parent_id=None)
        assert resolved == "42"

    async def test_page_id_missing_raises(self, mock_client: ConfluenceClient) -> None:
        mock_client._confluence_instance.get_page_by_id.return_value = None
        with pytest.raises(ValueError, match="page_id"):
            await resolve_page_identity(mock_client, space="SP", title="ignored", page_id="999", parent_id=None)

    async def test_parent_scoped_match(self, mock_client: ConfluenceClient) -> None:
        mock_client._confluence_instance.get_page_child_by_type.return_value = [
            {"id": "100", "title": "Report"},
            {"id": "101", "title": "Other"},
        ]
        resolved = await resolve_page_identity(mock_client, space="SP", title="Report", page_id=None, parent_id="50")
        assert resolved == "100"
        call = mock_client._confluence_instance.get_page_child_by_type.call_args
        assert call.args[0] == "50"

    async def test_parent_scoped_no_match_returns_none(self, mock_client: ConfluenceClient) -> None:
        mock_client._confluence_instance.get_page_child_by_type.return_value = [{"id": "100", "title": "X"}]
        resolved = await resolve_page_identity(mock_client, space="SP", title="Missing", page_id=None, parent_id="50")
        assert resolved is None

    async def test_space_root_match(self, mock_client: ConfluenceClient) -> None:
        mock_client._confluence_instance.get_page_by_title.return_value = {"id": "200", "title": "Top"}
        resolved = await resolve_page_identity(mock_client, space="SP", title="Top", page_id=None, parent_id=None)
        assert resolved == "200"

    async def test_space_root_no_match_returns_none(self, mock_client: ConfluenceClient) -> None:
        mock_client._confluence_instance.get_page_by_title.return_value = None
        resolved = await resolve_page_identity(mock_client, space="SP", title="Nope", page_id=None, parent_id=None)
        assert resolved is None
```

- [ ] **Step 2: Run — expect failure**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run pytest tests/confluence/test_pages.py::TestResolveIdentity -x -q
```

- [ ] **Step 3: Append the helper**

Append to `src/a2atlassian/confluence/pages.py`:

```python
async def resolve_page_identity(
    client: ConfluenceClient,
    space: str,
    title: str,
    page_id: str | None,
    parent_id: str | None,
) -> str | None:
    """Resolve a page id for upsert. Returns the id if an existing page matches, None if not.

    Precedence:
      1. page_id given → must exist; raise if missing.
      2. parent_id given → search that parent's children for a title match (scope: this parent only).
      3. Otherwise → search the space root by title.

    Per-parent scope is deliberate: same title under a different parent counts as a miss,
    so re-running with a new parent creates a new page. See spec §Design — Tool 4.
    """
    if page_id:
        existing = await client._call(client._confluence.get_page_by_id, page_id)
        if not existing:
            msg = f"page_id {page_id} not found"
            raise ValueError(msg)
        return page_id

    if parent_id:
        children = await client._call(
            client._confluence.get_page_child_by_type, parent_id, type="page", start=0, limit=200
        )
        items = children if isinstance(children, list) else (children or {}).get("results", [])
        for child in items:
            if child.get("title") == title:
                return str(child.get("id"))
        return None

    top = await client._call(client._confluence.get_page_by_title, space=space, title=title)
    if top:
        return str(top.get("id"))
    return None
```

- [ ] **Step 4: Run — expect pass**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run pytest tests/confluence/test_pages.py -x -q
```

- [ ] **Step 5: Commit**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
git add src/a2atlassian/confluence/pages.py tests/confluence/test_pages.py
git commit -m "feat(confluence): identity resolution for upsert"
```

---

## Task 13 — Upsert single page (create or update)

**Files:**
- Modify: `src/a2atlassian/confluence/pages.py`
- Modify: `tests/confluence/test_pages.py`
- Create: `tests/fixtures/confluence_create_page_response.json`
- Create: `tests/fixtures/confluence_update_page_response.json`

- [ ] **Step 1: Fixtures**

`tests/fixtures/confluence_create_page_response.json`:

```json
{"id": "900", "title": "New", "version": {"number": 1}, "_links": {"webui": "/pages/900"}}
```

`tests/fixtures/confluence_update_page_response.json`:

```json
{"id": "900", "title": "New", "version": {"number": 4}, "_links": {"webui": "/pages/900"}}
```

- [ ] **Step 2: Append tests**

Append to `tests/confluence/test_pages.py`:

```python
import json as _json
from a2atlassian.confluence.pages import upsert_page


class TestUpsertSingle:
    async def test_create_when_no_existing(self, mock_client: ConfluenceClient) -> None:
        mock_client._confluence_instance.get_page_by_title.return_value = None
        mock_client._confluence_instance.create_page.return_value = _json.loads(
            (FIXTURES / "confluence_create_page_response.json").read_text()
        )
        result = await upsert_page(
            mock_client,
            space="SP",
            title="New",
            content="# hi",
            parent_id=None,
            page_id=None,
            content_format="markdown",
            page_width=None,
            emoji=None,
            labels=None,
        )
        assert result["status"] == "created"
        assert result["page_id"] == "900"
        assert result["version"] == 1
        call = mock_client._confluence_instance.create_page.call_args
        assert call.kwargs.get("representation") == "storage"
        # content got translated
        assert "<h1>hi</h1>" in call.kwargs.get("body", "")

    async def test_update_when_match(self, mock_client: ConfluenceClient) -> None:
        mock_client._confluence_instance.get_page_by_title.return_value = {"id": "900", "title": "New"}
        mock_client._confluence_instance.update_page.return_value = _json.loads(
            (FIXTURES / "confluence_update_page_response.json").read_text()
        )
        result = await upsert_page(
            mock_client,
            space="SP",
            title="New",
            content="body",
            parent_id=None,
            page_id=None,
            content_format="markdown",
            page_width=None,
            emoji=None,
            labels=None,
        )
        assert result["status"] == "updated"
        assert result["page_id"] == "900"
        assert result["version"] == 4

    async def test_storage_bypasses_translator(self, mock_client: ConfluenceClient) -> None:
        mock_client._confluence_instance.get_page_by_title.return_value = None
        mock_client._confluence_instance.create_page.return_value = {"id": "1", "version": {"number": 1}, "_links": {"webui": "/p/1"}}
        raw = '<ac:structured-macro ac:name="info"><ac:rich-text-body><p>x</p></ac:rich-text-body></ac:structured-macro>'
        await upsert_page(
            mock_client, space="SP", title="T", content=raw,
            parent_id=None, page_id=None, content_format="storage",
            page_width=None, emoji=None, labels=None,
        )
        call = mock_client._confluence_instance.create_page.call_args
        assert call.kwargs.get("body") == raw  # passed through unchanged
```

- [ ] **Step 3: Run — expect failure**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run pytest tests/confluence/test_pages.py::TestUpsertSingle -x -q
```

- [ ] **Step 4: Append implementation**

Append to `src/a2atlassian/confluence/pages.py`:

```python
from a2atlassian.confluence.content_format import markdown_to_storage  # placed near top in final layout


async def upsert_page(
    client: ConfluenceClient,
    *,
    space: str,
    title: str,
    content: str,
    parent_id: str | None,
    page_id: str | None,
    content_format: str,
    page_width: str | None,
    emoji: str | None,
    labels: list[str] | None,
) -> dict[str, Any]:
    """Create or update a single Confluence page. Returns a succeeded-shaped dict.

    Caller (batch upsert) wraps exceptions; this function may raise.
    """
    body = content if content_format == "storage" else markdown_to_storage(content)
    resolved = await resolve_page_identity(client, space=space, title=title, page_id=page_id, parent_id=parent_id)

    if resolved is None:
        raw = await client._call(
            client._confluence.create_page,
            space=space,
            title=title,
            body=body,
            parent_id=parent_id,
            type="page",
            representation="storage",
        )
        status = "created"
    else:
        raw = await client._call(
            client._confluence.update_page,
            page_id=resolved,
            title=title,
            body=body,
            parent_id=parent_id,
            representation="storage",
        )
        status = "updated"

    links = raw.get("_links") or {}
    version = (raw.get("version") or {}).get("number", 0)
    page_id_out = str(raw.get("id", resolved or ""))

    # Post-save knobs (labels / emoji / page_width) are applied in Task 15.
    return {
        "title": title,
        "page_id": page_id_out,
        "status": status,
        "url": links.get("webui", ""),
        "version": version,
    }
```

Move the `from a2atlassian.confluence.content_format import markdown_to_storage` import to the top-of-file imports block (after `from a2atlassian.formatter import OperationResult`).

- [ ] **Step 5: Run — expect pass**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run pytest tests/confluence/test_pages.py -x -q
```

- [ ] **Step 6: Commit**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
git add src/a2atlassian/confluence/pages.py tests/confluence/test_pages.py tests/fixtures/confluence_create_page_response.json tests/fixtures/confluence_update_page_response.json
git commit -m "feat(confluence): single-page upsert with identity + translator"
```

---

## Task 14 — Batch upsert with structured partial-failure

**Files:**
- Modify: `src/a2atlassian/confluence/pages.py`
- Modify: `tests/confluence/test_pages.py`

- [ ] **Step 1: Append tests**

Append to `tests/confluence/test_pages.py`:

```python
from a2atlassian.confluence.pages import upsert_pages


class TestUpsertBatch:
    async def test_all_success(self, mock_client: ConfluenceClient) -> None:
        mock_client._confluence_instance.get_page_by_title.return_value = None
        mock_client._confluence_instance.create_page.side_effect = [
            {"id": "1", "version": {"number": 1}, "_links": {"webui": "/p/1"}},
            {"id": "2", "version": {"number": 1}, "_links": {"webui": "/p/2"}},
        ]
        result = await upsert_pages(
            mock_client,
            pages=[
                {"space": "SP", "title": "A", "content": "hi"},
                {"space": "SP", "title": "B", "content": "hello"},
            ],
        )
        assert isinstance(result, OperationResult)
        assert result.data["summary"] == {"total": 2, "created": 2, "updated": 0, "failed": 0}
        assert len(result.data["succeeded"]) == 2
        assert result.data["failed"] == []

    async def test_partial_failure_does_not_raise(self, mock_client: ConfluenceClient) -> None:
        from requests.exceptions import HTTPError
        from requests.models import Response

        def _err(status: int) -> HTTPError:
            r = Response()
            r.status_code = status
            return HTTPError(response=r)

        mock_client._confluence_instance.get_page_by_title.return_value = None
        mock_client._confluence_instance.create_page.side_effect = [
            {"id": "1", "version": {"number": 1}, "_links": {"webui": "/p/1"}},
            _err(403),
            _err(400),
        ]
        result = await upsert_pages(
            mock_client,
            pages=[
                {"space": "SP", "title": "A", "content": "hi"},
                {"space": "SP", "title": "B", "content": "hi"},
                {"space": "SP", "title": "C", "content": "hi"},
            ],
        )
        assert result.data["summary"] == {"total": 3, "created": 1, "updated": 0, "failed": 2}
        assert len(result.data["succeeded"]) == 1
        assert len(result.data["failed"]) == 2
        categories = {f["error_category"] for f in result.data["failed"]}
        assert "permission" in categories  # 403
        assert "format" in categories      # 400

    async def test_empty_batch(self, mock_client: ConfluenceClient) -> None:
        result = await upsert_pages(mock_client, pages=[])
        assert result.data["summary"] == {"total": 0, "created": 0, "updated": 0, "failed": 0}
```

Note: the 403/400 side-effects need to raise `HTTPError`. `mock.side_effect` with an exception instance raises it. The retry logic in `_call` sees 403 → `AuthenticationError`; the 400 passes through as raw `HTTPError`. Both become `failed` entries in the batch.

- [ ] **Step 2: Run — expect failure**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run pytest tests/confluence/test_pages.py::TestUpsertBatch -x -q
```

- [ ] **Step 3: Append implementation**

Append to `src/a2atlassian/confluence/pages.py`:

```python
from a2atlassian.errors import AuthenticationError  # import near top


def _classify_error(exc: BaseException) -> str:
    if isinstance(exc, AuthenticationError):
        return "permission"
    status = None
    from requests.exceptions import HTTPError  # noqa: PLC0415

    if isinstance(exc, HTTPError):
        status = getattr(exc.response, "status_code", None)
    if status == 400:
        return "format"
    if status == 409:
        return "conflict"
    if status in (401, 403):
        return "permission"
    return "other"


async def upsert_pages(
    client: ConfluenceClient,
    pages: list[dict[str, Any]],
) -> OperationResult:
    """Batch create-or-update. Returns per-page outcomes; never raises on partial failure."""
    t0 = time.monotonic()
    succeeded: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    created = updated = 0

    for page in pages:
        title = page.get("title", "")
        try:
            out = await upsert_page(
                client,
                space=page["space"],
                title=title,
                content=page["content"],
                parent_id=page.get("parent_id"),
                page_id=page.get("page_id"),
                content_format=page.get("content_format", "markdown"),
                page_width=page.get("page_width"),
                emoji=page.get("emoji"),
                labels=page.get("labels"),
            )
            succeeded.append(out)
            if out["status"] == "created":
                created += 1
            else:
                updated += 1
        except Exception as exc:  # noqa: BLE001 — batch semantics require swallowing per-page errors
            failed.append(
                {"title": title, "error": str(exc), "error_category": _classify_error(exc)}
            )

    elapsed = int((time.monotonic() - t0) * 1000)
    summary = {"total": len(pages), "created": created, "updated": updated, "failed": len(failed)}

    return OperationResult(
        name="upsert_pages",
        data={"succeeded": succeeded, "failed": failed, "summary": summary},
        count=len(pages),
        truncated=False,
        time_ms=elapsed,
    )
```

Note the `noqa: BLE001` — this is a deliberate broad except because the spec explicitly requires the tool to not raise on partial failure.

- [ ] **Step 4: Run — expect pass**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run pytest tests/confluence/test_pages.py -x -q
```

- [ ] **Step 5: Commit**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
git add src/a2atlassian/confluence/pages.py tests/confluence/test_pages.py
git commit -m "feat(confluence): batch upsert with partial-failure shape"
```

---

## Task 15 — Page-level knobs: labels, emoji, page_width

**Files:**
- Modify: `src/a2atlassian/confluence/pages.py`
- Modify: `tests/confluence/test_pages.py`

- [ ] **Step 1: Append tests**

Append to `tests/confluence/test_pages.py`:

```python
class TestUpsertKnobs:
    async def test_labels_applied_after_save(self, mock_client: ConfluenceClient) -> None:
        mock_client._confluence_instance.get_page_by_title.return_value = None
        mock_client._confluence_instance.create_page.return_value = {
            "id": "9", "version": {"number": 1}, "_links": {"webui": "/p/9"}
        }
        await upsert_page(
            mock_client, space="SP", title="T", content="x",
            parent_id=None, page_id=None, content_format="markdown",
            page_width=None, emoji=None, labels=["alpha", "beta"],
        )
        calls = mock_client._confluence_instance.set_page_label.call_args_list
        assert len(calls) == 2
        assert {c.args[1] for c in calls} == {"alpha", "beta"}
        assert all(c.args[0] == "9" for c in calls)

    async def test_emoji_and_page_width_invoke_property_set(self, mock_client: ConfluenceClient) -> None:
        mock_client._confluence_instance.get_page_by_title.return_value = None
        mock_client._confluence_instance.create_page.return_value = {
            "id": "9", "version": {"number": 1}, "_links": {"webui": "/p/9"}
        }
        await upsert_page(
            mock_client, space="SP", title="T", content="x",
            parent_id=None, page_id=None, content_format="markdown",
            page_width="full-width", emoji="📄", labels=None,
        )
        assert mock_client._confluence_instance.set_page_property.call_count >= 1

    async def test_page_width_none_on_update_does_not_touch_property(self, mock_client: ConfluenceClient) -> None:
        mock_client._confluence_instance.get_page_by_title.return_value = {"id": "9", "title": "T"}
        mock_client._confluence_instance.update_page.return_value = {
            "id": "9", "version": {"number": 2}, "_links": {"webui": "/p/9"}
        }
        mock_client._confluence_instance.set_page_property.reset_mock()
        await upsert_page(
            mock_client, space="SP", title="T", content="x",
            parent_id=None, page_id=None, content_format="markdown",
            page_width=None, emoji=None, labels=None,
        )
        mock_client._confluence_instance.set_page_property.assert_not_called()
```

- [ ] **Step 2: Run — expect failure**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run pytest tests/confluence/test_pages.py::TestUpsertKnobs -x -q
```

- [ ] **Step 3: Extend `upsert_page`**

In `src/a2atlassian/confluence/pages.py`, add helpers above `upsert_page`:

```python
async def _apply_labels(client: ConfluenceClient, page_id: str, labels: list[str] | None) -> None:
    if not labels:
        return
    for label in labels:
        await client._call(client._confluence.set_page_label, page_id, label)


async def _apply_emoji(client: ConfluenceClient, page_id: str, emoji: str | None) -> None:
    if emoji is None:
        return
    await client._call(
        client._confluence.set_page_property,
        page_id,
        {"key": "emoji-title-published", "value": emoji},
    )


async def _apply_page_width(client: ConfluenceClient, page_id: str, page_width: str | None) -> None:
    if page_width is None:
        return
    await client._call(
        client._confluence.set_page_property,
        page_id,
        {"key": "content-appearance-published", "value": page_width},
    )
```

**Important:** The property keys above (`emoji-title-published`, `content-appearance-published`) match Atlassian's published content-property names as of 2026. If the spike in Task 1 showed that `atlassian-python-api` does not expose `set_page_property`, replace those `_call(client._confluence.set_page_property, ...)` invocations with raw REST puts, e.g. `await client._call(client._confluence.put, f"rest/api/content/{page_id}/property/{key}", data={"value": value, "version": {"number": 1}})`. Keep the helper names and call sites identical — only the body of the helpers changes.

Then extend `upsert_page` to call them just before the return:

```python
    # ...after status assignment, before the return dict...
    await _apply_labels(client, page_id_out, labels)
    await _apply_emoji(client, page_id_out, emoji)
    # On create, default page_width to "fixed-width" if caller did not specify.
    effective_width = page_width if page_width is not None else ("fixed-width" if status == "created" else None)
    await _apply_page_width(client, page_id_out, effective_width)

    return {
        ...
    }
```

- [ ] **Step 4: Run — expect pass**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run pytest tests/confluence/test_pages.py -x -q
```

- [ ] **Step 5: Commit**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
git add src/a2atlassian/confluence/pages.py tests/confluence/test_pages.py
git commit -m "feat(confluence): labels, emoji, page_width knobs on upsert"
```

---

## Task 16 — MCP tools: `confluence_get_page`, `confluence_get_page_children`

**Files:**
- Create: `src/a2atlassian/confluence_tools/__init__.py`
- Create: `src/a2atlassian/confluence_tools/pages.py`

- [ ] **Step 1: Write `confluence_tools/__init__.py`**

```python
"""Confluence MCP tool modules — one per feature domain.

Each module exposes register_read and/or register_write accepting
(server, get_client_or_connection, enricher).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType

from a2atlassian.confluence_tools import pages, search

FEATURES: dict[str, ModuleType] = {
    "pages": pages,
    "search": search,
}
```

- [ ] **Step 2: Write read-side of `confluence_tools/pages.py`**

```python
"""Confluence page tools — get, get_children, upsert."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from a2atlassian.confluence.pages import get_page, get_page_children, upsert_pages
from a2atlassian.confluence_client import ConfluenceClient
from a2atlassian.decorators import check_writable, mcp_tool
from a2atlassian.formatter import OperationResult  # noqa: TC001 — FastMCP needs runtime annotation

if TYPE_CHECKING:
    from collections.abc import Callable

    from mcp.server.fastmcp import FastMCP

    from a2atlassian.connections import ConnectionInfo
    from a2atlassian.errors import ErrorEnricher


def register_read(
    server: FastMCP,
    get_client: Callable[[str], ConfluenceClient],
    enricher: ErrorEnricher,
) -> None:
    @server.tool()
    @mcp_tool(enricher)
    async def confluence_get_page(
        connection: str,
        page_id: str,
        expand: str | None = None,
        format: Literal["toon", "json"] = "json",  # noqa: A002
    ) -> OperationResult:
        """Get a Confluence page by id. Returns title, body (storage format), version, space, url."""
        return await get_page(get_client(connection), page_id, expand=expand)

    @server.tool()
    @mcp_tool(enricher)
    async def confluence_get_page_children(
        connection: str,
        page_id: str,
        limit: int = 50,
        offset: int = 0,
        format: Literal["toon", "json"] = "toon",  # noqa: A002
    ) -> OperationResult:
        """List direct children of a Confluence page. Paginated."""
        return await get_page_children(get_client(connection), page_id, limit=limit, offset=offset)
```

(Leave `register_write` stubbed for Task 18; do not emit it yet.)

- [ ] **Step 3: Run lint+tests**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && make lint && uv run pytest tests/confluence/ -x -q
```

Expected: lint passes; existing tests pass. No new tests yet (tool-registration test lives in Task 20 against the full feature set).

- [ ] **Step 4: Commit**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
git add src/a2atlassian/confluence_tools/
git commit -m "feat(confluence_tools): register get_page + get_page_children"
```

---

## Task 17 — MCP tool: `confluence_search`

**Files:**
- Create: `src/a2atlassian/confluence_tools/search.py`

- [ ] **Step 1: Write the module**

```python
"""Confluence CQL search tool."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from a2atlassian.confluence.search import search as _search
from a2atlassian.confluence_client import ConfluenceClient
from a2atlassian.decorators import mcp_tool
from a2atlassian.formatter import OperationResult  # noqa: TC001

if TYPE_CHECKING:
    from collections.abc import Callable

    from mcp.server.fastmcp import FastMCP

    from a2atlassian.errors import ErrorEnricher


def register_read(
    server: FastMCP,
    get_client: Callable[[str], ConfluenceClient],
    enricher: ErrorEnricher,
) -> None:
    @server.tool()
    @mcp_tool(enricher)
    async def confluence_search(
        connection: str,
        cql: str,
        limit: int = 25,
        offset: int = 0,
        format: Literal["toon", "json"] = "toon",  # noqa: A002
    ) -> OperationResult:
        """Search Confluence via CQL. Returns minimal row per match.

        Gotcha: `text ~ "..."` in CQL is broad and expensive — prefer `title ~` or
        `space = KEY AND type = page` predicates first.
        """
        return await _search(get_client(connection), cql, limit=limit, offset=offset)
```

- [ ] **Step 2: Run lint + tests**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && make lint && uv run pytest tests/confluence/ -x -q
```

- [ ] **Step 3: Commit**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
git add src/a2atlassian/confluence_tools/search.py
git commit -m "feat(confluence_tools): register confluence_search"
```

---

## Task 18 — MCP tool: `confluence_upsert_pages`

**Files:**
- Modify: `src/a2atlassian/confluence_tools/pages.py`

- [ ] **Step 1: Append `register_write` to `confluence_tools/pages.py`**

```python
def register_write(
    server: FastMCP,
    get_connection: Callable[[str], ConnectionInfo],
    enricher: ErrorEnricher,
) -> None:
    @server.tool()
    @mcp_tool(enricher)
    async def confluence_upsert_pages(
        connection: str,
        pages: list[dict[str, Any]],
        format: Literal["toon", "json"] = "json",  # noqa: A002
    ) -> OperationResult:
        """Batch create-or-update Confluence pages.

        Each page spec:
          space (str, required)
          title (str, required)
          content (str, required)
          parent_id (str | None)
          page_id (str | None) — if set, always updates this id.
          content_format: "markdown" (default) | "storage"
          page_width: "full-width" | "fixed-width" | None (on update, None preserves existing)
          emoji: str | None
          labels: list[str] | None

        Identity resolution per page (in order):
          1. page_id
          2. parent_id → title match under that parent only
          3. space root → title match at top level

        Returns {succeeded: [...], failed: [...], summary: {...}}. Does NOT raise on
        partial failure — inspect `failed` to see per-page errors with error_category
        (permission | format | conflict | other).
        """
        conn = get_connection(connection)
        check_writable(conn, connection)
        client = ConfluenceClient(conn)
        return await upsert_pages(client, pages)
```

- [ ] **Step 2: Run lint + tests**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && make lint && uv run pytest tests/confluence/ -x -q
```

- [ ] **Step 3: Commit**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
git add src/a2atlassian/confluence_tools/pages.py
git commit -m "feat(confluence_tools): register confluence_upsert_pages"
```

---

## Task 19 — Wire Confluence into `mcp_server.py`

**Files:**
- Modify: `src/a2atlassian/mcp_server.py`
- Modify: `tests/test_mcp_server.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_mcp_server.py` (create the file if absent with the existing Jira tests preserved):

```python
class TestConfluenceWiring:
    def test_known_domains_includes_confluence(self) -> None:
        from a2atlassian.mcp_server import _parse_enable_args

        parsed = _parse_enable_args(["--enable", "confluence"])
        assert "confluence" in parsed

    def test_instructions_mentions_confluence(self) -> None:
        from a2atlassian.mcp_server import server

        # Basic sanity: the user-facing instructions no longer say "Jira only".
        text = getattr(server, "instructions", "") or ""
        assert "Confluence" in text
        assert "Jira only today" not in text

    def test_get_confluence_client_returns_confluence_client(self, tmp_path) -> None:
        from a2atlassian.confluence_client import ConfluenceClient
        from a2atlassian.mcp_server import _ephemeral_connections, _get_confluence_client
        from a2atlassian.connections import ConnectionInfo

        _ephemeral_connections["mp"] = ConnectionInfo(
            connection="mp", url="https://x.atlassian.net", email="a@b", token="t", read_only=True
        )
        try:
            client = _get_confluence_client("mp")
            assert isinstance(client, ConfluenceClient)
        finally:
            _ephemeral_connections.pop("mp", None)
```

- [ ] **Step 2: Run — expect failure**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run pytest tests/test_mcp_server.py::TestConfluenceWiring -x -q
```

- [ ] **Step 3: Edit `mcp_server.py`**

Changes to `src/a2atlassian/mcp_server.py`:

- Add import: `from a2atlassian.confluence_client import ConfluenceClient`
- Add import: `from a2atlassian.confluence_tools import FEATURES as CONFLUENCE_FEATURES`
- Rewrite the `instructions=` block — replace the `"Scope today: Jira only. For Confluence, use mcp__atlassian (sooperset). "` sentence with `"Works with both Jira and Confluence. "`. Keep the rest identical.
- Add accessor after `_get_jira_client`:

```python
def _get_confluence_client(connection: str) -> ConfluenceClient:
    """Resolve a connection and return a Confluence client."""
    return ConfluenceClient(_get_connection(connection))
```

- Add `_register_confluence_tools` mirroring `_register_jira_tools`:

```python
def _register_confluence_tools(features: set[str] | None) -> None:
    if features is not None:
        unknown = features - set(CONFLUENCE_FEATURES.keys())
        if unknown:
            sys.exit(
                f"Error: unknown Confluence feature(s): {', '.join(sorted(unknown))}. "
                f"Available: {', '.join(sorted(CONFLUENCE_FEATURES.keys()))}"
            )
    for name, mod in CONFLUENCE_FEATURES.items():
        if features is not None and name not in features:
            continue
        if hasattr(mod, "register_read"):
            mod.register_read(server, _get_confluence_client, _enricher)
        if hasattr(mod, "register_write"):
            mod.register_write(server, _get_connection, _enricher)
```

- In `main()`: change `known_domains = {"jira"}  # add "confluence" when it ships` → `known_domains = {"jira", "confluence"}`. Add after the Jira registration block:

```python
    if _domain_enabled("confluence", enable):
        _register_confluence_tools(_domain_features("confluence", enable))
```

- [ ] **Step 4: Run tests — expect pass**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run pytest tests/test_mcp_server.py -x -q
```

- [ ] **Step 5: Commit**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
git add src/a2atlassian/mcp_server.py tests/test_mcp_server.py
git commit -m "feat(mcp): wire Confluence domain — accessor, registration, instructions"
```

---

## Task 20 — Client module-boundary test

**Files:**
- Create: `tests/confluence_tools/__init__.py` (empty)
- Create: `tests/confluence_tools/test_registration.py`

**Why:** Spec §Testing requires "a fixture that boots a ConfluenceClient without importing any Jira modules." This asserts the module split actually holds.

- [ ] **Step 1: Write the test**

`tests/confluence_tools/test_registration.py`:

```python
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
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        pytest.fail(f"stdout={result.stdout!r} stderr={result.stderr!r}")


def test_all_four_confluence_tools_registered() -> None:
    import a2atlassian.mcp_server as ms

    ms._scope_filter.clear()
    ms._register_confluence_tools(None)

    # FastMCP exposes registered tool names through the underlying tool manager.
    tool_names = {t.name for t in ms.server._tool_manager.list_tools()}
    assert "confluence_get_page" in tool_names
    assert "confluence_get_page_children" in tool_names
    assert "confluence_search" in tool_names
    assert "confluence_upsert_pages" in tool_names
```

Note: `server._tool_manager.list_tools()` is the FastMCP internal API used by existing tests elsewhere in the repo. If a different accessor pattern is already used in `tests/test_mcp_server.py`, mirror that pattern instead.

- [ ] **Step 2: Run — expect pass**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && uv run pytest tests/confluence_tools/test_registration.py -x -q
```

If the second test fails because tools were already registered by previous tests, adjust by checking `in tool_names` only (registration is idempotent enough — Fast MCP will raise on duplicate registration; wrap the call in try/except or use a single module-load guard).

- [ ] **Step 3: Commit**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
git add tests/confluence_tools/
git commit -m "test(confluence): module boundary + tool registration"
```

---

## Task 21 — Extend `scripts/record_fixtures.py` for Confluence

**Files:**
- Modify: `scripts/record_fixtures.py`

- [ ] **Step 1: Read the existing recorder**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && sed -n '1,200p' scripts/record_fixtures.py | head -200
```

Identify the pattern (anonymization helpers + per-endpoint record functions + a main()).

- [ ] **Step 2: Add Confluence recording helpers**

Append a new section to `scripts/record_fixtures.py` that:

1. Reads env vars `A2ATLASSIAN_TEST_CONFLUENCE_SPACE` and `A2ATLASSIAN_TEST_CONFLUENCE_PAGE_ID`.
2. Instantiates `ConfluenceClient` instead of `AtlassianClient`.
3. Calls `_confluence.get_page_by_id(page_id, expand="body.storage,version,space")` and writes to `tests/fixtures/confluence_page.json` (overwriting the synthetic fixture from Task 6 with a real anonymized sample).
4. Calls `_confluence.get_page_child_by_type(page_id, type="page", start=0, limit=50)` → `tests/fixtures/confluence_page_children.json`.
5. Calls `_confluence.cql(f'space = {space} AND type = page', start=0, limit=10)` → `tests/fixtures/confluence_cql_search.json`.
6. Runs a create+delete probe to capture `tests/fixtures/confluence_create_page_response.json` and similarly an update probe for `tests/fixtures/confluence_update_page_response.json`. Name the probe page `"a2atlassian fixture probe <timestamp>"` so it's obvious; delete it at the end of the recording run.

Use the existing anonymization helpers for account ids and user display names. Reuse the file-writing helper pattern (write JSON pretty-printed, drop any `_expandable` keys).

- [ ] **Step 3: Document env vars**

Update the usage comment at the top of `scripts/record_fixtures.py` to list the two new env vars.

- [ ] **Step 4: Run harness lint**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && make lint
```

Expected: pass. Recording itself is not run in CI — the script executes only when a human provides creds.

- [ ] **Step 5: Commit**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
git add scripts/record_fixtures.py
git commit -m "chore(fixtures): extend recorder with Confluence endpoints"
```

---

## Task 22 — README + CHANGELOG + version bump

**Files:**
- Modify: `pyproject.toml`
- Modify: `README.md`
- Modify or create: `CHANGELOG.md`

- [ ] **Step 1: Bump the version**

In `pyproject.toml`, change `version = "0.3.1"` to `version = "0.4.0"`.

- [ ] **Step 2: Update the README tool table**

Open `README.md` and find the Jira tool table. Add a "Confluence" section with four rows:

```markdown
## Confluence tools

| Tool                         | Purpose                                                     |
|------------------------------|-------------------------------------------------------------|
| confluence_get_page          | Fetch a page by id (body storage, version, space)           |
| confluence_get_page_children | List direct children of a page (paginated)                  |
| confluence_search            | CQL search; minimal per-match rows                          |
| confluence_upsert_pages      | Batch create-or-update with per-page status + partial-failure shape |
```

If the README has a "Scope" paragraph that says Confluence is unsupported, replace it with a line noting that Confluence support shipped in v0.4.0.

- [ ] **Step 3: CHANGELOG entry**

If `CHANGELOG.md` does not exist, create it with:

```markdown
# Changelog

## v0.4.0 — 2026-04-23

### Added
- Confluence domain: `confluence_get_page`, `confluence_get_page_children`, `confluence_search`, `confluence_upsert_pages`.
- Markdown → Confluence storage translator; recursive `<details>` → expand-macro translation.
- Per-page upsert with identity resolution (page_id → parent-scoped title match → space-root title match).
- Batch upsert returns `{succeeded, failed, summary}`; does not raise on partial failure.
- Page-level knobs on upsert: `labels`, `emoji`, `page_width`.
- `--enable confluence` flag; MCP server instructions updated to reflect Confluence scope.

### Changed
- `AtlassianClient` split into `AtlassianClientBase` + `JiraClient` (+ new `ConfluenceClient`). Existing Jira code continues to work; imports change from `a2atlassian.client.AtlassianClient` → `a2atlassian.jira_client.JiraClient`.

## v0.3.1
(previous releases)
```

If it already exists, insert the v0.4.0 block at the top.

- [ ] **Step 4: Commit**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
git add pyproject.toml README.md CHANGELOG.md
git commit -m "release: v0.4.0 — Confluence support"
```

---

## Task 23 — Final gate, merge, tag

- [ ] **Step 1: Full quality gate**

```bash
cd /Users/iorlas/Workspaces/a2atlassian && make check
```

Expected: all green — lint + test + coverage-diff ≥ 95% on the touched lines + security-audit. If coverage-diff fails on specific lines, add targeted tests (e.g. more translator edge cases or branches in `resolve_page_identity`) until it passes. Do **not** weaken the threshold.

- [ ] **Step 2: Fast-forward merge to main**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
git switch main
git merge --ff-only feat/v0.4.0-confluence
```

Expected: `Fast-forward` merge. If main has moved, rebase `feat/v0.4.0-confluence` onto main first (`git rebase main feat/v0.4.0-confluence`) and re-run `make check`.

- [ ] **Step 3: Tag and push**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
git tag v0.4.0
git push origin main --tags
```

Expected: push succeeds; CI (MCP registry publish via GitHub OIDC after PyPI) runs.

- [ ] **Step 4: Delete the feature branch**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
git branch -d feat/v0.4.0-confluence
git push origin --delete feat/v0.4.0-confluence
```

Expected: local and remote branches gone.

---

## Self-review checklist (run after finishing all tasks)

- [ ] Every spec Scope tool (`confluence_get_page`, `confluence_get_page_children`, `confluence_search`, `confluence_upsert_pages`) has a registration task and a functional test.
- [ ] Identity resolution precedence (page_id → parent-scoped → space-root) is covered by Task 12's six-case matrix.
- [ ] Partial-failure batch does not raise (Task 14 `test_partial_failure_does_not_raise`).
- [ ] `<details>` → expand macro re-parses body (Task 11 `test_details_contains_translated_table` + `test_nested_details`).
- [ ] Storage-format escape hatch bypasses translation (Task 13 `test_storage_bypasses_translator`).
- [ ] `--enable confluence` is recognized by `known_domains` (Task 19).
- [ ] Module boundary test confirms `ConfluenceClient` does not pull in Jira modules (Task 20).
- [ ] `AtlassianClient` shim is removed; no dangling imports remain (`grep -rn "AtlassianClient" src/ tests/ scripts/` returns empty after Task 4).
- [ ] README + CHANGELOG mention Confluence; `mcp_server.py` instructions no longer say "Jira only today".
- [ ] Final `make check` is green on the merge commit.
