"""Tests for the @mcp_tool decorator."""

from __future__ import annotations

from typing import Literal

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
        assert "a" in result
        assert "b" in result
        assert "c" in result

    async def test_enum_validation_multiple_literals(self) -> None:
        """Both format and detail being invalid surfaces at least one clearly."""
        enricher = ErrorEnricher()

        @mcp_tool(enricher)
        async def t(connection: str, format: Literal["toon", "json"] = "toon") -> OperationResult:  # noqa: A002
            return OperationResult(name="t", data=[], count=0, truncated=False, time_ms=0)

        result = await t(connection="c1", format="tooon")  # type: ignore[arg-type]
        assert "Invalid value" in result
        assert "format" in result
