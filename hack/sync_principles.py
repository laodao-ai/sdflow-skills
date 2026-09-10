"""把托管区块同步进目标文件——目前管两个独立 marker 家族：「四条通则」（principles）与
「广审镜定义」（broad-mirror-def，absorb-gstack-autoplan · design DD7）。

【为什么是内联复制，不是一行指针】
skill 是【独立分发单元】——symlink 装到 ~/.claude/skills/，跑在别的项目里，
那里读不到本仓的 CLAUDE.md。而「四条通则」是【每问一句话都要触发的立场】，
立场 MUST 在 prompt 里，不能藏在一个「模型可能不去 Read」的指针后面。「广审镜定义」道理
类似但对象不同——sdflow-spec-review 与 sdflow-roadmap 两个 SKILL 派生的广审双镜必须审
同一套职责划分，不能各自维护一份、悄悄分叉（同 DD7「同源机制=模板注入」，优于 prose 引用
或复制+parity 两个被砍掉的候选）。

【那怎么防漂移】
每个家族真相源唯一（principles 见下方 SOURCE / SOURCE_PROJECT，broad-mirror-def 见
SOURCE_BROAD_MIRRORS），注入机械化（本脚本），漂移机械可查（--check）。
—— 这正是 CLAUDE.md 基准 1：能用「可固化规则 + 脚本」保证的一致性，优先机械化。

【语法面】
每个家族只认两个 marker token（start / end）+ 首个 H1（无既有块时的插入锚点）。都是
【单行字面量匹配】，语法面有界（基准 5）。MUST NOT 演化成「解析 Markdown 结构」。

用法：
    python3 hack/sync_principles.py --check     # 任一家族漂了 → exit 1（CI / pytest 用）
    python3 hack/sync_principles.py --apply     # 回填全部家族
"""
import argparse
import os
import sys

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ASSETS = REPO / "sdflow-init" / "assets"

# 【两个源，因为受众不同 —— 不是同一段话的两份拷贝】
#   skill 味  → 读者是 skill 自己（含 fan-out / outside-voice 的传播纪律、SKILL 内部口径）
#   项目味    → 读者是「在这个项目里干活的 agent」（不该出现 skill 内部的话）
# 三条 headline 一条不许少 —— hack/tests/ 机械守（加第四条时两个源一起红）。
#
# 【为什么源在 assets/ 而不在 hack/】（CLAUDE.md：assets/ 是 bundle 的唯一权威源）：
#   - skill 味的源【就是】outside-voice.sh 要 cat 的那个文件 —— setup.sh 已经把 assets/hack/*.md
#     装进 ~/.sdflow/hack/。源放别处 = 凭空多一份拷贝 = 凭空多一个漂移面。
#   - 项目味的源【就是】init 推给消费项目的那份 snippet 的一部分。
SOURCE = ASSETS / "hack" / "skill-principles.md"                    # skill 味（= outside-voice 读的那个文件）
SOURCE_PROJECT = ASSETS / "snippets" / "principles-project.md"      # 项目味

# 项目味的投放面：
#   本仓 CLAUDE.md / AGENTS.md —— dogfood（我们自己就是一个「在这个项目里干活」的场景）
#   claude-section.md          —— sdflow-init 铺进【消费项目】CLAUDE.md/AGENTS.md 的托管块模版
PROJECT_TARGETS = [
    REPO / "CLAUDE.md",
    REPO / "AGENTS.md",
    ASSETS / "snippets" / "claude-section.md",
]

# agent 定义（~/.claude/agents/ 的投放面）= 【目录, 该用哪个源】。
#
# 【为什么是独立的一项，不并进 PROJECT_TARGETS】
#   PROJECT_TARGETS 固定配 SOURCE_PROJECT（项目味）。agent 定义的读者是【被下发的子代理】,
#   受众与 SKILL.md 相同 ⇒ 必须用 skill 味 SOURCE（含 fan-out 传播纪律那一段）。
#   直接加进 PROJECT_TARGETS = 给子代理注入错误味源，而 --check 照样报绿。
#
# 【为什么成员靠 glob 发现，不写死清单】
#   写死清单的话，「新增一个 agent 定义却忘了纳入投放面」这个失效场景【做不出来】——
#   新文件不在清单里，--check 看不见它，绿。glob 使新文件自动进入检查范围。
AGENT_TARGETS = (REPO / "sdflow-spec" / "agents", SOURCE)

START = "<!-- sdflow:principles:start"
END = "<!-- sdflow:principles:end -->"

# 【第二个独立 marker 家族：广审镜定义（absorb-gstack-autoplan · design DD7「同源机制=模板注入」）】
#
# 与上面的「四条通则」同一套机制（真相源唯一 + 注入机械化 + 漂移机械可查），但守的是不同内容：
# sdflow-spec-review 与 sdflow-roadmap 两个 SKILL 的「广审镜（strategy/plan-eng）职责定义」逐字节
# 相同——这两个 SKILL 各自派生的广审双镜必须审同一套 base R 项划分，不能各自维护一份、悄悄分叉。
#
# 【为什么不复用 START/END 常量】：两个家族的托管块可能同时出现在同一份 SKILL.md 里（如
# sdflow-spec-review/SKILL.md 已同时含 principles 与 broad-mirror-def 两类块）——marker 字面量
# 必须不同，否则 _blocks() 的扫描会把两类块混为一谈。
#
# 【为什么 render()/_blocks() 接受 marker 参数而不是新写一套】：注入逻辑（找 span、保留块前空行、
# 幂等改写）与 marker 家族无关，只有字面量不同——参数化比复制一份平行实现更不容易漂（基准 1）。
SOURCE_BROAD_MIRRORS = ASSETS / "snippets" / "broad-mirrors.md"

BROAD_MIRROR_START = "<!-- sdflow:broad-mirror-def:start"
BROAD_MIRROR_END = "<!-- sdflow:broad-mirror-def:end -->"

# 【为什么是列表字面量、可变】：测试用 `BROAD_MIRROR_TARGETS[:] = [...]` 原地替换成员来做
# 隔离探针（同 AGENT_TARGETS 的 monkeypatch 精神），不写真实工作树。与 skills()/agent_defs()
# 的 glob 发现不同——这两个投放面是**固定的两个 SKILL**（DD7 明确的同源范围，非"任何含某
# marker 的文件"），没有"新增就自动发现"的诉求，写死清单是诚实的（不是偷懒）。
BROAD_MIRROR_TARGETS = [
    REPO / "sdflow-spec-review" / "SKILL.md",
    REPO / "sdflow-roadmap" / "SKILL.md",
]


def block(src):
    """真相源的内容【就是】要注入的文本。零解析。"""
    return src.read_text(encoding="utf-8").strip() + "\n"


def skills():
    return sorted(p / "SKILL.md" for p in REPO.iterdir()
                  if p.is_dir() and (p / "SKILL.md").is_file())


def agent_defs():
    """AGENT_TARGETS 目录下的全部 agent 定义 —— 【每次调用重新 glob】。

    不在 import 期定死：否则「往 agents/ 放一个新 .md → --check 必红」这个场景
    在同一个进程里测不出来（测试写完文件，模块级常量早已算好，看不见它）。
    """
    d, _ = AGENT_TARGETS
    return sorted(d.glob("*.md")) if d.is_dir() else []


def _blocks(text, start=START, end=END):
    """→ [(start_idx, end_idx)]：文本里【全部】托管块的行区间（含首尾 marker 行）。

    【为什么是「全部」而不是「首个」】：CLAUDE.md / AGENTS.md 各有【两份】——
    顶部一份（本仓 dogfood）+ 文末一份（sdflow-init 铺设的工作流托管区块自带）。
    只更新首个 ⇒ 第二份静默留旧版 ⇒ 同一文件里两份通则自相矛盾，而 --check 照样报绿。
    这是【假绿】，不是省事。

    【为什么 start/end 是参数、不是硬编码全局】：本文件现管两个独立 marker 家族
    （principles / broad-mirror-def），字面量不同、扫描逻辑相同——参数化复用，
    不新写一份平行实现（基准 1：能机械化的一致性别靠两份手写代码各自维护）。
    默认值保持向后兼容——现有调用点 `_blocks(text)` 无需改动。
    """
    lines = text.splitlines(keepends=True)
    out, cursor = [], 0
    for i, l in enumerate(lines):
        if i < cursor or not l.startswith(start):
            continue
        ends = [j for j in range(i, len(lines)) if lines[j].startswith(end)]
        if not ends:
            raise SystemExit("[sync_principles] FAIL: 有 start 无 end —— 区块被手改坏了")
        out.append((i, ends[0]))
        cursor = ends[0] + 1
    return out


def _insert_anchor(lines):
    """无块时的插入点：首个 H1 之后；无 H1 则 frontmatter 之后。

    【只服务 principles 家族】：broad-mirror-def 的两个投放面（DD7 固定两个 SKILL）
    MUST 已手工放好一对空 marker（`<!-- sdflow:broad-mirror-def:start -->` 紧跟
    `<!-- sdflow:broad-mirror-def:end -->`）在各自 SKILL.md 里想要的落位——那两个
    位置各有各的上下文（spec-review 挂在广审镜小节、roadmap 挂在 review 小节），
    不该也不能靠「首个 H1 之后」这个通用兜底猜。若 broad_mirror_targets() 里的文件
    缺失该 marker，`render()` 会退回本函数、把内容插到 H1 后——那是**未装配好投放面**
    的信号，不是本函数支持的正常路径。
    """
    anchor = 0
    if lines and lines[0].strip() == "---":
        for j in range(1, len(lines)):
            if lines[j].strip() == "---":
                anchor = j + 1
                break

    for j in range(anchor, len(lines)):
        if lines[j].startswith("# "):
            anchor = j + 1
            break
    return anchor


def render(text, src, start=START, end=END):
    body = block(src)
    lines = text.splitlines(keepends=True)

    spans = _blocks(text, start, end)
    if not spans:
        anchor = _insert_anchor(lines)
        spans = [(anchor, anchor - 1)]   # 空区间 = 纯插入，不吞掉任何行

    out, cursor = "", 0
    for s, e in spans:
        head = out + "".join(lines[cursor:s])
        # 块前恰好一个空行（文件以块开头时不加）
        out = f"{head.rstrip(chr(10))}\n\n{body}" if head.strip() else body
        cursor = e + 1
    tail = "".join(lines[cursor:]).lstrip("\n")
    return f"{out}\n{tail}"


def targets():
    """→ [(文件, 该用哪个源)] —— 「四条通则」marker 家族的投放面。"""
    pairs = [(p, SOURCE) for p in skills()]
    pairs += [(p, SOURCE_PROJECT) for p in PROJECT_TARGETS]
    pairs += [(p, AGENT_TARGETS[1]) for p in agent_defs()]
    return pairs


def broad_mirror_targets():
    """→ [(文件, 该用哪个源)] —— 「广审镜定义」marker 家族的投放面（固定两个 SKILL，见上方注记）。"""
    return [(p, SOURCE_BROAD_MIRRORS) for p in BROAD_MIRROR_TARGETS]


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)

    # 两个独立 marker 家族，各自的 (投放面, start, end)——都过同一套 render/--check/--apply。
    # 【为什么在这里合并遍历而不是两次 main() 调用】：--check/--apply 是【一次】门禁动作，
    # 调用方（setup.sh）只关心「有没有漂」，不关心漂的是哪个家族；分两次调用会让 setup.sh
    # 也要跟着改，且两次调用各自的 exit code 需要再合并——不如在此处一次归约。
    groups = [
        (targets(), START, END),
        (broad_mirror_targets(), BROAD_MIRROR_START, BROAD_MIRROR_END),
    ]

    drift = []
    total = 0
    for group_targets, start, end in groups:
        total += len(group_targets)
        for p, src in group_targets:
            cur = p.read_text(encoding="utf-8")
            want = render(cur, src, start, end)
            if cur == want:
                continue
            # os.path.relpath 而非 Path.relative_to：后者对【仓外】的投放面直接抛 ValueError，
            # 于是「报告一个漂移」变成「整个 --check 崩掉」。投放面目录可被测试 monkeypatch 到
            # 仓外，此处只是【打印用的显示形式】，不该有能力中止判定。
            try:
                display = os.path.relpath(p, REPO)
            except ValueError:
                display = str(p)
            drift.append(display)
            if args.apply:
                p.write_text(want, encoding="utf-8")

    if not drift:
        print(f"[sync_principles] ✅ {total} 个投放面全部与真相源一致（四条通则 + 广审镜定义）")
        return 0

    if args.apply:
        print(f"[sync_principles] ✅ 已回填 {len(drift)} 个：")
        for d in drift:
            print(f"   {d}")
        return 0

    print("[sync_principles] FAIL: 这些文件的托管块（四条通则 / 广审镜定义）缺失或已漂移：", file=sys.stderr)
    for d in drift:
        print(f"   {d}", file=sys.stderr)
    print("   修：python3 hack/sync_principles.py --apply", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
