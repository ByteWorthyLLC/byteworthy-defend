"""Application Whitelisting for HifzDefend.

This module provides application whitelisting/blacklisting:
- Hash-based verification (SHA256)
- Digital signature verification
- Path-based whitelisting
- Dynamic whitelist management
- Blacklist support
"""

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class WhitelistEntry:
    """Application whitelist entry."""

    file_path: str
    file_hash: str  # SHA256 hash
    added_date: datetime
    description: str = ""
    verified_signature: bool = False
    publisher: str = ""


class ApplicationWhitelist:
    """Manage application whitelist/blacklist."""

    def __init__(self, whitelist_mode: bool = False):
        """Initialize application whitelist.

        Args:
            whitelist_mode: If True, only whitelisted apps allowed.
                           If False, blacklist mode (all allowed except blacklisted).
        """
        self.whitelist_mode = whitelist_mode

        # Whitelist (hash -> entry)
        self._whitelist: dict[str, WhitelistEntry] = {}

        # Blacklist (hash -> entry)
        self._blacklist: dict[str, WhitelistEntry] = {}

        # Path-based whitelist (for directories)
        self._whitelisted_paths: set[str] = set()

        # Default safe paths (Windows system directories)
        self._whitelisted_paths.update(
            [
                "c:\\windows\\system32",
                "c:\\windows\\syswow64",
                "c:\\program files",
                "c:\\program files (x86)",
            ]
        )

        # Statistics
        self._stats = {
            "checks_performed": 0,
            "whitelist_hits": 0,
            "blacklist_hits": 0,
            "hash_verifications": 0,
            "signature_verifications": 0,
        }

        logger.info(
            f"Application whitelist initialized (mode: {'whitelist' if whitelist_mode else 'blacklist'})"
        )

    def is_whitelisted(self, file_path: Path) -> bool:
        """Check if application is whitelisted.

        Args:
            file_path: Path to executable

        Returns:
            True if whitelisted
        """
        self._stats["checks_performed"] += 1

        if not file_path.exists():
            logger.warning(f"File does not exist: {file_path}")
            return False

        # Check path-based whitelist first (faster)
        if self._is_path_whitelisted(file_path):
            self._stats["whitelist_hits"] += 1
            return True

        # Calculate file hash
        file_hash = self._calculate_file_hash(file_path)
        if not file_hash:
            return False

        # Check hash-based whitelist
        if file_hash in self._whitelist:
            self._stats["whitelist_hits"] += 1
            self._stats["hash_verifications"] += 1
            logger.debug(f"File whitelisted by hash: {file_path}")
            return True

        return False

    def is_blacklisted(self, file_path: Path) -> bool:
        """Check if application is blacklisted.

        Args:
            file_path: Path to executable

        Returns:
            True if blacklisted
        """
        if not file_path.exists():
            return False

        # Calculate file hash
        file_hash = self._calculate_file_hash(file_path)
        if not file_hash:
            return False

        # Check hash-based blacklist
        if file_hash in self._blacklist:
            self._stats["blacklist_hits"] += 1
            logger.warning(f"File blacklisted: {file_path}")
            return True

        return False

    def add_to_whitelist(
        self,
        file_path: Path,
        description: str = "",
        verify_signature: bool = False,
    ) -> bool:
        """Add application to whitelist.

        Args:
            file_path: Path to executable
            description: Optional description
            verify_signature: Whether to verify digital signature

        Returns:
            True if added successfully
        """
        if not file_path.exists():
            logger.error(f"Cannot whitelist non-existent file: {file_path}")
            return False

        # Calculate file hash
        file_hash = self._calculate_file_hash(file_path)
        if not file_hash:
            return False

        # Create whitelist entry
        entry = WhitelistEntry(
            file_path=str(file_path),
            file_hash=file_hash,
            added_date=datetime.now(),
            description=description,
            verified_signature=False,
            publisher="",
        )

        # Verify signature if requested
        if verify_signature:
            signature_valid, publisher = self._verify_signature(file_path)
            entry.verified_signature = signature_valid
            entry.publisher = publisher

        # Add to whitelist
        self._whitelist[file_hash] = entry

        logger.info(f"Added to whitelist: {file_path} (hash: {file_hash[:16]}...)")

        return True

    def add_to_blacklist(
        self,
        file_path: Path,
        description: str = "",
    ) -> bool:
        """Add application to blacklist.

        Args:
            file_path: Path to executable
            description: Reason for blacklisting

        Returns:
            True if added successfully
        """
        if not file_path.exists():
            logger.error(f"Cannot blacklist non-existent file: {file_path}")
            return False

        # Calculate file hash
        file_hash = self._calculate_file_hash(file_path)
        if not file_hash:
            return False

        # Create blacklist entry
        entry = WhitelistEntry(
            file_path=str(file_path),
            file_hash=file_hash,
            added_date=datetime.now(),
            description=description,
        )

        # Add to blacklist
        self._blacklist[file_hash] = entry

        logger.warning(f"Added to blacklist: {file_path} (hash: {file_hash[:16]}...)")

        return True

    def remove_from_whitelist(self, file_hash: str) -> bool:
        """Remove entry from whitelist.

        Args:
            file_hash: SHA256 hash of file

        Returns:
            True if removed
        """
        if file_hash in self._whitelist:
            entry = self._whitelist[file_hash]
            del self._whitelist[file_hash]
            logger.info(f"Removed from whitelist: {entry.file_path}")
            return True

        return False

    def remove_from_blacklist(self, file_hash: str) -> bool:
        """Remove entry from blacklist.

        Args:
            file_hash: SHA256 hash of file

        Returns:
            True if removed
        """
        if file_hash in self._blacklist:
            entry = self._blacklist[file_hash]
            del self._blacklist[file_hash]
            logger.info(f"Removed from blacklist: {entry.file_path}")
            return True

        return False

    def add_whitelisted_path(self, path: str):
        """Add directory to path-based whitelist.

        Args:
            path: Directory path
        """
        path_lower = path.lower()
        self._whitelisted_paths.add(path_lower)
        logger.info(f"Added whitelisted path: {path}")

    def remove_whitelisted_path(self, path: str):
        """Remove directory from path-based whitelist.

        Args:
            path: Directory path
        """
        path_lower = path.lower()
        if path_lower in self._whitelisted_paths:
            self._whitelisted_paths.remove(path_lower)
            logger.info(f"Removed whitelisted path: {path}")

    def _is_path_whitelisted(self, file_path: Path) -> bool:
        """Check if file path is in whitelisted directory.

        Args:
            file_path: Path to file

        Returns:
            True if path is whitelisted
        """
        path_str = str(file_path).lower()

        for whitelisted_path in self._whitelisted_paths:
            if path_str.startswith(whitelisted_path):
                return True

        return False

    def _calculate_file_hash(self, file_path: Path) -> Optional[str]:
        """Calculate SHA256 hash of file.

        Args:
            file_path: Path to file

        Returns:
            SHA256 hash or None on error
        """
        try:
            sha256_hash = hashlib.sha256()

            with open(file_path, "rb") as f:
                # Read in 64kb chunks
                for byte_block in iter(lambda: f.read(65536), b""):
                    sha256_hash.update(byte_block)

            return sha256_hash.hexdigest()

        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}", exc_info=True)
            return None

    def _verify_signature(self, file_path: Path) -> tuple[bool, str]:
        """Verify digital signature of file.

        Args:
            file_path: Path to file

        Returns:
            Tuple of (is_valid, publisher_name)
        """
        # TODO: Implement signature verification using Windows API
        # For now, return placeholder
        self._stats["signature_verifications"] += 1

        # On Windows, would use:
        # - wintrust.dll and WinVerifyTrust API
        # - Or PowerShell Get-AuthenticodeSignature

        logger.debug(f"Signature verification not yet implemented for {file_path}")

        return False, ""

    def get_whitelist_entries(self) -> list[WhitelistEntry]:
        """Get all whitelist entries."""
        return list(self._whitelist.values())

    def get_blacklist_entries(self) -> list[WhitelistEntry]:
        """Get all blacklist entries."""
        return list(self._blacklist.values())

    def get_statistics(self) -> dict:
        """Get whitelist statistics."""
        return {
            "mode": "whitelist" if self.whitelist_mode else "blacklist",
            "checks_performed": self._stats["checks_performed"],
            "whitelist_hits": self._stats["whitelist_hits"],
            "blacklist_hits": self._stats["blacklist_hits"],
            "hash_verifications": self._stats["hash_verifications"],
            "signature_verifications": self._stats["signature_verifications"],
            "whitelist_size": len(self._whitelist),
            "blacklist_size": len(self._blacklist),
            "whitelisted_paths": len(self._whitelisted_paths),
        }

    def export_whitelist(self, output_path: Path) -> bool:
        """Export whitelist to JSON file.

        Args:
            output_path: Path to output file

        Returns:
            True if exported successfully
        """
        try:
            import json

            data = {
                "mode": "whitelist" if self.whitelist_mode else "blacklist",
                "exported_date": datetime.now().isoformat(),
                "whitelist": [
                    {
                        "file_path": entry.file_path,
                        "file_hash": entry.file_hash,
                        "added_date": entry.added_date.isoformat(),
                        "description": entry.description,
                        "verified_signature": entry.verified_signature,
                        "publisher": entry.publisher,
                    }
                    for entry in self._whitelist.values()
                ],
                "blacklist": [
                    {
                        "file_path": entry.file_path,
                        "file_hash": entry.file_hash,
                        "added_date": entry.added_date.isoformat(),
                        "description": entry.description,
                    }
                    for entry in self._blacklist.values()
                ],
                "whitelisted_paths": list(self._whitelisted_paths),
            }

            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Exported whitelist to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting whitelist: {e}", exc_info=True)
            return False

    def import_whitelist(self, input_path: Path) -> bool:
        """Import whitelist from JSON file.

        Args:
            input_path: Path to input file

        Returns:
            True if imported successfully
        """
        try:
            import json

            with open(input_path, "r") as f:
                data = json.load(f)

            # Import whitelist entries
            for entry_data in data.get("whitelist", []):
                entry = WhitelistEntry(
                    file_path=entry_data["file_path"],
                    file_hash=entry_data["file_hash"],
                    added_date=datetime.fromisoformat(entry_data["added_date"]),
                    description=entry_data.get("description", ""),
                    verified_signature=entry_data.get("verified_signature", False),
                    publisher=entry_data.get("publisher", ""),
                )
                self._whitelist[entry.file_hash] = entry

            # Import blacklist entries
            for entry_data in data.get("blacklist", []):
                entry = WhitelistEntry(
                    file_path=entry_data["file_path"],
                    file_hash=entry_data["file_hash"],
                    added_date=datetime.fromisoformat(entry_data["added_date"]),
                    description=entry_data.get("description", ""),
                )
                self._blacklist[entry.file_hash] = entry

            # Import whitelisted paths
            for path in data.get("whitelisted_paths", []):
                self._whitelisted_paths.add(path.lower())

            logger.info(f"Imported whitelist from {input_path}")
            return True

        except Exception as e:
            logger.error(f"Error importing whitelist: {e}", exc_info=True)
            return False
