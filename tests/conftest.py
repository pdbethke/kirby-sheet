"""Make `tests` importable as a package, as kirby-cost's suite does."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
