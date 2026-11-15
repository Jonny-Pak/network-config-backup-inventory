"""Compatibility SSH diagnostic using allowlist and strict host-key checks."""
from pathlib import Path
import sys
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.test_ssh import main
if __name__ == "__main__":
    main()
