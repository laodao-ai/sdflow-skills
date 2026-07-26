"""canonical 规则单一源：阶段一「四入口选择规则 + G1 具名例外 + FF-0 三分支判定」不得分叉。

【为什么要有本文件】
`add-sdflow-spec` 引入的阶段一单入口与**七处**既有权威源冲突。本仓运行时经
`resolve-workflow.sh` 解析到**全局 canonical**、仓内不留规则副本 ⇒ 任何一处漏改，
结果就是「人从 README/CLAUDE.md 读到新入口，AI 从 bundle 读到旧入口」，且两者对
`/clear` 直接矛盾。这类分叉没有自然的报错口——不机械钉住，就只能靠人记得。

【锚的质量纪律（本文件的重点）】
- **MUST 单行命中**：G1 的两处载体措辞不同（`workflow.md` 写「全流程不用 `/clear`」，
  `quality-layering.md` 写「无 `/clear`（G1）」），**一条 grep 命不中两处**，必须分开断言。
- **MUST NOT 用跨行结构当判据**：`generation-process.md` §四 是跨行 ASCII 图，
  `explore.*ff.*grill` 这类单行正则对它**实测零命中** = 一个永远不会红的空判据。
  故本文件一律锚**单行散文/表格行**，不锚图。
- 每条断言都做过**定点变异回验**（把被锚的那句话改掉 → 该断言必红）。

【谁不在本文件里，为什么】
- `WORKFLOW-GUIDE.md` 是**生成物**：与单一源的一致性由 `test_workflow_split.py` 的
  `gen_workflow_guide --check` 守；这里只补一条「重生成后阶段一段落确实带上了新入口」。
- `ff0-branch-guard.py` 的**行为**由 `sdflow-init/tests/test_ff0_branch_guard.py` 守
  （真跑 hook）；这里只守「规则文本与 hook 提到的是同一个逃生口口令」。
"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WF = REPO / "sdflow-init" / "assets" / "workflow"

WORKFLOW = WF / "workflow.md"
GENERATION = WF / "generation-process.md"
QUALITY = WF / "reference" / "quality-layering.md"
FF_CONSTRAINTS = WF / "ff-generation-constraints.md"
GUIDE = WF / "WORKFLOW-GUIDE.md"
CLAUDE_SECTION = REPO / "sdflow-init" / "assets" / "snippets" / "claude-section.md"
SPEC_WORKFLOW = REPO / "openspec" / "specs" / "spec-workflow" / "spec.md"
HOOK = REPO / "sdflow-init" / "assets" / "hooks" / "ff0-branch-guard.py"


def lines(p: Path):
    return p.read_text(encoding="utf-8").splitlines()


def has_line(p: Path, *needles: str) -> bool:
    """存在**同一行**同时含全部 needles。跨行结构一律不算命中。"""
    return any(all(n in ln for n in needles) for ln in lines(p))


def require(p: Path, *needles: str):
    assert has_line(p, *needles), (
        f"{p.relative_to(REPO)} 里找不到同时含 {needles!r} 的**单行** —— "
        "canonical 与本 change 的阶段一规则已分叉，或这条锚失鲜了（先核对再改测试）"
    )


# ── ① generation-process.md：推荐流水线两分支 + 四入口选择规则 ─────────────

def test_generation_process_has_two_branches():
    require(GENERATION, "分支 A", "sdflow-spec")
    require(GENERATION, "分支 B", "未装")


def test_generation_process_states_entry_selection_rule():
    require(GENERATION, "默认走 `/sdflow-spec`")
    require(GENERATION, "仅下列三种情形用旧三步")
    require(GENERATION, "模型侧", "MUST NOT", "opsx:ff")


def test_generation_process_keeps_legacy_path_alive():
    """旧三步未被删除——它仍是三种例外情形下的合法路径。"""
    require(GENERATION, "opsx:explore")
    require(GENERATION, "grill-with-docs")


# ── ② workflow.md：G1 具名例外（载体一，措辞「全流程不用 `/clear`」）──────

def test_workflow_md_g1_still_states_the_rule():
    require(WORKFLOW, "全流程不用 `/clear`")


def test_workflow_md_g1_names_the_exception():
    require(WORKFLOW, "具名例外", "阶段一 → 阶段二")


def test_workflow_md_g1_exception_cites_exactly_the_two_allowed_reasons():
    require(WORKFLOW, "cache 按模型隔离")
    require(WORKFLOW, "产 / 审错档")


def test_workflow_md_g1_exception_forbids_the_cold_view_reason():
    """「主审裁决需冷视角」已被 G1 正面回答 ⇒ MUST 有一行明令禁止拿它当本例外的理由。

    ⚠️ 判据是「存在这条禁令行」，**不是**「全文提到冷视角的行都带 MUST NOT」——
    后者会被 §一流程图里那句「独立冷视角·强制主审」误伤（那是在说 code-review，不是理由）。
    """
    require(WORKFLOW, "MUST NOT", "冷视角")


# ── ③ quality-layering.md：G1 具名例外（载体二，措辞「无 `/clear`（G1）」）─
#     ⚠️ 与 ② 字面不同，一条 grep 命不中两处 —— 故必须分开断言。

def test_quality_layering_still_states_the_rule():
    require(QUALITY, "无 `/clear`（G1）")


def test_quality_layering_names_the_same_exception():
    require(QUALITY, "具名例外", "sdflow-spec")
    require(QUALITY, "cache 按模型隔离")
    require(QUALITY, "产 / 审错档")


def test_quality_layering_forbids_the_cold_view_reason():
    require(QUALITY, "MUST NOT", "冷视角")


def test_quality_layering_checklist_carries_the_exception():
    """检查清单是另一处载体（`:117` 那条）—— 清单说「不许 /clear」而正文说「有例外」即分叉。"""
    checklist = [ln for ln in lines(QUALITY) if ln.startswith("- [ ]") or ln.startswith("      ")]
    assert any("例外" in ln and "sdflow-spec" in ln for ln in checklist), \
        "quality-layering.md 的检查清单没跟上 G1 例外"


# ── ④ ff-generation-constraints.md + hook：FF-0 三分支判定 ────────────────

def test_ff0_rule_is_three_way():
    require(FF_CONSTRAINTS, "三分支判定")
    require(FF_CONSTRAINTS, "其它 feature 分支", "halt 问人")
    require(FF_CONSTRAINTS, "MUST NOT 沿用「已在 feature 分支就跳过」的弱判据")


def test_ff0_rule_and_hook_agree_on_the_escape_hatch():
    """规则文本与 hook 实现是两处载体 —— 逃生口口令必须是同一个字面量。"""
    require(FF_CONSTRAINTS, "SDFLOW_FF0_ACK=1")
    assert "SDFLOW_FF0_ACK=1" in HOOK.read_text(encoding="utf-8"), \
        "hook 没实现规则文本承诺的 ack 逃生口 —— 人拍板「就地继续」这条路会走不通"


# ── ⑤ claude-section.md（托管块源）：grill 条款分支化 + 归属修正 ──────────

def test_claude_section_scopes_the_grill_clause_to_branch_b():
    require(CLAUDE_SECTION, "ff 之后是 grill", "本条只管分支 B")


def test_claude_section_attribution_is_fixed():
    require(CLAUDE_SECTION, "Matt Pocock", "~/.agents/skills")
    blob = CLAUDE_SECTION.read_text(encoding="utf-8")
    assert "grill-with-docs" in blob
    assert "来自 superpowers 插件" not in blob, \
        "grill-with-docs 的归属仍写着 superpowers 插件（实为 Matt Pocock 的 ~/.agents/skills）"


def test_claude_section_carries_the_entry_selection_rule():
    require(CLAUDE_SECTION, "阶段一入口二选一")
    require(CLAUDE_SECTION, "FF-0 三分支判定")


# ── ⑥ 仓级主 spec：新旧入口共存与路由 ────────────────────────────────────

def test_spec_workflow_declares_coexistence_and_routing():
    require(SPEC_WORKFLOW, "新旧入口共存与路由")
    require(SPEC_WORKFLOW, "分支 A（默认）", "sdflow-spec")
    require(SPEC_WORKFLOW, "MUST NOT 沿用「已在 feature 分支就跳过」的弱判据")


# ── ⑦ 生成物：重生成后阶段一段落确实带上了新入口 ──────────────────────────

def test_generated_guide_reflects_the_new_entry():
    """一致性本身由 gen_workflow_guide --check 守（test_workflow_split.py）；
    这里只钉「新入口确实进了人读手册的阶段一段落」。"""
    require(GUIDE, "阶段一", "步骤 0", "/sdflow-spec")


# ── ⑧ 人核残余：如实登记，MUST NOT 假装有机械覆盖 ────────────────────────

MANUAL_ONLY = """
以下面无可靠单行锚点，如实留人核（MUST NOT 硬造恒真锚）：
  · generation-process.md §四 的两张 ASCII 流水线图本身（跨行结构；本文件只锚其周边散文）
  · workflow.md §一 的阶段一流程图分支框（同上）
  · 「例外情形①②③的语义是否真的互斥且穷尽」——语义判断，无确定性信号
"""


def test_manual_residue_is_declared():
    assert MANUAL_ONLY.strip(), "人核残余清单不许空着"
