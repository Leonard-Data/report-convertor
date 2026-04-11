"""Path helpers for template and output defaults."""

from __future__ import annotations

from pathlib import Path


def default_templates_dir() -> Path:
    """Return the default template directory for local storage."""

    return Path.cwd() / "templates"
