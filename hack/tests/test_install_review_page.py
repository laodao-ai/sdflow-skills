"""setup.sh 把评审页资产目录装进 ~/.sdflow/hack/review-page/（RVP-08，tasks 3.5、3.7）。

假 HOME 真跑 bash setup.sh（模式同 test_install_agents.py）。覆盖四种情形：
  - 正常拷贝，装后能用安装位置的脚本生成页面
  - 重装时清掉旧版残留文件
  - 旧目录清不掉（子目录只读）⇒ 进 skipped[]，不中止，其余照装
  - 源 review-page/ 目录缺失 ⇒ 进 skipped[]，不中止，其余照装
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

from test_support.windows import bash_executable, bash_path

if os.name == "nt":
    pytest.skip("assertions target the Unix install path", allow_module_level=True)

REPO = Path(__file__).resolve().parents[2]
SETUP = REPO / "setup.sh"
SRC = REPO / "sdflow-init" / "assets" / "hack" / "review-page"
REAL_SDFLOW = Path(os.path.expanduser("~")) / ".sdflow" / "hack" / "review-page"


def _snapshot():
    if not REAL_SDFLOW.is_dir():
        return None
    return sorted((p.name, p.stat().st_mtime_ns) for p in REAL_SDFLOW.iterdir())


@pytest.fixture
def fake_home(tmp_path):
    before = _snapshot()
    home = tmp_path / "home"
    home.mkdir()
    yield home
    assert _snapshot() == before, "真实 ~/.sdflow/hack/review-page 被测试改动了"


@pytest.fixture(scope="module")
def installed_once(tmp_path_factory):
    """整个模块只为「装完后的只读断言」跑一次 setup.sh；会改动安装目录的用例仍用 fake_home 自跑。"""
    before = _snapshot()
    home = tmp_path_factory.mktemp("installed-once-home")
    r = _run_setup(home)
    yield home, r
    assert _snapshot() == before, "真实 ~/.sdflow/hack/review-page 被测试改动了"


def _run_setup(home):
    env = dict(os.environ)
    env["HOME"] = str(home)
    env.pop("SDFLOW_HOME", None)
    return subprocess.run([bash_executable(), bash_path(SETUP)], cwd=str(REPO), env=env,
                          capture_output=True, text=True, timeout=300, encoding="utf-8", errors="replace")


def _installed(home):
    return home / ".sdflow" / "hack" / "review-page"


def test_assets_are_copied_and_page_generates_from_install_location(installed_once, tmp_path):
    fake_home, r = installed_once
    assert r.returncode == 0, r.stdout + r.stderr
    dest = _installed(fake_home)
    for name in ("template.html", "marked.umd.js", "LICENSE.marked"):
        assert (dest / name).read_bytes() == (SRC / name).read_bytes(), name
    assert not dest.is_symlink()

    script = fake_home / ".sdflow" / "hack" / "render-review-page.py"
    assert script.is_file()
    md = tmp_path / "a.md"
    md.write_text("# 安装后可生成\n", encoding="utf-8")
    out = tmp_path / "out" / "p.html"
    g = subprocess.run([sys.executable, "-I", str(script), "--out", str(out), "--title", "t",
                        "--doc", f"甲={md}", "--no-open"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    assert g.returncode == 0, g.stderr
    page = out.read_text(encoding="utf-8")
    assert "marked v18.1.1" in page  # 页面含内联渲染库


def test_reinstall_removes_stale_files(fake_home):
    assert _run_setup(fake_home).returncode == 0
    stale = _installed(fake_home) / "stale-from-old-version.js"
    stale.write_text("old", encoding="utf-8")
    assert _run_setup(fake_home).returncode == 0
    assert not stale.exists()
    assert (_installed(fake_home) / "template.html").is_file()


def test_copy_failure_goes_to_skipped_without_aborting_or_breaking_manifest(fake_home):
    """旧 review-page 目录里有删不掉的文件（子目录只读）⇒ 进 skipped[]，其余照装，manifest 照写。"""
    if os.geteuid() == 0:
        pytest.skip("root 无视目录权限")
    stuck = _installed(fake_home) / "sub"
    stuck.mkdir(parents=True)
    (stuck / "f").write_text("x", encoding="utf-8")
    stuck.chmod(0o500)  # 里面的文件删不掉 ⇒ 旧目录清不掉
    try:
        r = _run_setup(fake_home)
    finally:
        stuck.chmod(0o700)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "review-page" in r.stdout and "skipped" in r.stdout
    assert "capability-manifest 跳过" not in r.stdout
    assert (fake_home / ".sdflow" / "hack" / "capability-manifest.json").is_file()
    assert (fake_home / ".sdflow" / "hack" / "render-review-page.py").is_file()


def _farm_without_review_page(tmp_path):
    """REPO_DIR 替身：顶层与 sdflow-init/assets/hack 逐层软链回真仓，只有 review-page/ 不存在。

    REPO_DIR 由 dirname $0 决定，要让源目录缺失又不动真仓，只能造替身（模式同 test_install_agents.py）。
    """
    farm = tmp_path / "farm-repo"
    farm.mkdir()
    hack_rel = Path("sdflow-init") / "assets" / "hack"
    # 从 sdflow-init 到 hack 的每一层目录：真目录，内容逐项软链回真仓，
    # 唯独跳过「下一层目录」（由下一轮重建）与最后一层里的 review-page/。
    levels = [Path("sdflow-init"), Path("sdflow-init") / "assets", hack_rel]
    for entry in REPO.iterdir():
        if entry.name != "sdflow-init":
            os.symlink(str(entry), str(farm / entry.name))
    for i, level in enumerate(levels):
        real, fake = REPO / level, farm / level
        fake.mkdir()
        is_last = i == len(levels) - 1
        skip = {"review-page"} if is_last else {levels[i + 1].name}
        for e in real.iterdir():
            if e.name not in skip:
                os.symlink(str(e), str(fake / e.name))
    return farm


def test_missing_source_dir_goes_to_skipped_without_aborting(fake_home, tmp_path):
    """源 review-page/ 缺失 ⇒ 汇总里有一行 skipped，setup 不中止，其余 hack 脚本照装。"""
    farm = _farm_without_review_page(tmp_path)
    assert not (farm / "sdflow-init" / "assets" / "hack" / "review-page").exists()
    env = dict(os.environ)
    env["HOME"] = str(fake_home)
    env.pop("SDFLOW_HOME", None)
    r = subprocess.run([bash_executable(), bash_path(farm / "setup.sh")], cwd=str(farm), env=env,
                       capture_output=True, text=True, timeout=300, encoding="utf-8", errors="replace")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "hack/review-page @" in r.stdout and "源目录缺失" in r.stdout
    assert not _installed(fake_home).exists()
    assert (fake_home / ".sdflow" / "hack" / "render-review-page.py").is_file()
    assert (fake_home / ".sdflow" / "hack" / "capability-manifest.json").is_file()


def test_check_notes_path_script_is_installed(installed_once):
    """tasks 5.0：setup 按 *.py 拷贝，check-notes-path.py 随之装到 ~/.sdflow/hack/（假 HOME 替代真实 HOME）。"""
    fake_home, r = installed_once
    assert r.returncode == 0, r.stdout + r.stderr
    dest = fake_home / ".sdflow" / "hack" / "check-notes-path.py"
    src = REPO / "sdflow-init" / "assets" / "hack" / "check-notes-path.py"
    assert dest.read_bytes() == src.read_bytes()
