"""`setup.sh install_agents()` 的铺设契约（add-sdflow-spec · SA-07 / tasks 6.8）。

【全仓首个 setup.sh 测试】
在此之前 `setup.sh` 的行为**一行机械覆盖都没有**——所有权守卫、孤儿清理、幂等，
全靠人手工跑一遍看输出。而 `~/.claude/agents/` 是**全局命名空间**：守卫写错的后果是
「把别的工具的同名定义覆盖掉」= 数据丢失。∴ 这一片必须有机械门。

【怎么跑】`tmp_path` 当**假 HOME** 真跑 `bash setup.sh`。
🔴 **MUST NOT 污染真实 `~/.claude/agents/`** —— 每个用例都断言真实目录的快照前后不变
（见 `_real_agents_snapshot`）。这不是装饰：`install_agents()` 里任何一处写死 `$HOME` 之外的
绝对路径，都会在这里当场暴露。

【本文件照不到的面（诚实边界）】
- **Windows 分支**：`IS_WINDOWS` 由 `uname -s` 决定，无环境变量覆盖入口 ⇒ 本机（Darwin）
  测不到。它只有一条 `skipped+=` + `return 0`；如实登记为无机械覆盖，MUST NOT 假装测过。
  （为了测它去给生产代码开一个覆盖开关 = 为测试放宽生产逻辑，不做。）
- **真实 `~/.claude/agents/` 里的实际内容**：本文件只断言「没被本次测试动过」，
  不断言它此刻是什么（那取决于人上次在哪个 checkout 跑的 setup）。
"""
import os
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SETUP = REPO / "setup.sh"
SRC_DIR = REPO / "sdflow-spec" / "agents"
REAL_AGENTS = Path(os.path.expanduser("~")) / ".claude" / "agents"

# 期望铺出的定义 = 源目录里的**全部** `.md`（不写死三个名字：新增一个定义就该自动纳入，
# 与 sync_principles 的 glob 投放面同口径）。
def _expected_names():
    return sorted(p.name for p in SRC_DIR.glob("*.md"))


def _real_agents_snapshot():
    """真实 agents 目录的 (名字 → 软链指向/`<file>`) 快照。目录不存在 → None。"""
    if not REAL_AGENTS.is_dir():
        return None
    out = {}
    for p in sorted(REAL_AGENTS.iterdir()):
        out[p.name] = os.readlink(p) if p.is_symlink() else "<file>"
    return out


def _run_setup(home):
    """用假 HOME 跑一次 setup.sh，返回 CompletedProcess。"""
    env = dict(os.environ)
    env["HOME"] = str(home)
    env.pop("SDFLOW_HOME", None)          # 否则 install_sdflow 会写到真实 ~/.sdflow
    return subprocess.run(["bash", str(SETUP)], cwd=str(REPO), env=env,
                          capture_output=True, text=True, timeout=300)


@pytest.fixture
def fake_home(tmp_path):
    """跑 setup.sh 前后各拍一次真实 agents 目录 —— 被动过就红。"""
    before = _real_agents_snapshot()
    home = tmp_path / "home"
    home.mkdir()
    yield home
    assert _real_agents_snapshot() == before, \
        "真实 ~/.claude/agents/ 被测试改动了 —— install_agents() 里有不走 $HOME 的路径"


def _agents_dir(home):
    return home / ".claude" / "agents"


def test_three_defs_are_symlinked_into_the_fake_home(fake_home):
    """① 每个定义各铺出一条软链，且**指向本仓源文件**（不是拷贝、不是别处）。"""
    r = _run_setup(fake_home)
    assert r.returncode == 0, r.stdout + r.stderr

    dest = _agents_dir(fake_home)
    names = _expected_names()
    assert len(names) >= 3, f"源目录里只有 {names} —— 三个 agent 定义不全"
    for name in names:
        link = dest / name
        assert link.is_symlink(), f"{name} 不是软链（成了拷贝？）"
        assert os.readlink(link) == str(SRC_DIR / name)
        assert link.is_file(), f"{name} 软链悬空"
        assert f"agents/{name} @ {dest}" in r.stdout


def test_a_foreign_file_is_never_clobbered_and_lands_in_skipped(fake_home):
    """② 预置**非本仓**同名条目 ⇒ 不覆盖 + 进 `skipped[]`。

    两种形态各测一次：真实文件 / 指向仓外的**悬空**软链。
    第二种形态专守存在性判据：`-e` 对悬空软链为 false ⇒ 判据必须是 `-e || -L`，
    只用 `-e` 会把别人的（碰巧悬空的）软链直接 `ln -snf` 覆盖掉 = 静默数据丢失。
    """
    dest = _agents_dir(fake_home)
    dest.mkdir(parents=True)
    names = _expected_names()
    victim_file, victim_link = names[0], names[1]

    (dest / victim_file).write_text("third party content", encoding="utf-8")
    os.symlink("/nonexistent/foreign-agent.md", dest / victim_link)

    r = _run_setup(fake_home)
    assert r.returncode == 0, r.stdout + r.stderr

    assert (dest / victim_file).read_text(encoding="utf-8") == "third party content"
    assert not (dest / victim_file).is_symlink()
    assert (dest / victim_link).is_symlink()
    assert os.readlink(dest / victim_link) == "/nonexistent/foreign-agent.md"

    assert "已存在真实文件，非本仓软链，未接管" in r.stdout
    assert "（非本仓），未接管" in r.stdout
    for victim in (victim_file, victim_link):
        assert f"agents/{victim} @ {dest}" in r.stdout
        # 被 skip 的项 MUST NOT 同时出现在 installed 段（那说明既报跳过又真覆盖了）
        assert f"✓ agents/{victim} @ {dest}" not in r.stdout


def test_dangling_link_of_a_deleted_source_is_cleaned(fake_home):
    """③ 源已删 ⇒ 悬空软链被清；**有效链保留**（别把还活着的一起扫了）。"""
    dest = _agents_dir(fake_home)
    dest.mkdir(parents=True)
    gone = dest / "sdflow-gone-agent.md"
    os.symlink(str(SRC_DIR / "sdflow-gone-agent.md"), gone)      # 源不存在 → 悬空
    foreign_dangling = dest / "someone-elses.md"
    os.symlink("/nonexistent/elsewhere.md", foreign_dangling)     # 不是本仓的，别碰

    r = _run_setup(fake_home)
    assert r.returncode == 0, r.stdout + r.stderr

    assert not gone.is_symlink() and not gone.exists(), "悬空孤儿链没被清"
    assert f"agents/{gone.name} @ {dest}" in r.stdout
    assert foreign_dangling.is_symlink(), "清了别人的悬空链 —— 守卫太宽"
    for name in _expected_names():
        assert (dest / name).is_file(), f"{name} 被孤儿清理误伤"


def test_rerun_is_idempotent(fake_home):
    """④ 重跑幂等：链指向不变、不产生 skip、不产生 cleaned。"""
    first = _run_setup(fake_home)
    assert first.returncode == 0, first.stdout + first.stderr
    dest = _agents_dir(fake_home)
    before = {n: os.readlink(dest / n) for n in _expected_names()}

    second = _run_setup(fake_home)
    assert second.returncode == 0, second.stdout + second.stderr

    after = {n: os.readlink(dest / n) for n in _expected_names()}
    assert after == before
    assert "agents/" not in _skipped_section(second.stdout), "幂等重跑不该有 agents 被跳过"
    assert "agents/" not in _cleaned_section(second.stdout), "幂等重跑不该清掉自己刚铺的链"


def _section(stdout, header):
    """取 setup.sh 汇总里某一段（`skipped (N):` / `cleaned orphans (N):`）的正文。"""
    lines = stdout.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith(header):
            body = []
            for nxt in lines[i + 1:]:
                if not nxt.strip() or not nxt.startswith("    "):
                    break
                body.append(nxt)
            return "\n".join(body)
    return ""


def _skipped_section(stdout):
    return _section(stdout, "skipped (")


def _cleaned_section(stdout):
    return _section(stdout, "cleaned orphans (")
