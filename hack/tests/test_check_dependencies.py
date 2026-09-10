"""`setup.sh check_dependencies()` 的依赖预检契约（shared-yaml-subset-parser · Task 1 · R1/R2）。

统一检测并报告全部运行依赖：python3 >= 3.7 / git / yq(mikefarah, >= 4.16.0) / openspec（可选）/
pytest（开发可选）。调用点在 `install_sdflow` 之后、门禁检查之前；不中止 setup.sh
——降级汇报，与既有 `skipped[]` 范式一致（同 `install_agents` 的既定取向）。

【怎么跑】沿用 `test_install_agents.py` 的既定模式：`tmp_path` 当假 `HOME` 真跑 `bash setup.sh`。
yq 分支（mikefarah / kislyuk / 版本过低 / 未安装）通过在 `PATH` 前置一个假 `yq` 可执行脚本来
确定性复现——同 `test_sdflow_spec_agents.py::_scan_with_broken_grep` 注入假 `grep` 的手法。

【本文件照不到的面（诚实边界）】
- 不断言 openspec / pytest 分支的 ✓/· 具体取值——那取决于本机是否装了这两样，
  本文件只断言「有且仅有一行状态」，不锁死本机环境的偶然状态。
- 不测试 `_py`（python3 候选选择本身，[T48]）——那段功能性逻辑早于 `install_sdflow` 运行，
  是脚本自身的执行前提（`install_sdflow` 消费 `$_py`），不能挪到 `check_dependencies()` 之后；
  本文件只守「报告不重复」，不守选择算法本身。
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


def _path_without_yq():
    """把真实 PATH 中含可解析 `yq` 的目录剔除——让"未安装"分支在任何机器上都确定性复现。"""
    real_yq = shutil.which("yq")
    raw = os.environ.get("PATH", "")
    if not real_yq:
        return raw
    yq_dir = os.path.normcase(os.path.normpath(os.path.dirname(real_yq)))
    parts = [p for p in raw.split(os.pathsep)
             if os.path.normcase(os.path.normpath(p)) != yq_dir]
    return os.pathsep.join(parts)


def _fake_yq(bin_dir, version_line):
    """造一个假 `yq`：`--version` 时打印 `version_line`，其余调用恒 exit 0。"""
    bin_dir.mkdir(exist_ok=True)
    fake = bin_dir / "yq"
    fake.write_text(f"#!/bin/sh\necho '{version_line}'\nexit 0\n", encoding="utf-8")
    fake.chmod(0o755)
    return fake


def _deps_section(stdout):
    """截出 `check_dependencies()` 的输出块（"运行依赖预检：" 到下一个 "退役 hook 清理" 之间）。

    🔴 **不能对整份 stdout 做子串/正则匹配**——`tmp_path` 由 pytest 按测试函数名生成，
    像 `test_mikefarah_yq_with_sufficient_version_reports_ok` 这样的用例名本身就含 "yq"，
    会被安装/清理汇总段落里打印的临时路径（如 `.../test_mikefarah_yq_with_suffici0/...`）
    意外命中，产生假阳性/假阴性。调用点顺序固定为 `check_dependencies` 后紧跟 retire-hooks
    段，故用后者的标题行做右边界，是稳定可依赖的锚点。
    """
    start = stdout.index("运行依赖预检：")
    end = stdout.index("退役 hook 清理", start)
    return stdout[start:end]


def _run_setup(home, path=None):
    """用假 HOME（+ 可选自定义 PATH）真跑一次 setup.sh。"""
    env = dict(os.environ)
    env["HOME"] = str(home)
    env.pop("SDFLOW_HOME", None)  # 否则 install_sdflow 会写到真实 ~/.sdflow
    if path is not None:
        env["PATH"] = path
    return subprocess.run(
        [bash_executable(), bash_path(SETUP)], cwd=str(REPO), env=env,
        capture_output=True, text=True, timeout=300, encoding="utf-8", errors="replace",
    )


@pytest.fixture
def fake_home(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    return home


def test_reports_a_status_line_for_each_of_the_five_dependencies(fake_home):
    """① python3 / git / yq / openspec / pytest 各恰好一行状态（✓/✗/·），且不中止 setup。"""
    r = _run_setup(fake_home)
    assert r.returncode == 0, r.stdout + r.stderr

    deps = _deps_section(r.stdout)
    # python3 与 git 是本仓测试自身运行的前提，本机必然存在 ⇒ 可断言为 ✓。
    assert re.search(r"✓ python3", deps), deps
    assert re.search(r"✓ git", deps), deps
    # yq / openspec / pytest 的具体取值取决于本机环境，只断言「行存在且恰好一行」——
    # 用行首锚定（`^  [✓✗·] <label>\b`），避免匹配到别的行里偶然带出的同名子串。
    for label in ("yq", "openspec", "pytest"):
        matches = re.findall(rf"^  [✓✗·] {label}\b.*$", deps, re.MULTILINE)
        assert len(matches) == 1, f"{label} 状态行应恰好一条，实际 {matches}\n{deps}"


def test_python3_status_line_is_not_duplicated(fake_home):
    """② 既有 python3 检测逻辑迁入 `check_dependencies()`，不重复——全输出中只有一条 python3 状态行。

    回归的是「既有 `_py` 检测/报告散落多处」的失效模式：若某处又单独 echo 了一条
    `✓ python3` / `✗ python3`，这里会从 1 变成 ≥2。
    """
    r = _run_setup(fake_home)
    assert r.returncode == 0, r.stdout + r.stderr
    matches = re.findall(r"^  [✓✗] python3\b.*$", _deps_section(r.stdout), re.MULTILINE)
    assert len(matches) == 1, f"python3 状态行重复或缺失：{matches}\n{r.stdout}"


def test_missing_yq_reports_cross_and_three_platform_install_commands(fake_home):
    """③ yq 未安装 ⇒ `✗ yq` + 三平台安装命令，且 setup.sh 不中止。"""
    r = _run_setup(fake_home, path=_path_without_yq())
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

    r = _run_setup(fake_home, path=path)
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

    r = _run_setup(fake_home, path=path)
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

    r = _run_setup(fake_home, path=path)
    assert r.returncode == 0, r.stdout + r.stderr

    deps = _deps_section(r.stdout)
    assert "版本过低" in deps, deps
    assert "4.16" in deps
    assert "✓ yq" not in deps
