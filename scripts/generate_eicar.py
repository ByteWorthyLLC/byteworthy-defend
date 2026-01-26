"""
EICAR test file generator.

Generates the standard EICAR anti-virus test file and stores it in a
password-protected ZIP file for safe handling.

EICAR is a harmless test file recognized by all antivirus software.
Password: infected
"""

import sys
import zipfile
from pathlib import Path


# EICAR test string (harmless test file recognized by all AV software)
EICAR_STRING = (
    b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'
)


def generate_eicar_zip(output_path: Path, password: str = "infected") -> None:
    """
    Generate password-protected ZIP with EICAR test file.

    Args:
        output_path: Path to output ZIP file
        password: ZIP password (default: "infected")
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create password-protected ZIP
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.setpassword(password.encode('utf-8'))
        zf.writestr('eicar.txt', EICAR_STRING)

    print(f"✓ EICAR test file created: {output_path}")
    print(f"  Password: {password}")
    print(f"  File size: {output_path.stat().st_size} bytes")


def generate_plain_eicar(output_path: Path) -> None:
    """
    Generate plain (unencrypted) EICAR test file.

    WARNING: This file will be detected by antivirus software!

    Args:
        output_path: Path to output file
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write EICAR string
    with open(output_path, 'wb') as f:
        f.write(EICAR_STRING)

    print(f"✓ Plain EICAR test file created: {output_path}")
    print(f"  WARNING: This file will be detected by antivirus software!")
    print(f"  File size: {output_path.stat().st_size} bytes")


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate EICAR test files for antivirus testing"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output path (default: tests/fixtures/eicar_test.zip)",
    )
    parser.add_argument(
        "--plain",
        action="store_true",
        help="Generate plain (unencrypted) EICAR file (WARNING: detected by AV)",
    )
    parser.add_argument(
        "--password",
        "-p",
        default="infected",
        help="ZIP password (default: infected)",
    )

    args = parser.parse_args()

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        # Default to tests/fixtures
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        if args.plain:
            output_path = project_root / "tests" / "fixtures" / "eicar.txt"
        else:
            output_path = project_root / "tests" / "fixtures" / "eicar_test.zip"

    # Generate file
    if args.plain:
        print("\nWARNING: Generating plain EICAR file!")
        print("This file will be detected by your antivirus software.")
        print("Ensure Windows Defender exclusions are set up.\n")

        response = input("Continue? (yes/no): ")
        if response.lower() != "yes":
            print("Cancelled.")
            return

        generate_plain_eicar(output_path)
    else:
        generate_eicar_zip(output_path, args.password)

    print("\nEICAR Info:")
    print("  The EICAR test file is a harmless test pattern recognized by")
    print("  all antivirus software. It contains no actual malicious code.")
    print("  More info: https://www.eicar.org/")


if __name__ == "__main__":
    main()
