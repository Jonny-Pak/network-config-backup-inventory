"""Compatibility entry point for the shared sanitized backup workflow."""
from pathlib import Path
import sys
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.main import main
if __name__ == "__main__":
    raise SystemExit(main())
