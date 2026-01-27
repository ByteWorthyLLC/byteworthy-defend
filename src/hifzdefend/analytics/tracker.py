"""Analytics event tracking."""

import hashlib
import json
import logging
import platform
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..core.config import get_app_data_dir
from .models import AnalyticsEvent, EventType, AnalyticsSettings, UsageStats

logger = logging.getLogger(__name__)


class AnalyticsTracker:
    """Track usage analytics and telemetry."""

    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize analytics tracker.

        Args:
            data_dir: Directory for analytics data storage
        """
        self.data_dir = data_dir or get_app_data_dir() / "analytics"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.settings_file = self.data_dir / "settings.json"
        self.stats_file = self.data_dir / "stats.json"
        self.events_file = self.data_dir / "events.jsonl"

        # Load or create settings
        self.settings = self._load_settings()

        # Generate anonymous user ID
        self.user_id = self._get_or_create_user_id()

        # Current session ID
        self.session_id = str(uuid.uuid4())

        # Track session start
        self.session_start = datetime.utcnow()

    def track_event(self, event_type: EventType, properties: Optional[dict] = None) -> None:
        """Track analytics event.

        Args:
            event_type: Type of event
            properties: Event properties
        """
        if not self.settings.enabled:
            return

        try:
            event = AnalyticsEvent(
                event_type=event_type,
                properties=properties or {},
                user_id=self.user_id if self.settings.anonymize else None,
                session_id=self.session_id,
                app_version="0.3.0",
                os_version=platform.platform(),
            )

            # Save to local log
            self._save_event(event)

            # Send to analytics service (stub)
            # self._send_to_service(event)

        except Exception as e:
            logger.error(f"Failed to track event: {e}")

    def update_stats(self, updates: dict) -> None:
        """Update usage statistics.

        Args:
            updates: Statistics updates
        """
        try:
            stats = self._load_stats()

            for key, value in updates.items():
                if hasattr(stats, key):
                    if isinstance(value, (int, float)):
                        # Increment numeric values
                        current = getattr(stats, key)
                        setattr(stats, key, current + value)
                    else:
                        # Replace other values
                        setattr(stats, key, value)

            self._save_stats(stats)

        except Exception as e:
            logger.error(f"Failed to update stats: {e}")

    def get_stats(self) -> UsageStats:
        """Get current usage statistics.

        Returns:
            Usage statistics
        """
        return self._load_stats()

    def update_settings(self, updates: dict) -> None:
        """Update analytics settings.

        Args:
            updates: Settings updates
        """
        try:
            for key, value in updates.items():
                if hasattr(self.settings, key):
                    setattr(self.settings, key, value)

            self._save_settings(self.settings)

        except Exception as e:
            logger.error(f"Failed to update settings: {e}")

    def track_app_start(self) -> None:
        """Track application start."""
        self.track_event(EventType.APP_STARTED, {
            "os": platform.system(),
            "python_version": platform.python_version(),
        })

    def track_app_stop(self) -> None:
        """Track application stop."""
        uptime = (datetime.utcnow() - self.session_start).total_seconds() / 3600

        self.track_event(EventType.APP_STOPPED, {
            "uptime_hours": uptime,
        })

        self.update_stats({"uptime_hours": uptime})

    def track_scan(self, threats_found: int, duration_seconds: float, success: bool) -> None:
        """Track scan event.

        Args:
            threats_found: Number of threats found
            duration_seconds: Scan duration
            success: Whether scan succeeded
        """
        event_type = EventType.SCAN_COMPLETED if success else EventType.SCAN_FAILED

        self.track_event(event_type, {
            "threats_found": threats_found,
            "duration_seconds": duration_seconds,
        })

        self.update_stats({
            "total_scans": 1,
            "threats_detected": threats_found,
            "last_scan": datetime.utcnow(),
        })

    def track_threat(self, threat_name: str, file_path: str, quarantined: bool) -> None:
        """Track threat detection.

        Args:
            threat_name: Name of threat
            file_path: Path to infected file (hashed)
            quarantined: Whether file was quarantined
        """
        # Hash file path for privacy
        path_hash = hashlib.sha256(file_path.encode()).hexdigest()[:16]

        self.track_event(EventType.THREAT_DETECTED, {
            "threat_name": threat_name,
            "path_hash": path_hash,
            "quarantined": quarantined,
        })

        if quarantined:
            self.track_event(EventType.FILE_QUARANTINED)
            self.update_stats({"files_quarantined": 1})

    def track_ai_usage(self, analysis_type: str, tokens_used: int) -> None:
        """Track AI feature usage.

        Args:
            analysis_type: Type of AI analysis
            tokens_used: Tokens consumed
        """
        self.track_event(EventType.AI_ANALYSIS, {
            "analysis_type": analysis_type,
            "tokens_used": tokens_used,
        })

        self.update_stats({"ai_analyses": 1})

    def track_purchase(self, license_type: str, amount: float) -> None:
        """Track purchase event.

        Args:
            license_type: Type of license purchased
            amount: Purchase amount
        """
        self.track_event(EventType.PURCHASE_COMPLETED, {
            "license_type": license_type,
            "amount": amount,
        })

    def _get_or_create_user_id(self) -> str:
        """Get or create anonymous user ID.

        Returns:
            Anonymous user ID
        """
        user_id_file = self.data_dir / "user_id.txt"

        if user_id_file.exists():
            try:
                return user_id_file.read_text().strip()
            except Exception:
                pass

        # Generate new user ID
        user_id = str(uuid.uuid4())

        try:
            user_id_file.write_text(user_id)
        except Exception:
            pass

        return user_id

    def _load_settings(self) -> AnalyticsSettings:
        """Load analytics settings.

        Returns:
            Analytics settings
        """
        try:
            if self.settings_file.exists():
                with open(self.settings_file, "r") as f:
                    data = json.load(f)
                return AnalyticsSettings(**data)
        except Exception:
            pass

        # Return defaults
        settings = AnalyticsSettings()
        self._save_settings(settings)
        return settings

    def _save_settings(self, settings: AnalyticsSettings) -> None:
        """Save analytics settings.

        Args:
            settings: Analytics settings
        """
        try:
            with open(self.settings_file, "w") as f:
                json.dump(settings.dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def _load_stats(self) -> UsageStats:
        """Load usage statistics.

        Returns:
            Usage statistics
        """
        try:
            if self.stats_file.exists():
                with open(self.stats_file, "r") as f:
                    data = json.load(f)
                return UsageStats(**data)
        except Exception:
            pass

        return UsageStats()

    def _save_stats(self, stats: UsageStats) -> None:
        """Save usage statistics.

        Args:
            stats: Usage statistics
        """
        try:
            with open(self.stats_file, "w") as f:
                json.dump(stats.dict(), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")

    def _save_event(self, event: AnalyticsEvent) -> None:
        """Save event to local log.

        Args:
            event: Analytics event
        """
        try:
            with open(self.events_file, "a") as f:
                f.write(json.dumps(event.dict(), default=str) + "\n")
        except Exception as e:
            logger.error(f"Failed to save event: {e}")

    def _send_to_service(self, event: AnalyticsEvent) -> None:
        """Send event to analytics service.

        Args:
            event: Analytics event
        """
        # This would send to a service like Mixpanel, Amplitude, or self-hosted
        # For privacy, all data should be anonymized
        pass
