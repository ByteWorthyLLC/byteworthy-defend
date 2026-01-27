"""License management and storage."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from ..core.config import get_app_data_dir
from .crypto import LicenseCrypto
from .hardware import HardwareFingerprint
from .models import License, LicenseActivation, LicenseStatus, LicenseType, LicenseValidation
from .validator import LicenseValidator


class LicenseManager:
    """Manage license activation and storage."""

    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize license manager.

        Args:
            data_dir: Directory for license storage
        """
        self.data_dir = data_dir or get_app_data_dir()
        self.license_file = self.data_dir / "license.json"
        self.public_key_file = Path(__file__).parent / "keys" / "public.pem"

        self.validator = LicenseValidator(self.public_key_file)
        self._current_license: Optional[License] = None

    def activate_license(self, activation: LicenseActivation) -> LicenseValidation:
        """Activate a license on this device.

        Args:
            activation: Activation request

        Returns:
            Validation result
        """
        # Validate the license key
        validation = self.validator.validate(activation.license_key, check_hardware=False)

        if not validation.valid:
            return validation

        license = validation.license

        # Check if already activated
        if license.hardware_id:
            # License is already bound to hardware
            current_hardware = activation.hardware_id
            if current_hardware != license.hardware_id:
                return LicenseValidation(
                    valid=False,
                    license=license,
                    error="License already activated on another device"
                )

        # Save license locally
        self.save_license(activation.license_key, license)

        # Update activation timestamp
        if not license.activated_at:
            license.activated_at = datetime.utcnow()

        self._current_license = license

        return LicenseValidation(
            valid=True,
            license=license,
            warnings=["License activated successfully"]
        )

    def deactivate_license(self) -> bool:
        """Deactivate current license.

        Returns:
            Success status
        """
        if self.license_file.exists():
            self.license_file.unlink()
            self._current_license = None
            return True
        return False

    def get_current_license(self) -> Optional[License]:
        """Get currently activated license.

        Returns:
            Current license or None
        """
        if self._current_license:
            return self._current_license

        # Load from disk
        if not self.license_file.exists():
            return None

        try:
            with open(self.license_file, "r") as f:
                data = json.load(f)

            # Validate stored license
            validation = self.validator.validate(data["license_key"])

            if validation.valid:
                self._current_license = validation.license
                return self._current_license

        except Exception:
            pass

        return None

    def save_license(self, license_key: str, license: License) -> None:
        """Save license to disk.

        Args:
            license_key: License key
            license: License data
        """
        self.data_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "license_key": license_key,
            "activated_at": datetime.utcnow().isoformat(),
            "hardware_id": HardwareFingerprint.get_fingerprint(),
            "device_name": HardwareFingerprint.get_device_name(),
        }

        with open(self.license_file, "w") as f:
            json.dump(data, f, indent=2)

    def is_licensed(self) -> bool:
        """Check if application is properly licensed.

        Returns:
            Whether valid license exists
        """
        license = self.get_current_license()
        if not license:
            return False

        validation = self.validator.validate(license.license_key)
        return validation.valid

    def get_license_info(self) -> dict:
        """Get license information for display.

        Returns:
            License information dictionary
        """
        license = self.get_current_license()

        if not license:
            return {
                "status": "unlicensed",
                "message": "No active license",
            }

        validation = self.validator.validate(license.license_key)

        info = {
            "status": "active" if validation.valid else "invalid",
            "license_type": license.license_type,
            "customer_email": license.customer_email,
            "expires_at": license.expires_at.isoformat() if license.expires_at else None,
            "features": {
                "ai_analysis": license.ai_enabled,
                "real_time_protection": license.real_time_protection,
                "cloud_backup": license.cloud_backup,
                "priority_support": license.priority_support,
            },
        }

        if not validation.valid:
            info["error"] = validation.error

        if validation.warnings:
            info["warnings"] = validation.warnings

        return info

    @staticmethod
    def create_trial_license(email: str, days: int = 14) -> dict:
        """Create trial license data (for server-side generation).

        Args:
            email: User email
            days: Trial duration in days

        Returns:
            License data dictionary
        """
        return {
            "license_type": LicenseType.TRIAL,
            "customer_email": email,
            "issued_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=days)).isoformat(),
            "max_activations": 1,
            "ai_enabled": True,
            "real_time_protection": True,
            "cloud_backup": False,
            "priority_support": False,
            "max_scans_per_day": 50,
        }

    @staticmethod
    def create_paid_license(email: str, license_type: str, duration_days: Optional[int] = 365) -> dict:
        """Create paid license data (for server-side generation).

        Args:
            email: Customer email
            license_type: Type of license (personal, professional, enterprise)
            duration_days: License duration in days (None for perpetual)

        Returns:
            License data dictionary
        """
        features = {
            "personal": {
                "max_activations": 1,
                "ai_enabled": True,
                "real_time_protection": True,
                "cloud_backup": True,
                "priority_support": False,
                "max_scans_per_day": None,
            },
            "professional": {
                "max_activations": 3,
                "ai_enabled": True,
                "real_time_protection": True,
                "cloud_backup": True,
                "priority_support": True,
                "max_scans_per_day": None,
            },
            "enterprise": {
                "max_activations": 10,
                "ai_enabled": True,
                "real_time_protection": True,
                "cloud_backup": True,
                "priority_support": True,
                "max_scans_per_day": None,
            },
        }

        base_data = {
            "license_type": license_type,
            "customer_email": email,
            "issued_at": datetime.utcnow().isoformat(),
        }

        if duration_days:
            base_data["expires_at"] = (datetime.utcnow() + timedelta(days=duration_days)).isoformat()

        base_data.update(features.get(license_type, features["personal"]))

        return base_data
