"""Tests for resolve-workflow.sh（三步链契约）。SDFLOW_HOME 一律重定向，绝不写真实 $HOME。"""
import os
import stat
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "assets" / "hack" / "resolve-workflow.sh"


def run_resolve(cwd, sdflow_home, args=()):
    env = dict(os.environ, SDFLOW_HOME=str(sdflow_home))
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        cwd=str(cwd), env=env, capture_output=True, text=True)


def make_bundle(path):
    """一个健全的 bundle：workflow.md 非空 + 两个清单目录。"""
    path.mkdir(parents=True)
    (path / "workflow.md").write_text("# wf\n", encoding="utf-8")
    (path / "spec-checklists").mkdir()
    (path / "code-checklists").mkdir()
    return path


def make_repo(path, with_rules=False):
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    wf = path / "openspec" / "workflow"
    (wf / "tools").mkdir(parents=True)          # tools/ 恒存在——判据必须查规则本体
    if with_rules:
        (wf / "workflow.md").write_text("# pinned\n", encoding="utf-8")
        (wf / "spec-checklists").mkdir()
        (wf / "code-checklists").mkdir()
    return path


class TestHappyPaths:
    def test_local_pin_hit(self, tmp_path):
        repo = make_repo(tmp_path / "repo", with_rules=True)
        r = run_resolve(repo, tmp_path / "nonexistent-sdflow")
        assert r.returncode == 0
        assert r.stdout.strip() == str(repo / "openspec" / "workflow")

    def test_tools_only_repo_falls_to_global_symlink(self, tmp_path):
        repo = make_repo(tmp_path / "repo", with_rules=False)
        bundle = make_bundle(tmp_path / "bundle")
        sdflow = tmp_path / "sdflow"
        sdflow.mkdir()
        (sdflow / "workflow").symlink_to(bundle)
        r = run_resolve(repo, sdflow)
        assert r.returncode == 0
        assert Path(r.stdout.strip()).resolve() == bundle.resolve()

    def test_pointer_file_fallback(self, tmp_path):
        repo = make_repo(tmp_path / "repo", with_rules=False)
        bundle = make_bundle(tmp_path / "bundle")
        sdflow = tmp_path / "sdflow"
        sdflow.mkdir()
        (sdflow / "workflow-path").write_text(str(bundle) + "\n", encoding="utf-8")
        r = run_resolve(repo, sdflow)
        assert r.returncode == 0
        assert r.stdout.strip() == str(bundle)

    def test_script_is_executable(self):
        assert SCRIPT.stat().st_mode & stat.S_IXUSR
