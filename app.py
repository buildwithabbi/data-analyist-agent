"""Backward-compatible script entry point.

Prefer ``python -m data_analyst_agent`` or ``data-analyst-agent`` after the
project has been installed in editable mode.
"""

import sys
from pathlib import Path

# Allow ``python3 app.py`` from a fresh checkout, before ``pip install -e .``.
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from data_analyst_agent.cli import main


if __name__ == "__main__":
    main()
