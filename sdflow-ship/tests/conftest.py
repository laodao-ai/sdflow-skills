import subprocess
import pytest

def _git(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True,
                   capture_output=True, text=True)

@pytest.fixture
def repo(tmp_path):
    _git_init = ["init", "-q", "-b", "main"]
    subprocess.run(["git", "-C", str(tmp_path), *_git_init], check=True,
                   capture_output=True, text=True)
    _git(tmp_path, "config", "user.name", "t")
    _git(tmp_path, "config", "user.email", "t@t")
    return tmp_path

def commit_all(root, msg):
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", msg, "--allow-empty")

def mkchange(root, name="demo"):
    d = root / "openspec" / "changes" / name
    d.mkdir(parents=True, exist_ok=True)
    return d
