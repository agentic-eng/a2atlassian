"""Tests for the CLI frontend."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

if TYPE_CHECKING:
    from pathlib import Path

import pytest
from click.testing import CliRunner

from a2atlassian.cli import cli


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestCli:
    def test_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "a2atlassian" in result.output

    def test_version(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestLogin:
    def test_login_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["login", "--help"])
        assert result.exit_code == 0
        assert "--connection" in result.output or "-c" in result.output

    @patch("a2atlassian.cli.AtlassianClient")
    def test_login_success(self, mock_client_cls, runner: CliRunner, tmp_path: Path) -> None:
        mock_instance = mock_client_cls.return_value
        mock_instance.validate = AsyncMock(return_value={"displayName": "Alice"})

        with patch("a2atlassian.cli._store") as mock_store_fn:
            store = mock_store_fn.return_value
            store.save.return_value = tmp_path / "test.toml"
            result = runner.invoke(
                cli,
                [
                    "login",
                    "-c",
                    "test",
                    "--url",
                    "https://test.atlassian.net",
                    "--email",
                    "t@t.com",
                    "--token",
                    "tok123",
                ],
            )

        assert result.exit_code == 0
        assert "saved" in result.output.lower() or "Alice" in result.output


class TestLogout:
    def test_logout_success(self, runner: CliRunner) -> None:
        with patch("a2atlassian.cli._store"):
            result = runner.invoke(cli, ["logout", "-c", "test"])
        assert result.exit_code == 0
        assert "removed" in result.output.lower()


class TestConnections:
    def test_list_empty(self, runner: CliRunner) -> None:
        with patch("a2atlassian.cli._store") as mock_store_fn:
            mock_store_fn.return_value.list_connections.return_value = []
            result = runner.invoke(cli, ["connections"])
        assert result.exit_code == 0
        assert "no connections" in result.output.lower()


def _patch_cli_for_login_test(monkeypatch, tmp_path):
    """Patch AtlassianClient.validate to stub network + point store at tmp_path."""
    from unittest.mock import AsyncMock

    from a2atlassian import cli as cli_mod
    from a2atlassian.connections import ConnectionStore

    monkeypatch.setattr(
        "a2atlassian.client.AtlassianClient.validate",
        AsyncMock(return_value={"displayName": "test-user"}),
    )
    monkeypatch.setattr(cli_mod, "_store", lambda: ConnectionStore(tmp_path))


class TestLoginTimezone:
    def test_iana_is_stored_as_is(self, tmp_path, monkeypatch) -> None:
        _patch_cli_for_login_test(monkeypatch, tmp_path)
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "login",
                "-c",
                "c1",
                "--url",
                "https://x.atlassian.net",
                "--email",
                "a@b.com",
                "--token",
                "t",
                "--tz",
                "Europe/Istanbul",
            ],
        )
        assert result.exit_code == 0, result.output
        content = (tmp_path / "c1.toml").read_text()
        assert 'timezone = "Europe/Istanbul"' in content

    def test_cet_alias_resolves_to_iana(self, tmp_path, monkeypatch) -> None:
        _patch_cli_for_login_test(monkeypatch, tmp_path)
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "login",
                "-c",
                "c1",
                "--url",
                "https://x.atlassian.net",
                "--email",
                "a@b.com",
                "--token",
                "t",
                "--tz",
                "CET",
            ],
        )
        assert result.exit_code == 0, result.output
        content = (tmp_path / "c1.toml").read_text()
        assert 'timezone = "Europe/Paris"' in content

    def test_et_alias_resolves_to_iana(self, tmp_path, monkeypatch) -> None:
        _patch_cli_for_login_test(monkeypatch, tmp_path)
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "login",
                "-c",
                "c1",
                "--url",
                "https://x.atlassian.net",
                "--email",
                "a@b.com",
                "--token",
                "t",
                "--tz",
                "ET",
            ],
        )
        assert result.exit_code == 0, result.output
        content = (tmp_path / "c1.toml").read_text()
        assert 'timezone = "America/New_York"' in content

    def test_utc_default(self, tmp_path, monkeypatch) -> None:
        _patch_cli_for_login_test(monkeypatch, tmp_path)
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "login",
                "-c",
                "c1",
                "--url",
                "https://x.atlassian.net",
                "--email",
                "a@b.com",
                "--token",
                "t",
            ],
        )
        assert result.exit_code == 0, result.output
        content = (tmp_path / "c1.toml").read_text()
        assert 'timezone = "UTC"' in content

    def test_invalid_tz_fails(self, tmp_path, monkeypatch) -> None:
        _patch_cli_for_login_test(monkeypatch, tmp_path)
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "login",
                "-c",
                "c1",
                "--url",
                "https://x.atlassian.net",
                "--email",
                "a@b.com",
                "--token",
                "t",
                "--tz",
                "NotAZone",
            ],
        )
        assert result.exit_code != 0
        assert "Unknown timezone" in result.output


class TestLoginWorklogAdmins:
    def test_multiple_admins(self, tmp_path, monkeypatch) -> None:
        _patch_cli_for_login_test(monkeypatch, tmp_path)
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "login",
                "-c",
                "c1",
                "--url",
                "https://x.atlassian.net",
                "--email",
                "a@b.com",
                "--token",
                "t",
                "--worklog-admin",
                "a@x.com",
                "--worklog-admin",
                "b@x.com",
            ],
        )
        assert result.exit_code == 0, result.output
        content = (tmp_path / "c1.toml").read_text()
        assert '"a@x.com"' in content
        assert '"b@x.com"' in content

    def test_no_admins_default_empty(self, tmp_path, monkeypatch) -> None:
        _patch_cli_for_login_test(monkeypatch, tmp_path)
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "login",
                "-c",
                "c1",
                "--url",
                "https://x.atlassian.net",
                "--email",
                "a@b.com",
                "--token",
                "t",
            ],
        )
        assert result.exit_code == 0, result.output
        content = (tmp_path / "c1.toml").read_text()
        assert "worklog_admins = []" in content
