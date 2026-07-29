from pathlib import Path

from test_support.windows import bash_path


def test_bash_path_converts_windows_drive_and_separators():
    assert bash_path(r"C:\dir with spaces\a;$()&.sh") == "/c/dir with spaces/a;$()&.sh"


def test_bash_path_keeps_posix_path():
    assert bash_path(Path("/tmp/example")) == "/tmp/example"
