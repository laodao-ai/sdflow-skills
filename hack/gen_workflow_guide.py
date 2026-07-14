"""生成 WORKFLOW-GUIDE.md —— 给【人】看的完整手册（每步 prompt 全文内联）。

【为什么要生成，不能手写】
手册要含每步 prompt 全文 ⇒ 若手写，它就是 prompt 的【第二份拷贝】⇒ 必漂。
∴ 单一源永远是 `prompts/step*.md`，手册【机械拼装】出来，`--check` 守。

【为什么要有这份手册】（拆分的另一半）
拆 prompts/ 是为了【机器】——模型取一行 prompt 不必读 17KB 的 workflow.md。
但【人】需要一份从头到尾、不用跳文件的完整参考。两个需求方向相反，所以分两份产物：

    prompts/step*.md   机读单一源 —— 一步一文件，模型只读它要的那 300~800 字节
    workflow.md        机读骨架 —— 流程图 + 表格（prompt 列只留指针）+ 设计决策
    WORKFLOW-GUIDE.md  人读手册 —— 本脚本生成；prompt 全文内联；init 拷进消费仓

【表格解析的语法面】（基准 5：有界可手写 / 无界禁手搓）
只切 `| a | b | c |` 这一种行形态，按 ` | ` 分列，断言恰好 6 列——语法面穷举得完 ⇒ 合法。
列数不符即 fail-closed（stderr + exit 2），MUST NOT 猜。

用法：
    python3 hack/gen_workflow_guide.py --check     # 漂了 → exit 1
    python3 hack/gen_workflow_guide.py --write     # 生成/刷新
"""
import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WF_DIR = REPO / "sdflow-init" / "assets" / "workflow"
WORKFLOW = WF_DIR / "workflow.md"
PROMPTS = WF_DIR / "prompts"
GUIDE = WF_DIR / "WORKFLOW-GUIDE.md"

BANNER = """<!-- 本文件由 hack/gen_workflow_guide.py 从 workflow.md + prompts/ 机械生成。DO NOT EDIT。 -->
<!-- 改 prompt → 改 prompts/step*.md（单一源）；改流程 → 改 workflow.md；然后跑 --write。 -->

# Spec 工作流 —— 完整参考手册（给人看）

> **这份是给人读的**：从头到尾，每步 prompt 全文都在，不用跳文件。
>
> **模型 MUST NOT 读本文** —— 要取某一步的 prompt，直接读 `workflow/prompts/step*.md`
> （一步一文件，几百字节）。读本文 = 为你不需要的 90% 付 token。
>
> **MUST NOT 手改本文**：prompt 的单一源是 `prompts/step*.md`，流程的单一源是 `workflow.md`；
> 手改这里，下次生成即被覆盖，而且会与单一源漂移。
"""

# 表格 prompt 列里的指针 → 对应文件
STEP_FILES = {
    "1": "step1-explore", "2": "step2-ff", "3": "step3-grill",
    "4": "step4-spec-review", "5.5": "step5_5-embedded-sop",
    "6": "step6-writing-plans", "7": "step7-subagent-dev",
    "8": "step8-code-review", "9": "step9-done",
}


def _rows():
    """从 workflow.md 的步骤表抽行。列数不符 ⇒ fail-closed。"""
    out = []
    for line in WORKFLOW.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ") or line.startswith("| 阶段") or line.startswith("|---"):
            continue
        cells = line.split(" | ")
        if len(cells) != 6:
            raise SystemExit(
                f"[gen_workflow_guide] FAIL: 步骤表这一行不是 6 列（得 {len(cells)}）——"
                f"单元格里出现了裸 ' | '？\n  {line[:90]}")
        stage, step, skill, prompt_cell, artifact, rule = (c.strip() for c in cells)
        out.append({"stage": stage.lstrip("| ").strip(), "step": step, "skill": skill,
                    "prompt_cell": prompt_cell, "artifact": artifact,
                    "rule": rule.rstrip("|").strip()})
    if not out:
        raise SystemExit("[gen_workflow_guide] FAIL: workflow.md 里找不到步骤表")
    return out


def render():
    parts = [BANNER, "\n---\n"]
    for r in _rows():
        parts.append(f"\n## 阶段{r['stage']} · 步骤 {r['step']} — `{r['skill']}`\n")

        f = STEP_FILES.get(r["step"])
        if f:
            body = (PROMPTS / f"{f}.md").read_text(encoding="utf-8").strip()
            note = r["prompt_cell"].split("**→")[0].strip()   # 如「（由步骤 6 自动触发）」
            if note:
                parts.append(f"\n{note}\n")
            parts.append(f"\n**prompt**（原样复制，勿转述 · 单一源 `prompts/{f}.md`）：\n")
            parts.append(f"\n```\n{body}\n```\n")
        else:
            # 无 prompt 的步（1b 描述 / 5 人类门）—— prompt 列本身就是说明
            parts.append(f"\n{r['prompt_cell']}\n")

        parts.append(f"\n**产出物**：{r['artifact']}\n")
        parts.append(f"\n**规则 · 条件**：{r['rule']}\n")

    parts.append("\n---\n\n*流程骨架与设计决策 → [workflow.md](./workflow.md)"
                 " · 演进史 → [workflow-history.md](./workflow-history.md)*\n")
    return "".join(parts)


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)

    want = render()
    cur = GUIDE.read_text(encoding="utf-8") if GUIDE.exists() else None

    if cur == want:
        print(f"[gen_workflow_guide] ✅ WORKFLOW-GUIDE.md 与单一源一致")
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
