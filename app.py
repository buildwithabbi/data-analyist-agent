"""Backward-compatible script entry point.

Prefer ``python -m data_analyst_agent`` or ``data-analyst-agent`` after the
project has been installed in editable mode.
"""

from data_analyst_agent.cli import main


if __name__ == "__main__":
    main()
