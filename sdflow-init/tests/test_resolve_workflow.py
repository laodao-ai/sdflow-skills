"""Tests for resolve-workflow.sh（两步链契约：全局 canonical → 显式降级）。

fix-probe-scan-precision：本地 pin 判定步（原「步1」）已从生产脚本删除——规则解析恒指全局
canonical，仓内放多完整的规则副本都不再被读取。SDFLOW_HOME 一律重定向，绝不写真实 $HOME。
"""
import os
import stat
import subprocess
from pathlib import Path

import pytest

from test_support.windows import bash_executable, bash_path

SCRIPT = Path(__file__).parent.parent / "assets" / "hack" / "resolve-workflow.sh"


def _symlink_or_skip(link, target):
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError as exc:
        if os.name == "nt" and getattr(exc, "winerror", None) == 1314:
            pytest.skip("Windows symlink creation requires Developer Mode or elevated privilege")
        raise


def run_resolve(cwd, sdflow_home, args=()):
    env = dict(os.environ, SDFLOW_HOME=bash_path(sdflow_home))
    return subprocess.run(
        [bash_executable(), bash_path(SCRIPT), *args],
        cwd=str(cwd), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")


def make_bundle(path, with_tools=True, with_contract=True):
    """一个健全的 bundle：workflow.md 非空 + 两个清单目录（各含至少一个条目，CR-F1 sane 判据）+
    tools/ 目录非空 + lens-metric-contract.md 非空（fix-probe-scan-precision sane() 扩面，
    形状级判据）。`with_tools`/`with_contract` 用于反向锚——造一个缺其一的半坏 canonical。"""
    path.mkdir(parents=True)
    (path / "workflow.md").write_text("# wf\n", encoding="utf-8")
    (path / "spec-checklists").mkdir()
    (path / "spec-checklists" / "domains.md").write_text("# spec\n", encoding="utf-8")
    (path / "code-checklists").mkdir()
    (path / "code-checklists" / "domains.md").write_text("# code\n", encoding="utf-8")
    if with_tools:
        (path / "tools").mkdir()
        (path / "tools" / "anchor_lint.py").write_text("# tool\n", encoding="utf-8")
    if with_contract:
        (path / "lens-metric-contract.md").write_text("# contract\n", encoding="utf-8")
    return path


def make_repo(path):
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    return path


def make_repo_with_full_rule_copy(path):
    """仓内放一套完整规则副本（含 tools/）——反向锚 fixture：旧实现（保留步①）在此必命中
    本地 pin 并把 stdout 指向这里；新实现（两步链）MUST NOT 读它，恒指全局 canonical。"""
    repo = make_repo(path)
    wf = repo / "openspec" / "workflow"
    wf.mkdir(parents=True)
    (wf / "workflow.md").write_text("# locally pinned copy\n", encoding="utf-8")
    (wf / "spec-checklists").mkdir()
    (wf / "spec-checklists" / "domains.md").write_text("# spec\n", encoding="utf-8")
    (wf / "code-checklists").mkdir()
    (wf / "code-checklists" / "domains.md").write_text("# code\n", encoding="utf-8")
    (wf / "tools").mkdir()
    (wf / "tools" / "anchor_lint.py").write_text("# local tool copy\n", encoding="utf-8")
    (wf / "lens-metric-contract.md").write_text("# local contract copy\n", encoding="utf-8")
    return repo


class TestHappyPaths:
    def test_global_canonical_symlink_hit(self, tmp_path):
        repo = make_repo(tmp_path / "repo")
        bundle = make_bundle(tmp_path / "bundle")
        sdflow = tmp_path / "sdflow"
        sdflow.mkdir()
        _symlink_or_skip(sdflow / "workflow", bundle)
        r = run_resolve(repo, sdflow)
        assert r.returncode == 0
        assert Path(r.stdout.strip()).resolve() == bundle.resolve()

    def test_pointer_file_fallback(self, tmp_path):
        repo = make_repo(tmp_path / "repo")
        bundle = make_bundle(tmp_path / "bundle")
        sdflow = tmp_path / "sdflow"
        sdflow.mkdir()
        (sdflow / "workflow-path").write_text(str(bundle) + "\n", encoding="utf-8")
        r = run_resolve(repo, sdflow)
        assert r.returncode == 0
        assert Path(r.stdout.strip()).resolve() == bundle.resolve()

    def test_script_is_executable(self):
        if os.name == "nt":
            pytest.skip("Windows does not expose POSIX executable mode bits")
        assert SCRIPT.stat().st_mode & stat.S_IXUSR


class TestLocalCopyIgnored:
    """D13 核心不变量的反向锚（task 2.3）：仓内放全套规则副本（含 tools/）不改变解析结果——
    旧实现（保留步①本地 pin 判定）在此必红（会把 stdout 指向仓内副本，而非全局 canonical）。"""

    def test_full_local_rule_copy_still_resolves_to_global_canonical(self, tmp_path):
        repo = make_repo_with_full_rule_copy(tmp_path / "repo")
        bundle = make_bundle(tmp_path / "bundle")
        sdflow = tmp_path / "sdflow"
        sdflow.mkdir()
        _symlink_or_skip(sdflow / "workflow", bundle)
        r = run_resolve(repo, sdflow)
        assert r.returncode == 0
        resolved = Path(r.stdout.strip()).resolve()
        assert resolved == bundle.resolve()
        assert resolved != (repo / "openspec" / "workflow").resolve()

    def test_explain_reports_global_canonical_source_even_with_local_copy(self, tmp_path):
        repo = make_repo_with_full_rule_copy(tmp_path / "repo")
        bundle = make_bundle(tmp_path / "bundle")
        sdflow = tmp_path / "sdflow"
        sdflow.mkdir()
        _symlink_or_skip(sdflow / "workflow", bundle)
        r = run_resolve(repo, sdflow, args=("--explain",))
        assert "source=global-canonical" in r.stderr


class TestSaneExpandedShapeChecks:
    """task 2.5：sane() 扩面反向锚——canonical 缺 tools/（或非空）或缺 lens-metric-contract.md
    （或非空）→ exit 2（视同「全局 bundle 不完整」，MUST NOT 仍判健全）。"""

    def test_missing_tools_dir_exits_2(self, tmp_path):
        repo = make_repo(tmp_path / "repo")
        bundle = make_bundle(tmp_path / "bundle", with_tools=False)
        sdflow = tmp_path / "sdflow"
        sdflow.mkdir()
        _symlink_or_skip(sdflow / "workflow", bundle)
        r = run_resolve(repo, sdflow)
        assert r.returncode == 2

    def test_empty_tools_dir_exits_2(self, tmp_path):
        repo = make_repo(tmp_path / "repo")
        bundle = make_bundle(tmp_path / "bundle")
        (bundle / "tools" / "anchor_lint.py").unlink()  # tools/ 存在但空
        sdflow = tmp_path / "sdflow"
        sdflow.mkdir()
        _symlink_or_skip(sdflow / "workflow", bundle)
        r = run_resolve(repo, sdflow)
        assert r.returncode == 2

    def test_missing_contract_exits_2(self, tmp_path):
        repo = make_repo(tmp_path / "repo")
        bundle = make_bundle(tmp_path / "bundle", with_contract=False)
        sdflow = tmp_path / "sdflow"
        sdflow.mkdir()
        _symlink_or_skip(sdflow / "workflow", bundle)
        r = run_resolve(repo, sdflow)
        assert r.returncode == 2

    def test_empty_contract_exits_2(self, tmp_path):
        repo = make_repo(tmp_path / "repo")
        bundle = make_bundle(tmp_path / "bundle")
        (bundle / "lens-metric-contract.md").write_text("", encoding="utf-8")  # 存在但空
        sdflow = tmp_path / "sdflow"
        sdflow.mkdir()
        _symlink_or_skip(sdflow / "workflow", bundle)
        r = run_resolve(repo, sdflow)
        assert r.returncode == 2

    def test_full_shape_still_sane(self, tmp_path):
        """正向对照：tools/ 与 contract 都齐全非空时仍判健全（防扩面判据误伤既有健全 bundle）。"""
        repo = make_repo(tmp_path / "repo")
        bundle = make_bundle(tmp_path / "bundle")
        sdflow = tmp_path / "sdflow"
        sdflow.mkdir()
        _symlink_or_skip(sdflow / "workflow", bundle)
        r = run_resolve(repo, sdflow)
        assert r.returncode == 0


class TestEdgeCases:
    def test_global_missing_exits_2_with_guard_message(self, tmp_path):
        repo = make_repo(tmp_path / "repo")
        r = run_resolve(repo, tmp_path / "no-sdflow")
        assert r.returncode == 2
        assert r.stdout == ""
        assert "显式降级" in r.stderr and "setup.sh" in r.stderr

    def test_insane_bundle_treated_as_missing(self, tmp_path):
        repo = make_repo(tmp_path / "repo")
        bundle = tmp_path / "bundle"                  # 半坏：workflow.md 为空文件
        bundle.mkdir()
        (bundle / "workflow.md").touch()
        (bundle / "spec-checklists").mkdir()
        (bundle / "code-checklists").mkdir()
        (bundle / "tools").mkdir()
        (bundle / "tools" / "x.py").write_text("# x\n", encoding="utf-8")
        (bundle / "lens-metric-contract.md").write_text("# c\n", encoding="utf-8")
        sdflow = tmp_path / "sdflow"
        sdflow.mkdir()
        _symlink_or_skip(sdflow / "workflow", bundle)
        r = run_resolve(repo, sdflow)
        assert r.returncode == 2                      # 健全性不过检 = 缺失

    def test_pointer_with_trailing_crlf_and_spaces(self, tmp_path):
        repo = make_repo(tmp_path / "repo")
        bundle = make_bundle(tmp_path / "bun dle")    # 路径含空格
        sdflow = tmp_path / "sdflow"
        sdflow.mkdir()
        (sdflow / "workflow-path").write_text(str(bundle) + "  \r\n", encoding="utf-8")
        r = run_resolve(repo, sdflow)
        assert r.returncode == 0
        assert Path(r.stdout.strip()).resolve() == bundle.resolve()

    def test_root_flag_overrides_cwd(self, tmp_path):
        repo = make_repo(tmp_path / "repo")
        bundle = make_bundle(tmp_path / "bundle")
        sdflow = tmp_path / "sdflow"
        sdflow.mkdir()
        _symlink_or_skip(sdflow / "workflow", bundle)
        sub = repo / "some" / "deep" / "dir"
        sub.mkdir(parents=True)
        r = run_resolve(sub, sdflow, args=("--root", str(repo)))
        assert r.returncode == 0
        assert Path(r.stdout.strip()).resolve() == bundle.resolve()

    def test_explain_reports_source(self, tmp_path):
        repo = make_repo(tmp_path / "repo")
        bundle = make_bundle(tmp_path / "bundle")
        sdflow = tmp_path / "sdflow"
        sdflow.mkdir()
        _symlink_or_skip(sdflow / "workflow", bundle)
        r = run_resolve(repo, sdflow, args=("--explain",))
        assert "source=global-canonical" in r.stderr

    def test_unknown_arg_exits_64(self, tmp_path):
        repo = make_repo(tmp_path / "repo")
        r = run_resolve(repo, tmp_path / "no-sdflow", args=("--bogus",))
        assert r.returncode == 64

    def test_unreadable_pointer_degrades_not_crashes(self, tmp_path):
        repo = make_repo(tmp_path / "repo")
        sdflow = tmp_path / "sdflow"
        sdflow.mkdir()
        pointer = sdflow / "workflow-path"
        pointer.write_text(str(tmp_path / "bundle") + "\n", encoding="utf-8")
        pointer.chmod(0o000)
        try:
            r = run_resolve(repo, sdflow)
            assert r.returncode == 2
            assert "显式降级" in r.stderr
            assert r.stdout.strip() == ""       # T13: 降级路径不得往 stdout 吐路径（防 skill 误把告警当解析结果）
        finally:
            pointer.chmod(0o644)  # 允许 tmp_path 清理时删除

    def test_root_missing_value_exits_64(self, tmp_path):
        repo = make_repo(tmp_path / "repo")
        r = run_resolve(repo, tmp_path / "no-sdflow", args=("--root",))
        assert r.returncode == 64
        assert "--root requires a value" in r.stderr   # T13: 缺值须显式报错文案，非静默 exit

    def test_root_flag_swallows_next_flag_exits_64(self, tmp_path):
        """--root 后紧跟另一个 flag（如 --explain）时不得把它当值吞掉（B1-F4）。"""
        repo = make_repo(tmp_path / "repo")
        r = run_resolve(repo, tmp_path / "no-sdflow", args=("--root", "--explain"))
        assert r.returncode == 64

    def test_deleted_cwd_exits_64(self, tmp_path):
        """cwd 被删时不得静默 fallback 到失败的 pwd（B1-F1）——显式 exit 64 + 指引 --root。"""
        if os.name == "nt":
            pytest.skip("Git Bash retains a usable logical cwd after Windows removes the directory")
        d = tmp_path / "will-be-deleted"
        d.mkdir()
        r = subprocess.run(
            [bash_executable(), "-c", f'cd "{bash_path(d)}" && rmdir "{bash_path(d)}" && bash "{bash_path(SCRIPT)}" --explain'],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert r.returncode == 64
        assert "无法确定仓根" in r.stderr

    def test_relative_sdflow_home_exits_2_and_warns(self, tmp_path):
        """SDFLOW_HOME 非绝对路径时忽略全局 canonical 探测 → 步2降级 exit 2（B1-F3）。"""
        repo = make_repo(tmp_path / "repo")
        r = run_resolve(repo, "relative/sdflow/path")
        assert r.returncode == 2
        assert "非绝对路径" in r.stderr

    def test_sane_rejects_empty_checklist_dir(self, tmp_path):
        """sane() 须要求两个清单目录各至少含一个条目，防「目录存在但空」静默判健全（CR-F1）。"""
        repo = make_repo(tmp_path / "repo")
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "workflow.md").write_text("# wf\n", encoding="utf-8")
        (bundle / "spec-checklists").mkdir()  # 空目录
        (bundle / "code-checklists").mkdir()
        (bundle / "code-checklists" / "domains.md").write_text("# code\n", encoding="utf-8")
        (bundle / "tools").mkdir()
        (bundle / "tools" / "x.py").write_text("# x\n", encoding="utf-8")
        (bundle / "lens-metric-contract.md").write_text("# c\n", encoding="utf-8")
        sdflow = tmp_path / "sdflow"
        sdflow.mkdir()
        _symlink_or_skip(sdflow / "workflow", bundle)
        r = run_resolve(repo, sdflow)
        assert r.returncode == 2

    def test_pointer_path_with_chinese_dir_resolves(self, tmp_path):
        """指针文件指向含中文目录名的路径须能正常解析（gstack 5.3 缺口）。"""
        repo = make_repo(tmp_path / "repo")
        bundle = make_bundle(tmp_path / "中文目录" / "bundle")
        sdflow = tmp_path / "sdflow"
        sdflow.mkdir()
        (sdflow / "workflow-path").write_text(str(bundle) + "\n", encoding="utf-8")
        r = run_resolve(repo, sdflow)
        assert r.returncode == 0
        assert Path(r.stdout.strip()).resolve() == bundle.resolve()
