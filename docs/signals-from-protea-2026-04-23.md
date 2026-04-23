# Signals from Protea — 2026-04-23

Pre-triaged bundle for the a2atlassian maintainer agent. Synthesizes five
Protea-side reflection signals (2105, 2120, 2140, 2210, 0714, 0733) into a
single actionable list, ordered by priority. Each item carries a status tag:

- **✅ FIXED** — landed in this repo (commit hash noted).
- **🛠 OPEN** — not yet addressed; actionable here.
- **↗ UPSTREAM** — outside a2atlassian scope (routed to other owner).

Sources:

- `Evolution/signals/2026-04-23-2105-a2atlassian-confluence-gaps.yaml`
- `Evolution/signals/2026-04-23-2120-protea-atlassian-session-scan.yaml`
- `Evolution/signals/2026-04-23-2140-file-state-friction.yaml` (Claude Code tooling; not a2atlassian)
- `Evolution/signals/2026-04-23-2210-protea-final-pass.yaml`
- `Evolution/signals/2026-04-23-0714-a2atlassian-page-width-silent-fail.yaml`
- `Evolution/signals/2026-04-23-0733-confluence-near-miss-data-loss.yaml`

---

## S1 — `jira_get_boards` attribute error  🛠 OPEN

`jira_get_boards(connection=protea)` raises `'Jira' object has no attribute
'boards'`. Every Protea daily report has to fall back to sooperset for
sprint discovery.

Likely root cause: `atlassian-python-api` 4.x exposes boards under
`Jira.boards` only when the agile module is imported, or the method name
has shifted. Needs verification against the installed version.

**Fix direction:** either switch to `Jira.get_all_agile_boards()` or import
the agile sub-client. Add a fixture test against a recorded board-list
response.

---

## S2 — No Confluence tools in a2atlassian  ✅ FIXED (v0.4.0, commit 3f36959)

Confluence domain (pages, search, upsert, labels, emoji, page_width)
shipped. Remaining parity items tracked in `TODO.md` (delete_page,
comments, attachments).

---

## S3 — `page_width` silently ignored on update  ✅ FIXED (commit f232b3e)

Width went through `set_page_property` (POST, create-only); conflicts
swallowed by the batch handler. Now uses `_upsert_page_property` helper:
GET → `update_page_property` with version bump, fallback to POST on 404.
Same fix applied to `emoji`.

---

## S4 — Lossy markdown → storage converter  ✅ FIXED (this session)

Hand-rolled translator rendered `**bold**`, `*italic*`, bullets, numbered
lists, setext headers, and `---` horizontal rules as literal text. Replaced
with `markdown-it-py` + `mdit-py-plugins` (tables, strikethrough, tasklist)
in `content_format.py`. Preserved hooks: `<details>` → expand macro, raw
`<ac:…>` passthrough, `@user:ACCOUNT_ID` mention shorthand, fenced code →
`ac:code` macro. All 31 content-format tests pass, including new coverage
for bold/italic/bullets/numbered/HR/blockquote/strikethrough/setext.

---

## S5 — `content: ""` destructively wipes page body  ✅ FIXED (this session)

`confluence_upsert_pages` with `content: ""` on a known `page_id` wiped the
body. Caused a near-miss data-loss event on 2026-04-23. Now:

- Omit `content` entirely → page body is preserved (status
  `"metadata-updated"`).
- Empty string `""` is explicit and still wipes (callers that want this
  keep it).
- Creating a new page with `content=None` raises `ValueError` early.

Summary shape gained a `metadata_updated` counter.

---

## S6 — No metadata-only write path  ✅ FIXED (this session)

Added `confluence_set_page_properties(connection, page_id, page_width?,
emoji?, labels?)`. Physically cannot touch body or title. Useful for safe
width/emoji flips on live pages without any data-loss risk. Verifies page
existence up-front; raises cleanly on missing `page_id`.

---

## S7 — Pydantic response-parse crash on every tool call  ✅ FIXED (commit f232b3e)

Tool functions declared `-> OperationResult` but `@mcp_tool` wraps them to
return a JSON/TOON string. MCP ≥1.9 validates output against the declared
schema, so the string failed validation. Decorator now rewrites the
annotation to `str` on both the wrapper and its `__wrapped__` target.
Regression test: every registered tool's return hint is `str`;
`fn_metadata.convert_result` round-trips.

---

## S8 — `connection` parameter vs Jira project key confusion  ✅ FIXED (this session)

Highest-volume schema-confusion across Protea sessions (5 wrong / 96 right
in one session). `connection` is the saved a2atlassian connection name
(e.g. `"protea"`), not the Jira project key (`"PE0"`) or Confluence space
key. Clarifier hoisted to server `instructions` (shown in every MCP
preamble), and repeated on the two newest tool docstrings
(`confluence_upsert_pages`, `confluence_set_page_properties`).

Follow-up idea: when `Connection not found: X` fires, list available
connection names in the error body. Tracked as nice-to-have.

---

## S9 — Confluence upsert idempotency  ✅ FIXED (v0.4.0, 982be9e)

Daily-report re-runs used to fail with "page already exists with the same
TITLE". `confluence_upsert_pages` now resolves identity by `page_id` →
`parent_id + title` → `space + title` and updates in place. Batch-level
partial failures no longer raise; per-page errors surface in `failed[]`
with `error_category`.

---

## S10 — Fabric-editor rejects certain storage macros  🛠 OPEN

`confluence_create_page` with `content_format: "storage"` occasionally
returns `BadRequestException: Content contains unsupported extensions and
cannot be edited in Fabric editor`. No hint as to which extensions.

**Fix direction:** (a) document the known-safe macro palette
(info/note/warning/expand/code/children-display/jira-issues), (b) surface
the raw Confluence error body verbatim so the caller can see which
extension tripped, (c) optional `editor` hint parameter.

Low frequency (2 occurrences in a week); acceptable to punt to a follow-up
release.

---

## S11 — `jira_search` result overflow  🛠 OPEN (partially mitigated)

Broad JQL queries return 50k–120k character results and exceed the tool
ceiling. Already mitigated by `fields=minimal` default intent, but Protea
sessions still hit this on wide selections.

**Fix direction:**

- Default `limit=50` (already the case in most paths — audit).
- Default `fields` to a lean set (`key, summary, status, assignee,
  priority, updated`) unless caller specifies.
- `jira_search_count` already exists — emphasize it in tool docs as the
  pre-check for "is this going to be huge?"

---

## S12 — Tool-XML contamination in `content` field  ↗ UPSTREAM / 🛠 OPEN

Seen in session `3fc516da`: `confluence_create_page`'s `content` field
received literal `</content>\n<parameter name="content_format">…`. Agent
scaffolding leaked into the payload. Server returned a misleading
permission error rather than a clear "contamination" error.

**Fix direction:** add server-side validation — if `content` contains a
literal `<parameter name=` token, reject with "content appears to contain
tool-invocation scaffolding; `content_format` must be a separate top-level
argument." Low-risk guard; catches agent bugs early.

---

## S13 — Namespace confusion (a2atlassian ↔ mcp__atlassian)  ↗ UPSTREAM

Two MCP connectors expose nearly identical Jira tool names. When the agent
picks the wrong one, errors are recoverable but burn turns + ToolSearch
cycles.

**Action:** not fixable inside a2atlassian alone. Routed to Protea-side
CLAUDE.md (prescriptive wording) and a future `protea-atlassian` K-skill
that codifies the preferred namespace.

---

## S14 — Worklog author misattribution  🛠 OPEN (ergonomics)

Protea PM (Denis) proxy-logs hours on team members' tickets. JQL
`worklogAuthor = {person}` excludes those hours, producing false gaps in
reports.

**Fix direction:** a convenience tool `jira_get_person_daily_hours(
assignee, date, project)` that queries per-ticket worklogs and attributes
to `assignee` regardless of logger. Not critical — can also live in the
daily-report prompt — but the connector is the right home for the correct
query shape.

---

## Out of scope / routed elsewhere

- **File-state friction (Write/Edit "not read"/"modified since read")** —
  Claude Code tooling, not a2atlassian (signal 2140).
- **Attention-ordering / inverted-pyramid** on daily reports — Protea
  prompt concern (signal 2210 §D).
- **Transport/channel constraint probing, roster-completeness, commit
  hygiene, Epic-vs-Story drift, Vitalii-CR semantics** — all Protea prompt
  / CLAUDE.md concerns (signal 2210 §E–§I).

---

## Summary: what landed this pass

In commit `f232b3e`:

- S7 pydantic crash → fixed
- S3 page_width / emoji on existing pages → fixed

In this follow-up commit (v0.5.2 target):

- S4 markdown fidelity (full CommonMark + GFM via markdown-it-py)
- S5 `content` preserve-on-omit semantics
- S6 `confluence_set_page_properties` metadata-only tool
- S8 `connection` param clarifier in server instructions
- Adopted linters from a2sdlc-engine: `jscpd` copy-paste detection,
  `actionlint` for GH workflows, `find_similar.py` advisory script,
  `pytest-xdist`/`timeout`/`recording` in dev deps.

Remaining open: S1 (boards), S10 (fabric rejection messaging), S11
(search overflow defaults audit), S12 (content contamination guard),
S14 (worklog helper).
