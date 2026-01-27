"""Generate RSA keys and sample licenses for HifzDefend."""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hifzdefend.licensing.crypto import LicenseCrypto
from hifzdefend.licensing.manager import LicenseManager


def generate_keys(keys_dir: Path) -> None:
    """Generate RSA key pair.

    Args:
        keys_dir: Directory to save keys
    """
    keys_dir.mkdir(parents=True, exist_ok=True)

    private_key_path = keys_dir / "private.pem"
    public_key_path = keys_dir / "public.pem"

    if private_key_path.exists():
        response = input(f"{private_key_path} already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            return

    print("Generating RSA key pair...")
    crypto = LicenseCrypto()
    crypto.generate_key_pair(str(private_key_path), str(public_key_path))

    print(f"✓ Private key: {private_key_path}")
    print(f"✓ Public key: {public_key_path}")
    print("\n⚠ WARNING: Keep private key secure! It's used to sign licenses.")


def generate_trial_license(email: str, days: int, output_file: Path, crypto: LicenseCrypto) -> None:
    """Generate trial license.

    Args:
        email: Customer email
        days: Trial duration
        output_file: Output file path
        crypto: License crypto instance
    """
    license_data = LicenseManager.create_trial_license(email, days)
    license_key = crypto.generate_license_key(license_data)

    # Format key for display
    formatted_key = LicenseCrypto.format_key(license_key)

    result = {
        "license_key": license_key,
        "formatted_key": formatted_key,
        "license_data": license_data,
    }

    # Save to file
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n✓ Trial license generated:")
    print(f"  Email: {email}")
    print(f"  Duration: {days} days")
    print(f"  Expires: {license_data['expires_at']}")
    print(f"\n  License Key:\n  {formatted_key}")
    print(f"\n  Saved to: {output_file}")


def generate_paid_license(
    email: str,
    license_type: str,
    duration_days: int | None,
    output_file: Path,
    crypto: LicenseCrypto
) -> None:
    """Generate paid license.

    Args:
        email: Customer email
        license_type: License type (personal, professional, enterprise)
        duration_days: Duration in days (None for perpetual)
        output_file: Output file path
        crypto: License crypto instance
    """
    license_data = LicenseManager.create_paid_license(email, license_type, duration_days)
    license_key = crypto.generate_license_key(license_data)

    # Format key for display
    formatted_key = LicenseCrypto.format_key(license_key)

    result = {
        "license_key": license_key,
        "formatted_key": formatted_key,
        "license_data": license_data,
    }

    # Save to file
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)

    duration_str = f"{duration_days} days" if duration_days else "perpetual"
    expires_str = license_data.get('expires_at', 'Never')

    print(f"\n✓ {license_type.capitalize()} license generated:")
    print(f"  Email: {email}")
    print(f"  Duration: {duration_str}")
    print(f"  Expires: {expires_str}")
    print(f"\n  License Key:\n  {formatted_key}")
    print(f"\n  Saved to: {output_file}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate licenses for HifzDefend")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Generate keys command
    keys_parser = subparsers.add_parser("keys", help="Generate RSA key pair")
    keys_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "src" / "hifzdefend" / "licensing" / "keys",
        help="Output directory for keys"
    )

    # Generate trial license command
    trial_parser = subparsers.add_parser("trial", help="Generate trial license")
    trial_parser.add_argument("email", help="Customer email")
    trial_parser.add_argument("--days", type=int, default=14, help="Trial duration in days")
    trial_parser.add_argument("--output", type=Path, help="Output file path")

    # Generate paid license command
    paid_parser = subparsers.add_parser("paid", help="Generate paid license")
    paid_parser.add_argument("email", help="Customer email")
    paid_parser.add_argument(
        "type",
        choices=["personal", "professional", "enterprise"],
        help="License type"
    )
    paid_parser.add_argument("--days", type=int, default=365, help="License duration (omit for perpetual)")
    paid_parser.add_argument("--perpetual", action="store_true", help="Create perpetual license")
    paid_parser.add_argument("--output", type=Path, help="Output file path")

    args = parser.parse_args()

    if args.command == "keys":
        generate_keys(args.output_dir)

    elif args.command == "trial":
        # Load private key
        keys_dir = Path(__file__).parent.parent / "src" / "hifzdefend" / "licensing" / "keys"
        private_key_path = keys_dir / "private.pem"

        if not private_key_path.exists():
            print(f"Error: Private key not found at {private_key_path}")
            print("Run 'python generate_licenses.py keys' first to generate keys.")
            sys.exit(1)

        crypto = LicenseCrypto(private_key_path=str(private_key_path))

        output_file = args.output or Path(f"trial_{args.email.replace('@', '_')}.json")
        generate_trial_license(args.email, args.days, output_file, crypto)

    elif args.command == "paid":
        # Load private key
        keys_dir = Path(__file__).parent.parent / "src" / "hifzdefend" / "licensing" / "keys"
        private_key_path = keys_dir / "private.pem"

        if not private_key_path.exists():
            print(f"Error: Private key not found at {private_key_path}")
            print("Run 'python generate_licenses.py keys' first to generate keys.")
            sys.exit(1)

        crypto = LicenseCrypto(private_key_path=str(private_key_path))

        duration_days = None if args.perpetual else args.days
        output_file = args.output or Path(f"{args.type}_{args.email.replace('@', '_')}.json")
        generate_paid_license(args.email, args.type, duration_days, output_file, crypto)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
