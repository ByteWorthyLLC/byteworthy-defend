"""File Type Blocking for HifzDefend.

This module provides context-aware file blocking:
- Block dangerous file extensions
- Context-aware blocking (block .exe in Downloads, allow in Program Files)
- Path-based rules
- Temporary file blocking
- Archive content blocking
"""

import logging
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class BlockReason(str, Enum):
    """Reasons for blocking a file."""

    DANGEROUS_EXTENSION = "dangerous_extension"  # Inherently dangerous extension
    SUSPICIOUS_LOCATION = "suspicious_location"  # Dangerous file in wrong location
    TEMPORARY_LOCATION = "temporary_location"  # Executable in temp directory
    DOUBLE_EXTENSION = "double_extension"  # Deceptive double extension
    ARCHIVE_EXECUTABLE = "archive_executable"  # Executable in archive
    BLACKLISTED_PATH = "blacklisted_path"  # Path is explicitly blacklisted


class FileBlocker:
    """Context-aware file type blocking."""

    def __init__(self):
        # Dangerous extensions (always suspicious)
        self._dangerous_extensions = {
            ".scr",  # Screen saver (common malware vector)
            ".pif",  # Program Information File
            ".application",  # ClickOnce application
            ".gadget",  # Windows gadget
            ".msi",  # Windows Installer (suspicious in wrong context)
            ".msp",  # Windows Installer patch
            ".com",  # DOS executable
            ".hta",  # HTML application
            ".cpl",  # Control Panel item
            ".msc",  # Microsoft Console
            ".jar",  # Java archive (can be malicious)
            ".vb",  # VBScript
            ".vbs",  # VBScript
            ".vbe",  # Encrypted VBScript
            ".js",  # JavaScript (dangerous outside web context)
            ".jse",  # Encrypted JavaScript
            ".ws",  # Windows Script
            ".wsf",  # Windows Script File
            ".wsc",  # Windows Script Component
            ".wsh",  # Windows Script Host
            ".ps1",  # PowerShell script
            ".ps1xml",  # PowerShell XML
            ".ps2",  # PowerShell script
            ".ps2xml",  # PowerShell XML
            ".psc1",  # PowerShell console
            ".psc2",  # PowerShell console
            ".msh",  # Monad script
            ".msh1",  # Monad script
            ".msh2",  # Monad script
            ".mshxml",  # Monad XML
            ".msh1xml",  # Monad XML
            ".msh2xml",  # Monad XML
        }

        # Potentially dangerous extensions (context-dependent)
        self._context_dependent_extensions = {
            ".exe",  # Executable
            ".dll",  # Dynamic Link Library
            ".bat",  # Batch file
            ".cmd",  # Command script
            ".reg",  # Registry file
        }

        # Safe directories where executables are allowed
        self._safe_executable_directories = {
            "program files",
            "program files (x86)",
            "windows",
            "programdata",
        }

        # Suspicious/dangerous directories
        self._suspicious_directories = {
            "temp",
            "tmp",
            "downloads",
            "appdata\\local\\temp",
            "appdata\\roaming\\temp",
        }

        # Double extension patterns (deceptive)
        self._deceptive_extension_patterns = [
            ".pdf.exe",
            ".doc.exe",
            ".docx.exe",
            ".xls.exe",
            ".xlsx.exe",
            ".jpg.exe",
            ".png.exe",
            ".txt.exe",
            ".zip.exe",
        ]

        # Statistics
        self._stats = {
            "files_checked": 0,
            "files_blocked": 0,
            "dangerous_extensions": 0,
            "suspicious_locations": 0,
            "double_extensions": 0,
        }

        logger.info("File blocker initialized")

    def should_block_file(self, file_path: Path) -> tuple[bool, Optional[BlockReason]]:
        """Check if file should be blocked.

        Args:
            file_path: Path to file

        Returns:
            Tuple of (should_block, reason)
        """
        self._stats["files_checked"] += 1

        # Get extension and path info
        extension = file_path.suffix.lower()
        path_str = str(file_path).lower()

        # 1. Check for dangerous extensions (always block)
        if extension in self._dangerous_extensions:
            self._stats["files_blocked"] += 1
            self._stats["dangerous_extensions"] += 1
            logger.warning(f"Blocking file with dangerous extension: {file_path}")
            return True, BlockReason.DANGEROUS_EXTENSION

        # 2. Check for double extensions (deceptive)
        if self._has_double_extension(file_path):
            self._stats["files_blocked"] += 1
            self._stats["double_extensions"] += 1
            logger.warning(f"Blocking file with double extension: {file_path}")
            return True, BlockReason.DOUBLE_EXTENSION

        # 3. Check context-dependent extensions
        if extension in self._context_dependent_extensions:
            # Check if in suspicious location
            if self._is_in_suspicious_location(file_path):
                self._stats["files_blocked"] += 1
                self._stats["suspicious_locations"] += 1
                logger.warning(f"Blocking executable in suspicious location: {file_path}")
                return True, BlockReason.SUSPICIOUS_LOCATION

            # Check if in temporary location
            if self._is_in_temporary_location(file_path):
                self._stats["files_blocked"] += 1
                logger.warning(f"Blocking executable in temporary location: {file_path}")
                return True, BlockReason.TEMPORARY_LOCATION

        # File is allowed
        return False, None

    def _has_double_extension(self, file_path: Path) -> bool:
        """Check if file has deceptive double extension.

        Args:
            file_path: Path to file

        Returns:
            True if double extension detected
        """
        file_name = file_path.name.lower()

        for pattern in self._deceptive_extension_patterns:
            if file_name.endswith(pattern):
                return True

        return False

    def _is_in_suspicious_location(self, file_path: Path) -> bool:
        """Check if file is in a suspicious location.

        Args:
            file_path: Path to file

        Returns:
            True if in suspicious location
        """
        path_str = str(file_path).lower()

        # Check if in safe directory
        for safe_dir in self._safe_executable_directories:
            if safe_dir in path_str:
                return False

        # Check if in suspicious directory
        for suspicious_dir in self._suspicious_directories:
            if suspicious_dir in path_str:
                return True

        # Default: Downloads directory is suspicious
        if "downloads" in path_str:
            return True

        return False

    def _is_in_temporary_location(self, file_path: Path) -> bool:
        """Check if file is in a temporary location.

        Args:
            file_path: Path to file

        Returns:
            True if in temporary location
        """
        path_str = str(file_path).lower()

        temp_indicators = ["\\temp\\", "\\tmp\\", "\\appdata\\local\\temp\\"]

        for indicator in temp_indicators:
            if indicator in path_str:
                return True

        return False

    def is_dangerous_extension(self, extension: str) -> bool:
        """Check if extension is inherently dangerous.

        Args:
            extension: File extension (e.g., '.exe')

        Returns:
            True if dangerous
        """
        return extension.lower() in self._dangerous_extensions

    def is_context_dependent_extension(self, extension: str) -> bool:
        """Check if extension is context-dependent.

        Args:
            extension: File extension

        Returns:
            True if context-dependent
        """
        return extension.lower() in self._context_dependent_extensions

    def add_dangerous_extension(self, extension: str):
        """Add extension to dangerous list.

        Args:
            extension: Extension to add (e.g., '.xyz')
        """
        if not extension.startswith("."):
            extension = f".{extension}"

        self._dangerous_extensions.add(extension.lower())
        logger.info(f"Added dangerous extension: {extension}")

    def remove_dangerous_extension(self, extension: str):
        """Remove extension from dangerous list.

        Args:
            extension: Extension to remove
        """
        extension = extension.lower()
        if extension in self._dangerous_extensions:
            self._dangerous_extensions.remove(extension)
            logger.info(f"Removed dangerous extension: {extension}")

    def add_safe_directory(self, directory: str):
        """Add directory to safe list.

        Args:
            directory: Directory name or path
        """
        self._safe_executable_directories.add(directory.lower())
        logger.info(f"Added safe directory: {directory}")

    def add_suspicious_directory(self, directory: str):
        """Add directory to suspicious list.

        Args:
            directory: Directory name or path
        """
        self._suspicious_directories.add(directory.lower())
        logger.info(f"Added suspicious directory: {directory}")

    def get_statistics(self) -> dict:
        """Get file blocker statistics."""
        return {
            "files_checked": self._stats["files_checked"],
            "files_blocked": self._stats["files_blocked"],
            "dangerous_extensions": self._stats["dangerous_extensions"],
            "suspicious_locations": self._stats["suspicious_locations"],
            "double_extensions": self._stats["double_extensions"],
            "dangerous_extension_count": len(self._dangerous_extensions),
            "context_dependent_extension_count": len(
                self._context_dependent_extensions
            ),
        }

    def get_dangerous_extensions(self) -> set[str]:
        """Get set of dangerous extensions."""
        return self._dangerous_extensions.copy()

    def get_context_dependent_extensions(self) -> set[str]:
        """Get set of context-dependent extensions."""
        return self._context_dependent_extensions.copy()
