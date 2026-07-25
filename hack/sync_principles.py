"""把「四条通则」托管区块同步进每个 SKILL.md。

【为什么是内联复制，不是一行指针】
skill 是【独立分发单元】——symlink 装到 ~/.claude/skills/，跑在别的项目里，
那里读不到本仓的 CLAUDE.md。而这三条是【每问一句话都要触发的立场】，
立场 MUST 在 prompt 里，不能藏在一个「模型可能不去 Read」的指针后面。

【那怎么防漂移】
真相源唯一（sdflow-init/assets/ 下的两个源，见下方 SOURCE / SOURCE_PROJECT），
注入机械化（本脚本），漂移机械可查（--check）。
—— 这正是 CLAUDE.md 基准 1：能用「可固化规则 + 脚本」保证的一致性，优先机械化。

【语法面】
只认两个 marker token（start / end）+ 首个 H1。都是【单行字面量匹配】，语法面有界（基准 5）。
MUST NOT 演化成「解析 Markdown 结构」。

用法：
    python3 hack/sync_principles.py --check     # 漂了 → exit 1（CI / pytest 用）
    python3 hack/sync_principles.py --apply     # 回填
"""
import argparse
import sys
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

START = "<!-- sdflow:principles:start"
END = "<!-- sdflow:principles:end -->"


def block(src):
    """真相源的内容【就是】要注入的文本。零解析。"""
    return src.read_text(encoding="utf-8").strip() + "\n"


def skills():
    return sorted(p / "SKILL.md" for p in REPO.iterdir()
                  if p.is_dir() and (p / "SKILL.md").is_file())


def _blocks(text):
    """→ [(start_idx, end_idx)]：文本里【全部】托管块的行区间（含首尾 marker 行）。

    【为什么是「全部」而不是「首个」】：CLAUDE.md / AGENTS.md 各有【两份】——
    顶部一份（本仓 dogfood）+ 文末一份（sdflow-init 铺设的工作流托管区块自带）。
    只更新首个 ⇒ 第二份静默留旧版 ⇒ 同一文件里两份通则自相矛盾，而 --check 照样报绿。
    这是【假绿】，不是省事。
    """
    lines = text.splitlines(keepends=True)
    out, cursor = [], 0
    for i, l in enumerate(lines):
        if i < cursor or not l.startswith(START):
            continue
        ends = [j for j in range(i, len(lines)) if lines[j].startswith(END)]
        if not ends:
            raise SystemExit("[sync_principles] FAIL: 有 start 无 end —— 区块被手改坏了")
        out.append((i, ends[0]))
        cursor = ends[0] + 1
    return out


def _insert_anchor(lines):
    """无块时的插入点：首个 H1 之后；无 H1 则 frontmatter 之后。"""
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


def render(text, src):
    body = block(src)
    lines = text.splitlines(keepends=True)

    spans = _blocks(text)
    if not spans:
        anchor = _insert_anchor(lines)
        spans = [(anchor, anchor - 1)]   # 空区间 = 纯插入，不吞掉任何行

    out, cursor = "", 0
    for start, end in spans:
        head = out + "".join(lines[cursor:start])
        # 块前恰好一个空行（文件以块开头时不加）
        out = f"{head.rstrip(chr(10))}\n\n{body}" if head.strip() else body
        cursor = end + 1
    tail = "".join(lines[cursor:]).lstrip("\n")
    return f"{out}\n{tail}"


def targets():
    """→ [(文件, 该用哪个源)]"""
    pairs = [(p, SOURCE) for p in skills()]
    pairs += [(p, SOURCE_PROJECT) for p in PROJECT_TARGETS]
    return pairs


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)

    drift = []
    for p, src in targets():
        cur = p.read_text(encoding="utf-8")
        want = render(cur, src)
        if cur == want:
            continue
        drift.append(p.relative_to(REPO))
        if args.apply:
            p.write_text(want, encoding="utf-8")

    if not drift:
        print(f"[sync_principles] ✅ {len(targets())} 个投放面全部与真相源一致")
        return 0

    if args.apply:
        print(f"[sync_principles] ✅ 已回填 {len(drift)} 个：")
        for d in drift:
            print(f"   {d}")
        return 0

    print("[sync_principles] FAIL: 这些文件的「四条通则」缺失或已漂移：", file=sys.stderr)
    for d in drift:
        print(f"   {d}", file=sys.stderr)
    print("   修：python3 hack/sync_principles.py --apply", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
