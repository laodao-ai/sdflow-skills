"""通则承载与前缀文件的文本契约守卫（HAE-16、HAE-19、SW-04、SW-05）。

【这测的是什么】派发 prompt 不再内联通则或前缀原文。Claude 软链判定通过时通则由 agent 定义承载；
否则子代理读渲染器生成的文件，把文件首行原样作为结果首行，主 session 比对回执。
本文件只锁文本契约（SKILL / 契约 / 真相源的措辞），渲染器本身的行为见 test_render_review_prefix.py。

【诚实边界】回执只证明子代理读到了文件首行，不证明读完全文；「子代理是否读完」无确定性信号，
本文件不声称守住它。
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "sdflow-init/assets/workflow/subagent-dispatch-contract.md"

READ_INSTRUCTION = "先完整读取 `<path>`；把该文件第一行原样作为你结果的第一行。"
SECTION = "## 通则承载与前缀文件"
RECEIPT_WRITE_NOTE = "回执不符，产出未采信"

REVIEW_SKILLS = {
    "sdflow-spec-review": "spec-review",
    "sdflow-code-review": "code-review",
}

# 八个派发入口 → run 目录父目录（design「文件落点与创建时机」表）
DISPATCH_ENTRIES = {
    "sdflow-spec-review": "{change_dir}/.outside-voice/",
    "sdflow-code-review": "{change_dir}/.outside-voice/",
    "sdflow-implement": "{change_dir}/.outside-voice/",
    "sdflow-done": "openspec/.outside-voice/",
    "sdflow-roadmap": "openspec/roadmaps/{name}/.outside-voice/",  # SKILL 内一律写 {name}；契约写 <name>
    "sdflow-adr": "openspec/adr/.outside-voice/",
    "sdflow-architecture": "openspec/architecture/.outside-voice/",
    "sdflow-devenv": "openspec/architecture/.outside-voice/",
}

# 回执不符的重派规则原文只在契约「读文件指令与回执」小节（HAE-22）；入口只留一句引用。
RECEIPT_REF = "回执不符的重派规则以契约「通则承载与前缀文件」节「读文件指令与回执」为准"
# 原文特征：只读任务重派一次 / 写入任务不重派。入口里出现即视为复述。
# 收窄到回执语境：同一句里「回执」与「重派一次 / 不重派」同现才算复述，避免误报其他场景的「不重派」。
# 第二组覆盖不含「回执」二字、改说「首行」的复述（如「首行不符时重派一次」）。
RECEIPT_RESTATEMENT = re.compile(
    r"回执[^。\n]*?(重派一次|不重派)|(重派一次|不重派)[^。\n]*?回执"
    r"|首行[^。\n]*?(重派一次|不重派)|(重派一次|不重派)[^。\n]*?首行"
)
# effort 回退与门禁放行条件原文只在契约「Codex effort 回退与门禁」节（HAE-22）。
EFFORT_REF = "effort 回退与门禁放行条件以契约「Codex effort 回退与门禁」节为准"
EFFORT_RESTATEMENT = ("accepted_request_evidence", "最初被拒的 high 请求", "不得猜相邻")
# 入口侧复述特征：契约原文特征 + 回退两级顺序 / effective_effort 记录句的措辞。
EFFORT_ENTRY_RESTATEMENT = EFFORT_RESTATEMENT + (
    "effective_effort", "两级回退", "再省略", "省略 `reasoning_effort`", "省略后记录",
)
EFFORT_ENTRIES = (
    "sdflow-done", "sdflow-adr", "sdflow-architecture", "sdflow-devenv",
    "sdflow-implement", "sdflow-spec-review", "sdflow-code-review", "sdflow-roadmap",
)
# 入口特有门禁档位字面（按入口分别断言；没有门禁档位的入口不列）。
EFFORT_GATE_LITERAL = {
    "sdflow-done": "请求 effort 为 `low` 或 `medium` 时派发前拒绝",
    "sdflow-adr": "请求 effort 不低于 high",
    "sdflow-architecture": "high` 或更高",
    "sdflow-devenv": "不低于 high",
    "sdflow-spec-review": "MUST NOT 以低于 high 的 effort 执行",
    "sdflow-code-review": "MUST NOT 以低于 high 的 effort 执行",
}
# 有写副作用的入口
WRITE_ENTRIES = ("sdflow-implement", "sdflow-done", "sdflow-adr")
# 只读入口
READ_ONLY_ENTRIES = (
    "sdflow-spec-review",
    "sdflow-code-review",
    "sdflow-roadmap",
    "sdflow-architecture",
    "sdflow-devenv",
)


def _t(path) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _skill(name: str) -> str:
    return _t(f"{name}/SKILL.md")


def _receipt_section(skill: str) -> str:
    """截出「回执与失败出口」那条列表项：从标题行起，到下一个顶格行为止（缩进子项算本条）。"""
    t = _skill(skill)
    assert "**回执与失败出口**" in t, skill
    lines = ("**回执与失败出口**" + t.split("**回执与失败出口**", 1)[1]).splitlines()
    kept = [lines[0]]
    for line in lines[1:]:
        if line.strip() and not line.startswith(" "):
            break
        kept.append(line)
    return "\n".join(kept)


# ── 契约：通则承载与前缀文件 ─────────────────────────────────────────

def test_contract_has_carriage_section_with_full_rules():
    t = _t("sdflow-init/assets/workflow/subagent-dispatch-contract.md")
    assert SECTION in t
    body = t.split(SECTION, 1)[1].split("\n## ", 1)[0]
    for token in (
        READ_INSTRUCTION,
        "readlink",
        "sdflow-spec/agents/",
        "not-carried",
        "prefix-principles.md",
        "prefix-<layer>-np.md",
        "prefix-<layer>.md",
        "mktemp -d",
        "basename",
        "git check-ignore -q",
        "sdflow-init update",
        "--layer principles --out-dir",
        "prefix_path",
        "prefix_version",
        "result-invalid-or-unattributed",
        RECEIPT_WRITE_NOTE,
        "MUST NOT 写出期望",
        "不证明读完全文",
        "剥掉",
    ):
        assert token in body, f"契约「通则承载与前缀文件」节缺：{token}"
    for parent in {v.replace("{name}", "<name>") for v in DISPATCH_ENTRIES.values()}:
        assert parent in body, f"契约缺 run 目录父目录：{parent}"
    # 只读重派一次 / 写入任务不重派 两条都在
    assert "重派一次" in body and "不重派" in body


# ── 两评审 SKILL：段① 改为读文件 ─────────────────────────────────────

@pytest.mark.parametrize("skill,layer", REVIEW_SKILLS.items())
def test_review_skill_writes_prefix_files_and_reads_them(skill, layer):
    t = _skill(skill)
    for cmd in (
        f"render-review-prefix.sh --layer {layer} --out-dir",
        f"render-review-prefix.sh --layer {layer} --no-principles --out-dir",
        "render-review-prefix.sh --layer principles --out-dir",
    ):
        assert cmd in t, f"{skill} 缺渲染命令：{cmd}"
    assert READ_INSTRUCTION in t
    assert "prefix-version" in t
    assert "MUST NOT 写出期望" in t


@pytest.mark.parametrize("skill", REVIEW_SKILLS)
def test_review_skill_does_not_paste_prefix_into_prompt(skill):
    t = _skill(skill)
    for stale in ("stdout 原文整体", "作为 dispatch prompt 的开头", "段①已含四条通则原文"):
        assert stale not in t, f"{skill} 仍保留旧的贴 stdout 措辞：{stale}"


@pytest.mark.parametrize("skill", REVIEW_SKILLS)
def test_review_run_dir_is_created_in_step_zero_and_voice_reuses_it(skill):
    t = _skill(skill)
    step0, rest = t.split("## 第零步", 1)[1].split("## 第一步", 1)
    assert "mktemp -d" in step0, "run 目录占坑必须在第零步，不在第一步之后"
    assert "git check-ignore -q" in step0
    assert "$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX" in step0
    # voice 协议复用同一个 run 目录，不再另建
    voice = t.split("## outside-voice helper 调用协议", 1)[1]
    assert "复用第零步" in voice
    assert "本轮**起手先占一个 run 目录**" not in voice


@pytest.mark.parametrize("skill", REVIEW_SKILLS)
def test_review_selects_variant_by_carrier(skill):
    t = _skill(skill)
    for token in ("readlink", "sdflow-spec/agents/", "-np", "not-carried", "prefix_path", "prefix_version"):
        assert token in t, f"{skill} 缺承载判定/变体选用锚：{token}"
    assert "result-invalid-or-unattributed" in t
    assert RECEIPT_REF in t


# ── 八个派发入口：run 目录、父目录、记录字段 ───────────────────────────

@pytest.mark.parametrize("skill,parent", DISPATCH_ENTRIES.items())
def test_dispatch_entry_declares_parent_and_references_contract(skill, parent):
    # 契约节持有全文；非评审入口的 SKILL 只声明父目录并引用契约节，不再复制命令与三段式。
    t = _skill(skill)
    assert parent in t, f"{skill} 缺 run 目录父目录：{parent}"
    assert "通则承载与前缀文件" in t
    if skill not in REVIEW_SKILLS:
        for copied in ("mktemp -d", "git check-ignore -q", "--layer principles --out-dir"):
            assert copied not in t, f"{skill} 重复了契约该节的内容：{copied}"


@pytest.mark.parametrize("skill", WRITE_ENTRIES + READ_ONLY_ENTRIES)
def test_receipt_rule_is_referenced_not_restated(skill):
    # HAE-22：入口含引用句，且不含「只读重派一次 / 写入不重派」原文。
    t = _skill(skill)
    assert RECEIPT_REF in t, f"{skill} 缺回执规则引用句"
    hits = [m.group(0) for m in RECEIPT_RESTATEMENT.finditer(t)]
    assert not hits, f"{skill} 仍复述回执规则原文：{hits}"
    assert RECEIPT_WRITE_NOTE not in t, f"{skill} 复述了契约的回执标注句"


def test_receipt_restatement_pattern_is_scoped_to_receipt_context():
    assert RECEIPT_RESTATEMENT.search("回执不符时，同一镜重派一次；写入任务不重派")
    assert RECEIPT_RESTATEMENT.search("同一任务重派一次，再不符按回执失败处理")
    assert not RECEIPT_RESTATEMENT.search("容量满载时等待，被停的写入任务不重派。")
    assert not RECEIPT_RESTATEMENT.search("回执不符的重派规则以契约为准。其余失败路径同一镜重派一次。")
    # 不含「回执」二字的复述形态
    assert RECEIPT_RESTATEMENT.search("结果首行与前缀文件首行不符时，同一镜重派一次")
    assert RECEIPT_RESTATEMENT.search("同一任务重派一次，再不符按首行缺失处理")
    assert RECEIPT_RESTATEMENT.search("首行不符的写入任务不重派")
    # 合法引用句：只说首行原样 / 比对，不带重派规则
    assert not RECEIPT_RESTATEMENT.search("子代理**把文件首行原样作为结果首行**，主 session 比对回执；prompt MUST NOT 写出期望版本值。")
    assert not RECEIPT_RESTATEMENT.search("结果首行缺失或不符 → 记 `result-invalid-or-unattributed`。其余失败路径同一镜重派一次。")


def test_receipt_rule_original_lives_in_contract():
    body = _t("sdflow-init/assets/workflow/subagent-dispatch-contract.md")
    sub = body.split("### 读文件指令与回执", 1)[1].split("\n### ", 1)[0]
    assert "同一任务重派一次" in sub and "不重派" in sub and RECEIPT_WRITE_NOTE in sub


@pytest.mark.parametrize("skill", EFFORT_ENTRIES)
def test_effort_fallback_is_referenced_not_restated(skill):
    t = _skill(skill)
    assert EFFORT_REF in t, f"{skill} 缺 effort 回退引用句"
    for token in EFFORT_ENTRY_RESTATEMENT:
        assert token not in t, f"{skill} 复述了契约 effort 回退原文：{token}"
    # 入口特有的门禁档位保留在入口
    if skill in EFFORT_GATE_LITERAL:
        assert EFFORT_GATE_LITERAL[skill] in t, f"{skill} 丢了入口门禁档位句"


def test_effort_fallback_original_lives_in_contract():
    body = _t("sdflow-init/assets/workflow/subagent-dispatch-contract.md")
    sub = body.split("## Codex effort 回退与门禁", 1)[1].split("\n## ", 1)[0]
    for token in EFFORT_RESTATEMENT:
        assert token in sub, token
    # main 上各入口的 effort 回退正向断言，搬走后在契约侧逐条守住
    for token in (
        "canonical 默认",            # 两级回退第一级（spec-review/code-review/roadmap 原文）
        "省略 `reasoning_effort`",    # 两级回退第二级（done/implement/spec-review 原文）
        "同一 model、任务、prompt 和 runner",  # 回退时的派发身份
        "不得改变 model、任务、prompt、runner 或完整派发任务清单",
        "此时 `effective_effort=unknown` 可以放行，但必须显著披露实际值未获证明。",  # done/implement 原文
        "省略 effort 后记录 `effective_effort=unknown`，不得写成已证明的 high；",
        "不得写成已证明的 high",       # implement 原文
        "实际低于 high 时不得放行",    # done 原文：已知 low/medium 不放行
        "`requested_effort`", "`accepted_request_evidence`", "`effective_effort`", "`fallback_reason`",
    ):
        assert token in sub, token
    # 两级顺序：canonical 默认在前，省略在后
    assert sub.index("canonical 默认") < sub.index("省略 `reasoning_effort`")


def test_adr_audit_failure_exit_is_entry_specific():
    # audit 再不符的失败路径是入口特有出口：该批记为未完成，且不进基线对比
    t = _receipt_section("sdflow-adr")
    assert "该批记为未完成" in t
    assert "不计入基线对比" in t


def test_done_and_implement_strip_receipt_before_consuming_result():
    # 结果消费方核对（tasks 3.2）：implementer 状态词在结果首行、verify 的 PASS/FAIL 在末行；
    # 回执占首行，故状态解析之前主 session 必须先剥掉回执行。
    impl = _skill("sdflow-implement")
    assert "先剥掉回执行" in impl
    done = _skill("sdflow-done")
    assert "先剥掉回执行" in done


# ── 旧措辞：不得再要求把通则原文复制进 prompt ─────────────────────────

# 一行里同时出现「通则」字样与「原文携带 / 整段复制」类指令即视为旧措辞。
_PRINCIPLES_WORDS = ("四条通则", "这四条", "sdflow:principles")
_COPY_WORDS = ("原文携带", "原文带上", "原文带这", "原文整段", "整段复制")


def _stale_lines(path: Path):
    """只拦已知旧句式：「通则」字样与复制类词出现在同一行。
    换了措辞的内联要求（例如不含上述词的“把通则贴进 prompt”）抓不到。
    """
    out = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if any(w in line for w in _PRINCIPLES_WORDS) and any(w in line for w in _COPY_WORDS):
            out.append((i, line.strip()[:80]))
    return out


def _top_skills():
    return sorted(p for p in ROOT.glob("sdflow-*/SKILL.md"))


def test_no_dispatch_text_requires_inlining_principles():
    files = [
        *_top_skills(),
        ROOT / "sdflow-init/assets/hack/skill-principles.md",
        ROOT / "sdflow-init/assets/snippets/principles-project.md",
        ROOT / "sdflow-init/assets/snippets/claude-section.md",
        ROOT / "sdflow-init/assets/snippets/broad-mirrors.md",
        ROOT / "sdflow-init/assets/workflow/workflow.md",
        ROOT / "sdflow-init/assets/workflow/WORKFLOW-GUIDE.md",
        ROOT / "sdflow-spec/references/delegation-protocol.md",
        ROOT / "sdflow-adr/references/sync-prompt.md",
        ROOT / "sdflow-adr/references/audit-prompt.md",
        ROOT / "CLAUDE.md",
        ROOT / "AGENTS.md",
        *sorted((ROOT / "sdflow-spec/agents").glob("*.md")),
    ]
    bad = {str(f.relative_to(ROOT)): _stale_lines(f) for f in files if f.exists() and _stale_lines(f)}
    assert not bad, f"仍有「把通则原文复制进 prompt」类指令：{bad}"


def test_adr_prompt_templates_do_not_embed_principles():
    for ref in ("sync-prompt.md", "audit-prompt.md"):
        t = _t(f"sdflow-adr/references/{ref}")
        assert "四条通则（所有 sdflow skill 共用" not in t, f"{ref} 仍内联通则块"
        assert "sdflow:principles" not in t


def test_signal_authority_and_checklist_carry_sentences_are_kept():
    # 这些「原文携带」指信号权威表 / Fowler 清单 / TDD 规则，不是通则，保留不动。
    impl = _skill("sdflow-implement")
    for token in (
        "**原文携带**，非可省的 prose 叮嘱",
        "MUST 原文携带进 implementer dispatch prompt",
        "MUST 原文携带进 Standards 轴 dispatch prompt",
        "fix 子代理的 dispatch prompt 同样 MUST 原文携带",
    ):
        assert token in impl, f"implement SKILL 误删了保留句：{token}"


# ── 真相源：传播纪律改为承载规则 ───────────────────────────────────────

def test_skill_principles_source_states_carriage_rule():
    t = _t("sdflow-init/assets/hack/skill-principles.md")
    assert "传播纪律" in t
    for token in ("agent 定义承载", "把文件首行原样作为结果首行", "MUST NOT 内联"):
        assert token in t, f"skill 味真相源缺：{token}"


def test_project_source_states_carriage_rule():
    t = _t("sdflow-init/assets/snippets/principles-project.md")
    assert "agent 定义" in t and "读文件" in t
    assert "原文带上这四条" not in t


def test_broad_mirror_contract_item_two_follows_carriage_rule():
    t = _t("sdflow-init/assets/snippets/broad-mirrors.md")
    item2 = [ln for ln in t.splitlines() if ln.startswith("2.")]
    assert item2, "broad-mirrors.md 找不到 prompt 契约第 2 条"
    assert "原文整段复制" not in item2[0]
    assert "通则承载与前缀文件" in item2[0]


def test_delegation_protocol_uses_agent_definition_carrier():
    t = _t("sdflow-spec/references/delegation-protocol.md")
    for token in ("由 agent 定义承载", "MUST NOT 内联通则原文", "MUST NOT 改派通用子代理"):
        assert token in t, f"外派协议缺：{token}"


def test_workflow_rule_follows_new_rule():
    wf = _t("sdflow-init/assets/workflow/workflow.md")
    assert "通则由承载方提供" in wf


# 发布快照剔除 CLAUDE.md（开发期资产）⇒ 缺载体时显式 skip，完整仓里照跑
needs_human_carriers = pytest.mark.skipif(
    not (ROOT / "CLAUDE.md").exists(),
    reason="本门守本仓手写 CLAUDE.md 一节；发布 clone 不含 CLAUDE.md",
)


@needs_human_carriers
def test_hand_written_claude_section_follows_new_rule():
    claude = _t("CLAUDE.md")
    hand = claude.split("## 四条通则的托管机制", 1)[1].split("## 修改本仓库的注意", 1)[0]
    assert "- **传播**" in hand
    assert "agent 定义" in hand and "读文件" in hand
    assert "附录" in hand  # DOC-1：旧理由进附录说明


def test_html_guide_p9_follows_new_rule():
    t = _t("sdflow-init/assets/workflow/sdflow-guide.html")
    assert "prompt 必须原文携带" not in t
