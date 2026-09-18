"""依赖预检分层覆盖：6 个真实函数测试 + 1 个隔离 HOME 的完整安装测试。

快速层仅替代 git/openspec/Python 的版本探针，yq 用 PATH 注入不同实现；
预检判定、版本比较与安装指引均运行生产代码。完整安装层检查调用接线、
报告唯一性和缺失 yq 的非致命语义。另有一个 PATH 多提供者隔离回归。
Python 候选选择仍由 setup.sh 负责，不属于快速层的覆盖范围。
"""
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from test_support.windows import bash_executable, bash_path

REPO = Path(__file__).resolve().parents[2]
SETUP = REPO / "setup.sh"
DEPENDENCIES = REPO / "hack" / "setup-dependencies.sh"


def _path_without_yq():
    """把真实 PATH 中含可解析 `yq` 的目录剔除——让"未安装"分支在任何机器上都确定性复现。"""
    raw = os.environ.get("PATH", "")
    # A user shell may expose both a shim and the actual installation. Remove
    # every provider, including extensionless Git Bash shims on Windows.
    parts = [p for p in raw.split(os.pathsep)
             if not shutil.which("yq", path=p)
             and not (Path(p) / "yq").is_file()]
    return os.pathsep.join(parts)


def _fake_yq(bin_dir, version_line):
    """造一个假 `yq`：`--version` 时打印 `version_line`，其余调用恒 exit 0。"""
    bin_dir.mkdir(exist_ok=True)
    fake = bin_dir / "yq"
    fake.write_text(f"#!/bin/sh\necho '{version_line}'\nexit 0\n", encoding="utf-8")
    fake.chmod(0o755)
    return fake


def test_missing_yq_path_removes_every_provider(tmp_path, monkeypatch):
    providers = [tmp_path / "shim", tmp_path / "installation"]
    for provider in providers:
        _fake_yq(provider, "fixture yq")
    clean = tmp_path / "clean"
    clean.mkdir()
    monkeypatch.setenv("PATH", os.pathsep.join(map(str, [*providers, clean])))
    filtered = _path_without_yq()
    assert filtered == str(clean)


def _deps_section(stdout):
    """截出 `check_dependencies()` 的输出块（"运行依赖预检：" 到下一个 "退役 hook 清理" 之间）。

    🔴 **不能对整份 stdout 做子串/正则匹配**——`tmp_path` 由 pytest 按测试函数名生成，
    像 `test_mikefarah_yq_with_sufficient_version_reports_ok` 这样的用例名本身就含 "yq"，
    会被安装/清理汇总段落里打印的临时路径（如 `.../test_mikefarah_yq_with_suffici0/...`）
    意外命中，产生假阳性/假阴性。调用点顺序固定为 `check_dependencies` 后紧跟 retire-hooks
    段，故用后者的标题行做右边界，是稳定可依赖的锚点。
    """
    start = stdout.index("运行依赖预检：")
    end = stdout.find("退役 hook 清理", start)
    if end < 0:
        end = len(stdout)
    return stdout[start:end]


def _run_full_setup(home, path=None):
    """用假 HOME（+ 可选自定义 PATH）真跑一次 setup.sh。"""
    env = dict(os.environ)
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    env["CLAUDE_CONFIG_DIR"] = str(home / ".claude")
    env.pop("SDFLOW_HOME", None)  # 否则 install_sdflow 会写到真实 ~/.sdflow
    if path is not None:
        env["PATH"] = path
    return subprocess.run(
        [bash_executable(), bash_path(SETUP)], cwd=str(REPO), env=env,
        capture_output=True, text=True, timeout=300, encoding="utf-8", errors="replace",
    )


def _run_dependencies(home, path=None):
    """只运行生产预检函数；替代慢的版本探针，不替代预检判定。"""
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    if path is not None:
        env["PATH"] = path
    command = '''
set -e
source "$1"
git() { printf 'git version 2.45.0\n'; }
openspec() { printf '1.7.0\n'; }
dependency_test_python() {
  case "$*" in
    --version) printf 'Python 3.12.0\n' ;;
    '-m pytest --version') printf 'pytest 8.0.0\n' ;;
    *) return 99 ;;
  esac
}
check_dependencies dependency_test_python
'''
    result = subprocess.run(
        [bash_executable(), "-c", command, "dependency-test", bash_path(DEPENDENCIES)],
        cwd=str(home), env=env, capture_output=True, text=True,
        timeout=30, encoding="utf-8", errors="replace",
    )
    assert not list(home.iterdir()), "预检不应创建安装目录"
    return result


@pytest.fixture
def fake_home(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    return home


def test_reports_a_status_line_for_each_of_the_five_dependencies(fake_home):
    """① python3 / git / yq / openspec / pytest 各恰好一行状态（✓/✗/·），且不中止 setup。"""
    r = _run_dependencies(fake_home)
    assert r.returncode == 0, r.stdout + r.stderr

    deps = _deps_section(r.stdout)
    # 快速层控制 python3/git 版本探针，真实报告逻辑应给出成功状态。
    assert re.search(r"✓ python3", deps), deps
    assert re.search(r"✓ git", deps), deps
    # yq 取值随 PATH 场景变化；三者都应有且仅有一行状态。
    # 用行首锚定（`^  [✓✗·] <label>\b`），避免匹配到别的行里偶然带出的同名子串。
    for label in ("yq", "openspec", "pytest"):
        matches = re.findall(rf"^  [✓✗·] {label}\b.*$", deps, re.MULTILINE)
        assert len(matches) == 1, f"{label} 状态行应恰好一条，实际 {matches}\n{deps}"


def test_python3_status_line_is_not_duplicated(fake_home):
    """② 既有 python3 检测逻辑迁入 `check_dependencies()`，不重复——全输出中只有一条 python3 状态行。

    回归的是「既有 `_py` 检测/报告散落多处」的失效模式：若某处又单独 echo 了一条
    `✓ python3` / `✗ python3`，这里会从 1 变成 ≥2。
    """
    r = _run_dependencies(fake_home)
    assert r.returncode == 0, r.stdout + r.stderr
    matches = re.findall(r"^  [✓✗] python3\b.*$", _deps_section(r.stdout), re.MULTILINE)
    assert len(matches) == 1, f"python3 状态行重复或缺失：{matches}\n{r.stdout}"


def test_missing_yq_reports_cross_and_three_platform_install_commands(fake_home):
    """③ yq 未安装 ⇒ `✗ yq` + 三平台安装命令，且 setup.sh 不中止。"""
    r = _run_dependencies(fake_home, path=_path_without_yq())
    assert r.returncode == 0, r.stdout + r.stderr

    deps = _deps_section(r.stdout)
    assert "✗ yq" in deps, deps
    assert "brew install yq" in deps
    assert "winget install --id MikeFarah.yq" in deps
    assert "snap install yq" in deps
    # 末尾汇总也要点名缺了 yq（不中止，但要让人看到）
    assert re.search(r"缺.*yq", deps), "末尾汇总没有提到 yq 缺失\n" + deps


def test_kislyuk_yq_warns_and_gives_correct_install_guidance(fake_home, tmp_path):
    """④ 已安装但是 kislyuk/yq（无 `mikefarah` 字样）⇒ 警告 + 正确版本安装指引，不中止。"""
    bin_dir = tmp_path / "fake-bin-kislyuk"
    _fake_yq(bin_dir, "yq 3.4.1")
    path = f"{bin_dir}{os.pathsep}{_path_without_yq()}"

    r = _run_dependencies(fake_home, path=path)
    assert r.returncode == 0, r.stdout + r.stderr

    deps = _deps_section(r.stdout)
    assert "⚠" in deps and "yq" in deps
    assert "kislyuk" in deps, deps
    assert "brew install yq" in deps
    assert "winget install --id MikeFarah.yq" in deps
    assert "snap install yq" in deps
    assert "✓ yq" not in deps


def test_mikefarah_yq_with_sufficient_version_reports_ok(fake_home, tmp_path):
    """⑤ mikefarah/yq 且版本 >= 4.16.0 ⇒ `✓ yq`，不告警。"""
    bin_dir = tmp_path / "fake-bin-ok"
    _fake_yq(bin_dir, "yq (https://github.com/mikefarah/yq/) version v4.44.3")
    path = f"{bin_dir}{os.pathsep}{_path_without_yq()}"

    r = _run_dependencies(fake_home, path=path)
    assert r.returncode == 0, r.stdout + r.stderr

    deps = _deps_section(r.stdout)
    assert "✓ yq" in deps, deps
    assert "版本过低" not in deps
    assert not re.search(r"⚠[^\n]*yq", deps), deps


def test_mikefarah_yq_below_min_version_warns_upgrade(fake_home, tmp_path):
    """⑥ mikefarah/yq 但版本 < 4.16.0（`--front-matter` 支持下限，spec R1）⇒ 版本过低警告 + 升级指引。"""
    bin_dir = tmp_path / "fake-bin-old"
    _fake_yq(bin_dir, "yq (https://github.com/mikefarah/yq/) version v4.9.2")
    path = f"{bin_dir}{os.pathsep}{_path_without_yq()}"

    r = _run_dependencies(fake_home, path=path)
    assert r.returncode == 0, r.stdout + r.stderr

    deps = _deps_section(r.stdout)
    assert "版本过低" in deps, deps
    assert "4.16" in deps
    assert "✓ yq" not in deps


def test_full_setup_reports_missing_yq_once_and_continues(fake_home):
    """缺失 yq 仍完成真实安装；预检接线、非致命性、重复报告一起守住。"""
    r = _run_full_setup(fake_home, path=_path_without_yq())
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.count("运行依赖预检：") == 1
    deps = _deps_section(r.stdout)
    assert "✗ yq" in deps
    assert "winget install --id MikeFarah.yq" in deps
    assert len(re.findall(r"^  [✓✗] python3\b.*$", r.stdout, re.MULTILINE)) == 1
    assert "ready →" in r.stdout
    assert (fake_home / ".codex" / "skills" / "sdflow-init" / "SKILL.md").is_file()
