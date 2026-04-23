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
