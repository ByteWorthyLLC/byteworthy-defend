"""License validation logic."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .crypto import LicenseCrypto
from .hardware import HardwareFingerprint
from .models import License, LicenseStatus, LicenseType, LicenseValidation


class LicenseValidator:
    """Validate license keys and check entitlements."""

    def __init__(self, public_key_path: Optional[Path] = None):
        """Initialize validator.

        Args:
            public_key_path: Path to public key for validation
        """
        self.crypto = LicenseCrypto(
            public_key_path=str(public_key_path) if public_key_path else None
        )

    def validate(self, license_key: str, check_hardware: bool = True) -> LicenseValidation:
        """Validate license key.

        Args:
            license_key: License key to validate
            check_hardware: Whether to check hardware binding

        Returns:
            Validation result
        """
        warnings = []

        # Decode and verify signature
        license_data = self.crypto.validate_license_key(license_key)
        if not license_data:
            return LicenseValidation(
                valid=False,
                error="Invalid license key signature"
            )

        # Parse license
        try:
            license = License(**license_data)
        except Exception as e:
            return LicenseValidation(
                valid=False,
                error=f"Invalid license data: {e}"
            )

        # Check status
        if license.status != LicenseStatus.ACTIVE:
            return LicenseValidation(
                valid=False,
                license=license,
                error=f"License is {license.status}"
            )

        # Check expiration
        if license.expires_at:
            if datetime.utcnow() > license.expires_at:
                return LicenseValidation(
                    valid=False,
                    license=license,
                    error="License has expired"
                )

            # Warn if expiring soon (7 days)
            days_until_expiry = (license.expires_at - datetime.utcnow()).days
            if days_until_expiry <= 7:
                warnings.append(f"License expires in {days_until_expiry} days")

        # Check hardware binding
        if check_hardware and license.hardware_id:
            current_hardware = HardwareFingerprint.get_fingerprint()
            if current_hardware != license.hardware_id:
                return LicenseValidation(
                    valid=False,
                    license=license,
                    error="License is bound to different hardware"
                )

        # Check activation limit
        if license.activation_count > license.max_activations:
            return LicenseValidation(
                valid=False,
                license=license,
                error="Maximum activations exceeded"
            )

        # Trial license warning
        if license.license_type == LicenseType.TRIAL:
            if license.expires_at:
                days_remaining = (license.expires_at - datetime.utcnow()).days
                warnings.append(f"Trial license - {days_remaining} days remaining")

        return LicenseValidation(
            valid=True,
            license=license,
            warnings=warnings
        )

    def check_feature(self, license: License, feature: str) -> bool:
        """Check if license has access to feature.

        Args:
            license: License to check
            feature: Feature name

        Returns:
            Whether feature is enabled
        """
        feature_map = {
            "ai_analysis": license.ai_enabled,
            "real_time": license.real_time_protection,
            "cloud_backup": license.cloud_backup,
            "priority_support": license.priority_support,
        }

        return feature_map.get(feature, False)

    def get_scan_limit(self, license: License) -> Optional[int]:
        """Get daily scan limit for license.

        Args:
            license: License to check

        Returns:
            Daily scan limit, or None for unlimited
        """
        return license.max_scans_per_day
