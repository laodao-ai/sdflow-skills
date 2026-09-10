"""生成 WORKFLOW-GUIDE.md —— 给【人】看的完整手册（prompt 全文内联）。

【做法】
复制 workflow.md 全文，把步骤表里的 prompt 指针（`**→ [prompts/step*.md]**（…）`）
替换成对应 prompts/ 文件的实际内容。加一行生成标记。

【为什么要生成，不能手写】
手册要含每步 prompt 全文 ⇒ 若手写，它就是 prompt 的【第二份拷贝】⇒ 必漂。
∴ 单一源永远是 `prompts/step*.md` + `workflow.md`，手册【机械替换】出来，`--check` 守。

用法：
    python3 hack/gen_workflow_guide.py --check     # 漂了 → exit 1
    python3 hack/gen_workflow_guide.py --write      # 生成/刷新
"""
import argparse
import re
import sys

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WF_DIR = REPO / "sdflow-init" / "assets" / "workflow"
WORKFLOW = WF_DIR / "workflow.md"
PROMPTS = WF_DIR / "prompts"
GUIDE = WF_DIR / "WORKFLOW-GUIDE.md"

BANNER = (
    "<!-- 本文件由 hack/gen_workflow_guide.py 从 workflow.md + prompts/ 机械生成。DO NOT EDIT。 -->\n"
    "<!-- 改 prompt → 改 prompts/step*.md（单一源）；改流程 → 改 workflow.md；然后跑 --write。 -->\n"
    "<!-- [fix-probe-scan-precision task4 · adr/0039] 本文件是消费仓 openspec/workflow/ 下 -->\n"
    "<!-- 唯一落地文件（tools/ 与规则均全局单份共享、不再铺设）。文中对其它规则文件的提及 -->\n"
    "<!-- （如 `quality-layering.md`）已降为纯文字引用，非本文件内的可点链接——那些文件不随 -->\n"
    "<!-- GUIDE 分发，如需查看请见 sdflow-skills 仓 sdflow-init/assets/workflow/ 对应文件。 -->\n\n"
)

# 匹配 **→ [`prompts/step*.md`](./prompts/step*.md)**（原样复制，勿转述）
_POINTER_RE = re.compile(
    r'\*\*→ \[`prompts/(step[^`]+\.md)`\]\(\./prompts/\1\)\*\*（原样复制，勿转述）'
)

# [fix-probe-scan-precision task4 · adr/0039 D14] GUIDE 是消费仓唯一落地文件，指向以下
# sibling 规则文件的相对链接在该目录下全部断链——降为纯文字引用（去链接语法，保留可读文件名）。
# canonical 侧的 workflow.md 原文不变（那里 sibling 文件确实同目录存在，链接有效）。
# 有界枚举（3 个已知目标，非无界语法面，故手写正则不违反基准 5）。
_SIBLING_LINK_TARGETS = (
    "ff-generation-constraints.md",
    "reference/quality-layering.md",
    "workflow-history.md",
)
_SIBLING_LINK_RE = re.compile(
    r'\[([^\]]+)\]\(\./(' + '|'.join(re.escape(t) for t in _SIBLING_LINK_TARGETS) + r')\)'
)


def _resolve_pointer(m):
    """把一个 prompt 指针替换成文件实际内容。找不到文件 → fail-closed。"""
    fname = m.group(1)
    p = PROMPTS / fname
    if not p.is_file():
        raise SystemExit(f"[gen_workflow_guide] FAIL: 指针悬空 — prompts/{fname} 不存在")
    return p.read_text(encoding="utf-8").strip()


def _downgrade_sibling_link(m):
    """`[quality-layering.md](./reference/quality-layering.md)` → `` `quality-layering.md` ``
    （原展示文字保留、去掉链接语法），MUST NOT 保留 `(./...)` ——GUIDE 单独存在时那是死链接。"""
    label = m.group(1)
    return f"`{label}`"


def render():
    src = WORKFLOW.read_text(encoding="utf-8")
    out = _POINTER_RE.sub(_resolve_pointer, src)
    out = _SIBLING_LINK_RE.sub(_downgrade_sibling_link, out)
    return BANNER + out


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)

    want = render()
    cur = GUIDE.read_text(encoding="utf-8") if GUIDE.exists() else None

    if cur == want:
        print("[gen_workflow_guide] ✅ WORKFLOW-GUIDE.md 与单一源一致")
        return 0

    if args.write:
        GUIDE.write_text(want, encoding="utf-8")
        print(f"[gen_workflow_guide] ✅ 已生成 WORKFLOW-GUIDE.md（{len(want.encode())} 字节）")
        return 0

    print("[gen_workflow_guide] FAIL: WORKFLOW-GUIDE.md 与单一源（workflow.md + prompts/）不一致",
          file=sys.stderr)
    print("   修：python3 hack/gen_workflow_guide.py --write", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
