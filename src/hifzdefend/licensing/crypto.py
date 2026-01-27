"""Cryptographic functions for license key generation and validation."""

import base64
import hashlib
import json
from datetime import datetime
from typing import Dict, Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend


class LicenseCrypto:
    """License key cryptography."""

    def __init__(self, private_key_path: Optional[str] = None, public_key_path: Optional[str] = None):
        """Initialize license crypto.

        Args:
            private_key_path: Path to RSA private key (for signing)
            public_key_path: Path to RSA public key (for validation)
        """
        self.private_key = None
        self.public_key = None

        if private_key_path:
            self.load_private_key(private_key_path)

        if public_key_path:
            self.load_public_key(public_key_path)

    def generate_key_pair(self, private_key_path: str, public_key_path: str) -> None:
        """Generate RSA key pair for license signing.

        Args:
            private_key_path: Where to save private key
            public_key_path: Where to save public key
        """
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # Save private key
        with open(private_key_path, "wb") as f:
            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
            )

        # Get public key
        public_key = private_key.public_key()

        # Save public key
        with open(public_key_path, "wb") as f:
            f.write(
                public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
            )

        self.private_key = private_key
        self.public_key = public_key

    def load_private_key(self, path: str) -> None:
        """Load private key from file."""
        with open(path, "rb") as f:
            self.private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )

    def load_public_key(self, path: str) -> None:
        """Load public key from file."""
        with open(path, "rb") as f:
            self.public_key = serialization.load_pem_public_key(
                f.read(),
                backend=default_backend()
            )

    def generate_license_key(self, license_data: Dict) -> str:
        """Generate signed license key.

        Args:
            license_data: License information dictionary

        Returns:
            Base64-encoded signed license key
        """
        if not self.private_key:
            raise ValueError("Private key not loaded")

        # Serialize license data
        data_json = json.dumps(license_data, sort_keys=True, default=str)
        data_bytes = data_json.encode()

        # Sign the data
        signature = self.private_key.sign(
            data_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        # Combine data and signature
        license_package = {
            "data": base64.b64encode(data_bytes).decode(),
            "signature": base64.b64encode(signature).decode()
        }

        # Encode as base64
        license_json = json.dumps(license_package)
        license_key = base64.b64encode(license_json.encode()).decode()

        return license_key

    def validate_license_key(self, license_key: str) -> Optional[Dict]:
        """Validate and decode license key.

        Args:
            license_key: Base64-encoded signed license key

        Returns:
            License data if valid, None otherwise
        """
        if not self.public_key:
            raise ValueError("Public key not loaded")

        try:
            # Decode base64
            license_json = base64.b64decode(license_key).decode()
            license_package = json.loads(license_json)

            # Extract data and signature
            data_bytes = base64.b64decode(license_package["data"])
            signature = base64.b64decode(license_package["signature"])

            # Verify signature
            self.public_key.verify(
                signature,
                data_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

            # Signature is valid, decode data
            license_data = json.loads(data_bytes.decode())

            return license_data

        except Exception:
            return None

    @staticmethod
    def format_key(license_key: str, group_size: int = 5, separator: str = "-") -> str:
        """Format license key for display.

        Args:
            license_key: Raw license key
            group_size: Characters per group
            separator: Group separator

        Returns:
            Formatted license key
        """
        # Remove existing separators
        clean_key = license_key.replace(separator, "")

        # Split into groups
        groups = [clean_key[i:i+group_size] for i in range(0, len(clean_key), group_size)]

        return separator.join(groups)
