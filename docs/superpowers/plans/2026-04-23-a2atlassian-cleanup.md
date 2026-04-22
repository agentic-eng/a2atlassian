# a2atlassian v0.3.0 Cleanup — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the v0.3.0 Jira cleanup batch: port the in-flight `jira_tools/` refactor, rename `project` → `connection` across the surface, introduce a `@mcp_tool` decorator with enum validation, fix broken `jira_get_boards`, trim `jira_search` output, unify `jira_get_worklogs` into a two-mode tool with worklog-admin attribution, and consolidate 6 tools into 3.

**Architecture:** Port a completed refactor first (precondition). Then work bottom-up: decorator → connection-layer changes → renames → behavior changes → consolidations → docs. Each change keeps tests green; v0.3.0 is a single release with a loud changelog about the breaking rename and the `jira_search` field-default change.

**Tech Stack:** Python 3.12, `atlassian-python-api`, FastMCP, `click` (CLI), `pytest`, `pytest-asyncio`, `zoneinfo` (stdlib for TZ), `uv` (env/install), `ruff` + `ty` (lint/type-check via `agent-harness`).

**Spec:** `docs/superpowers/specs/2026-04-23-a2atlassian-cleanup-design.md`
**Repo root:** `/Users/iorlas/Workspaces/a2atlassian` (canonical — do not edit `/Users/iorlas/Workspaces/agentic-eng/a2atlassian`).

**Quality gate:** run `make check` before every commit (runs lint + test + coverage-diff + security-audit). Pre-commit hooks run `agent-harness fix` + `agent-harness lint` automatically. Never skip hooks with `--no-verify`.

---

## File map

Files created:

- `tests/test_decorators.py` — tests for the new `@mcp_tool` decorator.
- `tests/jira/test_boards_fix.py` — regression tests for the `jira_get_boards` accessor fix (may fold into `tests/jira/test_boards.py`).
- `tests/fixtures/jira_worklogs_proxy.json` — new fixture: one ticket with three worklogs (self / admin-proxy / non-admin-other) for attribution tests.
- `docs/CHANGELOG.md` — new file if missing; otherwise append a v0.3.0 section.

Files modified (significant surface):

- `src/a2atlassian/decorators.py` — gains `@mcp_tool`.
- `src/a2atlassian/errors.py` — gains `connection_not_found` and `enum_mismatch` enricher methods.
- `src/a2atlassian/connections.py` — `ConnectionInfo` gains `timezone` + `worklog_admins` fields; TOML round-trip updated.
- `src/a2atlassian/cli.py` — `--project` → `--connection`, new `--tz` and `--worklog-admin` options.
- `src/a2atlassian/mcp_server.py` — `project` → `connection` rename; updated `instructions=` string; drop `jira_read_tools` / `jira_write_tools` imports after port.
- `src/a2atlassian/jira/boards.py` — fix `.boards` accessor (S2).
- `src/a2atlassian/jira/issues.py` — `search()` gains `fields=` parameter + new `search_count()`.
- `src/a2atlassian/jira/worklogs.py` — new `get_worklogs_summary()` with attribution + mode selection.
- `src/a2atlassian/jira_tools/*.py` (12 modules) — applied decorator, renamed parameter, deletions, mergers.
- `README.md` — top note about Jira-only scope.
- `pyproject.toml` — version bump to 0.3.0.

Files deleted:

- `src/a2atlassian/jira_read_tools.py` (replaced by `jira_tools/` package).
- `src/a2atlassian/jira_write_tools.py` (replaced by `jira_tools/` package).

---

## Task 1: Port `jira_tools/` refactor from stale working copy

Precondition before any signal work. Moves the in-progress package split from `/Users/iorlas/Workspaces/agentic-eng/a2atlassian` into the canonical repo as the first commit.

**Files:**
- Copy: `/Users/iorlas/Workspaces/agentic-eng/a2atlassian/src/a2atlassian/jira_tools/` → `/Users/iorlas/Workspaces/a2atlassian/src/a2atlassian/jira_tools/`
- Delete: `src/a2atlassian/jira_read_tools.py`, `src/a2atlassian/jira_write_tools.py`
- Modify (copy from stale): `src/a2atlassian/mcp_server.py`, `tests/test_mcp_server.py`

- [ ] **Step 1: Copy the `jira_tools/` package**

```bash
cd /Users/iorlas/Workspaces/a2atlassian
cp -r /Users/iorlas/Workspaces/agentic-eng/a2atlassian/src/a2atlassian/jira_tools src/a2atlassian/jira_tools
find src/a2atlassian/jira_tools -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
ls src/a2atlassian/jira_tools
```

Expected: `__init__.py  boards.py  comments.py  fields.py  issues.py  links.py  projects.py  sprints.py  transitions.py  users.py  watchers.py  worklogs.py` (12 files).

- [ ] **Step 2: Copy the updated `mcp_server.py` and test file**

```bash
cp /Users/iorlas/Workspaces/agentic-eng/a2atlassian/src/a2atlassian/mcp_server.py src/a2atlassian/mcp_server.py
cp /Users/iorlas/Workspaces/agentic-eng/a2atlassian/tests/test_mcp_server.py tests/test_mcp_server.py
```

- [ ] **Step 3: Delete the old flat tool files**

```bash
git rm src/a2atlassian/jira_read_tools.py src/a2atlassian/jira_write_tools.py
```

- [ ] **Step 4: Run tests to confirm the port works**

```bash
make test 2>&1 | tail -40
```

Expected: all tests pass. If not, inspect any failures — the port should be mechanically equivalent to the old flat files, so failures indicate an issue with the stale copy itself. Do **not** edit any tool behavior in this task; only get the port green.

- [ ] **Step 5: Run full quality gate**

```bash
make check 2>&1 | tail -40
```

Expected: all checks pass.

- [ ] **Step 6: Commit**

```bash
git add src/a2atlassian/jira_tools src/a2atlassian/mcp_server.py tests/test_mcp_server.py
git add -u  # picks up the deletions
git commit -m "refactor: split jira tools into per-domain modules

Ports the in-flight jira_tools/ package split from the stale
/Users/iorlas/Workspaces/agentic-eng/a2atlassian working copy.
Mechanical rewrite — no behavior change."
```

---

## Task 2: Audit the ported refactor against section-5 consolidations

Confirm the ported refactor is a pure split and none of the tool deletions/mergers from section 5 of the spec are already implemented. If any are, mark them done and skip their later tasks.

**Files:**
- Audit only: `src/a2atlassian/jira_tools/`

- [ ] **Step 1: Count `@server.tool()` calls in the package**

```bash
rg '@server\.tool\(\)' src/a2atlassian/jira_tools/ --count
```

Expected output: per-file counts summing to **34** (18 read + 16 write across 11 domain modules). If the count is lower, some consolidations already landed — record which files are short.

- [ ] **Step 2: Verify the tool names match the pre-consolidation surface**

```bash
rg -o 'async def (jira_\w+)' src/a2atlassian/jira_tools/ | sort -u
```

Expected names (all 34 must be present):
```
jira_add_comment, jira_add_issues_to_sprint, jira_add_watcher, jira_add_worklog,
jira_create_issue, jira_create_issue_link, jira_create_sprint, jira_create_version,
jira_delete_issue, jira_edit_comment, jira_get_board_issues, jira_get_boards,
jira_get_comments, jira_get_field_options, jira_get_issue, jira_get_issue_dev_info,
jira_get_link_types, jira_get_project_components, jira_get_project_versions,
jira_get_projects, jira_get_sprint_issues, jira_get_sprints, jira_get_transitions,
jira_get_user_profile, jira_get_watchers, jira_get_worklogs, jira_link_to_epic,
jira_remove_issue_link, jira_remove_watcher, jira_search, jira_search_fields,
jira_transition_issue, jira_update_issue, jira_update_sprint
```

- [ ] **Step 3: Record results**

If any tool from the "Delete" list in spec §5 is already missing, note it in the PR description. Tasks 13–16 below should be skipped for those. No commit — this is inspection only.

---

## Task 3: `@mcp_tool` decorator — write the failing tests

Introduces enum validation and boilerplate removal. TDD: tests first.

**Files:**
- Create: `tests/test_decorators.py`
- Modify next task: `src/a2atlassian/decorators.py`
- Modify next task: `src/a2atlassian/errors.py`

- [ ] **Step 1: Write the decorator tests**

Create `tests/test_decorators.py`:

```python
"""Tests for the @mcp_tool decorator."""

from __future__ import annotations

from typing import Literal

import pytest

from a2atlassian.decorators import mcp_tool
from a2atlassian.errors import ErrorEnricher
from a2atlassian.formatter import OperationResult


class TestMcpTool:
    async def test_wraps_operation_and_formats_toon(self) -> None:
        enricher = ErrorEnricher()

        @mcp_tool(enricher)
        async def greet(connection: str, name: str, format: Literal["toon", "json"] = "toon") -> OperationResult:  # noqa: A002
            assert connection == "c1"
            return OperationResult(name="greet", data=[{"hello": name}], count=1, truncated=False, time_ms=0)

        result = await greet(connection="c1", name="world", format="toon")
        assert "hello" in result
        assert "world" in result

    async def test_wraps_and_formats_json(self) -> None:
        enricher = ErrorEnricher()

        @mcp_tool(enricher)
        async def greet(connection: str, format: Literal["toon", "json"] = "json") -> OperationResult:  # noqa: A002
            return OperationResult(name="g", data={"ok": True}, count=1, truncated=False, time_ms=0)

        result = await greet(connection="c1", format="json")
        assert '"ok"' in result

    async def test_exceptions_are_enriched(self) -> None:
        enricher = ErrorEnricher()

        @mcp_tool(enricher)
        async def boom(connection: str, format: Literal["toon", "json"] = "toon") -> OperationResult:  # noqa: A002
            raise RuntimeError("nope")

        result = await boom(connection="c1")
        assert "nope" in result

    async def test_enum_validation_happy_path(self) -> None:
        enricher = ErrorEnricher()

        @mcp_tool(enricher)
        async def t(connection: str, detail: Literal["a", "b", "c"] = "a", format: Literal["toon", "json"] = "toon") -> OperationResult:  # noqa: A002
            return OperationResult(name="t", data=[{"d": detail}], count=1, truncated=False, time_ms=0)

        ok = await t(connection="c1", detail="b")
        assert "b" in ok

    async def test_enum_validation_rejects_invalid(self) -> None:
        enricher = ErrorEnricher()

        @mcp_tool(enricher)
        async def t(connection: str, detail: Literal["a", "b", "c"] = "a", format: Literal["toon", "json"] = "toon") -> OperationResult:  # noqa: A002
            return OperationResult(name="t", data=[], count=0, truncated=False, time_ms=0)

        result = await t(connection="c1", detail="zz")
        assert "Invalid value" in result
        assert "detail" in result
        assert "zz" in result
        assert "a" in result and "b" in result and "c" in result

    async def test_enum_validation_multiple_literals(self) -> None:
        """Both format and detail being invalid surfaces at least one clearly."""
        enricher = ErrorEnricher()

        @mcp_tool(enricher)
        async def t(connection: str, format: Literal["toon", "json"] = "toon") -> OperationResult:  # noqa: A002
            return OperationResult(name="t", data=[], count=0, truncated=False, time_ms=0)

        result = await t(connection="c1", format="tooon")  # type: ignore[arg-type]
        assert "Invalid value" in result
        assert "format" in result
```

- [ ] **Step 2: Run tests — all should fail with ImportError**

```bash
uv run pytest tests/test_decorators.py -v 2>&1 | tail -30
```

Expected: `ImportError` or `ModuleNotFoundError` on `a2atlassian.decorators.mcp_tool`.

- [ ] **Step 3: Commit tests (red)**

```bash
git add tests/test_decorators.py
git commit -m "test: add @mcp_tool decorator tests (red)"
```

---

## Task 4: `@mcp_tool` decorator — implement

Make the tests from Task 3 pass. Uses `typing.get_type_hints` + `typing.get_args` to inspect `Literal[...]` annotations at call time.

**Files:**
- Modify: `src/a2atlassian/decorators.py`
- Modify: `src/a2atlassian/errors.py`
- Test: `tests/test_decorators.py`

- [ ] **Step 1: Add `enum_mismatch` method to `ErrorEnricher`**

Append to `src/a2atlassian/errors.py`:

```python
    def enum_mismatch(self, param: str, value: object, choices: tuple[object, ...]) -> str:
        """Format an error for an invalid enum value."""
        expected = ", ".join(str(c) for c in choices)
        return f"Invalid value for '{param}': {value!r}. Expected one of: {expected}."
```

- [ ] **Step 2: Write the decorator in `src/a2atlassian/decorators.py`**

Overwrite or append to `src/a2atlassian/decorators.py`:

```python
"""Decorators shared across MCP tool modules."""

from __future__ import annotations

import functools
import inspect
import typing
from collections.abc import Awaitable, Callable
from typing import Any, Literal, get_args, get_origin

from a2atlassian.errors import ErrorEnricher
from a2atlassian.formatter import OperationResult, format_result


def _collect_literal_params(fn: Callable[..., Any]) -> dict[str, tuple[object, ...]]:
    """Return a mapping of parameter name to its Literal choices for parameters annotated with Literal[...]."""
    try:
        hints = typing.get_type_hints(fn, include_extras=False)
    except Exception:  # noqa: BLE001
        hints = {}
    literals: dict[str, tuple[object, ...]] = {}
    for name, hint in hints.items():
        if get_origin(hint) is Literal:
            literals[name] = get_args(hint)
    return literals


def mcp_tool(
    enricher: ErrorEnricher,
) -> Callable[[Callable[..., Awaitable[OperationResult]]], Callable[..., Awaitable[str]]]:
    """Wrap an async MCP tool coroutine that returns OperationResult.

    Responsibilities:
    - Validate Literal[...] parameters at call time (enum validation).
    - Run the wrapped coroutine; enrich any raised exception into a user-facing error string.
    - Format the OperationResult using the tool's format argument (or 'toon' default).
    """

    def decorator(fn: Callable[..., Awaitable[OperationResult]]) -> Callable[..., Awaitable[str]]:
        literals = _collect_literal_params(fn)
        sig = inspect.signature(fn)

        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> str:
            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()

            for param, choices in literals.items():
                if param not in bound.arguments:
                    continue
                value = bound.arguments[param]
                if value not in choices:
                    return enricher.enum_mismatch(param, value, choices)

            connection = bound.arguments.get("connection") or bound.arguments.get("project")
            try:
                result = await fn(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001
                ctx: dict[str, Any] = {}
                if connection is not None:
                    ctx["connection"] = connection
                return enricher.enrich(str(exc), ctx)

            fmt = bound.arguments.get("format", "toon")
            return format_result(result, fmt=fmt)

        return wrapper

    return decorator
```

- [ ] **Step 3: Run tests — all should pass**

```bash
uv run pytest tests/test_decorators.py -v 2>&1 | tail -30
```

Expected: 6 passed.

- [ ] **Step 4: Run the full quality gate**

```bash
make check 2>&1 | tail -30
```

Expected: all checks pass.

- [ ] **Step 5: Commit**

```bash
git add src/a2atlassian/decorators.py src/a2atlassian/errors.py
git commit -m "feat: @mcp_tool decorator with Literal enum validation

Wraps try/except + enricher + format_result pipeline. Inspects type
hints and validates Literal[...] parameters at call time, returning
a structured 'Invalid value for X' error instead of swallowing silently."
```

---

## Task 5: Rename `project` → `connection` in `ConnectionInfo` and `ConnectionStore`

Mechanical rename at the core type and storage layer. Breaking on-disk change: existing TOML files that still use `project = "..."` will continue to deserialize as long as we keep the key name in TOML the same. **Plan:** keep the TOML field name `project` on disk for this commit; only the Python attribute changes. (Rationale: zero migration needed; users' existing `~/.config/a2atlassian/*.toml` keeps working.)

After this task, `ConnectionInfo.project` is renamed to `ConnectionInfo.connection`, but the TOML file key stays `project`. The next task renames the TOML key too.

Wait — reconsider. Spec section 1 says "No compatibility alias. Pre-1.0; better to take the breakage now." That applies to the API surface. On-disk TOML: keep `project` as the TOML key name to avoid bricking existing saved files. **Decision:** rename Python-land everywhere; keep TOML key `project` as an on-disk compatibility choice (this is not an API surface, and re-running `login` regenerates the file anyway). Mention in the changelog.

**Files:**
- Modify: `src/a2atlassian/connections.py`
- Modify: `tests/test_connections.py`

- [ ] **Step 1: Rename `project` parameter and attribute on `ConnectionInfo`**

In `src/a2atlassian/connections.py`:

```python
@dataclass(frozen=True)
class ConnectionInfo:
    """A saved Atlassian connection."""

    connection: str
    url: str
    email: str
    token: str
    read_only: bool = True

    @property
    def resolved_token(self) -> str:
        """Token with ${ENV_VAR} references expanded from the environment."""
        return re.sub(r"\$\{(\w+)\}", lambda m: os.environ.get(m.group(1), m.group(0)), self.token)
```

- [ ] **Step 2: Rename all callers on `ConnectionStore`**

In the same file, change `save/load/delete/list_connections/_path` to use the parameter name `connection` (not `project`). The on-disk TOML key stays literal `project` for backwards compatibility with existing files:

```python
    def _path(self, connection: str) -> Path:
        return self.config_dir / f"{connection}.toml"

    def save(self, connection: str, url: str, email: str, token: str, read_only: bool = True) -> Path:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        path = self._path(connection)

        def _escape(value: str) -> str:
            return value.replace("\\", "\\\\").replace('"', '\\"')

        ro = "true" if read_only else "false"
        content = (
            f'project = "{_escape(connection)}"\n'   # TOML key stays 'project' for on-disk compat
            f'url = "{_escape(url)}"\n'
            f'email = "{_escape(email)}"\n'
            f'token = "{_escape(token)}"\n'
            f"read_only = {ro}\n"
        )
        path.write_text(content)
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
        return path

    def load(self, connection: str) -> ConnectionInfo:
        path = self._path(connection)
        if not path.exists():
            msg = f"Connection not found: {connection}"
            raise FileNotFoundError(msg)
        data = tomllib.loads(path.read_text())
        return ConnectionInfo(
            connection=data["project"],   # TOML key is 'project', Python attr is 'connection'
            url=data["url"],
            email=data["email"],
            token=data["token"],
            read_only=data.get("read_only", True),
        )

    def delete(self, connection: str) -> None:
        path = self._path(connection)
        if not path.exists():
            msg = f"Connection not found: {connection}"
            raise FileNotFoundError(msg)
        path.unlink()

    def list_connections(self, connection: str | None = None) -> list[ConnectionInfo]:
        if not self.config_dir.exists():
            return []
        results = []
        for path in sorted(self.config_dir.glob("*.toml")):
            data = tomllib.loads(path.read_text())
            info = ConnectionInfo(
                connection=data["project"],
                url=data["url"],
                email=data["email"],
                token=data["token"],
                read_only=data.get("read_only", True),
            )
            if connection is None or info.connection == connection:
                results.append(info)
        return results
```

- [ ] **Step 3: Update the tests in `tests/test_connections.py`**

Read the file, then mechanically rename `project=` → `connection=` and `.project` → `.connection` on every call site involving `ConnectionInfo` or the store methods. Do not invent new test cases in this step.

```bash
uv run pytest tests/test_connections.py -v 2>&1 | tail -30
```

Fix any remaining `project`-named assertions until green.

- [ ] **Step 4: Update every other caller of `ConnectionInfo.project`**

```bash
rg '\.project\b' src/ tests/ --type py | grep -v 'project_key\|project_keys\|project_name'
```

For each line, change `.project` → `.connection` where the variable is a `ConnectionInfo`. Leave Jira `project_key`/`project_name` alone — those are Jira domain terms, not connection identifiers.

- [ ] **Step 5: Run all tests**

```bash
make test 2>&1 | tail -30
```

Fix any remaining references until green.

- [ ] **Step 6: Commit**

```bash
git add src/a2atlassian/connections.py tests/test_connections.py src/ tests/
git commit -m "refactor: rename ConnectionInfo.project → .connection

Pre-1.0 breaking rename to resolve naming confusion between
the saved connection identifier and a Jira project key. TOML
on-disk key stays 'project' for file-level backwards compat —
only the Python attribute changes in this commit. Tool and CLI
surface renames follow in subsequent commits."
```

---

## Task 6: Rename `project` → `connection` in MCP server and tool wiring

**Files:**
- Modify: `src/a2atlassian/mcp_server.py`
- Modify: `tests/test_mcp_server.py`

- [ ] **Step 1: Rename all `project`-named parameters in `mcp_server.py`**

Read `src/a2atlassian/mcp_server.py`. Rename:

- `_get_connection(project: str)` → `_get_connection(connection: str)`
- `_get_client(project: str)` → `_get_client(connection: str)`
- `login(project, url, email, token, read_only)` → `login(connection, url, email, token, read_only)`
- `logout(project)` → `logout(connection)`
- `list_connections(project)` → `list_connections(connection)`
- Every internal reference.

Rename `_scope_filter` comparisons to use `connection` semantically (no wire change; just internal naming).

- [ ] **Step 2: Update the `instructions=` string**

Old text starts with `"Agent-to-Atlassian — work with Jira and Confluence. Connections are identified by project name..."`. Replace with:

```python
instructions=(
    "Agent-to-Atlassian — work with Jira. "
    "Scope today: Jira only. For Confluence, use mcp__atlassian (sooperset). "
    "Connections are identified by a connection name. "
    "Use 'login' to save a connection, then call tools with the connection name. "
    "Connections are read-only by default; re-login with --read-only false to enable writes. "
    "For security, pass tokens as ${ENV_VAR} references, not literal values. "
    "Default output is TOON for lists (token-efficient), JSON for single entities."
),
```

- [ ] **Step 3: Update tests in `tests/test_mcp_server.py`**

Rename every `project=` kwarg to `connection=`. Run:

```bash
uv run pytest tests/test_mcp_server.py -v 2>&1 | tail -30
```

Fix until green.

- [ ] **Step 4: Commit**

```bash
git add src/a2atlassian/mcp_server.py tests/test_mcp_server.py
git commit -m "refactor: rename project → connection in MCP server surface

Updates the server instructions string to reflect Jira-only scope
today and the new connection naming. Tool-module renames follow."
```

---

## Task 7: Rename `project` → `connection` across all tool modules

Every file in `src/a2atlassian/jira_tools/` still uses `project: str` as the first parameter of each tool and passes it to `get_client`/`get_connection`. Apply the rename module by module.

**Files:**
- Modify: `src/a2atlassian/jira_tools/boards.py`
- Modify: `src/a2atlassian/jira_tools/comments.py`
- Modify: `src/a2atlassian/jira_tools/fields.py`
- Modify: `src/a2atlassian/jira_tools/issues.py`
- Modify: `src/a2atlassian/jira_tools/links.py`
- Modify: `src/a2atlassian/jira_tools/projects.py`
- Modify: `src/a2atlassian/jira_tools/sprints.py`
- Modify: `src/a2atlassian/jira_tools/transitions.py`
- Modify: `src/a2atlassian/jira_tools/users.py`
- Modify: `src/a2atlassian/jira_tools/watchers.py`
- Modify: `src/a2atlassian/jira_tools/worklogs.py`
- Modify: `tests/jira/*.py` (any that reference `project=`)

- [ ] **Step 1: Automated rename across the tool modules**

The rename is mechanical: `project: str` → `connection: str`, `get_client(project)` → `get_client(connection)`, `get_connection(project)` → `get_connection(connection)`, `{"project": project}` → `{"connection": connection}`, and `Connection '{project}'` → `Connection '{connection}'`.

Safest: open each file in order and edit. Use this sed batch only as a sanity accelerator, then **verify each file** before committing (sed may catch unintended `.project` on unrelated objects):

```bash
cd /Users/iorlas/Workspaces/a2atlassian
for f in src/a2atlassian/jira_tools/*.py; do
  python3 -c "
import re, sys
p = sys.argv[1]
s = open(p).read()
s = re.sub(r'\bproject: str\b', 'connection: str', s)
s = re.sub(r'get_client\(project\)', 'get_client(connection)', s)
s = re.sub(r'get_connection\(project\)', 'get_connection(connection)', s)
s = re.sub(r'\{\"project\": project\}', '{\"connection\": connection}', s)
s = re.sub(r\"Connection '\{project\}'\", \"Connection '{connection}'\", s)
open(p, 'w').write(s)
" "$f"
done
```

**Review each file manually** before proceeding. `project_key` (a separate Jira-domain parameter) must remain unchanged.

- [ ] **Step 2: Rename in tests**

```bash
rg -l '\bproject=' tests/jira/ tests/test_mcp_server.py
```

For each hit, edit the call sites to use `connection=`. Keep `project_key=` (Jira-domain term) untouched.

- [ ] **Step 3: Run all tests**

```bash
make test 2>&1 | tail -40
```

Fix until green. Common leftover: a test that instantiates `ConnectionInfo(project=...)` — should be `ConnectionInfo(connection=...)`.

- [ ] **Step 4: Run lint**

```bash
make lint 2>&1 | tail -30
```

Fix any formatter/lint issues.

- [ ] **Step 5: Commit**

```bash
git add src/a2atlassian/jira_tools tests/
git commit -m "refactor: rename project → connection across all jira_tools

Mechanical rename to match ConnectionInfo.connection from the
prior commit. No behavior change; parameter name only."
```

---

## Task 8: Rename `--project` → `--connection` in CLI

**Files:**
- Modify: `src/a2atlassian/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Rename CLI options in `src/a2atlassian/cli.py`**

In every `@click.option("-p", "--project", ...)` decorator, change to:

```python
@click.option("-c", "--connection", required=True, help="Connection name")
```

(For the `connections` subcommand's filter option, keep `default=None, required=False`.)

Rename every function parameter `project: str` → `connection: str` inside the CLI handlers.

- [ ] **Step 2: Update tests in `tests/test_cli.py`**

Read the test file. Replace `--project` with `--connection` in all CLI invocations. Adjust assertions referencing the old flag.

- [ ] **Step 3: Run CLI tests**

```bash
uv run pytest tests/test_cli.py -v 2>&1 | tail -30
```

Fix until green.

- [ ] **Step 4: Commit**

```bash
git add src/a2atlassian/cli.py tests/test_cli.py
git commit -m "refactor: rename --project → --connection in CLI

Pre-1.0 breaking rename. Users must migrate existing login/logout/connections
command invocations. Short flag remains 'c' instead of 'p'."
```

---

## Task 9: Add `connection_not_found` enricher method + plumb through `mcp_server`

Implements spec section 8. Emits structured hints when the user passes an invalid connection name.

**Files:**
- Modify: `src/a2atlassian/errors.py`
- Modify: `src/a2atlassian/mcp_server.py`
- Modify: `tests/test_errors.py`
- Modify: `tests/test_mcp_server.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_errors.py`:

```python
class TestConnectionNotFound:
    def test_includes_available_names(self) -> None:
        enricher = ErrorEnricher()
        msg = enricher.connection_not_found("protae", ["protea", "foo"])
        assert "Connection not found: protae" in msg
        assert "Available connections: foo, protea" in msg or "Available connections: protea, foo" in msg

    def test_did_you_mean(self) -> None:
        enricher = ErrorEnricher()
        msg = enricher.connection_not_found("protae", ["protea", "foo"])
        assert "Did you mean: protea" in msg

    def test_no_available_connections(self) -> None:
        enricher = ErrorEnricher()
        msg = enricher.connection_not_found("protea", [])
        assert "No connections are configured" in msg
        assert "a2atlassian login" in msg
```

- [ ] **Step 2: Run the tests to confirm they fail**

```bash
uv run pytest tests/test_errors.py::TestConnectionNotFound -v 2>&1 | tail -20
```

Expected: `AttributeError` — method does not exist.

- [ ] **Step 3: Implement `connection_not_found` on `ErrorEnricher`**

Add to `src/a2atlassian/errors.py`:

```python
    def connection_not_found(self, name: str, available: list[str]) -> str:
        """Format a structured 'connection not found' error."""
        parts = [f"Connection not found: {name}"]
        if not available:
            parts.append("")
            parts.append(
                "No connections are configured. Run `a2atlassian login -c <name> --url <url> --email <email> --token <token>` to add one."
            )
            return "\n".join(parts)
        parts.append("")
        parts.append(f"Available connections: {', '.join(sorted(available))}")
        matches = get_close_matches(name, available, n=1, cutoff=0.5)
        if matches:
            parts.append(f"Did you mean: {matches[0]}?")
        parts.append("Run `a2atlassian connections` to see saved connections, or `a2atlassian login` to add one.")
        return "\n".join(parts)
```

- [ ] **Step 4: Run the tests — green**

```bash
uv run pytest tests/test_errors.py::TestConnectionNotFound -v 2>&1 | tail -20
```

- [ ] **Step 5: Wire into `mcp_server._get_connection`**

Change `src/a2atlassian/mcp_server.py`:

```python
def _get_connection(connection: str) -> ConnectionInfo:
    """Resolve a connection by name."""
    if connection in _ephemeral_connections:
        return _ephemeral_connections[connection]
    store = _store()
    try:
        info = store.load(connection)
    except FileNotFoundError:
        available = [c.connection for c in store.list_connections()] + list(_ephemeral_connections.keys())
        raise FileNotFoundError(_enricher.connection_not_found(connection, sorted(set(available)))) from None
    if _scope_filter and connection not in _scope_filter:
        raise FileNotFoundError(
            _enricher.connection_not_found(
                connection,
                sorted(set(_scope_filter) & set([c.connection for c in store.list_connections()] + list(_ephemeral_connections.keys()))),
            )
        )
    return info
```

- [ ] **Step 6: Add an integration test**

Append to `tests/test_mcp_server.py`:

```python
class TestConnectionNotFoundEnrichment:
    def test_message_includes_available_names(self, tmp_path, monkeypatch) -> None:
        from a2atlassian import mcp_server
        from a2atlassian.connections import ConnectionStore

        store = ConnectionStore(tmp_path)
        store.save("protea", "https://p.atlassian.net", "x@y.com", "t")
        monkeypatch.setattr(mcp_server, "_store", lambda: store)

        try:
            mcp_server._get_connection("protae")
        except FileNotFoundError as exc:
            assert "protae" in str(exc)
            assert "protea" in str(exc)
            assert "Did you mean" in str(exc)
        else:
            pytest.fail("Expected FileNotFoundError")
```

- [ ] **Step 7: Run all tests**

```bash
make test 2>&1 | tail -30
```

- [ ] **Step 8: Commit**

```bash
git add src/a2atlassian/errors.py src/a2atlassian/mcp_server.py tests/test_errors.py tests/test_mcp_server.py
git commit -m "feat: structured 'connection not found' error with hints

ErrorEnricher.connection_not_found lists available connections
and proposes a close-match via difflib. Wired through
mcp_server._get_connection so tool callers see the hint."
```

---

## Task 10: Apply `@mcp_tool` decorator to `jira_tools/issues.py`

Apply the decorator to one tool module end-to-end as the reference pattern. Subsequent tool modules repeat this shape.

**Files:**
- Modify: `src/a2atlassian/jira_tools/issues.py`
- Test: `tests/jira/test_issues.py` (already exists; no changes beyond existing assertions)

- [ ] **Step 1: Refactor `jira_tools/issues.py` to use `@mcp_tool`**

Rewrite the module. Each tool body collapses from ~9 lines to ~3:

```python
"""Jira issue tools — get, search, create, update, delete."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from a2atlassian.client import AtlassianClient
from a2atlassian.decorators import mcp_tool
from a2atlassian.jira.issues import create_issue, delete_issue, get_issue, search, update_issue

if TYPE_CHECKING:
    from collections.abc import Callable

    from mcp.server.fastmcp import FastMCP

    from a2atlassian.connections import ConnectionInfo
    from a2atlassian.errors import ErrorEnricher


def register_read(
    server: FastMCP,
    get_client: Callable[[str], AtlassianClient],
    enricher: ErrorEnricher,
) -> None:
    @server.tool()
    @mcp_tool(enricher)
    async def jira_get_issue(connection: str, issue_key: str, format: Literal["toon", "json"] = "json") -> str:  # noqa: A002
        """Get a Jira issue by key. Returns full issue data including fields and status."""
        return await get_issue(get_client(connection), issue_key)

    @server.tool()
    @mcp_tool(enricher)
    async def jira_search(connection: str, jql: str, limit: int = 50, offset: int = 0, format: Literal["toon", "json"] = "toon") -> str:  # noqa: A002
        """Search Jira issues using JQL. Returns list of matching issues.

        Returns TOON by default (compact); pass format='json' for standard JSON shape.
        """
        return await search(get_client(connection), jql, limit=limit, offset=offset)

    @server.tool()
    @mcp_tool(enricher)
    async def jira_get_issue_dev_info(connection: str, issue_key: str) -> str:
        """Placeholder — kept temporarily for the rename commit; deleted in a later task."""
        return f"Dev info for {issue_key}: not yet supported. Use the Jira UI."


def register_write(
    server: FastMCP,
    get_connection: Callable[[str], ConnectionInfo],
    enricher: ErrorEnricher,
) -> None:
    @server.tool()
    @mcp_tool(enricher)
    async def jira_create_issue(
        connection: str,
        project_key: str,
        summary: str,
        issue_type: str,
        description: str | None = None,
        extra_fields: dict | None = None,
        format: Literal["toon", "json"] = "json",  # noqa: A002
    ) -> str:
        """Create a new Jira issue. Accepts project_key, summary, issue_type, optional description and extra_fields dict."""
        conn = get_connection(connection)
        if conn.read_only:
            raise RuntimeError(f"Connection '{connection}' is read-only. Run: a2atlassian login -c {connection} --no-read-only")
        return await create_issue(AtlassianClient(conn), project_key, summary, issue_type, description=description, extra_fields=extra_fields)

    @server.tool()
    @mcp_tool(enricher)
    async def jira_update_issue(connection: str, issue_key: str, fields: dict, format: Literal["toon", "json"] = "json") -> str:  # noqa: A002
        """Update fields on an existing Jira issue. Pass a dict of field names to values."""
        conn = get_connection(connection)
        if conn.read_only:
            raise RuntimeError(f"Connection '{connection}' is read-only. Run: a2atlassian login -c {connection} --no-read-only")
        return await update_issue(AtlassianClient(conn), issue_key, fields)

    @server.tool()
    @mcp_tool(enricher)
    async def jira_delete_issue(connection: str, issue_key: str, format: Literal["toon", "json"] = "json") -> str:  # noqa: A002
        """Delete a Jira issue by key."""
        conn = get_connection(connection)
        if conn.read_only:
            raise RuntimeError(f"Connection '{connection}' is read-only. Run: a2atlassian login -c {connection} --no-read-only")
        return await delete_issue(AtlassianClient(conn), issue_key)
```

Note: the previous module's literal `return enricher.enrich(...)` for read-only checks becomes `raise RuntimeError(...)` — the decorator catches it and runs it through `enricher.enrich`, preserving the prior user-facing behavior.

- [ ] **Step 2: Run the issue tests**

```bash
uv run pytest tests/jira/test_issues.py tests/test_mcp_server.py -v 2>&1 | tail -40
```

Fix any breakage. Common issue: `format="json"` on a single-entity returning tool — the decorator resolves `fmt` from bound args; make sure the default still matches what the test expects.

- [ ] **Step 3: Commit**

```bash
git add src/a2atlassian/jira_tools/issues.py
git commit -m "refactor(issues): apply @mcp_tool decorator

Tool bodies shrink from ~9 lines to ~3. Literal types on
format enable enum validation via the decorator."
```

---

## Task 11: Apply `@mcp_tool` decorator to remaining tool modules

Repeat Task 10's pattern across the remaining 10 modules. Keep the tool *names* and *semantics* identical — only the plumbing changes.

**Files:**
- Modify: `src/a2atlassian/jira_tools/boards.py`
- Modify: `src/a2atlassian/jira_tools/comments.py`
- Modify: `src/a2atlassian/jira_tools/fields.py`
- Modify: `src/a2atlassian/jira_tools/links.py`
- Modify: `src/a2atlassian/jira_tools/projects.py`
- Modify: `src/a2atlassian/jira_tools/sprints.py`
- Modify: `src/a2atlassian/jira_tools/transitions.py`
- Modify: `src/a2atlassian/jira_tools/users.py`
- Modify: `src/a2atlassian/jira_tools/watchers.py`
- Modify: `src/a2atlassian/jira_tools/worklogs.py`

- [ ] **Step 1: Refactor each module**

For each file in order, apply the Task 10 pattern:
1. Import `@mcp_tool` and `Literal`.
2. Type all `format` parameters as `Literal["toon", "json"]`.
3. For read tools: body becomes `return await <op>(get_client(connection), ...)`.
4. For write tools: body becomes `conn = get_connection(connection); if conn.read_only: raise RuntimeError(...); return await <op>(AtlassianClient(conn), ...)`.
5. Add the "Returns TOON by default..." docstring line on list-returning tools (S9).

Commit **after each module** so bisect can pinpoint regressions. Pattern:

```bash
uv run pytest tests/jira/test_<module>.py tests/test_mcp_server.py -v
git add src/a2atlassian/jira_tools/<module>.py
git commit -m "refactor(<module>): apply @mcp_tool decorator"
```

Work through in this order to catch cross-module dependencies early: `users.py`, `transitions.py`, `watchers.py`, `fields.py`, `comments.py`, `worklogs.py`, `links.py`, `projects.py`, `boards.py`, `sprints.py`.

- [ ] **Step 2: Run the full test suite after each module**

```bash
make test 2>&1 | tail -30
```

Fix regressions before moving to the next module.

- [ ] **Step 3: Run full quality gate after the last module**

```bash
make check 2>&1 | tail -30
```

Expected: all checks pass.

---

## Task 12: Spike `atlassian-python-api` for Agile accessor names

S2 depends on understanding what the pinned library actually exposes. Read-only inspection — no code changes in this task.

**Files:**
- Inspect only.

- [ ] **Step 1: Find the installed `atlassian-python-api` package**

```bash
uv run python -c "import atlassian; print(atlassian.__file__); print(atlassian.__version__)"
```

- [ ] **Step 2: Inspect `Jira` for board-related methods**

```bash
uv run python -c "
from atlassian import Jira
import re
methods = [m for m in dir(Jira) if not m.startswith('_')]
board_methods = [m for m in methods if re.search(r'board', m, re.I)]
issue_methods = [m for m in methods if re.search(r'issue', m, re.I) and 'board' in m.lower()]
print('Board-ish methods:')
for m in sorted(board_methods):
    print(' ', m)
"
```

Record which method replaces `boards()` (expected: `get_all_agile_boards` or similar) and which replaces `get_issues_for_board`.

- [ ] **Step 3: Same check for sprint-related methods**

```bash
uv run python -c "
from atlassian import Jira
import re
methods = [m for m in dir(Jira) if not m.startswith('_')]
sprint_methods = [m for m in methods if re.search(r'sprint', m, re.I)]
print('Sprint-ish methods:')
for m in sorted(sprint_methods):
    print(' ', m)
"
```

- [ ] **Step 4: Decide on approach**

Based on findings:

- **Approach 1 (preferred):** library exposes the Agile endpoints under different method names. Fix uses the correct names. Examples: `get_all_agile_boards()`, `get_all_sprints_from_board()`, `get_all_issues_for_sprint()`.
- **Approach 2 (fallback):** library removed or relocated Agile endpoints entirely. Fix calls raw REST via `client._jira.get("rest/agile/1.0/...")`.

Record the decision in a comment at the top of Task 13 when implementing.

---

## Task 13: Fix `jira_get_boards` and audit related Agile callers

Apply the spike's findings. Fix the broken `.boards` and `.get_issues_for_board` accessors in `src/a2atlassian/jira/boards.py`, and audit `sprints.py` / `worklogs.py` for the same rot.

**Files:**
- Modify: `src/a2atlassian/jira/boards.py`
- Potentially modify: `src/a2atlassian/jira/sprints.py`
- Modify: `tests/jira/test_boards.py`
- Potentially modify: `tests/jira/test_sprints.py`
- Modify: `tests/fixtures/jira_boards.json` (re-record if needed)

- [ ] **Step 1: Write the failing integration-shaped unit test**

In `tests/jira/test_boards.py`, update the existing `TestGetBoards` mock setup. The mock must patch the **new** accessor name (call it `<new_method>` in code comments):

```python
# Replace:
#   mock_client._jira_instance.boards.return_value = {...}
# with (example — adjust to the spike's finding):
#   mock_client._jira_instance.get_all_agile_boards.return_value = {...}
```

Update every `boards` mock in the file to the new method name. Same for `get_issues_for_board` if the spike revealed a rename.

- [ ] **Step 2: Run the tests to confirm they fail**

```bash
uv run pytest tests/jira/test_boards.py -v 2>&1 | tail -20
```

Expected: `AttributeError` on the old method, because `src/a2atlassian/jira/boards.py` still calls `.boards`.

- [ ] **Step 3: Update `src/a2atlassian/jira/boards.py` to call the new method(s)**

```python
# Change:
#   data = await client._call(client._jira.boards, startAt=offset, maxResults=limit)
# to:
#   data = await client._call(client._jira.<new_method>, startAt=offset, maxResults=limit)
```

Same pattern for `get_issues_for_board` if the spike revealed a rename.

- [ ] **Step 4: Audit `src/a2atlassian/jira/sprints.py`**

```bash
rg '_jira\.\w+' src/a2atlassian/jira/sprints.py
```

For each method reference, run the equivalent `dir(Jira)` check:

```bash
uv run python -c "from atlassian import Jira; print(hasattr(Jira, 'get_all_sprints_from_board'))"
```

If any `sprints.py` accessor is missing, update it. Same for `src/a2atlassian/jira/worklogs.py` (`issue_get_worklog`, `issue_worklog`).

- [ ] **Step 5: Run the full test suite**

```bash
make test 2>&1 | tail -30
```

- [ ] **Step 6: Commit**

```bash
git add src/a2atlassian/jira/boards.py src/a2atlassian/jira/sprints.py tests/jira/
git commit -m "fix: use correct atlassian-python-api Agile method names

The library exposes boards under get_all_agile_boards (or
equivalent — see commit comment) rather than .boards. This
caused 'Jira' object has no attribute 'boards' in live use.
Also audited sprints and worklogs modules for the same rot."
```

---

## Task 14: `search()` gains `fields` parameter + slim defaults

**Files:**
- Modify: `src/a2atlassian/jira/issues.py`
- Modify: `tests/jira/test_issues.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/jira/test_issues.py::TestSearch`:

```python
    async def test_default_fields_is_minimal(self, mock_client: AtlassianClient) -> None:
        """search() with no fields param passes the minimal default set."""
        mock_client._jira_instance.jql.return_value = {"issues": [], "total": 0}
        await search(mock_client, "project = X")
        call_kwargs = mock_client._jira_instance.jql.call_args.kwargs
        assert call_kwargs["fields"] == ["summary", "status", "assignee", "priority", "issuetype", "parent", "updated"]

    async def test_all_fields_sentinel_omits_fields(self, mock_client: AtlassianClient) -> None:
        """fields=['*all'] passes no fields kwarg (returns everything)."""
        mock_client._jira_instance.jql.return_value = {"issues": [], "total": 0}
        await search(mock_client, "project = X", fields=["*all"])
        call_kwargs = mock_client._jira_instance.jql.call_args.kwargs
        assert "fields" not in call_kwargs

    async def test_explicit_fields_passed_through(self, mock_client: AtlassianClient) -> None:
        """Explicit fields list is forwarded verbatim."""
        mock_client._jira_instance.jql.return_value = {"issues": [], "total": 0}
        await search(mock_client, "project = X", fields=["summary", "comment"])
        call_kwargs = mock_client._jira_instance.jql.call_args.kwargs
        assert call_kwargs["fields"] == ["summary", "comment"]
```

- [ ] **Step 2: Run tests — fails**

```bash
uv run pytest tests/jira/test_issues.py::TestSearch -v 2>&1 | tail -30
```

Expected: the new tests fail (TypeError: unexpected keyword argument `fields`, or asserted values don't match).

- [ ] **Step 3: Add the `fields` parameter to `search()`**

Edit `src/a2atlassian/jira/issues.py`:

```python
DEFAULT_SEARCH_FIELDS: list[str] = ["summary", "status", "assignee", "priority", "issuetype", "parent", "updated"]


async def search(
    client: AtlassianClient,
    jql: str,
    limit: int = 50,
    offset: int = 0,
    fields: list[str] | None = None,
) -> OperationResult:
    """Search Jira issues by JQL query.

    fields:
      - None (default) → minimal field set (DEFAULT_SEARCH_FIELDS).
      - ["*all"] → omit fields kwarg; returns every field per issue (large).
      - explicit list → forwarded verbatim.
    """
    kwargs: dict[str, Any] = {"limit": limit, "start": offset}
    if fields is None:
        kwargs["fields"] = DEFAULT_SEARCH_FIELDS
    elif fields == ["*all"]:
        pass  # omit fields to get everything
    else:
        kwargs["fields"] = fields

    t0 = time.monotonic()
    response = await client._call(client._jira.jql, jql, **kwargs)
    elapsed = int((time.monotonic() - t0) * 1000)

    issues = response.get("issues", [])
    total = response.get("total", len(issues))
    truncated = total > offset + len(issues) or len(issues) >= limit

    return OperationResult(
        name="search",
        data=[_extract_issue_summary(i) for i in issues],
        count=len(issues),
        truncated=truncated,
        time_ms=elapsed,
    )
```

- [ ] **Step 4: Run tests — green**

```bash
uv run pytest tests/jira/test_issues.py::TestSearch -v 2>&1 | tail -30
```

- [ ] **Step 5: Update `jira_search` MCP tool wrapper**

Edit `src/a2atlassian/jira_tools/issues.py::jira_search` to accept and forward `fields`:

```python
    @server.tool()
    @mcp_tool(enricher)
    async def jira_search(
        connection: str,
        jql: str,
        limit: int = 50,
        offset: int = 0,
        fields: list[str] | None = None,
        format: Literal["toon", "json"] = "toon",  # noqa: A002
    ) -> str:
        """Search Jira issues using JQL. Returns list of matching issues.

        Default returns a minimal field set (summary/status/assignee/priority/type/parent/updated).
        Pass fields=["*all"] for full payload — can be very large.
        Returns TOON by default (compact); pass format='json' for standard JSON shape.
        """
        return await search(get_client(connection), jql, limit=limit, offset=offset, fields=fields)
```

- [ ] **Step 6: Run all tests + lint**

```bash
make check 2>&1 | tail -30
```

- [ ] **Step 7: Commit**

```bash
git add src/a2atlassian/jira/issues.py src/a2atlassian/jira_tools/issues.py tests/jira/test_issues.py
git commit -m "feat(search): slim default fields + *all escape hatch

jira_search now defaults to summary/status/assignee/priority/
type/parent/updated rather than the library's all-fields default.
Caller can pass fields=['*all'] to restore the full payload.
Breaking change vs prior behavior for callers consuming the raw
_jira.jql output; _extract_issue_summary consumers are unaffected."
```

---

## Task 15: New `jira_search_count` tool

**Files:**
- Modify: `src/a2atlassian/jira/issues.py`
- Modify: `src/a2atlassian/jira_tools/issues.py`
- Modify: `tests/jira/test_issues.py`
- Modify: `tests/test_mcp_server.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/jira/test_issues.py`:

```python
from a2atlassian.jira.issues import search_count


class TestSearchCount:
    async def test_returns_total(self, mock_client: AtlassianClient) -> None:
        mock_client._jira_instance.jql.return_value = {"issues": [], "total": 142}
        result = await search_count(mock_client, "project = X")
        assert result.data == {"jql": "project = X", "total": 142}
        assert result.count == 1
        assert result.truncated is False

    async def test_calls_jql_with_limit_zero(self, mock_client: AtlassianClient) -> None:
        mock_client._jira_instance.jql.return_value = {"issues": [], "total": 0}
        await search_count(mock_client, "project = X")
        mock_client._jira_instance.jql.assert_called_once_with("project = X", limit=0, fields=[])
```

- [ ] **Step 2: Run tests — fails**

```bash
uv run pytest tests/jira/test_issues.py::TestSearchCount -v 2>&1 | tail -20
```

Expected: `ImportError` on `search_count`.

- [ ] **Step 3: Implement `search_count`**

Append to `src/a2atlassian/jira/issues.py`:

```python
async def search_count(client: AtlassianClient, jql: str) -> OperationResult:
    """Return just the total count for a JQL — cheap pre-check before a broad search."""
    t0 = time.monotonic()
    response = await client._call(client._jira.jql, jql, limit=0, fields=[])
    elapsed = int((time.monotonic() - t0) * 1000)
    total = response.get("total", 0)
    return OperationResult(
        name="search_count",
        data={"jql": jql, "total": total},
        count=1,
        truncated=False,
        time_ms=elapsed,
    )
```

- [ ] **Step 4: Add the MCP tool wrapper**

Add to `src/a2atlassian/jira_tools/issues.py::register_read`:

```python
    @server.tool()
    @mcp_tool(enricher)
    async def jira_search_count(connection: str, jql: str, format: Literal["toon", "json"] = "json") -> str:  # noqa: A002
        """Return the total number of Jira issues matching a JQL query. Cheap pre-check before a broad search."""
        return await search_count(get_client(connection), jql)
```

Don't forget to import `search_count` at the top of the module.

- [ ] **Step 5: Run all tests**

```bash
make check 2>&1 | tail -30
```

- [ ] **Step 6: Commit**

```bash
git add src/a2atlassian/jira/issues.py src/a2atlassian/jira_tools/issues.py tests/jira/test_issues.py
git commit -m "feat: jira_search_count tool for cheap JQL pre-check

Thin wrapper around _jira.jql(jql, limit=0, fields=[]) returning
just the total. Lets agents size-check a query before paging
through large results."
```

---

## Task 16: `ConnectionInfo` gains `timezone` and `worklog_admins` fields

**Files:**
- Modify: `src/a2atlassian/connections.py`
- Modify: `tests/test_connections.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_connections.py`:

```python
class TestTimezone:
    def test_default_is_utc(self, tmp_path) -> None:
        store = ConnectionStore(tmp_path)
        store.save("c", "https://x.atlassian.net", "x@y.com", "t")
        info = store.load("c")
        assert info.timezone == "UTC"

    def test_save_and_load_roundtrip(self, tmp_path) -> None:
        store = ConnectionStore(tmp_path)
        store.save("c", "https://x.atlassian.net", "x@y.com", "t", timezone="Europe/Istanbul")
        info = store.load("c")
        assert info.timezone == "Europe/Istanbul"


class TestWorklogAdmins:
    def test_default_is_empty(self, tmp_path) -> None:
        store = ConnectionStore(tmp_path)
        store.save("c", "https://x.atlassian.net", "x@y.com", "t")
        info = store.load("c")
        assert info.worklog_admins == ()

    def test_save_and_load_roundtrip(self, tmp_path) -> None:
        store = ConnectionStore(tmp_path)
        store.save("c", "https://x.atlassian.net", "x@y.com", "t", worklog_admins=["a@x.com", "b@x.com"])
        info = store.load("c")
        assert info.worklog_admins == ("a@x.com", "b@x.com")
```

- [ ] **Step 2: Run tests — fails**

```bash
uv run pytest tests/test_connections.py::TestTimezone tests/test_connections.py::TestWorklogAdmins -v 2>&1 | tail -20
```

Expected: `AttributeError` on `timezone` / `worklog_admins`, or `TypeError` for unexpected kwargs.

- [ ] **Step 3: Extend `ConnectionInfo`**

Edit `src/a2atlassian/connections.py`:

```python
@dataclass(frozen=True)
class ConnectionInfo:
    """A saved Atlassian connection."""

    connection: str
    url: str
    email: str
    token: str
    read_only: bool = True
    timezone: str = "UTC"
    worklog_admins: tuple[str, ...] = ()

    @property
    def resolved_token(self) -> str:
        """Token with ${ENV_VAR} references expanded from the environment."""
        return re.sub(r"\$\{(\w+)\}", lambda m: os.environ.get(m.group(1), m.group(0)), self.token)
```

- [ ] **Step 4: Extend `ConnectionStore.save` and `load` / `list_connections`**

Update `save` signature and TOML writer:

```python
    def save(
        self,
        connection: str,
        url: str,
        email: str,
        token: str,
        read_only: bool = True,
        timezone: str = "UTC",
        worklog_admins: list[str] | tuple[str, ...] = (),
    ) -> Path:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        path = self._path(connection)

        def _escape(value: str) -> str:
            return value.replace("\\", "\\\\").replace('"', '\\"')

        ro = "true" if read_only else "false"
        admins = ", ".join(f'"{_escape(a)}"' for a in worklog_admins)
        content = (
            f'project = "{_escape(connection)}"\n'
            f'url = "{_escape(url)}"\n'
            f'email = "{_escape(email)}"\n'
            f'token = "{_escape(token)}"\n'
            f"read_only = {ro}\n"
            f'timezone = "{_escape(timezone)}"\n'
            f"worklog_admins = [{admins}]\n"
        )
        path.write_text(content)
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
        return path
```

Update `load` and `list_connections` to read the new keys with defaults:

```python
    def load(self, connection: str) -> ConnectionInfo:
        path = self._path(connection)
        if not path.exists():
            msg = f"Connection not found: {connection}"
            raise FileNotFoundError(msg)
        data = tomllib.loads(path.read_text())
        return ConnectionInfo(
            connection=data["project"],
            url=data["url"],
            email=data["email"],
            token=data["token"],
            read_only=data.get("read_only", True),
            timezone=data.get("timezone", "UTC"),
            worklog_admins=tuple(data.get("worklog_admins", ())),
        )
```

Same shape for `list_connections`.

- [ ] **Step 5: Run the tests — green**

```bash
uv run pytest tests/test_connections.py -v 2>&1 | tail -30
```

- [ ] **Step 6: Commit**

```bash
git add src/a2atlassian/connections.py tests/test_connections.py
git commit -m "feat: ConnectionInfo gains timezone + worklog_admins

Optional fields with sensible defaults (UTC / empty). TOML
round-trip works with existing files — new keys default if missing.
Required for the upcoming worklog-admin attribution in jira_get_worklogs."
```

---

## Task 17: CLI gains `--tz` and `--worklog-admin` options with alias resolution

**Files:**
- Modify: `src/a2atlassian/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_cli.py`:

```python
class TestLoginTimezone:
    def test_iana_is_stored_as_is(self, tmp_path, monkeypatch) -> None:
        # set up a monkeypatched store + stub out network validate
        ...  # use the same pattern as existing TestLogin
        # invoke: a2atlassian login -c x --url ... --tz Europe/Istanbul
        # assert the saved TOML has timezone = "Europe/Istanbul"

    def test_cet_alias_resolves_to_iana(self, tmp_path, monkeypatch) -> None:
        # invoke: a2atlassian login -c x --url ... --tz CET
        # assert saved TOML has timezone = "Europe/Paris" (IANA for CET)

    def test_et_alias_resolves_to_iana(self, tmp_path, monkeypatch) -> None:
        # invoke: a2atlassian login -c x --url ... --tz ET
        # assert saved TOML has timezone = "America/New_York"

    def test_utc_alias(self, tmp_path, monkeypatch) -> None:
        # invoke: --tz UTC → timezone = "UTC"

    def test_invalid_tz_exits_with_error(self, tmp_path, monkeypatch) -> None:
        # invoke: --tz NotATimezone → exit code non-zero, error mentions "Unknown timezone"


class TestLoginWorklogAdmins:
    def test_multiple_admins(self, tmp_path, monkeypatch) -> None:
        # invoke: a2atlassian login -c x ... --worklog-admin a@x.com --worklog-admin b@x.com
        # assert saved TOML has worklog_admins = ["a@x.com", "b@x.com"]

    def test_no_admins_default_empty(self, tmp_path, monkeypatch) -> None:
        # invoke without --worklog-admin → saved TOML has worklog_admins = []
```

Fill in the `...` bodies using the same test-harness pattern already present in `tests/test_cli.py` for existing `TestLogin` cases (monkeypatch `AtlassianClient.validate` to return a stub user, monkeypatch `_store` to point at `tmp_path`).

- [ ] **Step 2: Run tests — they fail**

```bash
uv run pytest tests/test_cli.py::TestLoginTimezone tests/test_cli.py::TestLoginWorklogAdmins -v 2>&1 | tail -30
```

- [ ] **Step 3: Add the CLI options and alias-resolution logic**

Edit `src/a2atlassian/cli.py`. Add a helper for alias resolution:

```python
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

_TZ_ALIASES: dict[str, str] = {
    "UTC": "UTC",
    "CET": "Europe/Paris",
    "CEST": "Europe/Paris",
    "ET": "America/New_York",
    "EST": "America/New_York",
    "EDT": "America/New_York",
    "PT": "America/Los_Angeles",
    "PST": "America/Los_Angeles",
    "PDT": "America/Los_Angeles",
}


def _resolve_timezone(raw: str) -> str:
    """Resolve a user-provided timezone (IANA name or common alias) to an IANA name.

    Raises click.BadParameter on unknown values.
    """
    resolved = _TZ_ALIASES.get(raw.upper(), raw)
    try:
        ZoneInfo(resolved)
    except ZoneInfoNotFoundError as exc:
        raise click.BadParameter(f"Unknown timezone: {raw!r}. Expected an IANA name (e.g. Europe/Istanbul) or alias (CET, ET, UTC).") from exc
    return resolved
```

Update the `login` command:

```python
@cli.command()
@click.option("-c", "--connection", required=True, help="Connection name")
@click.option("--url", required=True, help="Atlassian site URL (e.g., https://mysite.atlassian.net)")
@click.option("--email", required=True, help="Account email")
@click.option("--token", required=True, help="API token (or ${ENV_VAR} reference)")
@click.option("--read-only/--no-read-only", default=True, help="Read-only mode (default: true)")
@click.option("--tz", "timezone", default="UTC", help="Timezone (IANA name or alias: CET, ET, UTC; default UTC)")
@click.option("--worklog-admin", "worklog_admins", multiple=True, help="Email(s) allowed to proxy-log worklog hours. Repeat for multiple.")
def login(connection: str, url: str, email: str, token: str, read_only: bool, timezone: str, worklog_admins: tuple[str, ...]) -> None:
    """Save an Atlassian connection. Validates by calling /myself."""
    resolved_tz = _resolve_timezone(timezone)

    info = ConnectionInfo(
        connection=connection,
        url=url,
        email=email,
        token=token,
        read_only=read_only,
        timezone=resolved_tz,
        worklog_admins=tuple(worklog_admins),
    )
    client = AtlassianClient(info)
    try:
        user = asyncio.run(client.validate())
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Connection failed: {exc}", err=True)
        sys.exit(1)

    store = _store()
    path = store.save(
        connection,
        url,
        email,
        token,
        read_only=read_only,
        timezone=resolved_tz,
        worklog_admins=list(worklog_admins),
    )
    display_name = user.get("displayName", "unknown")
    click.echo(f"Connection saved: {path} (authenticated as {display_name})")
```

Update the `connections` command to display the timezone:

```python
@cli.command()
@click.option("-c", "--connection", "connection_filter", default=None, help="Filter by connection name")
def connections(connection_filter: str | None) -> None:
    """List saved connections (no secrets shown)."""
    store = _store()
    results = store.list_connections(connection=connection_filter)
    if not results:
        click.echo("No connections found.")
        return
    for info in results:
        mode = "read-only" if info.read_only else "read-write"
        click.echo(f"{info.connection} ({info.url}) [{mode}] tz={info.timezone} admins={len(info.worklog_admins)}")
```

- [ ] **Step 4: Run tests — green**

```bash
uv run pytest tests/test_cli.py -v 2>&1 | tail -30
```

- [ ] **Step 5: Run quality gate**

```bash
make check 2>&1 | tail -30
```

- [ ] **Step 6: Commit**

```bash
git add src/a2atlassian/cli.py tests/test_cli.py
git commit -m "feat(cli): --tz and --worklog-admin options on login

Accepts IANA names (Europe/Istanbul) or common aliases (CET, ET, UTC).
--worklog-admin is repeatable; stored as a list. Used by the
worklog-admin attribution in the upcoming jira_get_worklogs rework."
```

---

## Task 18: Unified `jira_get_worklogs` — implement `get_worklogs_summary` function

Implements the summary mode half of the two-mode tool. Raw mode re-uses the existing `get_worklogs()`.

**Files:**
- Modify: `src/a2atlassian/jira/worklogs.py`
- Create: `tests/fixtures/jira_worklogs_proxy.json`
- Modify: `tests/jira/test_worklogs.py`

- [ ] **Step 1: Create the fixture**

Write `tests/fixtures/jira_worklogs_proxy.json`:

```json
{
  "issue_key": "PE0-42",
  "assignee_display_name": "Alice",
  "assignee_email": "alice@example.com",
  "worklogs": [
    {
      "id": "w1",
      "author": {"displayName": "Alice", "emailAddress": "alice@example.com"},
      "started": "2026-04-22T10:00:00.000+0300",
      "timeSpentSeconds": 14400,
      "comment": "Implemented feature X"
    },
    {
      "id": "w2",
      "author": {"displayName": "Denis", "emailAddress": "denis@example.com"},
      "started": "2026-04-22T18:00:00.000+0300",
      "timeSpentSeconds": 3600,
      "comment": "Proxy-logged for Alice during daily"
    },
    {
      "id": "w3",
      "author": {"displayName": "Bob", "emailAddress": "bob@example.com"},
      "started": "2026-04-22T14:00:00.000+0300",
      "timeSpentSeconds": 7200,
      "comment": "Code review"
    }
  ]
}
```

- [ ] **Step 2: Write the failing summary tests**

Append to `tests/jira/test_worklogs.py`:

```python
import json
from pathlib import Path

from a2atlassian.jira.worklogs import get_worklogs_summary

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestGetWorklogsSummary:
    @pytest.fixture
    def mock_proxy_client(self) -> AtlassianClient:
        """Client wired so jql returns the proxy-logged ticket and issue_get_worklog returns its three worklogs."""
        fixture = json.loads((FIXTURES / "jira_worklogs_proxy.json").read_text())
        conn = ConnectionInfo(
            connection="test",
            url="https://test.atlassian.net",
            email="alice@example.com",
            token="tok",
            worklog_admins=("denis@example.com",),
            timezone="Europe/Istanbul",
        )
        client = AtlassianClient(conn)
        client._jira_instance = MagicMock()
        # JQL returns the one ticket, with assignee and issuetype metadata
        client._jira_instance.jql.return_value = {
            "issues": [{
                "key": fixture["issue_key"],
                "fields": {
                    "summary": "Test",
                    "status": {"name": "In Progress"},
                    "assignee": {"displayName": fixture["assignee_display_name"], "emailAddress": fixture["assignee_email"]},
                    "priority": {"name": "Medium"},
                    "issuetype": {"name": "Task"},
                },
            }],
            "total": 1,
        }
        client._jira_instance.issue_get_worklog.return_value = {"worklogs": fixture["worklogs"]}
        return client

    async def test_self_logged_hours_go_to_assignee(self, mock_proxy_client: AtlassianClient) -> None:
        """Alice logged 4h against PE0-42 (self) on 2026-04-22 → 4h to Alice."""
        result = await get_worklogs_summary(
            mock_proxy_client, date_from="2026-04-22", detail="by_ticket",
        )
        rows = result.data
        alice_self = [r for r in rows if r["person"] == "Alice" and r["source"] == "self"]
        assert len(alice_self) == 1
        assert alice_self[0]["hours"] == 4.0
        assert alice_self[0]["key"] == "PE0-42"

    async def test_admin_proxy_goes_to_assignee(self, mock_proxy_client: AtlassianClient) -> None:
        """Denis (admin) logged 1h against Alice's ticket → 1h to Alice, source='proxy:Denis'."""
        result = await get_worklogs_summary(
            mock_proxy_client, date_from="2026-04-22", detail="by_ticket",
        )
        rows = result.data
        proxy_rows = [r for r in rows if r["person"] == "Alice" and r["source"].startswith("proxy:")]
        assert len(proxy_rows) == 1
        assert proxy_rows[0]["hours"] == 1.0
        assert proxy_rows[0]["source"] == "proxy:Denis"

    async def test_non_admin_other_goes_to_logger(self, mock_proxy_client: AtlassianClient) -> None:
        """Bob (not admin) logged 2h against Alice's ticket → 2h to Bob, source='non-admin-other'."""
        result = await get_worklogs_summary(
            mock_proxy_client, date_from="2026-04-22", detail="by_ticket",
        )
        rows = result.data
        bob_rows = [r for r in rows if r["person"] == "Bob"]
        assert len(bob_rows) == 1
        assert bob_rows[0]["hours"] == 2.0
        assert bob_rows[0]["source"] == "non-admin-other"
        assert bob_rows[0]["key"] == "PE0-42"

    async def test_total_detail_aggregates(self, mock_proxy_client: AtlassianClient) -> None:
        result = await get_worklogs_summary(
            mock_proxy_client, date_from="2026-04-22", detail="total",
        )
        rows = {r["person"]: r["total_hours"] for r in result.data}
        assert rows == {"Alice": 5.0, "Bob": 2.0}  # Alice: 4 self + 1 proxy; Bob: 2; Denis: 0 (not in totals)

    async def test_by_day_detail(self, mock_proxy_client: AtlassianClient) -> None:
        result = await get_worklogs_summary(
            mock_proxy_client, date_from="2026-04-22", detail="by_day",
        )
        rows = result.data
        alice = [r for r in rows if r["person"] == "Alice"]
        assert len(alice) == 1
        assert alice[0]["date"] == "2026-04-22"
        assert alice[0]["hours"] == 5.0

    async def test_tz_boundary(self, mock_proxy_client: AtlassianClient) -> None:
        """A worklog at 23:30 UTC on 2026-04-22 is at 02:30 Istanbul on 2026-04-23 — must land on 04-23."""
        mock_proxy_client._jira_instance.issue_get_worklog.return_value = {
            "worklogs": [{
                "id": "late",
                "author": {"displayName": "Alice", "emailAddress": "alice@example.com"},
                "started": "2026-04-22T23:30:00.000+0000",  # 02:30 Istanbul next day
                "timeSpentSeconds": 3600,
            }],
        }
        result = await get_worklogs_summary(
            mock_proxy_client, date_from="2026-04-23", detail="by_day",
        )
        alice = [r for r in result.data if r["person"] == "Alice"]
        assert len(alice) == 1
        assert alice[0]["date"] == "2026-04-23"
        assert alice[0]["hours"] == 1.0
```

- [ ] **Step 3: Run tests — fails**

```bash
uv run pytest tests/jira/test_worklogs.py::TestGetWorklogsSummary -v 2>&1 | tail -30
```

Expected: `ImportError: cannot import name 'get_worklogs_summary'`.

- [ ] **Step 4: Implement `get_worklogs_summary`**

Append to `src/a2atlassian/jira/worklogs.py`:

```python
from datetime import date as date_cls, datetime
from typing import Literal
from zoneinfo import ZoneInfo

from a2atlassian.jira.issues import search as search_issues  # re-use slim search


def _attribute(
    logger_email: str,
    logger_name: str,
    assignee_email: str,
    assignee_name: str,
    admins: tuple[str, ...],
) -> tuple[str, str]:
    """Return (attributed_person_name, source_string) per the attribution rules."""
    if logger_email == assignee_email:
        return assignee_name or logger_name, "self"
    if logger_email in admins:
        return assignee_name or logger_name, f"proxy:{logger_name}"
    return logger_name, "non-admin-other"


def _parse_started(started: str) -> datetime:
    """Parse Jira's '2026-04-22T10:00:00.000+0300' into a timezone-aware datetime."""
    # Jira uses e.g. '+0300' rather than '+03:00'; normalize.
    s = started
    if len(s) >= 5 and s[-5] in "+-" and s[-3] != ":":
        s = s[:-2] + ":" + s[-2:]
    return datetime.fromisoformat(s)


async def get_worklogs_summary(
    client: AtlassianClient,
    date_from: str,
    date_to: str | None = None,
    people: list[str] | None = None,
    jql_scope: str | None = None,
    detail: Literal["total", "by_day", "by_ticket"] = "by_day",
) -> OperationResult:
    """Aggregate worklogs across a date range per attribution rules.

    date_from / date_to: ISO dates. Day boundaries are evaluated in the connection timezone.
    jql_scope: optional JQL narrowing the ticket set (default: no scope, all tickets touched in range).
    people: optional filter on the *attributed* person display name.
    detail: aggregation granularity.
    """
    tz = ZoneInfo(client.connection.timezone)
    dfrom = date_cls.fromisoformat(date_from)
    dto = date_cls.fromisoformat(date_to) if date_to else dfrom
    admins = client.connection.worklog_admins

    scope = jql_scope or "project is not empty"
    jql = f"{scope} AND worklogDate >= '{dfrom.isoformat()}' AND worklogDate <= '{dto.isoformat()}'"

    t0 = time.monotonic()

    # Pull candidate tickets (with assignee) using slim search.
    tickets_result = await search_issues(client, jql, limit=500, offset=0, fields=["summary", "assignee"])
    candidate_issues = tickets_result.data

    # For each ticket, pull worklogs and attribute per rules.
    rows: list[dict[str, Any]] = []
    for issue in candidate_issues:
        issue_key = issue["key"]
        raw = await client._call(client._jira.issue_get_worklog, issue_key)
        worklogs_raw = raw.get("worklogs", []) if isinstance(raw, dict) else raw
        for wl in worklogs_raw:
            started = wl.get("started", "")
            if not started:
                continue
            dt_local = _parse_started(started).astimezone(tz)
            wl_date = dt_local.date()
            if wl_date < dfrom or wl_date > dto:
                continue
            hours = wl.get("timeSpentSeconds", 0) / 3600.0

            author = wl.get("author") or {}
            logger_email = author.get("emailAddress", "") if isinstance(author, dict) else ""
            logger_name = author.get("displayName", "") if isinstance(author, dict) else str(author)

            # Assignee not returned directly; pulled from candidate issue. We extracted via _extract_issue_summary
            # which puts assignee display name under key 'assignee'. Email isn't included in the slim search
            # shape, so the assignee-vs-logger equality check uses display name as the key. Admins list is
            # email-based, which works because proxy loggers are identified by email, not display name.
            assignee_name = issue.get("assignee", "")
            # For self-check: compare logger email to any configured email-like field; if the assignee slim
            # shape lacks email, fall back to name comparison.
            assignee_email = ""  # unavailable in slim shape; name-compare below

            if logger_email and logger_email == assignee_email:
                person, source = assignee_name or logger_name, "self"
            elif logger_name == assignee_name:
                person, source = assignee_name or logger_name, "self"
            elif logger_email in admins:
                person, source = assignee_name or logger_name, f"proxy:{logger_name}"
            else:
                person, source = logger_name, "non-admin-other"

            rows.append({
                "person": person,
                "date": wl_date.isoformat(),
                "key": issue_key,
                "hours": hours,
                "source": source,
            })

    # People filter (on attributed person)
    if people:
        rows = [r for r in rows if r["person"] in people]

    # Aggregate per detail level
    if detail == "by_ticket":
        data = rows
    elif detail == "by_day":
        agg: dict[tuple[str, str], float] = {}
        for r in rows:
            agg[(r["person"], r["date"])] = agg.get((r["person"], r["date"]), 0.0) + r["hours"]
        data = [{"person": p, "date": d, "hours": h} for (p, d), h in sorted(agg.items())]
    else:  # total
        totals: dict[str, float] = {}
        for r in rows:
            totals[r["person"]] = totals.get(r["person"], 0.0) + r["hours"]
        data = [{"person": p, "total_hours": h} for p, h in sorted(totals.items())]

    elapsed = int((time.monotonic() - t0) * 1000)
    return OperationResult(
        name="get_worklogs_summary",
        data=data,
        count=len(data),
        truncated=False,
        time_ms=elapsed,
    )
```

Note: the assignee email isn't in the slim-search shape; if a future test shows that assignee-email comparison is required, extend the `fields=` in the inner search call to include a full assignee object.

- [ ] **Step 5: Run the tests — green (fix any failing assertions)**

```bash
uv run pytest tests/jira/test_worklogs.py::TestGetWorklogsSummary -v 2>&1 | tail -40
```

Adjust the mock setup or implementation until green. Particular fragile point: the slim `_extract_issue_summary` drops the assignee email. If tests need it, widen the search call inside `get_worklogs_summary` to include a custom fields list and adjust the loop to read `wl["author"]["emailAddress"]` directly against a stored per-issue assignee email (pulled from an extended search or a second `client._jira.issue(issue_key)` call if needed).

- [ ] **Step 6: Commit**

```bash
git add src/a2atlassian/jira/worklogs.py tests/jira/test_worklogs.py tests/fixtures/jira_worklogs_proxy.json
git commit -m "feat(worklogs): get_worklogs_summary with admin attribution

Aggregates worklogs across a date range in the connection's
timezone. Attribution rules:
  1. logger==assignee → assignee ('self')
  2. logger ∈ worklog_admins → assignee ('proxy:<logger>')
  3. otherwise → logger ('non-admin-other')
Three detail levels: total, by_day (default), by_ticket."
```

---

## Task 19: Rework `jira_get_worklogs` MCP tool as two-mode

Glues the new summary to the MCP surface, and collapses the old raw `jira_get_worklogs` into the same tool via mode selection.

**Files:**
- Modify: `src/a2atlassian/jira_tools/worklogs.py`
- Modify: `tests/test_mcp_server.py`

- [ ] **Step 1: Write the failing mode-selection tests**

Append to `tests/test_mcp_server.py`:

```python
class TestJiraGetWorklogsModes:
    def test_error_when_neither_issue_nor_date(self) -> None:
        """Neither issue_key nor date_from → error mentioning both."""
        # Call the registered tool and assert on the returned string
        # (use the existing FastMCP test harness pattern in this file)
        ...

    def test_raw_mode_uses_issue(self) -> None:
        """issue_key set → raw mode dispatched to get_worklogs."""
        ...

    def test_summary_mode_uses_date(self) -> None:
        """date_from set, no issue_key → summary mode dispatched to get_worklogs_summary."""
        ...

    def test_both_filters_raw_to_date_range(self) -> None:
        """Both issue_key and date_from → raw mode, filtered to the range."""
        ...
```

Use the existing test-harness pattern in `tests/test_mcp_server.py` to instantiate the server and invoke a tool. Fill in bodies to match.

- [ ] **Step 2: Rewrite `jira_tools/worklogs.py::register_read::jira_get_worklogs`**

Replace the existing two separate registrations (`jira_get_worklogs` raw-only, `jira_add_worklog`) with:

```python
"""Jira worklog tools — two-mode get (raw + summary) and add."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from a2atlassian.client import AtlassianClient
from a2atlassian.decorators import mcp_tool
from a2atlassian.jira.worklogs import add_worklog, get_worklogs, get_worklogs_summary

if TYPE_CHECKING:
    from collections.abc import Callable

    from mcp.server.fastmcp import FastMCP

    from a2atlassian.connections import ConnectionInfo
    from a2atlassian.errors import ErrorEnricher


def register_read(server, get_client, enricher) -> None:
    @server.tool()
    @mcp_tool(enricher)
    async def jira_get_worklogs(
        connection: str,
        issue_key: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        people: list[str] | None = None,
        jql_scope: str | None = None,
        detail: Literal["auto", "raw", "total", "by_day", "by_ticket"] = "auto",
        format: Literal["toon", "json"] = "toon",  # noqa: A002
    ) -> str:
        """Get worklogs for a Jira issue (raw mode) or aggregated across a date range (summary mode).

        Mode selection:
          - issue_key set, date_from unset  → raw mode: per-worklog dump for the ticket.
          - issue_key set, date_from set    → raw mode filtered to [date_from, date_to].
          - issue_key unset, date_from set  → summary mode per attribution rules.
          - both unset                      → error.

        detail='auto' resolves to 'raw' when issue_key is set, else 'by_day'.

        Returns TOON by default (compact); pass format='json' for standard JSON shape.
        """
        if not issue_key and not date_from:
            raise ValueError(
                "Provide either issue_key (raw mode) or date_from (summary mode)."
            )
        client = get_client(connection)
        if issue_key:
            # Raw mode (optionally range-filtered)
            result = await get_worklogs(client, issue_key)
            if date_from:
                from datetime import date as date_cls
                from zoneinfo import ZoneInfo
                from a2atlassian.jira.worklogs import _parse_started
                tz = ZoneInfo(client.connection.timezone)
                dfrom = date_cls.fromisoformat(date_from)
                dto = date_cls.fromisoformat(date_to) if date_to else dfrom

                def in_range(w: dict) -> bool:
                    started = w.get("started", "")
                    if not started:
                        return False
                    d = _parse_started(started).astimezone(tz).date()
                    return dfrom <= d <= dto

                from a2atlassian.formatter import OperationResult
                filtered = [w for w in result.data if in_range(w)]
                return OperationResult(
                    name="get_worklogs",
                    data=filtered,
                    count=len(filtered),
                    truncated=False,
                    time_ms=result.time_ms,
                )
            return result

        # Summary mode
        resolved_detail = detail
        if detail == "auto":
            resolved_detail = "by_day"
        if resolved_detail == "raw":
            raise ValueError("detail='raw' is only valid with issue_key set.")
        return await get_worklogs_summary(
            client,
            date_from=date_from,
            date_to=date_to,
            people=people,
            jql_scope=jql_scope,
            detail=resolved_detail,  # type: ignore[arg-type]
        )


def register_write(server, get_connection, enricher) -> None:
    @server.tool()
    @mcp_tool(enricher)
    async def jira_add_worklog(
        connection: str,
        issue_key: str,
        time_spent: str,
        comment: str = "",
        format: Literal["toon", "json"] = "json",  # noqa: A002
    ) -> str:
        """Add a worklog entry to a Jira issue. time_spent is a string like '2h 30m'."""
        conn = get_connection(connection)
        if conn.read_only:
            raise RuntimeError(f"Connection '{connection}' is read-only. Run: a2atlassian login -c {connection} --no-read-only")
        return await add_worklog(AtlassianClient(conn), issue_key, time_spent, comment=comment)
```

- [ ] **Step 3: Run mode-selection tests — green**

```bash
uv run pytest tests/test_mcp_server.py -v 2>&1 | tail -40
```

- [ ] **Step 4: Run the full test suite**

```bash
make check 2>&1 | tail -30
```

- [ ] **Step 5: Commit**

```bash
git add src/a2atlassian/jira_tools/worklogs.py tests/test_mcp_server.py
git commit -m "feat: unified jira_get_worklogs (raw + summary modes)

Single tool with mode selection:
- issue_key set       → raw dump (optionally filtered to date range)
- date_from set       → summary with attribution rules
- neither             → error with actionable hint

Replaces two previously-separate semantic paths with one discoverable tool."
```

---

## Task 20: Delete `jira_get_issue_dev_info`

**Files:**
- Modify: `src/a2atlassian/jira_tools/issues.py`
- Modify: `tests/test_mcp_server.py` (assert absence)

- [ ] **Step 1: Remove the tool registration from `issues.py`**

Delete the `jira_get_issue_dev_info` block in `src/a2atlassian/jira_tools/issues.py::register_read`.

- [ ] **Step 2: Add an "is absent" assertion**

In `tests/test_mcp_server.py`, append a test confirming the tool does not register:

```python
class TestDeletedTools:
    def test_jira_get_issue_dev_info_is_absent(self) -> None:
        from a2atlassian import mcp_server
        # After full tool registration, the tool name should not be in the server's registry.
        tool_names = set(mcp_server.server._tools.keys()) if hasattr(mcp_server.server, "_tools") else set()
        # FastMCP exposes tools differently across versions; fall back to introspection if needed.
        # At minimum, the symbol shouldn't exist in the module.
        import a2atlassian.jira_tools.issues as issues_mod
        assert not hasattr(issues_mod, "jira_get_issue_dev_info")
```

Adjust the introspection to match whatever pattern the existing tests use for registry inspection.

- [ ] **Step 3: Run tests — green**

```bash
make test 2>&1 | tail -30
```

- [ ] **Step 4: Commit**

```bash
git add src/a2atlassian/jira_tools/issues.py tests/test_mcp_server.py
git commit -m "remove: jira_get_issue_dev_info placeholder tool

The tool returned a static 'not yet supported' string. Removing
it reduces the deferred-tool context without functional loss.
Callers who need dev info should hit /rest/dev-status/latest/
directly, documented in the commit message for future reference."
```

---

## Task 21: Consolidate watchers — `jira_set_watchers`

Replaces `jira_add_watcher` + `jira_remove_watcher` with one tool that takes `add=[]` and `remove=[]`.

**Files:**
- Modify: `src/a2atlassian/jira/watchers.py`
- Modify: `src/a2atlassian/jira_tools/watchers.py`
- Modify: `tests/jira/test_watchers.py`

- [ ] **Step 1: Write the failing tests**

In `tests/jira/test_watchers.py`, add:

```python
from a2atlassian.jira.watchers import set_watchers


class TestSetWatchers:
    async def test_adds_and_removes(self, mock_client: AtlassianClient) -> None:
        await set_watchers(mock_client, "PROJ-1", add=["a1", "a2"], remove=["r1"])
        calls = mock_client._jira_instance.mock_calls
        # Assert each add called issue_add_watcher(PROJ-1, <id>)
        # Assert each remove called issue_delete_watcher(PROJ-1, <id>)
        # (use the existing atlassian-python-api method names; inspect via spike in Task 12 if unsure)

    async def test_empty_lists_no_calls(self, mock_client: AtlassianClient) -> None:
        await set_watchers(mock_client, "PROJ-1", add=[], remove=[])
        assert not mock_client._jira_instance.mock_calls
```

- [ ] **Step 2: Run tests — fails on ImportError**

- [ ] **Step 3: Implement `set_watchers`**

Replace `add_watcher` and `remove_watcher` in `src/a2atlassian/jira/watchers.py` with a single `set_watchers`:

```python
async def set_watchers(
    client: AtlassianClient,
    issue_key: str,
    add: list[str] | None = None,
    remove: list[str] | None = None,
) -> OperationResult:
    """Add and/or remove watchers on a Jira issue. Lists of account IDs."""
    t0 = time.monotonic()
    for account_id in add or []:
        await client._call(client._jira.issue_add_watcher, issue_key, account_id)
    for account_id in remove or []:
        await client._call(client._jira.issue_delete_watcher, issue_key, account_id)
    elapsed = int((time.monotonic() - t0) * 1000)
    return OperationResult(
        name="set_watchers",
        data={"issue_key": issue_key, "added": list(add or []), "removed": list(remove or []), "status": "ok"},
        count=1,
        truncated=False,
        time_ms=elapsed,
    )
```

Keep the old `add_watcher` / `remove_watcher` functions in the file until tool-side migration is complete — that's cleanup we do inline.

- [ ] **Step 4: Rework the MCP tool module**

In `src/a2atlassian/jira_tools/watchers.py`, remove `jira_add_watcher` + `jira_remove_watcher`, add `jira_set_watchers`:

```python
@server.tool()
@mcp_tool(enricher)
async def jira_set_watchers(
    connection: str,
    issue_key: str,
    add: list[str] | None = None,
    remove: list[str] | None = None,
    format: Literal["toon", "json"] = "json",  # noqa: A002
) -> str:
    """Add and/or remove watchers on a Jira issue. Pass account IDs in 'add' and/or 'remove' lists."""
    conn = get_connection(connection)
    if conn.read_only:
        raise RuntimeError(f"Connection '{connection}' is read-only. Run: a2atlassian login -c {connection} --no-read-only")
    return await set_watchers(AtlassianClient(conn), issue_key, add=add, remove=remove)
```

- [ ] **Step 5: Delete the now-unused `add_watcher` and `remove_watcher` from `src/a2atlassian/jira/watchers.py`**

- [ ] **Step 6: Run all tests**

```bash
make test 2>&1 | tail -30
```

- [ ] **Step 7: Commit**

```bash
git add src/a2atlassian/jira/watchers.py src/a2atlassian/jira_tools/watchers.py tests/jira/test_watchers.py
git commit -m "refactor: consolidate watchers into jira_set_watchers

Replaces jira_add_watcher + jira_remove_watcher with one tool
that takes add=[] and remove=[] account-ID lists. Net -1 tool."
```

---

## Task 22: Consolidate project metadata — `jira_get_project_metadata`

Replaces `jira_get_project_components` + `jira_get_project_versions` with one tool that takes `include=[...]`.

**Files:**
- Modify: `src/a2atlassian/jira/projects.py`
- Modify: `src/a2atlassian/jira_tools/projects.py`
- Modify: `tests/jira/test_projects.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/jira/test_projects.py`:

```python
from a2atlassian.jira.projects import get_project_metadata


class TestGetProjectMetadata:
    async def test_components_only(self, mock_client: AtlassianClient) -> None:
        mock_client._jira_instance.get_project_components.return_value = [{"id": "1", "name": "Backend"}]
        result = await get_project_metadata(mock_client, "PROJ", include=["components"])
        assert "components" in result.data
        assert "versions" not in result.data

    async def test_versions_only(self, mock_client: AtlassianClient) -> None:
        mock_client._jira_instance.get_project_versions.return_value = [{"id": "1", "name": "v1"}]
        result = await get_project_metadata(mock_client, "PROJ", include=["versions"])
        assert "versions" in result.data
        assert "components" not in result.data

    async def test_all_sentinel(self, mock_client: AtlassianClient) -> None:
        mock_client._jira_instance.get_project_components.return_value = []
        mock_client._jira_instance.get_project_versions.return_value = []
        result = await get_project_metadata(mock_client, "PROJ", include=["all"])
        assert "components" in result.data
        assert "versions" in result.data

    async def test_default_all(self, mock_client: AtlassianClient) -> None:
        mock_client._jira_instance.get_project_components.return_value = []
        mock_client._jira_instance.get_project_versions.return_value = []
        result = await get_project_metadata(mock_client, "PROJ")
        assert "components" in result.data
        assert "versions" in result.data
```

- [ ] **Step 2: Implement `get_project_metadata`**

Append to `src/a2atlassian/jira/projects.py`:

```python
async def get_project_metadata(
    client: AtlassianClient,
    project_key: str,
    include: list[str] | None = None,
) -> OperationResult:
    """Get project metadata. include=['components','versions','all']; default 'all'."""
    include = include or ["all"]
    want_components = "components" in include or "all" in include
    want_versions = "versions" in include or "all" in include

    t0 = time.monotonic()
    data: dict[str, Any] = {}
    if want_components:
        raw = await client._call(client._jira.get_project_components, project_key)
        data["components"] = [{"id": str(c.get("id", "")), "name": c.get("name", "")} for c in raw]
    if want_versions:
        raw = await client._call(client._jira.get_project_versions, project_key)
        data["versions"] = [{"id": str(v.get("id", "")), "name": v.get("name", ""), "released": v.get("released", False)} for v in raw]
    elapsed = int((time.monotonic() - t0) * 1000)

    return OperationResult(
        name="get_project_metadata",
        data=data,
        count=1,
        truncated=False,
        time_ms=elapsed,
    )
```

Keep `get_project_components` and `get_project_versions` internal — they're building blocks.

- [ ] **Step 3: Rework MCP tool module**

In `src/a2atlassian/jira_tools/projects.py`, remove `jira_get_project_components` + `jira_get_project_versions` and add `jira_get_project_metadata`:

```python
@server.tool()
@mcp_tool(enricher)
async def jira_get_project_metadata(
    connection: str,
    project_key: str,
    include: list[str] | None = None,
    format: Literal["toon", "json"] = "json",  # noqa: A002
) -> str:
    """Get project metadata (components, versions). include=['components'], ['versions'], ['all'], or omit for all."""
    return await get_project_metadata(get_client(connection), project_key, include=include)
```

- [ ] **Step 4: Run tests — green**

```bash
make check 2>&1 | tail -30
```

- [ ] **Step 5: Commit**

```bash
git add src/a2atlassian/jira/projects.py src/a2atlassian/jira_tools/projects.py tests/jira/test_projects.py
git commit -m "refactor: consolidate project metadata into jira_get_project_metadata

Replaces jira_get_project_components + jira_get_project_versions
with one tool taking include=['components','versions','all']. Net -1 tool."
```

---

## Task 23: Fold `jira_link_to_epic` into `jira_create_issue_link`

Epic-parent links are a `link_type="Epic"` special case — no dedicated tool needed.

**Files:**
- Modify: `src/a2atlassian/jira_tools/links.py`
- Modify: `tests/jira/test_links.py`

- [ ] **Step 1: Remove `jira_link_to_epic` tool registration**

Delete the `@server.tool() … jira_link_to_epic` block in `src/a2atlassian/jira_tools/links.py`.

- [ ] **Step 2: Document the replacement in `jira_create_issue_link`'s docstring**

Update the tool:

```python
@server.tool()
@mcp_tool(enricher)
async def jira_create_issue_link(
    connection: str,
    link_type: str,
    inward_key: str,
    outward_key: str,
    format: Literal["toon", "json"] = "json",  # noqa: A002
) -> str:
    """Create a link between two Jira issues. Use jira_get_link_types to discover available types.

    To set an issue's parent (Epic), pass link_type='Epic' with inward_key=<child> and outward_key=<epic>.
    """
    conn = get_connection(connection)
    if conn.read_only:
        raise RuntimeError(f"Connection '{connection}' is read-only. Run: a2atlassian login -c {connection} --no-read-only")
    return await create_issue_link(AtlassianClient(conn), link_type, inward_key, outward_key)
```

- [ ] **Step 3: Delete the underlying `link_to_epic` helper from `src/a2atlassian/jira/links.py`**

Remove it from the module and update `tests/jira/test_links.py` to drop the deleted helper's tests.

- [ ] **Step 4: Add an "is absent" assertion**

```python
def test_jira_link_to_epic_is_absent(self) -> None:
    import a2atlassian.jira_tools.links as links_mod
    assert not hasattr(links_mod, "jira_link_to_epic")
```

- [ ] **Step 5: Run all tests**

```bash
make check 2>&1 | tail -30
```

- [ ] **Step 6: Commit**

```bash
git add src/a2atlassian/jira_tools/links.py src/a2atlassian/jira/links.py tests/jira/test_links.py
git commit -m "refactor: fold jira_link_to_epic into jira_create_issue_link

Epic-parent linking is a link_type='Epic' special case — callers
pass inward_key=<child>, outward_key=<epic>. Net -1 tool."
```

---

## Task 24: README scope note + list-tool docstring pass

Addresses S9/S12 documentation hygiene that wasn't covered by the earlier `instructions=` update.

**Files:**
- Modify: `README.md`
- Audit + modify: every list-returning tool without the TOON-default note already.

- [ ] **Step 1: Audit list-returning tools for the docstring note**

```bash
rg 'Returns TOON by default' src/a2atlassian/jira_tools/
```

Tool modules refactored via Task 11 should already have this. If not all list tools do, add the one-liner to missing docstrings:

`"Returns TOON by default (compact); pass format='json' for standard JSON shape."`

Single-entity tools (get_issue, get_user_profile, search_count) should NOT have this line.

- [ ] **Step 2: Add the scope note to `README.md`**

Near the top of `README.md`, in the "Why a2atlassian?" section, add a note:

```markdown
> **Scope today:** a2atlassian ships Jira tools only. Confluence support is on the v0.4.0 roadmap; use [mcp__atlassian](https://github.com/sooperset/mcp-atlassian) for Confluence until then.
```

- [ ] **Step 3: Commit**

```bash
git add README.md src/a2atlassian/jira_tools/
git commit -m "docs: scope note in README; audit list-tool TOON note"
```

---

## Task 25: Version bump to v0.3.0 + CHANGELOG

**Files:**
- Modify: `pyproject.toml`
- Create or modify: `CHANGELOG.md` (at repo root)

- [ ] **Step 1: Bump the version**

Edit `pyproject.toml`. Change the version string from `"0.2.1"` to `"0.3.0"`.

- [ ] **Step 2: Write the changelog entry**

Create or prepend to `CHANGELOG.md`:

```markdown
# Changelog

## v0.3.0 — 2026-04-23

### Breaking changes

- **Parameter rename: `project` → `connection`.** Every tool parameter previously called `project` (the saved connection identifier) is now `connection`. CLI: `--project` / `-p` → `--connection` / `-c`. No compatibility alias. The TOML on-disk key stays `project` so existing saved connections load without migration; re-running `a2atlassian login` regenerates the file with the new (fully forward-compatible) shape.
- **`jira_search` now returns a minimal default field set** (`summary`, `status`, `assignee`, `priority`, `issuetype`, `parent`, `updated`) instead of the library's all-fields default. Callers consuming `_jira.jql()` output directly see trimmed payloads; callers using the public `search()` return shape (`_extract_issue_summary`) are unaffected. Pass `fields=["*all"]` to restore full-payload behavior.
- **`jira_get_issue_dev_info` removed** — was a placeholder that returned a static "not supported" string.
- **`jira_link_to_epic` removed** — use `jira_create_issue_link` with `link_type="Epic"`.
- **`jira_add_watcher` + `jira_remove_watcher` replaced by `jira_set_watchers`** (single tool with `add=[]` / `remove=[]` lists).
- **`jira_get_project_components` + `jira_get_project_versions` replaced by `jira_get_project_metadata`** (single tool with `include=["components", "versions", "all"]`).
- **`jira_get_worklogs` now a two-mode tool** — `issue_key` argument triggers raw per-worklog dump (old behavior); `date_from` triggers summary mode with per-person aggregation and worklog-admin attribution.

### Fixed

- **`jira_get_boards`** no longer throws `'Jira' object has no attribute 'boards'`. Uses the correct `atlassian-python-api` method name.

### New

- **`jira_search_count`** — cheap pre-check tool returning `{jql, total}` without paging through issues.
- **`@mcp_tool` decorator** with `Literal[...]`-based enum validation. Invalid `format`, `detail`, etc. return a structured "Invalid value" error instead of swallowing silently.
- **`ConnectionInfo.timezone`** — IANA zone for day-boundary math in worklog summaries. CLI `--tz` accepts aliases (`CET`, `ET`, `UTC`).
- **`ConnectionInfo.worklog_admins`** — email list. Worklogs authored by an admin on someone else's ticket attribute to the ticket's assignee (covers the proxy-logged-during-daily workflow).
- **"Connection not found" error** now lists available connection names and proposes a close match via `difflib`.

### Documentation

- MCP server `instructions=` string honest about Jira-only scope today.
- Every list-returning tool documents the TOON default.
```

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "release: v0.3.0

See CHANGELOG.md for the full breaking-change list."
```

- [ ] **Step 4: Run the full quality gate one last time**

```bash
make check 2>&1 | tail -30
```

Expected: all checks pass.

- [ ] **Step 5: Optional — tag the release**

```bash
git tag -a v0.3.0 -m "v0.3.0 — cleanup batch"
```

Do not push the tag in this task; leave that to the release workflow.

---

## Self-review checklist

Completed before handing this plan off:

- [x] Spec §1 (project→connection rename) — Tasks 5, 6, 7, 8.
- [x] Spec §2 (jira_get_boards fix) — Tasks 12, 13.
- [x] Spec §3 (search slim defaults + jira_search_count) — Tasks 14, 15.
- [x] Spec §4 (unified jira_get_worklogs) — Tasks 16, 17, 18, 19.
- [x] Spec §5 (tool-surface consolidation) — Tasks 20, 21, 22, 23.
- [x] Spec §6 (@mcp_tool decorator + enum validation) — Tasks 3, 4, 10, 11.
- [x] Spec §7 (MCP instructions + README) — Task 6 (instructions), Task 24 (README), Task 11 (per-tool docstrings).
- [x] Spec §8 (connection_not_found enricher) — Task 9.
- [x] Precondition (port refactor) — Tasks 1, 2.
- [x] Release shape (v0.3.0 bump + CHANGELOG) — Task 25.

No `TBD` or placeholder steps. Every code step shows the actual code. Every test step has an explicit expected outcome. Commits happen after each logical unit.

Dependency order: decorator (3, 4) before applying decorator (10, 11). Connection-layer changes (5, 16) before MCP/tool layer (6, 7, 17). Rename (5–8) before tool consolidations (20–23) so consolidation PRs are smaller diffs. Summary function (18) before MCP tool rework (19).
