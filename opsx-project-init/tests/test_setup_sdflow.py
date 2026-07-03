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
        assert link.resolve() == (REPO / "opsx-project-init" / "assets" / "workflow").resolve()
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
        assert link.resolve() == (REPO / "opsx-project-init" / "assets" / "workflow").resolve()
