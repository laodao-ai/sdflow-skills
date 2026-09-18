import os
import subprocess
from pathlib import Path

import pytest

from test_support.windows import bash_executable, bash_path


def test_bash_path_converts_windows_drive_and_separators():
    assert bash_path(r"C:\dir with spaces\a;$()&.sh") == "/c/dir with spaces/a;$()&.sh"


def test_bash_path_keeps_posix_path():
    assert bash_path(Path("/tmp/example")) == "/tmp/example"


@pytest.mark.skipif(os.name != "nt", reason="Windows-specific Bash selection")
def test_bash_executable_prefers_git_bash_over_wsl_launcher():
    selected = Path(bash_executable())

    assert "windowsapps" not in str(selected).lower()
    assert selected.name.lower() in {"bash.exe", "bash"}
    assert "git" in str(selected).lower()


@pytest.mark.skipif(os.name != "nt", reason="Windows-specific Bash selection")
def test_git_bash_preserves_path_command_overrides(tmp_path):
    stub = tmp_path / "grep"
    stub.write_text("#!/bin/sh\nexit 42\n", encoding="utf-8")
    result = subprocess.run(
        [bash_executable(), "-c", "grep anything"],
        env=dict(os.environ, PATH=f"{tmp_path}{os.pathsep}{os.environ['PATH']}"),
        capture_output=True, timeout=15,
    )
    assert result.returncode == 42, result.stderr
