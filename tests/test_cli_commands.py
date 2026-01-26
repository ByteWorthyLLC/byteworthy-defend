"""Tests for CLI commands.

Tests cover:
- Monitor management commands (start, stop, status, enable, disable)
- Alert management commands (list, clear)
- Rule management commands (list, add, remove)
- Threat intelligence commands (check ip/file/package)
- Whitelist management commands (add, remove)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from hifzdefend.cli.commands import cli
from hifzdefend.threat_intel.api_clients import ThreatIntelResponse, ThreatLevel


class TestMonitorCommands:
    """Test monitor management commands."""

    def test_monitor_start(self):
        """Test monitor start command."""
        runner = CliRunner()

        with patch("hifzdefend.cli.commands.MonitorManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_status.return_value = {
                "package_monitor": {
                    "running": True,
                    "events_generated": 0,
                }
            }

            with patch("hifzdefend.cli.commands.asyncio.run"):
                result = runner.invoke(cli, ["monitor", "start"])

            assert result.exit_code == 0
            assert "Starting Security Monitors" in result.output
            mock_manager.start_all.assert_called_once()

    def test_monitor_stop(self):
        """Test monitor stop command."""
        runner = CliRunner()

        with patch("hifzdefend.cli.commands.MonitorManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager

            with patch("hifzdefend.cli.commands.asyncio.run"):
                result = runner.invoke(cli, ["monitor", "stop"])

            assert result.exit_code == 0
            assert "Stopping Security Monitors" in result.output
            mock_manager.stop_all.assert_called_once()

    def test_monitor_status(self):
        """Test monitor status command."""
        runner = CliRunner()

        with patch("hifzdefend.cli.commands.MonitorManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_status.return_value = {
                "event_bus": {
                    "running": True,
                    "events_processed": 42,
                    "queue_size": 0,
                },
                "package_monitor": {
                    "running": True,
                    "enabled": True,
                    "events_generated": 5,
                    "last_check": "2024-01-01 12:00:00",
                },
            }

            result = runner.invoke(cli, ["monitor", "status"])

            assert result.exit_code == 0
            assert "Monitor Status" in result.output
            assert "Event Bus" in result.output
            assert "package_monitor" in result.output

    def test_monitor_enable(self):
        """Test monitor enable command."""
        runner = CliRunner()

        result = runner.invoke(cli, ["monitor", "enable", "package_monitor"])

        assert result.exit_code == 0
        assert "Enabling Monitor" in result.output
        assert "package_monitor" in result.output

    def test_monitor_disable(self):
        """Test monitor disable command."""
        runner = CliRunner()

        result = runner.invoke(cli, ["monitor", "disable", "package_monitor"])

        assert result.exit_code == 0
        assert "Disabling Monitor" in result.output
        assert "package_monitor" in result.output


class TestAlertsCommands:
    """Test alerts management commands."""

    def test_alerts_list(self):
        """Test alerts list command."""
        runner = CliRunner()

        result = runner.invoke(cli, ["alerts", "list"])

        assert result.exit_code == 0
        assert "Security Alerts" in result.output

    def test_alerts_list_with_limit(self):
        """Test alerts list with limit option."""
        runner = CliRunner()

        result = runner.invoke(cli, ["alerts", "list", "--limit", "10"])

        assert result.exit_code == 0
        assert "Security Alerts" in result.output

    def test_alerts_list_with_severity_filter(self):
        """Test alerts list with severity filter."""
        runner = CliRunner()

        result = runner.invoke(cli, ["alerts", "list", "--severity", "critical"])

        assert result.exit_code == 0
        assert "Security Alerts" in result.output

    def test_alerts_clear(self):
        """Test alerts clear command."""
        runner = CliRunner()

        result = runner.invoke(cli, ["alerts", "clear"])

        assert result.exit_code == 0
        assert "Clear Alert History" in result.output


class TestRulesCommands:
    """Test rules management commands."""

    def test_rules_list(self):
        """Test rules list command."""
        runner = CliRunner()

        with patch("hifzdefend.cli.commands.RulesEngine") as mock_engine_class:
            mock_engine = MagicMock()
            mock_engine_class.return_value = mock_engine

            result = runner.invoke(cli, ["rules", "list"])

            assert result.exit_code == 0
            assert "Active Detection Rules" in result.output
            assert "YARA Rules" in result.output
            assert "File Blocking Rules" in result.output

    def test_rules_add(self):
        """Test rules add command."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create a test rule file
            with open("test_rule.yar", "w") as f:
                f.write('rule test { condition: true }')

            with patch("hifzdefend.cli.commands.Path.mkdir"):
                result = runner.invoke(cli, ["rules", "add", "test_rule.yar"])

            assert result.exit_code == 0
            assert "Adding Custom Rule" in result.output
            assert "Rule added" in result.output

    def test_rules_remove(self):
        """Test rules remove command."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create custom signatures directory structure
            import os
            os.makedirs(".hifzdefend/signatures/custom", exist_ok=True)

            # Create a test rule file
            with open(".hifzdefend/signatures/custom/test_rule.yar", "w") as f:
                f.write('rule test { condition: true }')

            with patch("hifzdefend.cli.commands.get_config") as mock_config:
                mock_cfg = MagicMock()
                mock_cfg.rules.custom_signatures_path = ".hifzdefend/signatures/custom"
                mock_config.return_value = mock_cfg

                result = runner.invoke(cli, ["rules", "remove", "test_rule.yar"])

            assert result.exit_code == 0
            assert "Removing Custom Rule" in result.output


class TestThreatIntelCommands:
    """Test threat intelligence commands."""

    def test_threat_intel_check_ip(self):
        """Test threat intel check for IP address."""
        runner = CliRunner()

        mock_response = ThreatIntelResponse(
            source="abuseipdb",
            query="8.8.8.8",
            threat_level=ThreatLevel.CLEAN,
            threat_score=0,
            details={"country": "US"},
        )

        with patch("hifzdefend.cli.commands.ThreatIntelligenceManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.check_ip_reputation = AsyncMock(return_value=mock_response)
            mock_manager.close = AsyncMock()

            with patch("hifzdefend.cli.commands.asyncio.run") as mock_run:
                # Make asyncio.run return the mock response for check_ip_reputation
                def run_side_effect(coro):
                    import asyncio
                    if asyncio.iscoroutine(coro):
                        # Check which coroutine it is
                        coro.close()  # Clean up
                        return mock_response
                    return None

                mock_run.side_effect = run_side_effect

                result = runner.invoke(cli, ["threat-intel", "check", "ip", "8.8.8.8"])

            assert result.exit_code == 0
            assert "Threat Intelligence Check" in result.output
            assert "ip" in result.output

    def test_threat_intel_check_file(self):
        """Test threat intel check for file hash."""
        runner = CliRunner()

        file_hash = "a" * 64
        mock_response = ThreatIntelResponse(
            source="virustotal",
            query=file_hash,
            threat_level=ThreatLevel.CLEAN,
            threat_score=0,
            details={"malicious": 0},
        )

        with patch("hifzdefend.cli.commands.ThreatIntelligenceManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.check_file_reputation = AsyncMock(return_value=mock_response)
            mock_manager.close = AsyncMock()

            with patch("hifzdefend.cli.commands.asyncio.run") as mock_run:
                def run_side_effect(coro):
                    import asyncio
                    if asyncio.iscoroutine(coro):
                        coro.close()
                        return mock_response
                    return None

                mock_run.side_effect = run_side_effect

                result = runner.invoke(cli, ["threat-intel", "check", "file", file_hash])

            assert result.exit_code == 0
            assert "Threat Intelligence Check" in result.output
            assert "file" in result.output

    def test_threat_intel_check_package_npm(self):
        """Test threat intel check for npm package."""
        runner = CliRunner()

        mock_response = ThreatIntelResponse(
            source="snyk",
            query="lodash@4.17.21",
            threat_level=ThreatLevel.CLEAN,
            threat_score=0,
            details={"vulnerability_count": 0},
        )

        with patch("hifzdefend.cli.commands.ThreatIntelligenceManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.check_package_security = AsyncMock(return_value=mock_response)
            mock_manager.close = AsyncMock()

            with patch("hifzdefend.cli.commands.asyncio.run") as mock_run:
                def run_side_effect(coro):
                    import asyncio
                    if asyncio.iscoroutine(coro):
                        coro.close()
                        return mock_response
                    return None

                mock_run.side_effect = run_side_effect

                result = runner.invoke(cli, ["threat-intel", "check", "package", "lodash@4.17.21"])

            assert result.exit_code == 0
            assert "Threat Intelligence Check" in result.output
            assert "package" in result.output

    def test_threat_intel_check_package_pypi(self):
        """Test threat intel check for PyPI package."""
        runner = CliRunner()

        mock_response = ThreatIntelResponse(
            source="snyk",
            query="requests==2.28.0",
            threat_level=ThreatLevel.CLEAN,
            threat_score=0,
            details={"vulnerability_count": 0},
        )

        with patch("hifzdefend.cli.commands.ThreatIntelligenceManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.check_package_security = AsyncMock(return_value=mock_response)
            mock_manager.close = AsyncMock()

            with patch("hifzdefend.cli.commands.asyncio.run") as mock_run:
                def run_side_effect(coro):
                    import asyncio
                    if asyncio.iscoroutine(coro):
                        coro.close()
                        return mock_response
                    return None

                mock_run.side_effect = run_side_effect

                result = runner.invoke(cli, ["threat-intel", "check", "package", "requests==2.28.0"])

            assert result.exit_code == 0
            assert "Threat Intelligence Check" in result.output


class TestWhitelistCommands:
    """Test whitelist management commands."""

    def test_whitelist_add(self):
        """Test whitelist add command."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create a test executable
            with open("test_app.exe", "w") as f:
                f.write("test")

            result = runner.invoke(cli, ["whitelist", "add", "test_app.exe"])

            assert result.exit_code == 0
            assert "Adding to Whitelist" in result.output

    def test_whitelist_remove(self):
        """Test whitelist remove command."""
        runner = CliRunner()

        result = runner.invoke(cli, ["whitelist", "remove", "test_app.exe"])

        assert result.exit_code == 0
        assert "Removing from Whitelist" in result.output


class TestExistingCommands:
    """Test that existing commands still work."""

    def test_scan_command_exists(self):
        """Test that scan command is still available."""
        runner = CliRunner()

        result = runner.invoke(cli, ["scan", "--help"])

        assert result.exit_code == 0
        assert "Scan a file or directory" in result.output

    def test_status_command_exists(self):
        """Test that status command is still available."""
        runner = CliRunner()

        with patch("hifzdefend.cli.commands.ScanEngine"):
            result = runner.invoke(cli, ["status"])

        assert result.exit_code == 0
        assert "HifzDefend Status" in result.output

    def test_update_command_exists(self):
        """Test that update command is still available."""
        runner = CliRunner()

        result = runner.invoke(cli, ["update", "--help"])

        assert result.exit_code == 0
        assert "Update virus definitions" in result.output

    def test_quarantine_command_exists(self):
        """Test that quarantine command is still available."""
        runner = CliRunner()

        result = runner.invoke(cli, ["quarantine", "--help"])

        assert result.exit_code == 0
        assert "Manually quarantine a file" in result.output

    def test_list_quarantine_command_exists(self):
        """Test that list-quarantine command is still available."""
        runner = CliRunner()

        result = runner.invoke(cli, ["list-quarantine", "--help"])

        assert result.exit_code == 0
        assert "List quarantined files" in result.output

    def test_config_show_command_exists(self):
        """Test that config-show command is still available."""
        runner = CliRunner()

        result = runner.invoke(cli, ["config-show", "--help"])

        assert result.exit_code == 0
        assert "Display current configuration" in result.output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
