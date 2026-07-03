"""setup.sh 的 ~/.sdflow 建链测试。HOME/SDFLOW_HOME 全部重定向 tmp_path。"""
import os
import stat
import subprocess
from pathlib import Path

REPO = Path(__file__).parent.parent.parent


def run_setup(tmp_path):
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    env = dict(os.environ, HOME=str(home), SDFLOW_HOME=str(home / ".sdflow"))
    r = subprocess.run(["bash", str(REPO / "setup.sh")],
                       env=env, capture_output=True, text=True)
    return r, home / ".sdflow"


class TestInstallSdflow:
    def test_creates_canonical_symlink_and_hack_scripts(self, tmp_path):
        r, sdflow = run_setup(tmp_path)
        assert r.returncode == 0
        link = sdflow / "workflow"
        assert link.is_symlink()
        assert link.resolve() == (REPO / "sdflow-init" / "assets" / "workflow").resolve()
        for name in ("checkpoint-commit.sh", "resolve-workflow.sh"):
            f = sdflow / "hack" / name
            assert f.is_file() and not f.is_symlink()      # 拷贝，非软链
            assert f.stat().st_mode & stat.S_IXUSR          # exec 位一次设好

    def test_idempotent_rerun(self, tmp_path):
        run_setup(tmp_path)
        r, sdflow = run_setup(tmp_path)
        assert r.returncode == 0
        assert (sdflow / "workflow").is_symlink()

    def test_foreign_real_dir_not_clobbered(self, tmp_path):
        home = tmp_path / "home"
        (home / ".sdflow" / "workflow").mkdir(parents=True)   # 异物：真实目录
        (home / ".sdflow" / "workflow" / "alien.txt").write_text("x", encoding="utf-8")
        r, sdflow = run_setup(tmp_path)
        assert r.returncode == 0
        assert not (sdflow / "workflow").is_symlink()          # 未接管
        assert (sdflow / "workflow" / "alien.txt").exists()    # 数据未破坏
        assert "未接管" in (r.stdout + r.stderr)               # 停手告警显形

    def test_takeover_of_stale_symlink_is_visible(self, tmp_path):
        """B2-F1：既有软链目标与新目标不同时，接管须在摘要中显形（一行提示，非交互不阻断）。"""
        home = tmp_path / "home"
        (home / ".sdflow").mkdir(parents=True)
        elsewhere = tmp_path / "elsewhere-bundle"
        elsewhere.mkdir()
        (home / ".sdflow" / "workflow").symlink_to(elsewhere)
        r, sdflow = run_setup(tmp_path)
        assert r.returncode == 0
        assert "接管：" in (r.stdout + r.stderr)
        link = sdflow / "workflow"
        assert link.is_symlink()
        assert link.resolve() == (REPO / "sdflow-init" / "assets" / "workflow").resolve()


class TestCleanupOrphansDangling:
    """0.1：尾斜杠 glob 看不见 dangling 链（POSIX 语义）——修为 find 枚举后必须能清。"""

    def test_dangling_own_link_is_cleaned(self, tmp_path):
        home = tmp_path / "home"
        skills = home / ".claude" / "skills"
        skills.mkdir(parents=True)
        # 自属 dangling：目标路径含本仓名（basename REPO）但已不存在——模拟改名后的旧链。
        # 注意：entry_name 必须不撞真实现存 skill 名（如 "spec-review"）——否则
        # install_into（pipeline 中先于 cleanup_orphans 跑）会把它当同名活 skill 无条件
        # ln -snf 自愈修复，导致 cleanup_orphans 永远等不到它变成 "gone"，
        # 测试会因无关原因红/绿都失败，测不到本任务要修的枚举逻辑。
        (skills / "spec-review-legacy").symlink_to(REPO / "spec-review-legacy-GONE")
        env = dict(os.environ, HOME=str(home), SDFLOW_HOME=str(home / ".sdflow"))
        r = subprocess.run(["bash", str(REPO / "setup.sh")], env=env, capture_output=True, text=True)
        assert r.returncode == 0
        assert not (skills / "spec-review-legacy").is_symlink()   # dangling 自属链被清
        assert "spec-review-legacy" in (r.stdout + r.stderr)       # cleaned orphans 榜上有名

    def test_foreign_dangling_link_is_kept(self, tmp_path):
        home = tmp_path / "home"
        skills = home / ".claude" / "skills"
        skills.mkdir(parents=True)
        (skills / "alien-skill").symlink_to("/nonexistent/other-tool/alien-skill")
        env = dict(os.environ, HOME=str(home), SDFLOW_HOME=str(home / ".sdflow"))
        subprocess.run(["bash", str(REPO / "setup.sh")], env=env, capture_output=True, text=True)
        assert (skills / "alien-skill").is_symlink()               # 非自属不动（红线）
