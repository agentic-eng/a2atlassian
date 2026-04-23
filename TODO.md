# TODO

Backlog for a2atlassian after v0.5.1.

## Confluence parity (v0.6.0 target)

- [ ] `confluence_delete_page` — closes the CRUD asymmetry. ~5-line op + tool + 2 tests.
- [ ] Confluence `--integration` test path — mirror `tests/integration/` from Jira against a real Confluence space. Catches `atlassian-python-api` + Confluence API drift.

## Confluence content tools (ship only if the workflow hits the limit)

- [ ] `confluence_add_comment` / `confluence_get_comments` — inline discussion on pages.
- [ ] `confluence_attach_file` — upload images/artifacts for reports with diagrams. `Confluence.attach_file()` exists in atlassian-python-api.
- [ ] `confluence_add_label` / `confluence_remove_label` — post-creation label management (labels on upsert already supported).

## Ergonomics

- [ ] `a2atlassian test <connection>` CLI command — ping `/myself` to verify saved creds still work (especially the `op://` path when 1Password is signed out).
- [ ] `XDG_CONFIG_HOME` support — currently `~/.config` is hardcoded in `config.py`; respect the env var for portability across machines.
- [ ] Fix `a2atlassian --version` output (currently hardcodes `0.1.0` somewhere; should read from package metadata).

## Skip unless requested

- Keyring backend (op:// already covers secure-secret storage)
- Token rotation detection (Atlassian API tokens don't expire server-side)
- Recursive env-var references like `${PREFIX_${SUFFIX}}`
- Confluence `translation_warnings` field — HTML passthrough is already the graceful fallback
- Confluence restrictions API — niche
- ADF (Atlassian Document Format) as content-format option — storage format still canonical
- `doctor` / diagnostic command across all connections — premature
