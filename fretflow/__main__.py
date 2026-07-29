"""Allow running with ``python -m fretflow``."""

from fretflow.app import main

if __name__ == "__main__":
    raise SystemExit(main())
