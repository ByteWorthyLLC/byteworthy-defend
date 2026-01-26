"""
Utility helper functions for HifzDefend.
"""

import hashlib
import os
from pathlib import Path
from typing import Optional

from .exceptions import PathTraversalError, FileAccessError


def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate hash of a file.

    Args:
        file_path: Path to file
        algorithm: Hash algorithm (sha256, sha1, md5)

    Returns:
        Hex digest of file hash

    Raises:
        FileAccessError: If file cannot be read
        ValueError: If algorithm is invalid
    """
    try:
        hasher = hashlib.new(algorithm)
    except ValueError:
        raise ValueError(f"Invalid hash algorithm: {algorithm}")

    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (OSError, IOError) as e:
        raise FileAccessError(f"Failed to read file for hashing: {e}")


def validate_path(path: Path, base_path: Optional[Path] = None) -> Path:
    """
    Validate a path to prevent path traversal attacks.

    Args:
        path: Path to validate
        base_path: Optional base path to restrict access to

    Returns:
        Resolved absolute path

    Raises:
        PathTraversalError: If path traversal attempt detected
        FileAccessError: If path doesn't exist or is not accessible
    """
    try:
        resolved_path = path.resolve()
    except (OSError, RuntimeError) as e:
        raise FileAccessError(f"Cannot resolve path {path}: {e}")

    # Check if path exists
    if not resolved_path.exists():
        raise FileAccessError(f"Path does not exist: {resolved_path}")

    # If base_path specified, ensure resolved path is within it
    if base_path is not None:
        try:
            resolved_base = base_path.resolve()
            resolved_path.relative_to(resolved_base)
        except ValueError:
            raise PathTraversalError(
                f"Path {path} is outside allowed directory {base_path}"
            )
        except (OSError, RuntimeError) as e:
            raise FileAccessError(f"Cannot resolve base path {base_path}: {e}")

    return resolved_path


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def expand_windows_path(path: str) -> Path:
    """
    Expand Windows environment variables in path.

    Args:
        path: Path string with potential env vars (e.g., %LOCALAPPDATA%)

    Returns:
        Expanded Path object
    """
    # Expand environment variables
    expanded = os.path.expandvars(path)
    # Expand user home directory
    expanded = os.path.expanduser(expanded)
    return Path(expanded)
