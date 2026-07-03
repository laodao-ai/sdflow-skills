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


class TestEdgeCases:
    def test_partial_residue_pins_and_warns(self, tmp_path):
        repo = make_repo(tmp_path / "repo", with_rules=False)
        (repo / "openspec" / "workflow" / "spec-checklists").mkdir()  # 只残留一个单元
        r = run_resolve(repo, tmp_path / "no-sdflow")
        assert r.returncode == 0                      # any-of 即 pin
        assert r.stdout.strip() == str(repo / "openspec" / "workflow")
        assert "部分残留" in r.stderr                  # 专门告警，不静默

    def test_global_missing_exits_2_with_guard_message(self, tmp_path):
        repo = make_repo(tmp_path / "repo", with_rules=False)
        r = run_resolve(repo, tmp_path / "no-sdflow")
        assert r.returncode == 2
        assert r.stdout == ""
        assert "显式降级" in r.stderr and "setup.sh" in r.stderr

    def test_insane_bundle_treated_as_missing(self, tmp_path):
        repo = make_repo(tmp_path / "repo", with_rules=False)
        bundle = tmp_path / "bundle"                  # 半坏：workflow.md 为空文件
        bundle.mkdir()
        (bundle / "workflow.md").touch()
        (bundle / "spec-checklists").mkdir()
        (bundle / "code-checklists").mkdir()
        sdflow = tmp_path / "sdflow"
        sdflow.mkdir()
        (sdflow / "workflow").symlink_to(bundle)
        r = run_resolve(repo, sdflow)
        assert r.returncode == 2                      # 健全性不过检 = 缺失

    def test_pointer_with_trailing_crlf_and_spaces(self, tmp_path):
        repo = make_repo(tmp_path / "repo", with_rules=False)
        bundle = make_bundle(tmp_path / "bun dle")    # 路径含空格
        sdflow = tmp_path / "sdflow"
        sdflow.mkdir()
        (sdflow / "workflow-path").write_text(str(bundle) + "  \r\n", encoding="utf-8")
        r = run_resolve(repo, sdflow)
        assert r.returncode == 0
        assert r.stdout.strip() == str(bundle)

    def test_root_flag_overrides_cwd(self, tmp_path):
        repo = make_repo(tmp_path / "repo", with_rules=True)
        sub = repo / "some" / "deep" / "dir"
        sub.mkdir(parents=True)
        r = run_resolve(sub, tmp_path / "no-sdflow", args=("--root", str(repo)))
        assert r.returncode == 0
        assert r.stdout.strip() == str(repo / "openspec" / "workflow")

    def test_explain_reports_source(self, tmp_path):
        repo = make_repo(tmp_path / "repo", with_rules=True)
        r = run_resolve(repo, tmp_path / "no-sdflow", args=("--explain",))
        assert "source=local-pin" in r.stderr

    def test_unknown_arg_exits_64(self, tmp_path):
        repo = make_repo(tmp_path / "repo", with_rules=True)
        r = run_resolve(repo, tmp_path / "no-sdflow", args=("--bogus",))
        assert r.returncode == 64

    def test_unreadable_pointer_degrades_not_crashes(self, tmp_path):
        repo = make_repo(tmp_path / "repo", with_rules=False)
        sdflow = tmp_path / "sdflow"
        sdflow.mkdir()
        pointer = sdflow / "workflow-path"
        pointer.write_text(str(tmp_path / "bundle") + "\n", encoding="utf-8")
        pointer.chmod(0o000)
        try:
            r = run_resolve(repo, sdflow)
            assert r.returncode == 2
            assert "显式降级" in r.stderr
        finally:
            pointer.chmod(0o644)  # 允许 tmp_path 清理时删除

    def test_root_missing_value_exits_64(self, tmp_path):
        repo = make_repo(tmp_path / "repo", with_rules=True)
        r = run_resolve(repo, tmp_path / "no-sdflow", args=("--root",))
        assert r.returncode == 64
