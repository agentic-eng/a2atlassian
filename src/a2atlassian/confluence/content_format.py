"""Markdown → Confluence storage-format translator.

Uses markdown-it-py (CommonMark + GFM plugins) as the core renderer, then
post-processes HTML into Confluence storage format:

- Fenced code blocks (``) → ``<ac:structured-macro ac:name="code">``.
- ``<details>`` blocks → ``<ac:structured-macro ac:name="expand">``.
- ``@user:ACCOUNT_ID`` shorthand → ``<ac:link><ri:user ri:account-id="…"/></ac:link>``.
- Top-level blocks that *start* with a raw tag (``<ac:…>``, ``<ri:…>``, or any
  HTML element) pass through unchanged — the escape hatch for Confluence
  macros / layouts that markdown cannot express.

The translator is intentionally lossy-safe: anything markdown-it-py can render
to standard HTML produces valid storage format; richer Confluence constructs
require raw storage passthrough.
"""

from __future__ import annotations

import html
import re

from markdown_it import MarkdownIt
from mdit_py_plugins.tasklists import tasklists_plugin

_MENTION_RE = re.compile(r"@user:([A-Za-z0-9:_-]+)")

_DETAILS_OPEN = "<details>"
_DETAILS_CLOSE = "</details>"
_SUMMARY_OPEN = "<summary>"
_SUMMARY_CLOSE = "</summary>"


def _build_md() -> MarkdownIt:
    md = (
        MarkdownIt("commonmark", {"html": True, "breaks": False, "linkify": True})
        .enable(["table", "strikethrough"])
        .use(tasklists_plugin, enabled=True)
    )
    return md


_MD = _build_md()


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
            break
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
    regions = _extract_outermost_details(text)
    if not regions:
        return text
    pieces: list[str] = []
    cursor = 0
    for start, end, title, body in regions:
        pieces.append(text[cursor:start])
        inner = markdown_to_storage(body.strip())
        pieces.append(
            '<ac:structured-macro ac:name="expand">'
            f'<ac:parameter ac:name="title">{title}</ac:parameter>'
            f"<ac:rich-text-body>{inner}</ac:rich-text-body>"
            "</ac:structured-macro>"
        )
        cursor = end
    pieces.append(text[cursor:])
    return "".join(pieces)


_CODE_BLOCK_RE = re.compile(
    r'<pre><code(?:\s+class="language-(?P<lang>[^"]+)")?>(?P<body>.*?)</code></pre>',
    re.DOTALL,
)


def _code_to_macro(match: re.Match[str]) -> str:
    lang = match.group("lang") or ""
    body = html.unescape(match.group("body"))
    body = body.removesuffix("\n")
    lang_param = f'<ac:parameter ac:name="language">{lang}</ac:parameter>' if lang else ""
    return (
        f'<ac:structured-macro ac:name="code">{lang_param}<ac:plain-text-body><![CDATA[{body}]]></ac:plain-text-body></ac:structured-macro>'
    )


_MENTION_RENDERED_RE = re.compile(r"@user:([A-Za-z0-9:_-]+)")


def _apply_mentions(html_text: str) -> str:
    def repl(m: re.Match[str]) -> str:
        account_id = m.group(1)
        return f'<ac:link><ri:user ri:account-id="{account_id}"/></ac:link>'

    return _MENTION_RENDERED_RE.sub(repl, html_text)


def _is_raw_storage_block(block: str) -> bool:
    """Top-level blocks that begin with a raw tag pass through unchanged."""
    s = block.lstrip()
    return s.startswith("<")


def _split_top_level_blocks(text: str) -> list[tuple[str, bool]]:
    """Split on blank lines. Return (block, is_raw) pairs.

    Fenced code blocks are kept intact.
    """
    lines = text.splitlines()
    blocks: list[tuple[str, bool]] = []
    buf: list[str] = []
    in_fence = False
    fence_re = re.compile(r"^```")
    for line in lines:
        if fence_re.match(line.strip()):
            buf.append(line)
            in_fence = not in_fence
            continue
        if in_fence:
            buf.append(line)
            continue
        if line.strip() == "":
            if buf:
                block = "\n".join(buf)
                blocks.append((block, _is_raw_storage_block(block)))
                buf = []
            continue
        buf.append(line)
    if buf:
        block = "\n".join(buf)
        blocks.append((block, _is_raw_storage_block(block)))
    return blocks


_TAG_NL_RE = re.compile(r">\s*\n\s*<")
_LEADING_NL_RE = re.compile(r"^\s+|\s+$")


def _normalize_html(out: str) -> str:
    out = _TAG_NL_RE.sub("><", out)
    return _LEADING_NL_RE.sub("", out)


def _render_markdown_block(block: str) -> str:
    out = _MD.render(block)
    out = _CODE_BLOCK_RE.sub(_code_to_macro, out)
    out = _apply_mentions(out)
    return _normalize_html(out)


def markdown_to_storage(text: str) -> str:
    """Translate markdown source to Confluence storage format XHTML."""
    if not text:
        return ""
    text = _apply_details(text)
    pieces: list[str] = []
    for block, is_raw in _split_top_level_blocks(text):
        if is_raw:
            pieces.append(block.strip())
        else:
            pieces.append(_render_markdown_block(block))
    return "".join(pieces)
