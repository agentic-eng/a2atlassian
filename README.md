<p align="center">
  <h1 align="center">🏢 a2atlassian</h1>
  <p align="center">
    <em>Agent-to-Atlassian</em>
  </p>
  <p align="center">
    <strong>Give AI agents access to Jira and Confluence. Save credentials once, work from anywhere.</strong>
  </p>
  <p align="center">
    Jira + Confluence &middot; read-only by default &middot; pre-configured connections &middot; compact TSV output
  </p>
  <p align="center">
    <a href="https://pypi.org/project/a2atlassian/"><img src="https://img.shields.io/pypi/v/a2atlassian.svg" alt="PyPI"></a>
    <a href="https://pypi.org/project/a2atlassian/"><img src="https://img.shields.io/pypi/pyversions/a2atlassian.svg" alt="Python"></a>
    <a href="https://github.com/yoselabs/a2atlassian/blob/main/LICENSE"><img src="https://img.shields.io/github/license/yoselabs/a2atlassian.svg" alt="License"></a>
    <a href="https://github.com/yoselabs/a2atlassian/actions"><img src="https://img.shields.io/github/actions/workflow/status/yoselabs/a2atlassian/publish.yml" alt="CI"></a>
    <a href="https://registry.modelcontextprotocol.io/servers/io.github.yoselabs/a2atlassian"><img src="https://img.shields.io/badge/MCP-registry-blue" alt="MCP Registry"></a>
  </p>
  <p align="center">
    <a href="#quick-start">Quick Start</a> &middot;
    <a href="#mcp-tools">MCP Tools</a> &middot;
    <a href="#security">Security</a> &middot;
    <a href="#comparison">Comparison</a> &middot;
    <a href="#setup-by-environment">Setup</a>
  </p>
</p>

---

```
Agent: "What's the status of PROJ-42? Add a comment with the progress update."
  ↓
a2atlassian → get issue, add comment, transition to In Progress
  ↓
Agent: "Done — PROJ-42 updated and moved to In Progress."
```

## Why a2atlassian?

Existing Atlassian MCP servers (Rovo, sooperset) require Docker, `.env` files, and `mcp-remote` bridges. They dump 72 tools into agent context and have [known quirks](docs/) that silently fail. a2atlassian fixes all of that:

- **No Docker** — `pip install a2atlassian` and you're done
- **Pre-configured connections** — define projects in `.mcp.json` with `--register`, agent works immediately
- **Read-only by default** — write access is opt-in per connection
- **Connection scoping** — `--scope` limits which projects an agent can see
- **Compact output** — TSV for lists (30-60% fewer tokens), JSON for single entities
- **Dynamic tool loading** — MCP clients that support deferred tools (e.g., Claude Code) load tools on demand, keeping context lean
- **Error enrichment** — bad field names get suggestions, JQL typos get corrections, quirks get auto-fixed
- **Secrets stay in env** — `${ATLASSIAN_TOKEN}` in configs, expanded only at runtime

> **Scope today:** full Jira surface (issues, comments, sprints, boards, worklogs, links, versions, fields, watchers, projects) and Confluence core (pages CRUD, search, metadata-only writes).

## Quick Start

```bash
# Recommended — installs globally as a CLI tool
uv tool install a2atlassian

# Or with pip
pip install a2atlassian
```

### As an MCP Server (recommended)

**Claude Code** (with pre-configured connection):
```bash
claude mcp add -s user a2atlassian -- uvx --from a2atlassian a2atlassian-mcp \
  --register myproject https://mysite.atlassian.net user@company.com '${ATLASSIAN_TOKEN}'
```

**Claude Code** (minimal — agent calls `login` on demand):
```bash
claude mcp add -s user a2atlassian -- uvx --from a2atlassian a2atlassian-mcp
```

**Claude Desktop / Cursor / any MCP client** (`.mcp.json`):
```json
{
  "mcpServers": {
    "a2atlassian": {
      "command": "uvx",
      "args": [
        "--from", "a2atlassian", "a2atlassian-mcp",
        "--register", "myproject", "https://mysite.atlassian.net",
        "user@company.com", "${ATLASSIAN_TOKEN}"
      ],
      "env": {
        "ATLASSIAN_TOKEN": "your-api-token-here"
      }
    }
  }
}
```

**Multiple projects:**
```json
{
  "args": [
    "--from", "a2atlassian", "a2atlassian-mcp",
    "--register", "myproject", "https://mysite.atlassian.net", "user@a.com", "${TOKEN_A}",
    "--register", "personal", "https://personal.atlassian.net", "user@b.com", "${TOKEN_B}"
  ]
}
```

**Scoped connections** (limit agent to specific saved projects):
```json
{
  "args": ["--from", "a2atlassian", "a2atlassian-mcp", "--scope", "myproject"]
}
```

`--register` creates ephemeral in-memory connections (process lifetime, no files written). `--scope` filters which saved connections are visible. Both limit blast radius.

### As a CLI

```bash
# Save a connection (validates by calling /myself)
a2atlassian login -c myproject \
  --url https://mysite.atlassian.net \
  --email user@company.com \
  --token "$ATLASSIAN_TOKEN"

# Same, pulling the token from 1Password via `op`
a2atlassian login -c myproject \
  --url https://mysite.atlassian.net \
  --email user@company.com \
  --token "op://Personal/Atlassian/token"

# Enable writes
a2atlassian login -c myproject \
  --url https://mysite.atlassian.net \
  --email user@company.com \
  --token "$ATLASSIAN_TOKEN" \
  --no-read-only

# List / remove connections
a2atlassian connections
a2atlassian logout -c myproject
```

Tokens accept three forms: literal value, `${ENV_VAR}` reference, or
`op://vault/item/field` (resolved via the 1Password CLI at runtime).

## MCP Tools

### Connection Management

| Tool | Description |
|------|-------------|
| `login` | Save a connection — validates by calling /myself first |
| `logout` | Remove a saved connection |
| `list_connections` | List connections (no secrets exposed) |

### Jira — Read

| Tool | Description |
|------|-------------|
| `jira_get_issue` | Get issue by key — full fields, status, assignee |
| `jira_search` | Search by JQL with pagination — compact TSV output by default |
| `jira_search_count` | Count-only JQL — cheap pre-check for "is this going to be huge?" |
| `jira_search_fields` | Discover custom-field IDs by name |
| `jira_get_field_options` | List allowed values for a select / multi-select field |
| `jira_get_comments` | Get all comments for an issue |
| `jira_get_worklogs` | Get all worklogs for an issue |
| `jira_get_transitions` | Discover available status transitions |
| `jira_get_link_types` | List available issue-link types |
| `jira_get_watchers` | List watchers for an issue |
| `jira_get_projects` | List projects accessible to the connection |
| `jira_get_project_metadata` | Fetch creation metadata (issue types, required fields) |
| `jira_get_user_profile` | Resolve an email/accountId to a full user profile |
| `jira_get_boards` | List agile boards in a project |
| `jira_get_board_issues` | Issues on a board (paginated) |
| `jira_get_sprints` | List sprints on a board |
| `jira_get_sprint_issues` | Issues in a sprint (paginated) |

### Jira — Write (requires read-write connection)

| Tool | Description |
|------|-------------|
| `jira_create_issue` | Create a new issue |
| `jira_update_issue` | Update fields on an existing issue |
| `jira_delete_issue` | Delete an issue |
| `jira_transition_issue` | Move issue to a new status |
| `jira_add_comment` | Add comment (wiki markup, API v2) |
| `jira_edit_comment` | Update existing comment |
| `jira_add_worklog` | Log time on an issue |
| `jira_create_issue_link` | Link two issues |
| `jira_remove_issue_link` | Remove an issue link |
| `jira_set_watchers` | Replace the watcher set on an issue |
| `jira_create_sprint` | Create a sprint on a board |
| `jira_update_sprint` | Update sprint state / dates |
| `jira_add_issues_to_sprint` | Move issues into a sprint |
| `jira_create_version` | Create a project version |

### Confluence — Read

| Tool | Description |
|------|-------------|
| `confluence_get_page` | Fetch a page by id (body storage, version, space) |
| `confluence_get_page_children` | List direct children of a page (paginated) |
| `confluence_search` | CQL search; minimal per-match rows |

### Confluence — Write (requires read-write connection)

| Tool | Description |
|------|-------------|
| `confluence_upsert_pages` | Batch create-or-update with preserve-on-omit body semantics + per-page status + partial-failure shape |
| `confluence_set_page_properties` | Metadata-only write (page_width, emoji, labels) — physically cannot touch body or title |

### Output Formats

All tools accept a `format` parameter:

| Format | Default for | Description |
|--------|-------------|-------------|
| `toon` | Lists (search, comments) | TSV with header — shape once, data many. 30-60% fewer tokens than JSON |
| `json` | Single entities (get_issue) | Standard JSON with metadata envelope |

List responses use a compact TSV-style format (header row + tab-separated values) inspired by [TOON](https://toonformat.dev). This is the same approach a2db uses — column names appear once, then just values. For a 50-issue search result, this typically saves **40-60% of tokens** compared to JSON.

**TSV example (search results):**
```
# search (23 results, 50ms, truncated: False)
key	summary	assignee	status
PROJ-142	Fix auth timeout	Alice Smith	In Progress
PROJ-141	Add search filters	Bob Jones	To Do
```

**JSON example (single issue):**
```json
{
  "data": {"key": "PROJ-142", "fields": {"summary": "Fix auth timeout", ...}},
  "count": 1,
  "truncated": false,
  "time_ms": 85
}
```

### Error Enrichment

When something fails, a2atlassian tells the agent what to do:

```
Field 'asignee' does not exist
Did you mean: assignee?
```

```
Connection 'myproject' is read-only.
Run: a2atlassian login -p myproject --read-only false
```

**Quirks handled automatically:**
- Assignee requires display name (not `712020:` account IDs) — auto-detected with hint
- Parent field must be plain string — `{"key": "PROJ-14"}` normalized to `"PROJ-14"` silently
- Issue type conversion not supported via API — clear Jira UI instructions provided

## Security

### Read-Only by Default

Every connection starts read-only. Write tools check the connection flag before executing:

```
Connection 'myproject' is read-only.
Re-run 'a2atlassian login -p myproject --read-only false' to enable writes.
```

The human operator controls write access — not the agent.

### Credential Storage

Connections saved via `login` go to `~/.config/a2atlassian/connections/` as TOML files:

- **File permissions:** `0600` (owner read/write only)
- **`${ATLASSIAN_TOKEN}` syntax** — env var references stored literally, expanded at runtime
- **No secrets in output** — `list_connections` shows project name, URL, and mode — never tokens
- **Ephemeral mode** — `--register` keeps credentials in memory only, never written to disk

### Connection Scoping

Use `--scope` to limit which saved connections a specific MCP instance can access:

```bash
# Project config — only myproject visible, even if other connections are saved
uvx --from a2atlassian a2atlassian-mcp --scope myproject
```

Project-level MCP configs (`.claude/mcp.json`) override global configs — each repo sees only its own connections.

### Rate Limiting

Built-in retry with exponential backoff for Atlassian's rate limits (429) and transient server errors (500). Two retries at 1s and 3s intervals before surfacing the error.

## Comparison

| Feature | a2atlassian | Rovo (official) | sooperset/mcp-atlassian |
|---------|-------------|-----------------|------------------------|
| **Setup** | `pip install` | OAuth + Docker | Docker + .env + mcp-remote |
| **Tools in context** | ~35 (loaded on demand) | ~72 | ~72 |
| **Connection management** | TOML + `--register` + `--scope` | Per-session OAuth | .env file |
| **Multi-project** | Yes (scoped) | No | One .env per setup |
| **Read-only default** | Yes (per-connection) | No | No |
| **Output format** | TSV + JSON | JSON | JSON |
| **Error enrichment** | Field suggestions, quirk fixes | Generic errors | Generic errors |
| **Quirk handling** | Auto-fix (assignee, parent) | Documented workarounds | Documented workarounds |
| **Rate limiting** | Built-in retry | No | No |
| **CLI** | Yes | No | No |
| **License** | Apache 2.0 | Proprietary | MIT |

## Roadmap

**Shipped:** Jira full surface (v0.3.0) · Confluence core + markdown-to-storage with full CommonMark + GFM fidelity (v0.4.0, v0.5.2) · 1Password `op://` token refs (v0.5.1) · metadata-only Confluence writes + preserve-on-omit body semantics (v0.5.2).

**Next:** `confluence_delete_page`, Confluence comments + attachments, Confluence integration-test path. Backlog in [`TODO.md`](TODO.md).

## Setup by Environment

### Local (macOS / Linux)

```bash
# Recommended
uv tool install a2atlassian

# Or with pip
pip install a2atlassian

# CLI
a2atlassian login -p myproject --url https://mysite.atlassian.net --email me@co.com --token "$TOKEN"

# Or add as MCP server (see Quick Start)
```

### CI / Automation

```bash
uv tool install a2atlassian

# Pre-configured — no login needed
uvx --from a2atlassian a2atlassian-mcp --register ci https://mysite.atlassian.net ci-user@co.com "${CI_ATLASSIAN_TOKEN}"
```

## Development

```bash
make bootstrap   # Install deps + pnpm + git hooks
make check       # Lint + test + coverage-diff + security (full gate)
make test        # Tests with coverage
make lint        # agent-harness + jscpd + actionlint (never modifies files)
make fix         # Auto-fix + lint
make similar     # Advisory: report similarly-named functions/classes
```

Linters: `ruff` + `ty` (via agent-harness), `yamllint`, `jscpd` (copy-paste
detection via pnpm), `actionlint` (GitHub Actions workflows). Pre-commit
hooks run `agent-harness fix` + lint on every commit. Install `pnpm` and
`actionlint` via `brew install pnpm actionlint`.

## License

Apache 2.0

---

<p align="center">
  <sub>🏢 Agent-first Atlassian access since 2025.</sub>
</p>
<p align="center">
  <sub>Built by <a href="https://github.com/iorlas">Denis Tomilin</a></sub>
</p>

<!-- mcp-name: io.github.yoselabs/a2atlassian -->
