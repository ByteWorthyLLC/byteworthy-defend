"""
Structured logging system with JSON formatting.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Optional

from pythonjsonlogger import jsonlogger

from ..config.loader import LoggingConfig


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter with additional context fields.
    """

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)

        # Add standard fields
        log_record["timestamp"] = self.formatTime(record, self.datefmt)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno

        # Add extra context if present
        if hasattr(record, "file_path"):
            log_record["file_path"] = record.file_path
        if hasattr(record, "threat_name"):
            log_record["threat_name"] = record.threat_name
        if hasattr(record, "scan_id"):
            log_record["scan_id"] = record.scan_id
        if hasattr(record, "file_hash"):
            log_record["file_hash"] = record.file_hash
        if hasattr(record, "action"):
            log_record["action"] = record.action


def setup_logger(
    name: str, config: LoggingConfig, console: bool = True
) -> logging.Logger:
    """
    Set up a logger with file and console handlers.

    Args:
        name: Logger name
        config: Logging configuration
        console: Whether to add console handler

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.level))

    # Remove existing handlers
    logger.handlers.clear()

    # Ensure log directory exists
    log_dir = config.log_dir_path
    log_dir.mkdir(parents=True, exist_ok=True)

    # File handler with rotation
    log_file = log_dir / f"{name}.log"

    if config.format == "json":
        formatter = CustomJsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=config.max_log_size,
        backupCount=config.backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(getattr(logging, config.level))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler (optional)
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, config.level))

        # Use simple format for console
        console_formatter = logging.Formatter(
            "%(levelname)s: %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger


def setup_audit_logger(config: LoggingConfig) -> logging.Logger:
    """
    Set up separate audit logger with extended retention.

    Args:
        config: Logging configuration

    Returns:
        Configured audit logger instance
    """
    audit_logger = logging.getLogger("hifzdefend.audit")
    audit_logger.setLevel(logging.INFO)
    audit_logger.handlers.clear()

    # Ensure log directory exists
    log_dir = config.log_dir_path
    log_dir.mkdir(parents=True, exist_ok=True)

    # Audit log file with more backups
    audit_log_file = log_dir / "audit.log"

    formatter = CustomJsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Larger rotation for audit logs (50 MB, 20 backups)
    file_handler = RotatingFileHandler(
        audit_log_file,
        maxBytes=52428800,  # 50 MB
        backupCount=20,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    audit_logger.addHandler(file_handler)

    # Don't propagate to root logger
    audit_logger.propagate = False

    return audit_logger


def log_scan_event(
    logger: logging.Logger,
    action: str,
    file_path: str,
    threat_name: Optional[str] = None,
    file_hash: Optional[str] = None,
    scan_id: Optional[str] = None,
    level: int = logging.INFO,
) -> None:
    """
    Log a scan event with context.

    Args:
        logger: Logger instance
        action: Action performed (scan_start, scan_complete, threat_detected, etc.)
        file_path: Path to file being scanned
        threat_name: Name of detected threat (if any)
        file_hash: SHA256 hash of file
        scan_id: Unique scan identifier
        level: Log level
    """
    extra = {
        "action": action,
        "file_path": file_path,
    }

    if threat_name:
        extra["threat_name"] = threat_name
    if file_hash:
        extra["file_hash"] = file_hash
    if scan_id:
        extra["scan_id"] = scan_id

    message = f"Action: {action}, File: {file_path}"
    if threat_name:
        message += f", Threat: {threat_name}"

    logger.log(level, message, extra=extra)


def log_quarantine_event(
    logger: logging.Logger,
    action: str,
    file_path: str,
    quarantine_id: Optional[str] = None,
    threat_name: Optional[str] = None,
) -> None:
    """
    Log a quarantine event.

    Args:
        logger: Logger instance
        action: Action performed (quarantine, restore, delete)
        file_path: Original file path
        quarantine_id: Quarantine identifier
        threat_name: Name of threat
    """
    extra = {
        "action": action,
        "file_path": file_path,
    }

    if quarantine_id:
        extra["quarantine_id"] = quarantine_id
    if threat_name:
        extra["threat_name"] = threat_name

    message = f"Quarantine action: {action}, File: {file_path}"
    if quarantine_id:
        message += f", ID: {quarantine_id}"

    logger.info(message, extra=extra)
