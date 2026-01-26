"""YARA Rule Management for HifzDefend.

This module provides YARA rule compilation, management, and execution:
- Compile YARA rules from multiple directories
- Scan files with compiled rules
- Rule namespace management
- String/pattern matching
- Metadata extraction
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Try to import yara, handle gracefully if not available
try:
    import yara

    YARA_AVAILABLE = True
except ImportError:
    YARA_AVAILABLE = False
    logger.warning(
        "YARA module not available. Install with: pip install yara-python\n"
        "Custom YARA signatures will be disabled."
    )


@dataclass
class YARAMatch:
    """YARA rule match result."""

    rule_name: str
    namespace: str
    tags: list[str]
    meta: dict[str, Any]
    strings: list[tuple[int, str, bytes]]  # offset, identifier, data

    def __str__(self) -> str:
        return f"YARA Match: {self.rule_name} (namespace: {self.namespace})"


class YARAManager:
    """Manage YARA rules for threat detection."""

    def __init__(
        self,
        custom_rules_path: Optional[Path] = None,
        community_rules_path: Optional[Path] = None,
    ):
        if not YARA_AVAILABLE:
            raise RuntimeError(
                "YARA module not available. Install with: pip install yara-python"
            )

        self.custom_rules_path = custom_rules_path or Path("signatures/custom")
        self.community_rules_path = community_rules_path or Path(
            "signatures/community"
        )

        # Compiled rules
        self._compiled_rules: Optional[yara.Rules] = None

        # Rule sources (namespace -> file_path)
        self._rule_sources: dict[str, Path] = {}

        # Statistics
        self._stats = {
            "rules_compiled": 0,
            "files_scanned": 0,
            "matches_found": 0,
            "compilation_errors": 0,
        }

        logger.info("YARA manager initialized")

        # Auto-compile rules if directories exist
        self._auto_compile_rules()

    def _auto_compile_rules(self):
        """Automatically compile rules on initialization."""
        try:
            if self.custom_rules_path.exists() or self.community_rules_path.exists():
                logger.info("Auto-compiling YARA rules")
                self.compile_rules()
        except Exception as e:
            logger.error(f"Failed to auto-compile rules: {e}", exc_info=True)

    def compile_rules(self) -> bool:
        """Compile all YARA rules from configured directories.

        Returns:
            True if compilation succeeded
        """
        rule_files = {}

        try:
            # Collect custom rules
            if self.custom_rules_path.exists():
                custom_files = self._collect_yara_files(self.custom_rules_path)
                for file_path in custom_files:
                    namespace = f"custom_{file_path.stem}"
                    rule_files[namespace] = str(file_path)
                    self._rule_sources[namespace] = file_path

            # Collect community rules
            if self.community_rules_path.exists():
                community_files = self._collect_yara_files(self.community_rules_path)
                for file_path in community_files:
                    namespace = f"community_{file_path.stem}"
                    rule_files[namespace] = str(file_path)
                    self._rule_sources[namespace] = file_path

            if not rule_files:
                logger.warning("No YARA rule files found to compile")
                return False

            # Compile rules
            logger.info(f"Compiling {len(rule_files)} YARA rule files")
            self._compiled_rules = yara.compile(filepaths=rule_files)

            self._stats["rules_compiled"] = len(rule_files)
            logger.info(f"Successfully compiled {len(rule_files)} YARA rule files")

            return True

        except yara.SyntaxError as e:
            self._stats["compilation_errors"] += 1
            logger.error(f"YARA syntax error during compilation: {e}", exc_info=True)
            return False

        except Exception as e:
            self._stats["compilation_errors"] += 1
            logger.error(f"Error compiling YARA rules: {e}", exc_info=True)
            return False

    def _collect_yara_files(self, directory: Path) -> list[Path]:
        """Collect all .yar and .yara files from directory.

        Args:
            directory: Directory to search

        Returns:
            List of YARA rule files
        """
        yara_files = []

        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return yara_files

        # Find .yar and .yara files
        for pattern in ["*.yar", "*.yara"]:
            yara_files.extend(directory.glob(pattern))

        # Also search subdirectories
        for pattern in ["**/*.yar", "**/*.yara"]:
            yara_files.extend(directory.glob(pattern))

        # Remove duplicates
        yara_files = list(set(yara_files))

        logger.info(f"Found {len(yara_files)} YARA rule files in {directory}")

        return yara_files

    def scan_file(self, file_path: Path) -> list[YARAMatch]:
        """Scan file with compiled YARA rules.

        Args:
            file_path: Path to file to scan

        Returns:
            List of YARA matches
        """
        if not self._compiled_rules:
            logger.warning("No compiled YARA rules available")
            return []

        if not file_path.exists():
            logger.error(f"File does not exist: {file_path}")
            return []

        matches = []

        try:
            self._stats["files_scanned"] += 1

            # Scan file
            yara_matches = self._compiled_rules.match(str(file_path))

            # Convert to YARAMatch objects
            for match in yara_matches:
                yara_match = YARAMatch(
                    rule_name=match.rule,
                    namespace=match.namespace,
                    tags=list(match.tags),
                    meta=dict(match.meta),
                    strings=[(s[0], s[1], s[2]) for s in match.strings],
                )

                matches.append(yara_match)
                self._stats["matches_found"] += 1

                logger.info(f"YARA match: {match.rule} in {file_path}")

        except yara.Error as e:
            logger.error(f"YARA error scanning {file_path}: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Error scanning file {file_path}: {e}", exc_info=True)

        return matches

    def scan_data(self, data: bytes) -> list[YARAMatch]:
        """Scan raw data with compiled YARA rules.

        Args:
            data: Raw bytes to scan

        Returns:
            List of YARA matches
        """
        if not self._compiled_rules:
            logger.warning("No compiled YARA rules available")
            return []

        matches = []

        try:
            self._stats["files_scanned"] += 1

            # Scan data
            yara_matches = self._compiled_rules.match(data=data)

            # Convert to YARAMatch objects
            for match in yara_matches:
                yara_match = YARAMatch(
                    rule_name=match.rule,
                    namespace=match.namespace,
                    tags=list(match.tags),
                    meta=dict(match.meta),
                    strings=[(s[0], s[1], s[2]) for s in match.strings],
                )

                matches.append(yara_match)
                self._stats["matches_found"] += 1

        except yara.Error as e:
            logger.error(f"YARA error scanning data: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Error scanning data: {e}", exc_info=True)

        return matches

    def reload_rules(self) -> bool:
        """Reload all YARA rules from disk.

        Returns:
            True if reload succeeded
        """
        logger.info("Reloading YARA rules")

        # Clear existing rules
        self._compiled_rules = None
        self._rule_sources.clear()

        # Recompile
        return self.compile_rules()

    def add_rule_directory(self, directory: Path, namespace_prefix: str = "custom"):
        """Add a new directory to scan for YARA rules.

        Args:
            directory: Directory containing YARA rules
            namespace_prefix: Prefix for rule namespaces
        """
        if not directory.exists():
            logger.error(f"Directory does not exist: {directory}")
            return

        # Collect rules
        rule_files = self._collect_yara_files(directory)

        if not rule_files:
            logger.warning(f"No YARA rules found in {directory}")
            return

        # Add to sources
        for file_path in rule_files:
            namespace = f"{namespace_prefix}_{file_path.stem}"
            self._rule_sources[namespace] = file_path

        logger.info(f"Added {len(rule_files)} rules from {directory}")

        # Recompile
        self.compile_rules()

    def get_statistics(self) -> dict[str, Any]:
        """Get YARA manager statistics."""
        return {
            "rules_compiled": self._stats["rules_compiled"],
            "files_scanned": self._stats["files_scanned"],
            "matches_found": self._stats["matches_found"],
            "compilation_errors": self._stats["compilation_errors"],
            "custom_rules_path": str(self.custom_rules_path),
            "community_rules_path": str(self.community_rules_path),
            "rule_sources": len(self._rule_sources),
        }

    def list_rules(self) -> list[dict[str, Any]]:
        """List all loaded YARA rules.

        Returns:
            List of rule information
        """
        rules = []

        for namespace, file_path in self._rule_sources.items():
            rules.append(
                {"namespace": namespace, "file_path": str(file_path), "enabled": True}
            )

        return rules

    def validate_rule_file(self, file_path: Path) -> tuple[bool, str]:
        """Validate a YARA rule file.

        Args:
            file_path: Path to YARA rule file

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Try to compile the rule
            yara.compile(filepath=str(file_path))
            return True, "Rule is valid"

        except yara.SyntaxError as e:
            return False, f"Syntax error: {str(e)}"

        except Exception as e:
            return False, f"Error: {str(e)}"
