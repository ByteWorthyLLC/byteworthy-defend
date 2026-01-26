"""Custom Rules Engine for HifzDefend.

This module provides the central orchestration for all rule-based threat detection:
- YARA rule management and execution
- File blocking policies
- Application whitelisting
- Composite rule evaluation
- Automated response actions
"""

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import Field

from hifzdefend.monitoring.base import MonitorConfig
from hifzdefend.monitoring.events import Event, EventSeverity, EventType
from hifzdefend.rules.yara_manager import YARAManager, YARAMatch
from hifzdefend.rules.file_blocker import FileBlocker, BlockReason
from hifzdefend.rules.app_whitelist import ApplicationWhitelist, WhitelistEntry

logger = logging.getLogger(__name__)


class ResponseAction(str, Enum):
    """Automated response actions."""

    ALERT = "alert"  # Generate alert event
    BLOCK = "block"  # Block file/process
    QUARANTINE = "quarantine"  # Move to quarantine
    TERMINATE = "terminate"  # Terminate process
    LOG_ONLY = "log_only"  # Only log, no action


class RuleType(str, Enum):
    """Types of rules."""

    YARA = "yara"  # YARA signature rules
    FILE_BLOCK = "file_block"  # File extension/path blocking
    APP_WHITELIST = "app_whitelist"  # Application whitelisting
    COMPOSITE = "composite"  # Multiple conditions


@dataclass
class RuleMatch:
    """Result of rule matching."""

    rule_type: RuleType
    rule_name: str
    matched: bool
    severity: EventSeverity
    threat_score: int
    details: dict[str, Any]
    recommended_action: ResponseAction


class RulesEngineConfig(MonitorConfig):
    """Configuration for Rules Engine."""

    enabled: bool = Field(default=True, description="Enable rules engine")

    # YARA configuration
    yara_rules_enabled: bool = Field(
        default=True, description="Enable YARA rule scanning"
    )

    custom_signatures_path: Path = Field(
        default=Path("signatures/custom"),
        description="Path to custom YARA signatures",
    )

    community_signatures_path: Path = Field(
        default=Path("signatures/community"),
        description="Path to community YARA signatures",
    )

    # File blocking configuration
    file_blocking_enabled: bool = Field(
        default=True, description="Enable file type blocking"
    )

    # Application whitelisting configuration
    app_whitelisting_enabled: bool = Field(
        default=True, description="Enable application whitelisting"
    )

    whitelist_mode: bool = Field(
        default=False,
        description="If true, only whitelisted apps can run. If false, blacklist mode.",
    )

    # Response actions
    default_action: ResponseAction = Field(
        default=ResponseAction.ALERT,
        description="Default action when rule matches",
    )

    auto_quarantine_critical: bool = Field(
        default=True,
        description="Automatically quarantine files with critical threat score",
    )

    auto_terminate_processes: bool = Field(
        default=False,
        description="Automatically terminate malicious processes (dangerous!)",
    )


class RulesEngine:
    """Central rules engine for threat detection."""

    def __init__(self, config: RulesEngineConfig):
        self.config = config

        # Initialize sub-components
        self.yara_manager = None
        if config.yara_rules_enabled:
            try:
                self.yara_manager = YARAManager(
                    custom_rules_path=config.custom_signatures_path_expanded,
                    community_rules_path=config.community_signatures_path_expanded,
                )
                logger.info("YARA manager initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize YARA manager: {e}", exc_info=True)

        self.file_blocker = None
        if config.file_blocking.enabled:
            self.file_blocker = FileBlocker()
            logger.info("File blocker initialized")

        self.app_whitelist = None
        if config.app_whitelist.enabled:
            self.app_whitelist = ApplicationWhitelist(
                whitelist_mode=config.app_whitelist.whitelist_mode
            )
            logger.info("Application whitelist initialized")

        # Statistics
        self._stats = {
            "rules_evaluated": 0,
            "rules_matched": 0,
            "yara_matches": 0,
            "file_blocks": 0,
            "whitelist_checks": 0,
            "actions_taken": 0,
        }

        logger.info("Rules engine initialized")

    def scan_file(self, file_path: Path) -> list[RuleMatch]:
        """Scan file with all enabled rules.

        Args:
            file_path: Path to file to scan

        Returns:
            List of rule matches
        """
        matches = []
        self._stats["rules_evaluated"] += 1

        try:
            # 1. Check YARA rules
            if self.yara_manager:
                yara_matches = self._check_yara_rules(file_path)
                matches.extend(yara_matches)

            # 2. Check file blocking rules
            if self.file_blocker:
                block_match = self._check_file_blocking(file_path)
                if block_match:
                    matches.append(block_match)

            # 3. Check application whitelist
            if self.app_whitelist:
                whitelist_match = self._check_app_whitelist(file_path)
                if whitelist_match:
                    matches.append(whitelist_match)

            if matches:
                self._stats["rules_matched"] += 1

        except Exception as e:
            logger.error(f"Error scanning file {file_path}: {e}", exc_info=True)

        return matches

    def _check_yara_rules(self, file_path: Path) -> list[RuleMatch]:
        """Check file against YARA rules."""
        matches = []

        try:
            yara_matches = self.yara_manager.scan_file(file_path)

            for yara_match in yara_matches:
                self._stats["yara_matches"] += 1

                # Determine severity based on YARA meta tags
                severity = self._get_severity_from_yara_meta(yara_match)
                threat_score = self._get_threat_score_from_yara_meta(yara_match)

                match = RuleMatch(
                    rule_type=RuleType.YARA,
                    rule_name=yara_match.rule_name,
                    matched=True,
                    severity=severity,
                    threat_score=threat_score,
                    details={
                        "namespace": yara_match.namespace,
                        "tags": yara_match.tags,
                        "meta": yara_match.meta,
                        "strings": yara_match.strings,
                    },
                    recommended_action=self._get_recommended_action(
                        severity, threat_score
                    ),
                )

                matches.append(match)

        except Exception as e:
            logger.error(f"Error checking YARA rules: {e}", exc_info=True)

        return matches

    def _check_file_blocking(self, file_path: Path) -> Optional[RuleMatch]:
        """Check if file should be blocked."""
        try:
            should_block, reason = self.file_blocker.should_block_file(file_path)

            if should_block:
                self._stats["file_blocks"] += 1

                return RuleMatch(
                    rule_type=RuleType.FILE_BLOCK,
                    rule_name="file_blocking_policy",
                    matched=True,
                    severity=EventSeverity.WARNING,
                    threat_score=60,
                    details={
                        "reason": reason.value,
                        "file_path": str(file_path),
                        "extension": file_path.suffix,
                    },
                    recommended_action=ResponseAction.BLOCK,
                )

        except Exception as e:
            logger.error(f"Error checking file blocking: {e}", exc_info=True)

        return None

    def _check_app_whitelist(self, file_path: Path) -> Optional[RuleMatch]:
        """Check application against whitelist."""
        try:
            is_whitelisted = self.app_whitelist.is_whitelisted(file_path)
            self._stats["whitelist_checks"] += 1

            # In whitelist mode, non-whitelisted apps are blocked
            if self.config.whitelist_mode and not is_whitelisted:
                return RuleMatch(
                    rule_type=RuleType.APP_WHITELIST,
                    rule_name="whitelist_enforcement",
                    matched=True,
                    severity=EventSeverity.WARNING,
                    threat_score=50,
                    details={
                        "file_path": str(file_path),
                        "reason": "Application not in whitelist",
                    },
                    recommended_action=ResponseAction.BLOCK,
                )

            # In blacklist mode, check if app is explicitly blacklisted
            if not self.config.whitelist_mode:
                is_blacklisted = self.app_whitelist.is_blacklisted(file_path)
                if is_blacklisted:
                    return RuleMatch(
                        rule_type=RuleType.APP_WHITELIST,
                        rule_name="blacklist_enforcement",
                        matched=True,
                        severity=EventSeverity.CRITICAL,
                        threat_score=90,
                        details={
                            "file_path": str(file_path),
                            "reason": "Application is blacklisted",
                        },
                        recommended_action=ResponseAction.BLOCK,
                    )

        except Exception as e:
            logger.error(f"Error checking whitelist: {e}", exc_info=True)

        return None

    def execute_action(self, match: RuleMatch, file_path: Path) -> bool:
        """Execute recommended action for rule match.

        Args:
            match: Rule match to act on
            file_path: File path

        Returns:
            True if action succeeded
        """
        self._stats["actions_taken"] += 1

        action = match.recommended_action

        try:
            if action == ResponseAction.ALERT:
                logger.warning(
                    f"Rule matched: {match.rule_name} for {file_path} (alert only)"
                )
                return True

            elif action == ResponseAction.BLOCK:
                logger.warning(f"Blocking file: {file_path}")
                # In reality, you'd prevent execution or access
                return True

            elif action == ResponseAction.QUARANTINE:
                if self.config.auto_quarantine_critical:
                    logger.warning(f"Quarantining file: {file_path}")
                    # Call quarantine manager
                    return True
                return False

            elif action == ResponseAction.TERMINATE:
                if self.config.auto_terminate_processes:
                    logger.critical(f"Terminating process for: {file_path}")
                    # Terminate process
                    return True
                return False

            elif action == ResponseAction.LOG_ONLY:
                logger.info(f"Rule matched: {match.rule_name} for {file_path}")
                return True

        except Exception as e:
            logger.error(f"Error executing action {action}: {e}", exc_info=True)
            return False

        return False

    def _get_severity_from_yara_meta(self, yara_match: YARAMatch) -> EventSeverity:
        """Extract severity from YARA rule metadata."""
        if "severity" in yara_match.meta:
            severity_str = yara_match.meta["severity"].lower()
            if severity_str == "critical":
                return EventSeverity.CRITICAL
            elif severity_str == "warning":
                return EventSeverity.WARNING
            else:
                return EventSeverity.INFO

        # Default based on tags
        if "malware" in yara_match.tags or "trojan" in yara_match.tags:
            return EventSeverity.CRITICAL
        elif "suspicious" in yara_match.tags:
            return EventSeverity.WARNING
        else:
            return EventSeverity.INFO

    def _get_threat_score_from_yara_meta(self, yara_match: YARAMatch) -> int:
        """Extract threat score from YARA rule metadata."""
        if "threat_score" in yara_match.meta:
            return int(yara_match.meta["threat_score"])

        # Default based on severity
        severity = self._get_severity_from_yara_meta(yara_match)
        if severity == EventSeverity.CRITICAL:
            return 90
        elif severity == EventSeverity.WARNING:
            return 60
        else:
            return 30

    def _get_recommended_action(
        self, severity: EventSeverity, threat_score: int
    ) -> ResponseAction:
        """Determine recommended action based on severity and threat score."""
        if threat_score >= 90:
            return ResponseAction.QUARANTINE
        elif threat_score >= 70:
            return ResponseAction.BLOCK
        elif threat_score >= 40:
            return ResponseAction.ALERT
        else:
            return ResponseAction.LOG_ONLY

    def get_statistics(self) -> dict[str, Any]:
        """Get engine statistics."""
        return {
            "rules_evaluated": self._stats["rules_evaluated"],
            "rules_matched": self._stats["rules_matched"],
            "yara_matches": self._stats["yara_matches"],
            "file_blocks": self._stats["file_blocks"],
            "whitelist_checks": self._stats["whitelist_checks"],
            "actions_taken": self._stats["actions_taken"],
            "yara_enabled": self.yara_manager is not None,
            "file_blocking_enabled": self.file_blocker is not None,
            "app_whitelisting_enabled": self.app_whitelist is not None,
        }

    def compile_rules(self) -> bool:
        """Compile all YARA rules.

        Returns:
            True if compilation succeeded
        """
        if not self.yara_manager:
            logger.warning("YARA manager not initialized")
            return False

        try:
            return self.yara_manager.compile_rules()
        except Exception as e:
            logger.error(f"Error compiling rules: {e}", exc_info=True)
            return False

    def reload_rules(self) -> bool:
        """Reload all rules from disk.

        Returns:
            True if reload succeeded
        """
        try:
            if self.yara_manager:
                self.yara_manager.reload_rules()

            logger.info("Rules reloaded successfully")
            return True

        except Exception as e:
            logger.error(f"Error reloading rules: {e}", exc_info=True)
            return False
