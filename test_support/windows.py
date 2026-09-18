"""Small cross-platform adapters used by tests that exercise Bash assets."""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path


def bash_executable() -> str:
    """Return Git Bash on Windows, avoiding the System32 WSL launcher."""
    if os.name == "nt":
        program_files = (
            os.environ.get("ProgramW6432"),
            os.environ.get("ProgramFiles"),
            os.environ.get("ProgramFiles(x86)"),
        )
        for root in filter(None, program_files):
            # bin/bash.exe is a launcher that prepends its own PATH, hiding
            # command stubs supplied by subprocess tests. Use the shell itself.
            candidate = Path(root) / "Git" / "usr" / "bin" / "bash.exe"
            if candidate.is_file():
                return str(candidate)

    resolved = shutil.which("bash")
    if not resolved or (os.name == "nt" and any(
        part in resolved.replace("\\", "/").lower().split("/")
        for part in ("windowsapps", "system32", "sysnative")
    )):
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


# Native PowerShell Python sessions do not inherit Git Bash's coreutils PATH.
# Prepare it once, before test callers copy os.environ, so GNU tools also take
# precedence over Windows namesakes. Subsequent per-test PATH overrides remain
# authoritative because the actual Bash executable does not reset them.
if os.name == "nt":
    try:
        _bash_tools = str(Path(bash_executable()).parent)
    except RuntimeError:
        pass  # Pure path adapters remain importable when Git Bash is absent.
    else:
        _test_path = os.environ.get("PATH", "")
        if os.path.normcase(_bash_tools) not in {
            os.path.normcase(part) for part in _test_path.split(os.pathsep)
        }:
            os.environ["PATH"] = _bash_tools + os.pathsep + _test_path
