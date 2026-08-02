"""Backward-compatible entry point forwarding to data_analyst_agent.domain.models."""

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from data_analyst_agent.domain.models import *