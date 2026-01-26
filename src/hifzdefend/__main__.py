"""
HifzDefend CLI entry point.
"""

import sys
from .cli.commands import cli


def main():
    """Main entry point for HifzDefend CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
