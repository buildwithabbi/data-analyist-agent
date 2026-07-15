"""Consistent, readable console output for the application."""

import json
from typing import Any


def pretty_json(value: Any) -> str:
    """Return a JSON value as indented text; leave ordinary text unchanged."""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return value

    return json.dumps(value, indent=2, ensure_ascii=False, default=str)


def print_json(title: str, value: Any) -> None:
    """Print a titled, consistently formatted JSON block."""
    print(f"\n===== {title} =====")
    print(pretty_json(value))
