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

from test_support.windows import bash_executable, bash_path

if os.name == "nt":
    pytest.skip(
        "global agent installation intentionally does not create symlinks on Windows",
        allow_module_level=True,
    )

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
    return subprocess.run([bash_executable(), bash_path(SETUP)], cwd=str(REPO), env=env,
                          capture_output=True, text=True, timeout=300, encoding="utf-8", errors="replace")


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


def test_a_link_from_another_checkout_of_this_repo_is_taken_over(fake_home, tmp_path):
    """⭐ 跨 checkout：预置指向**另一个 checkout** 的自属软链 ⇒ MUST 被接管，不是 skip。

    🔴 **为什么这条是必须的**：`CLAUDE.md` 的 dev/runtime 纪律明写「测完/合并后在**运行
    checkout** 重跑 setup **还原**」「**回滚** = 运行 checkout `git checkout <良好 commit>` +
    重跑 setup.sh」。守卫若只认**当前** checkout 的路径前缀，这两条明文承诺对 agent 定义
    **静默失效**：从 B checkout 跑 setup，指向 A 的链既不被接管、也不进孤儿清理（清理判据更窄），
    名册**裂脑**（一条来自 A、其余来自 B）——而两个 checkout 目录名不同
    （`~/.skills/sdflow-skills` vs `04-sdflow-skills`），连 `cleanup_orphans` 的
    `*/$REPO_NAME/*` 子串 idiom 也匹配不上。∴ 这里的假 checkout **故意取一个不同的目录名**。

    ⚠️ 判据 MUST NOT 放宽成「是软链就覆盖」（`CLAUDE.md`：绝不覆盖非本仓库拥有的同名目录）
    —— 上一条用例（外来软链必须原样保留）守的正是那条边界，两条要一起绿。
    """
    dest = _agents_dir(fake_home)
    dest.mkdir(parents=True)
    other = tmp_path / "sdflow-skills-runtime" / "sdflow-spec" / "agents"
    other.mkdir(parents=True)

    names = _expected_names()
    victim = names[0]
    (other / victim).write_text("另一个 checkout 的同名定义\n", encoding="utf-8")
    os.symlink(str(other / victim), dest / victim)

    r = _run_setup(fake_home)
    assert r.returncode == 0, r.stdout + r.stderr

    assert os.readlink(dest / victim) == str(SRC_DIR / victim), \
        "指向另一 checkout 的自属链没被接管 —— dev/runtime 还原路径对 agent 定义静默失效"
    assert f"✓ agents/{victim} @ {dest}" in r.stdout
    # 名册不许裂脑：全部条目都指向**同一个** checkout
    for name in names:
        assert os.readlink(dest / name) == str(SRC_DIR / name), f"{name} 名册裂脑"


def test_dangling_link_of_a_deleted_source_is_cleaned(fake_home, tmp_path):
    """③ 源已删 ⇒ 悬空软链被清；**有效链保留**（别把还活着的一起扫了）。

    第三格（**跨 checkout 的悬空链**）守清理判据不比接管判据**窄**：判据若只认当前 checkout，
    「指向另一 checkout、且源已删」的链就永远留着 —— 既不被接管、也不被清理，
    正是名册裂脑的另一半。

    🔴 **两条判据在「名字」这一维上必然不同宽，这是设计**：接管只对 `$src_dir/*.md` 里现存的名字
    （循环源就是它），清理必须覆盖**已从本仓删掉的名字**——那正是「孤儿」的定义。
    第一格的 `sdflow-gone-agent.md` 就不在 `$src_dir` 里；给清理加上「名字 ∈ `$src_dir`」的
    限定，这一格当场红（实测），即孤儿清理的主用途被击穿。
    第四、五格把这条不同宽的**代价与边界**一起钉死（见各自的注释）。
    """
    dest = _agents_dir(fake_home)
    dest.mkdir(parents=True)
    gone = dest / "sdflow-gone-agent.md"
    os.symlink(str(SRC_DIR / "sdflow-gone-agent.md"), gone)      # 源不存在 → 悬空
    other_gone = dest / "sdflow-gone-from-other-checkout.md"      # 另一 checkout，源也不存在
    os.symlink(str(tmp_path / "sdflow-skills-runtime" / "sdflow-spec" / "agents"
                   / "sdflow-gone-from-other-checkout.md"), other_gone)
    foreign_dangling = dest / "someone-elses.md"
    os.symlink("/nonexistent/elsewhere.md", foreign_dangling)     # 不是本仓的路径形状，别碰
    # 第五格 = **承认的代价**：路径形状是本仓专有布局、但名字从不属于本仓的**悬空**链，
    # 会被一并清掉。钉在这里是为了让这条边界**可见且是有意的** —— 想「收严」的人会先看到
    # 第一格（收严即红）。只删悬空链 ⇒ 目标已不存在 ⇒ 零数据丢失。
    shaped_dangling = dest / "their-own-agent.md"
    os.symlink(str(tmp_path / "someone-else-repo" / "sdflow-spec" / "agents"
                   / "their-own-agent.md"), shaped_dangling)
    # 第六格 = 边界的另一侧：同样的路径形状但链**有效** ⇒ MUST 原样保留（不是悬空就不碰）。
    live_foreign_dir = tmp_path / "someone-else-repo" / "sdflow-spec" / "agents"
    live_foreign_dir.mkdir(parents=True)
    (live_foreign_dir / "their-live-agent.md").write_text("third party\n", encoding="utf-8")
    live_foreign = dest / "their-live-agent.md"
    os.symlink(str(live_foreign_dir / "their-live-agent.md"), live_foreign)

    r = _run_setup(fake_home)
    assert r.returncode == 0, r.stdout + r.stderr

    assert not gone.is_symlink() and not gone.exists(), "悬空孤儿链没被清"
    assert f"agents/{gone.name} @ {dest}" in r.stdout
    assert not other_gone.is_symlink() and not other_gone.exists(), \
        "跨 checkout 的悬空孤儿链没被清 —— 孤儿判据比接管判据窄"
    assert foreign_dangling.is_symlink(), "清了别人的悬空链 —— 守卫太宽"
    assert not shaped_dangling.exists() and not shaped_dangling.is_symlink(), \
        "承认的代价变了：本仓路径形状的悬空链不再被清 —— 要么代价被改小了，要么孤儿清理失灵"
    assert live_foreign.is_symlink() and live_foreign.is_file(), \
        "清了一条**有效**的第三方链 —— 那是真实数据丢失，MUST NOT"
    for name in _expected_names():
        assert (dest / name).is_file(), f"{name} 被孤儿清理误伤"


def _symlink_farm(tmp_path):
    """造一个**可写的 REPO_DIR 替身**：顶层条目全部软链回真仓，只有 `sdflow-spec/agents/`
    是真目录（内含指向真定义的软链）—— 于是它可以被删掉，而真仓一动不动。

    为什么需要它：`REPO_DIR` 由 `dirname $0` 决定，而本用例要验的正是「**源目录整体消失**
    时 setup 还清不清孤儿」。不造替身就只能删真仓的 `sdflow-spec/agents/`。
    （`hack/*.py` 里的 `Path(__file__).resolve()` 会穿过软链落回真仓 ⇒ 那几个 `--check`
    仍在真仓上跑，只读，不污染。）
    """
    farm = tmp_path / "farm-repo"
    farm.mkdir()
    for entry in REPO.iterdir():
        if entry.name == "sdflow-spec":
            continue
        os.symlink(str(entry), str(farm / entry.name))
    spec = farm / "sdflow-spec"
    spec.mkdir()
    for entry in (REPO / "sdflow-spec").iterdir():
        if entry.name == "agents":
            continue
        os.symlink(str(entry), str(spec / entry.name))
    agents = spec / "agents"
    agents.mkdir()
    for p in SRC_DIR.glob("*.md"):
        os.symlink(str(p), str(agents / p.name))
    return farm


def test_orphans_are_cleaned_even_when_the_whole_source_dir_is_gone(fake_home, tmp_path):
    """⑤ **整个 `sdflow-spec/agents/` 被删** ⇒ 悬空链**照样**被清。

    🔴 这一格守的是 design Migration Plan 的回滚故事本身。原实现在函数开头写
    `[ -d "$src_dir" ] || return 0`：源目录整体消失时**连孤儿清理都不跑** ⇒ 上一次铺出去的
    三条链永久留在**全局** `~/.claude/agents/` 里。而「删掉源再跑一次新版 setup」正是
    Migration Plan 要求的回滚第①步（先移除 agents、再 revert）的唯一可执行动作
    —— `setup.sh` 没有 uninstall 开关（实测：全文零命中）。
    ∴ 早退 = 那条回滚路径**根本走不通**，且失败是静默的。

    定点删门法：把 `install_agents` 里的 `cleanup_agent_orphans "$dest"` 调用删掉任一处，
    或把它改回源目录上的早退 ⇒ 本用例必须红。
    """
    # ① 先用替身仓铺一次 —— 链指向替身仓的 agents/
    farm = _symlink_farm(tmp_path)
    env = dict(os.environ)
    env["HOME"] = str(fake_home)
    env.pop("SDFLOW_HOME", None)
    first = subprocess.run([bash_executable(), bash_path(farm / "setup.sh")], cwd=str(farm), env=env,
                           capture_output=True, text=True, timeout=300, encoding="utf-8", errors="replace")
    assert first.returncode == 0, first.stdout + first.stderr
    dest = _agents_dir(fake_home)
    names = _expected_names()
    for name in names:
        assert (dest / name).is_symlink(), f"{name} 没铺出来，前提就不成立"

    # ② 「移除 agents」：删掉整个源目录（人手回滚时最自然的动作）
    for p in (farm / "sdflow-spec" / "agents").iterdir():
        p.unlink()
    (farm / "sdflow-spec" / "agents").rmdir()

    # ③ 仍在**新版 installer** 上重跑一次
    second = subprocess.run([bash_executable(), bash_path(farm / "setup.sh")], cwd=str(farm), env=env,
                            capture_output=True, text=True, timeout=300, encoding="utf-8", errors="replace")
    assert second.returncode == 0, second.stdout + second.stderr

    dangling = [n for n in names if (dest / n).is_symlink() and not (dest / n).exists()]
    assert not dangling, (
        f"源目录整体消失后仍留下悬空软链 {dangling} —— 全局命名空间被污染，"
        "且 Migration Plan 的回滚第①步无法执行\n" + second.stdout + second.stderr)
    for name in names:
        assert not (dest / name).is_symlink(), f"{name} 的链没被清"
        assert f"agents/{name} @ {dest}" in second.stdout, f"{name} 没进 cleaned 汇总"


def test_an_occupied_dest_degrades_to_skip_and_does_not_abort_setup(fake_home):
    """⑥ 落点被占为普通文件 ⇒ **skip + 汇总报告**，MUST NOT 中止整个 setup.sh。

    🔴 `install_agents` 排在 `install_sdflow` **之前**：`mkdir -p` 在 `set -e` 下失败会当场
    中止全脚本 ⇒ 连 `~/.sdflow/` 的 canonical 与 hack 脚本（resolve-models.sh /
    outside-voice.sh / checkpoint-commit.sh）都一并装不上，而用户只看到一行裸 `mkdir:` 错误。
    与本文件既定取向（外来同名条目 → skip + 汇总）不一致，故降级为 skip。
    """
    (fake_home / ".claude").mkdir(parents=True)
    (fake_home / ".claude" / "agents").write_text("被别的东西占了\n", encoding="utf-8")

    r = _run_setup(fake_home)

    assert r.returncode == 0, "落点被占竟中止了整个 setup.sh：\n" + r.stdout + r.stderr
    assert "agents @" in _skipped_section(r.stdout) and "落点建不出来" in r.stdout, \
        "没有进 skipped 汇总 —— 只剩一行裸 mkdir 错误"
    assert (fake_home / ".claude" / "agents").is_file(), "占位文件被动了"
    # 后续步骤 MUST 照常跑完：~/.sdflow/hack 是 /sdflow-spec 第零步档位解析的依赖
    assert (fake_home / ".sdflow" / "hack").is_dir(), \
        "install_sdflow 没跑到 —— agents 落点被占把整条安装链带崩了"


def test_a_readonly_dest_degrades_to_skip_and_does_not_abort_setup(fake_home):
    """⑦ 落点**已存在但只读** ⇒ `ln` 与 `rm` 双双失败 ⇒ 仍是 **skip + 汇总**，MUST NOT 中止 setup。

    🔴 上一条用例只覆盖了 `mkdir -p` 那一格（落点建不出来）。落点**建得出来、写不进去**是
    另一条路径：`mkdir -p` 对已存在目录返回 0，于是控制流一路走到 `ln -snf`（铺设）与
    `rm -f`（孤儿清理）—— 这两处在 `set -e` 下失败就**当场中止整个 setup.sh**，
    用户只看到一行裸 `ln:` / `rm:` 错误，而 `install_agents` 排在 `install_sdflow` 之前
    ⇒ `~/.sdflow/` 的 canonical 与 hack 脚本全装不上。
    与本文件既定取向（外来同名条目 → skip + 汇总）一致，两处一并降级为 skip。

    定点删门法：把 `install_agents` 的 `if ! ln -snf … then skipped+=…` 改回裸 `ln -snf`，
    或把 `cleanup_agent_orphans` 的 `if ! rm -f … then skipped+=…` 改回裸 `rm -f` ⇒ 本用例必须红。
    """
    if os.geteuid() == 0:
        pytest.skip("root 无视目录写权限位 —— 这条只在非 root 下有区分力")

    dest = _agents_dir(fake_home)
    dest.mkdir(parents=True)
    # 同形状**悬空**链：只读之下孤儿清理会试着 `rm` 它并失败 —— 专打 cleanup 那一格
    orphan = dest / "sdflow-gone-agent.md"
    os.symlink(str(SRC_DIR / "sdflow-gone-agent.md"), orphan)
    os.chmod(dest, 0o555)
    try:
        r = _run_setup(fake_home)
    finally:
        os.chmod(dest, 0o755)   # 还原，否则 tmp_path 清理也进不去

    assert r.returncode == 0, "落点只读竟中止了整个 setup.sh：\n" + r.stdout + r.stderr

    skipped = _skipped_section(r.stdout)
    for name in _expected_names():
        assert f"agents/{name} @ {dest}" in skipped, \
            f"{name} 铺设失败却没进 skipped 汇总 —— 只剩一行裸 ln 错误"
        assert f"✓ agents/{name} @ {dest}" not in r.stdout, \
            f"{name} 既报跳过又报安装成功"
    assert f"agents/{orphan.name} @ {dest}" in skipped, \
        "悬空孤儿链清不掉却没进 skipped 汇总 —— 只剩一行裸 rm 错误"
    assert f"✗ agents/{orphan.name} @ {dest}" not in r.stdout, \
        "清理失败却报进了 cleaned 段"

    assert orphan.is_symlink(), "只读落点里的条目居然被动了"
    # 后续步骤 MUST 照常跑完：~/.sdflow/hack 是 /sdflow-spec 第零步档位解析的依赖
    assert (fake_home / ".sdflow" / "hack").is_dir(), \
        "install_sdflow 没跑到 —— agents 落点只读把整条安装链带崩了"


def test_an_agent_deleted_in_the_new_checkout_is_retired_even_though_the_old_file_lives(
        fake_home, tmp_path):
    """🔴 复现（代码审 F3）：跨 checkout 删掉一个 agent 后，废弃定义**永久留在全局名册**。

    铺设循环只接管「**当前**源目录里还在的名字」，孤儿清理只删「**悬空**的链」——
    而「旧 checkout 里那个 .md 还在、新 checkout 已经删了它」同时落在两者之外：
    既不接管、也不清理 ⇒ 一份**已被废弃**、却仍持有 `Bash`/`Write` 的 agent 定义，
    对这台机器上的**所有**项目继续可见。现有用例只覆盖了跨 checkout 的**悬空**链。

    修法 = installer-owned manifest（`.sdflow-agents`）：只记**本安装器铺出去的名字**，
    下一趟清掉「manifest 里有、当前源集合里没有」的那些。
    ⚠️ MUST NOT 放宽成「本仓路径形状的链就删」—— 那会删掉别人仓里同布局的**有效**链
    （本文件第六格守的正是它），是真实数据丢失。manifest 的作用恰恰是把
    「我们装的」与「碰巧同形的」分开。
    """
    dest = _agents_dir(fake_home)
    env = dict(os.environ)
    env["HOME"] = str(fake_home)
    env.pop("SDFLOW_HOME", None)

    # ① 旧 checkout（替身仓）里**多一个** agent 定义 —— 用真实文件，删了源仓也不受影响
    farm = _symlink_farm(tmp_path)
    legacy = farm / "sdflow-spec" / "agents" / "sdflow-legacy-agent.md"
    legacy.write_text("---\nname: sdflow-legacy-agent\ntools: Bash, Write\n---\n旧定义\n",
                      encoding="utf-8")
    first = subprocess.run([bash_executable(), bash_path(farm / "setup.sh")], cwd=str(farm), env=env,
                           capture_output=True, text=True, timeout=300, encoding="utf-8", errors="replace")
    assert first.returncode == 0, first.stdout + first.stderr
    assert (dest / "sdflow-legacy-agent.md").is_symlink(), "前提不成立：旧定义没铺出去"

    # 别人仓里同布局的**有效**链：从头到尾 MUST 原样保留（manifest 里从来没有它）
    live_foreign_dir = tmp_path / "someone-else-repo" / "sdflow-spec" / "agents"
    live_foreign_dir.mkdir(parents=True)
    (live_foreign_dir / "their-live-agent.md").write_text("third party\n", encoding="utf-8")
    live_foreign = dest / "their-live-agent.md"
    os.symlink(str(live_foreign_dir / "their-live-agent.md"), live_foreign)

    # ② 新 checkout（真仓）里没有这个定义，而**旧 checkout 的文件仍然存在**（链有效）
    assert legacy.is_file(), "前提不成立：旧 checkout 的源文件应当还在"
    second = _run_setup(fake_home)
    assert second.returncode == 0, second.stdout + second.stderr

    leaked = dest / "sdflow-legacy-agent.md"
    assert not leaked.is_symlink() and not leaked.exists(), (
        "已废弃的 agent 定义仍留在全局名册里（旧 checkout 文件还在 ⇒ 链有效 ⇒ 孤儿清理不碰它）"
        "\n" + second.stdout + second.stderr)
    assert f"agents/sdflow-legacy-agent.md @ {dest}" in second.stdout, "撤下动作没进汇总"
    assert legacy.is_file(), "清理动作把**源文件**删了 —— 只该撤下名册里的链"
    assert live_foreign.is_symlink() and live_foreign.is_file(), \
        "误删了别人仓里同布局的**有效**链 —— 判据放宽成了「路径形状」"

    # ③ 再跑一次：不许把自己刚铺的链当废弃项扫掉（manifest 每趟重写）
    third = _run_setup(fake_home)
    assert third.returncode == 0, third.stdout + third.stderr
    for name in _expected_names():
        assert (dest / name).is_symlink() and (dest / name).is_file(), f"{name} 被误撤"
    assert live_foreign.is_symlink() and live_foreign.is_file()


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
