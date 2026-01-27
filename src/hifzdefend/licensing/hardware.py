"""Hardware fingerprinting for license binding."""

import hashlib
import platform
import subprocess
from typing import Optional


class HardwareFingerprint:
    """Generate hardware fingerprint for license binding."""

    @staticmethod
    def get_fingerprint() -> str:
        """Generate unique hardware fingerprint.

        Returns:
            Hardware fingerprint hash
        """
        components = []

        # CPU info
        try:
            cpu_info = platform.processor()
            components.append(cpu_info)
        except Exception:
            pass

        # System UUID (Windows)
        try:
            result = subprocess.run(
                ["wmic", "csproduct", "get", "UUID"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                uuid = result.stdout.strip().split("\n")[-1].strip()
                if uuid and uuid != "UUID":
                    components.append(uuid)
        except Exception:
            pass

        # Motherboard serial
        try:
            result = subprocess.run(
                ["wmic", "baseboard", "get", "serialnumber"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                serial = result.stdout.strip().split("\n")[-1].strip()
                if serial and serial != "SerialNumber":
                    components.append(serial)
        except Exception:
            pass

        # MAC address (first network adapter)
        try:
            import uuid
            mac = uuid.getnode()
            components.append(str(mac))
        except Exception:
            pass

        # Combine all components
        if not components:
            # Fallback to machine name
            components.append(platform.node())

        fingerprint_string = "|".join(components)

        # Generate SHA256 hash
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()

    @staticmethod
    def get_device_name() -> str:
        """Get device name.

        Returns:
            Device name
        """
        try:
            return platform.node()
        except Exception:
            return "Unknown Device"
