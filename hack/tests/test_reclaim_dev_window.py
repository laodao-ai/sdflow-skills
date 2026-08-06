"""`setup.sh` 的**开发窗口可还原性**契约（所有权守卫的自属判据）。

【这测的是什么】"开发窗口"= 在**开发 checkout** 跑一次 `setup.sh`，把 `~/.claude/skills/*`
等全局软链翻向开发树（CLAUDE.md「开发期测试三层」的第 3 层，时间盒操作）。
还原 = 回**运行 checkout** 再跑一次 `setup.sh` 把它们翻回去。

【它为什么必须有机械门】还原路径此前是**断的**，且断得很隐蔽——
自属判据只按**目录名**认（`$REPO_NAME` + 字面 `sdflow-skills` 兜底），而
`REPO_NAME="$(basename "$REPO_DIR")"` ⇒ 开发 checkout 叫什么名字完全由人定。
于是产生**不对称**：

  开发树跑 setup（REPO_NAME=04-sdflow-skills）→ 判据认自己 ∪ 字面 sdflow-skills ⇒ 抢得走
  运行树跑 setup（REPO_NAME=sdflow-skills）  → 只认 sdflow-skills              ⇒ 抢不回

结果是「窗口开得出、关不上」，而 `setup.sh` 只会打一行
`⚠ … 非自属软链（→ …），未覆盖` 进 skipped 汇总——**exit code 仍是 0**。
∴ 靠"跑一遍看输出"发现不了，必须机械守。

【怎么跑】`tmp_path` 造**两个假 checkout**（名字刻意不同：`sdflow-skills` 与
`04-sdflow-skills`，复现真实机器的形状）+ 假 HOME，真跑 `bash setup.sh`。
🔴 **MUST NOT 污染真实 `~/.claude/skills/`** —— 每个用例都断言真实目录快照前后不变。

【本文件照不到的面（诚实边界）】
- **Windows 分支**（copy + marker）：`IS_WINDOWS` 由 `uname -s` 决定、无覆盖入口 ⇒ 本机
  （Darwin）测不到。如实登记，MUST NOT 假装测过。
- 本文件只断言**软链指向**，不断言被链目录的内容（那是 `install_into` 的拷贝语义，
  由其它测试与 symlink 本身保证）。
"""
import os
import subprocess
from pathlib import Path

import pytest

from test_support.windows import bash_executable, bash_path

if os.name == "nt":
    pytest.skip(
        "开发窗口还原走 Unix 绝对软链；Windows 是 copy+marker 分支，本文件不覆盖",
        allow_module_level=True,
    )

REPO = Path(__file__).resolve().parents[2]
REAL_SKILLS = Path(os.path.expanduser("~")) / ".claude" / "skills"

# 造假 checkout 时最少要有的东西：一个可安装 skill + 让 is_our_checkout_path 认得出的两个特征文件。
_FINGERPRINT_REL = "sdflow-init/assets/hack/skill-principles.md"
_PROBE_SKILL = "sdflow-ship"


def _real_skills_snapshot():
    """真实 skills 目录的 (名字 → 软链指向/`<dir>`) 快照。目录不存在 → None。"""
    if not REAL_SKILLS.is_dir():
        return None
    out = {}
    for p in sorted(REAL_SKILLS.iterdir()):
        out[p.name] = os.readlink(p) if p.is_symlink() else "<dir>"
    return out


def _make_checkout(root: Path, *, fingerprint: bool = True) -> Path:
    """造一个最小 sdflow-skills checkout：setup.sh（真源码拷贝）+ 特征文件 + 一个 skill。"""
    root.mkdir(parents=True, exist_ok=True)
    (root / "setup.sh").write_bytes((REPO / "setup.sh").read_bytes())
    if fingerprint:
        fp = root / _FINGERPRINT_REL
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text("# 假特征文件（只判存在性）\n", encoding="utf-8")
    skill = root / _PROBE_SKILL
    skill.mkdir(parents=True, exist_ok=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: {_PROBE_SKILL}\ndescription: fixture\n---\n", encoding="utf-8"
    )
    return root


def _run_setup(checkout: Path, home: Path):
    env = dict(os.environ)
    env["HOME"] = str(home)
    env.pop("SDFLOW_HOME", None)  # 否则 install_sdflow 会写真实 ~/.sdflow
    # encoding/errors 显式声明：本仓 `test_subprocess_encoding_contract` 的硬契约——
    # text 模式不指定 utf-8 会在 Windows runner 上按 locale 解码而崩（实证坑）。
    return subprocess.run(
        [bash_executable(), bash_path(checkout / "setup.sh")],
        cwd=str(checkout),
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
        encoding="utf-8",
        errors="replace",
    )


def _link_of(home: Path, skill: str):
    p = home / ".claude" / "skills" / skill
    return os.readlink(p) if p.is_symlink() else None


@pytest.fixture()
def guard_real_skills():
    """真实 `~/.claude/skills/` 未被本次测试动过——写死 $HOME 之外的绝对路径会在此当场暴露。"""
    before = _real_skills_snapshot()
    yield
    assert _real_skills_snapshot() == before, "测试污染了真实 ~/.claude/skills/"


def test_runtime_checkout_reclaims_window_opened_by_dev_checkout(tmp_path, guard_real_skills):
    """核心回归：开发 checkout 开出的窗口，运行 checkout 必须能收回。

    两个 checkout 的**目录名刻意不同**（`04-` 前缀），复现真实机器的形状——
    路径名判据在此必然漏，只有内容指纹判据能接住。
    """
    home = tmp_path / "home"
    runtime = _make_checkout(tmp_path / "sdflow-skills")
    dev = _make_checkout(tmp_path / "04-sdflow-skills")

    # ① 运行 checkout 铺设（常态）
    assert _run_setup(runtime, home).returncode == 0
    assert _link_of(home, _PROBE_SKILL) == str(runtime / _PROBE_SKILL)

    # ② 开发 checkout 开窗（这一步本来就能成——不对称的"能开"那一半）
    assert _run_setup(dev, home).returncode == 0
    assert _link_of(home, _PROBE_SKILL) == str(dev / _PROBE_SKILL), "开窗失败，前提不成立"

    # ③ 运行 checkout 关窗 —— 修复前这里会停在 dev 上（skipped 里一行 ⚠，exit 仍 0）
    r = _run_setup(runtime, home)
    assert r.returncode == 0
    assert _link_of(home, _PROBE_SKILL) == str(runtime / _PROBE_SKILL), (
        "开发窗口未被收回——自属判据又退回成只认目录名了？\n"
        f"stdout:\n{r.stdout}"
    )
    assert "非自属软链" not in r.stdout, f"不该判非自属：\n{r.stdout}"


def test_foreign_symlink_is_still_not_taken_over(tmp_path, guard_real_skills):
    """守卫没被放宽：**不是** sdflow-skills checkout 的同名软链仍拒绝接管。

    这条与上一条是一对——上一条防"守卫过严导致关不上窗"，本条防"修法把守卫拆了"。
    """
    home = tmp_path / "home"
    runtime = _make_checkout(tmp_path / "sdflow-skills")
    # 第三方：有 SKILL.md，但**没有** checkout 特征文件（不是一份 sdflow-skills）
    foreign = _make_checkout(tmp_path / "someone-elses-tools", fingerprint=False)

    (home / ".claude" / "skills").mkdir(parents=True, exist_ok=True)
    os.symlink(foreign / _PROBE_SKILL, home / ".claude" / "skills" / _PROBE_SKILL)

    r = _run_setup(runtime, home)
    assert r.returncode == 0
    assert _link_of(home, _PROBE_SKILL) == str(foreign / _PROBE_SKILL), (
        f"第三方软链被接管了——守卫被拆松：\n{r.stdout}"
    )
    assert "非自属软链" in r.stdout, f"应报非自属并跳过：\n{r.stdout}"


def test_dangling_symlink_into_named_checkout_still_matches_path_predicate(tmp_path, guard_real_skills):
    """悬空链（源已删）指纹读不到 ⇒ 必须由**路径名判据**兜底，旧行为零回退。

    这是"内容指纹与路径判据是 OR、不是替代"的机械证据。
    """
    home = tmp_path / "home"
    runtime = _make_checkout(tmp_path / "sdflow-skills")

    (home / ".claude" / "skills").mkdir(parents=True, exist_ok=True)
    # 指向一个**名字命中路径判据**但根本不存在的 checkout
    dangling = tmp_path / "gone" / "sdflow-skills" / _PROBE_SKILL
    os.symlink(dangling, home / ".claude" / "skills" / _PROBE_SKILL)
    assert not dangling.exists(), "前提：目标确实不存在"

    r = _run_setup(runtime, home)
    assert r.returncode == 0
    assert _link_of(home, _PROBE_SKILL) == str(runtime / _PROBE_SKILL), (
        f"悬空自属链未被接管——路径判据兜底断了：\n{r.stdout}"
    )
