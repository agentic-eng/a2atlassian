"""MCP server frontend — server setup, connection management, and tool registration."""

from __future__ import annotations

import sys

from mcp.server.fastmcp import FastMCP

from a2atlassian.client import AtlassianClient
from a2atlassian.config import DEFAULT_CONFIG_DIR
from a2atlassian.connections import ConnectionInfo, ConnectionStore
from a2atlassian.errors import ErrorEnricher
from a2atlassian.jira_read_tools import register_jira_read_tools
from a2atlassian.jira_write_tools import register_jira_write_tools

server = FastMCP(
    "a2atlassian",
    instructions=(
        "Agent-to-Atlassian — work with Jira and Confluence. "
        "Connections are identified by project name. "
        "Use 'login' to save a connection, then call tools with the project name. "
        "Connections are read-only by default; re-login with --read-only false to enable writes. "
        "For security, pass tokens as ${ENV_VAR} references, not literal values. "
        "Default output is TOON for lists (token-efficient), JSON for single entities."
    ),
)

_ephemeral_connections: dict[str, ConnectionInfo] = {}
_scope_filter: list[str] = []
_enricher = ErrorEnricher()


def _store() -> ConnectionStore:
    return ConnectionStore(DEFAULT_CONFIG_DIR)


def _get_connection(project: str) -> ConnectionInfo:
    """Resolve a connection by project name."""
    if project in _ephemeral_connections:
        return _ephemeral_connections[project]
    store = _store()
    conn = store.load(project)
    if _scope_filter and project not in _scope_filter:
        msg = f"Connection '{project}' exists but is not in scope. Available: {', '.join(_scope_filter)}"
        raise FileNotFoundError(msg)
    return conn


def _get_client(project: str) -> AtlassianClient:
    """Resolve a connection and return a client."""
    return AtlassianClient(_get_connection(project))


# --- Connection management tools ---


@server.tool()
async def login(project: str, url: str, email: str, token: str, read_only: bool = True) -> str:
    """Save an Atlassian connection. Validates by calling /myself.

    For security, prefer passing token as ${ENV_VAR} reference (e.g., "${ATLASSIAN_TOKEN}")
    rather than a literal value. The variable is expanded at runtime, never stored resolved.
    """
    info = ConnectionInfo(project=project, url=url, email=email, token=token, read_only=read_only)
    client = AtlassianClient(info)
    user = await client.validate()
    store = _store()
    path = store.save(project, url, email, token, read_only=read_only)
    display_name = user.get("displayName", "unknown")
    return f"Connection saved: {path} (authenticated as {display_name})"


@server.tool()
def logout(project: str) -> str:
    """Remove a saved connection."""
    store = _store()
    store.delete(project)
    return f"Connection removed: {project}"


@server.tool()
def list_connections(project: str | None = None) -> str:
    """List saved connections (no secrets shown)."""
    store = _store()
    saved = store.list_connections(project=project)
    all_conns = list(saved)
    for p, info in _ephemeral_connections.items():
        if project is None or p == project:
            all_conns.append(info)
    if not all_conns:
        return "No connections found."
    lines = []
    for info in all_conns:
        mode = "read-only" if info.read_only else "read-write"
        ephemeral = " [ephemeral]" if info.project in _ephemeral_connections else ""
        lines.append(f"{info.project} ({info.url}) [{mode}]{ephemeral}")
    return "\n".join(lines)


# --- Register Jira tools ---

register_jira_read_tools(server, _get_client, _enricher)
register_jira_write_tools(server, _get_connection, _enricher)


# --- CLI argument parsing ---


def _parse_register_args(args: list[str]) -> list[ConnectionInfo]:
    """Parse --register args: --register project url email token [--rw]"""
    connections = []
    i = 0
    while i < len(args):
        if args[i] == "--register":
            if i + 4 >= len(args):
                msg = f"--register requires 4 arguments (project url email token), got {len(args) - i - 1}"
                raise ValueError(msg)
            project = args[i + 1]
            url = args[i + 2]
            email = args[i + 3]
            token = args[i + 4]
            i += 5
            read_only = True
            if i < len(args) and args[i] == "--rw":
                read_only = False
                i += 1
            connections.append(
                ConnectionInfo(
                    project=project,
                    url=url,
                    email=email,
                    token=token,
                    read_only=read_only,
                )
            )
        else:
            i += 1
    return connections


def _parse_scope_args(args: list[str]) -> list[str]:
    """Parse --scope args: --scope project [--scope project2]"""
    scopes = []
    i = 0
    while i < len(args):
        if args[i] == "--scope" and i + 1 < len(args):
            scopes.append(args[i + 1])
            i += 2
        else:
            i += 1
    return scopes


def main() -> None:
    """Run the MCP server (stdio transport)."""
    global _scope_filter  # noqa: PLW0603

    args = sys.argv[1:]

    for conn in _parse_register_args(args):
        _ephemeral_connections[conn.project] = conn

    _scope_filter = _parse_scope_args(args)

    server.run()


if __name__ == "__main__":
    main()
