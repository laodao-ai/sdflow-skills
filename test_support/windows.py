"""Small cross-platform adapters used by tests that exercise Bash assets."""

from __future__ import annotations

import os
import re
import shutil


def bash_executable() -> str:
    """Return Git Bash on Windows, avoiding the System32 WSL launcher."""
    resolved = shutil.which("bash")
    if not resolved:
        raise RuntimeError("bash executable not found")
    return resolved


def bash_path(value: str | os.PathLike[str]) -> str:
    """Translate a native absolute path to the spelling understood by Git Bash."""
    path = str(value).replace("\\", "/")
    if re.match(r"^[A-Za-z]:/", path):
        return f"/{path[0].lower()}{path[2:]}"
    return path


def bash_argv(values) -> list[str]:
    """Translate native path-shaped argv items while leaving ordinary text intact."""
    return [bash_path(value) for value in values]
