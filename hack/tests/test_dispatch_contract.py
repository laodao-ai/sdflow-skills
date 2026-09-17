"""共享子代理派发契约的静态守卫。"""
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "sdflow-init/assets/workflow/subagent-dispatch-contract.md"
needs_full_repo = pytest.mark.skipif(
    not (ROOT / "openspec").is_dir(),
    reason="本门核对本仓 openspec/ ADR、CONTEXT 与 INDEX；发布 clone 不含 openspec/",
)
ENTRIES = (
    ROOT / "sdflow-spec-review/SKILL.md",
    ROOT / "sdflow-code-review/SKILL.md",
    ROOT / "sdflow-implement/SKILL.md",
    ROOT / "sdflow-done/SKILL.md",
    ROOT / "sdflow-roadmap/SKILL.md",
)

DIAGNOSTIC_COLUMNS = ("诊断", "problem", "cause", "fix", "可执行恢复动作")
DIAGNOSTICS = (
    "capacity-rejected",
    "capacity-unknown",
    "terminal-not-completed",
    "result-invalid-or-unattributed",
    "effort-fallback",
    "dispatch-other-error",
)
EFFORT_FIELD_RULES = {
    "requested_effort": {
        "required": ("配置意图",),
        "forbidden": ("本轮成功调用", "接受证据", "可信宿主实际元数据", "unknown", "effort 不支持原因", "未回退"),
    },
    "accepted_request_evidence": {
        "required": ("本轮成功调用", "接受证据"),
        "forbidden": ("配置意图", "可信宿主实际元数据", "unknown", "effort 不支持原因", "未回退"),
    },
    "effective_effort": {
        "required": ("可信宿主实际元数据", "unknown"),
        "forbidden": ("配置意图", "本轮成功调用", "接受证据", "effort 不支持原因", "未回退"),
    },
    "fallback_reason": {
        "required": ("明确的 effort 不支持原因", "未回退"),
        "forbidden": ("配置意图", "本轮成功调用", "接受证据", "可信宿主实际元数据", "unknown"),
    },
}
ENTRYPOINT_TRIGGER_TERMS = {
    "sdflow-spec-review": ("sdflow 设计审", "/sdflow-spec-review"),
    "sdflow-code-review": ("sdflow 代码审", "/sdflow-code-review"),
    "sdflow-roadmap": (
        "做一个 roadmap",
        "帮我规划 xxx",
        "分阶段实现 xxx",
        "先想清楚再动手",
        "有一堆事不知道从哪开始",
        "重构计划",
        "新项目怎么起步",
        "这个项目太大了要拆",
        "/sdflow-roadmap",
    ),
    "sdflow-implement": ("tickets 唯一管线", "/sdflow-ship", "RUN_PLAN", "CONTINUE_IMPL"),
    "sdflow-done": ("implementation is complete and reviewed", "/sdflow-done"),
}
DESCRIPTION_FORBIDDEN_PROMISES = (
    "单批一条消息内并行",
    "单批 dispatch 全部镜",
    "Steps are fixed + each runs in its own subagent",
    "commit → the light tier (mechanical)",
)


def _table_rows(text, heading):
    """读取 heading 后的首张 Markdown 表，避免用全文关键词代替表格契约。"""
    section = text.split(heading, 1)[1]
    lines = section.splitlines()
    header_index = next(i for i, line in enumerate(lines) if line.startswith("|"))
    headers = [cell.strip() for cell in lines[header_index].strip().strip("|").split("|")]
    assert set(headers)
    rows = []
    for line in lines[header_index + 2:]:
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        rows.append(dict(zip(headers, cells, strict=True)))
    return rows


def _frontmatter_description(text):
    match = re.match(r"^---\nname: .+?\ndescription: (.*?)\n---", text, re.DOTALL)
    assert match, "缺少可解析的 name/description frontmatter"
    return match.group(1)


def _effort_semantic_errors(by_name):
    errors = []
    for field, rules in EFFORT_FIELD_RULES.items():
        meaning = by_name.get(field, "")
        for phrase in rules["required"]:
            if phrase not in meaning:
                errors.append(f"{field} 缺少 {phrase}")
        for phrase in rules["forbidden"]:
            if phrase in meaning:
                errors.append(f"{field} 混入 {phrase}")
    return errors


def _description_contract_errors(entry, description):
    errors = []
    for trigger in ENTRYPOINT_TRIGGER_TERMS[entry.parent.name]:
        if trigger not in description:
            errors.append(f"缺少原触发词 {trigger!r}")
    for promise in DESCRIPTION_FORBIDDEN_PROMISES:
        if promise in description:
            errors.append(f"含已退役承诺 {promise!r}")
    return errors


def test_dispatch_contract_covers_required_runtime_guards():
    """删除容量、终态或 effort 任一关键分支时，此测试必须失败。"""
    text = CONTRACT.read_text(encoding="utf-8")

    for required in (
        "完整派发任务清单",
        "max(0, N - 1 - A)",
        "容量或活动状态未知",
        "pending",
        "running",
        "completed",
        "failed",
        "interrupted",
        "cancelled",
        "result_ref",
        "run_id",
        "task_id",
        "requested_effort",
        "accepted_request_evidence",
        "effective_effort",
        "fallback_reason",
        "最终主审核验",
        "unknown",
    ):
        assert required in text


def test_dispatch_contract_separates_capacity_and_effort_from_other_errors():
    """权限、网络、未知模型和坏 prompt 不得走两类回退。"""
    text = CONTRACT.read_text(encoding="utf-8")

    assert "仅明确的容量拒绝" in text
    assert "仅明确的 effort 参数或 model×effort 组合不支持" in text
    for non_retry_error in ("权限", "网络", "未知模型", "坏 prompt"):
        assert non_retry_error in text


def test_all_five_entrypoints_reference_the_single_canonical_contract():
    """入口保留本职角色和失败策略，公共调度语义只在 canonical 定义。"""
    for entry in ENTRIES:
        text = entry.read_text(encoding="utf-8")
        assert "subagent-dispatch-contract.md" in text, entry


def test_shared_contract_does_not_decide_whether_to_dispatch():
    """共享层只约束已决定派发之后的行为，不能夺走入口或全局规则的决定权。"""
    text = CONTRACT.read_text(encoding="utf-8")
    scope = text.split("## 每轮任务记录", 1)[0]

    assert "已经决定派发子代理之后" in scope
    assert "不决定" in scope and "是否派发" in scope


def test_entrypoint_descriptions_preserve_triggers_without_retired_promises():
    """五入口保留原触发词，只禁止两类已退役的调度/commit 承诺。"""
    for entry in ENTRIES:
        description = _frontmatter_description(entry.read_text(encoding="utf-8"))
        assert not _description_contract_errors(entry, description), entry


def test_description_retired_promise_mutations_are_rejected():
    """允许 fan-out/dispatch 职责，拒绝单批全并行和逐步子代理 commit。"""
    entries = {entry.parent.name: entry for entry in ENTRIES}
    review_entry = entries["sdflow-spec-review"]
    review_description = _frontmatter_description(review_entry.read_text(encoding="utf-8"))
    assert not _description_contract_errors(
        review_entry,
        review_description
        + " 按完整任务清单分批 parallel fan-out，并派 fresh subagent；commit 可由主 session 选 light tier 文案。",
    )

    legacy_mutations = (
        (
            review_entry,
            review_description,
            "单批一条消息内并行 fan-out，产出一份评审。主 session 在 Step1 单批 dispatch 全部镜。",
        ),
        (
            entries["sdflow-done"],
            _frontmatter_description(entries["sdflow-done"].read_text(encoding="utf-8")),
            "Steps are fixed + each runs in its own subagent, so model choice is per-step: "
            "verify → the strong tier, archive → the mid tier, commit → the light tier (mechanical).",
        ),
    )
    for entry, description, legacy_promise in legacy_mutations:
        assert _description_contract_errors(entry, description + f" {legacy_promise}"), entry


def test_diagnostics_have_complete_structured_recovery_fields():
    """六类诊断都必须能报告问题、成因、修复和下一步动作。"""
    rows = _table_rows(CONTRACT.read_text(encoding="utf-8"), "## 运行诊断与恢复")
    assert {column for row in rows for column in row} == set(DIAGNOSTIC_COLUMNS)
    by_name = {row["诊断"].strip("`"): row for row in rows}
    assert set(by_name) == set(DIAGNOSTICS)
    for diagnostic in DIAGNOSTICS:
        assert all(by_name[diagnostic][column] for column in DIAGNOSTIC_COLUMNS[1:]), diagnostic


def test_diagnostic_missing_recovery_action_mutation_is_rejected():
    """删除诊断表任一恢复动作必须使结构验证失败。"""
    text = CONTRACT.read_text(encoding="utf-8")
    mutated = text.replace(
        "| `capacity-unknown` | 不能可靠计算可派发数。 | 总上限或活动状态不可得。 | 串行执行完整清单。 | 每批只派一个尚未处理的任务。 |",
        "| `capacity-unknown` | 不能可靠计算可派发数。 | 总上限或活动状态不可得。 | 串行执行完整清单。 |  |",
    )
    rows = _table_rows(mutated, "## 运行诊断与恢复")
    row = next(row for row in rows if row["诊断"] == "`capacity-unknown`")
    assert not all(row[column] for column in DIAGNOSTIC_COLUMNS[1:])


def test_effort_fields_have_distinct_semantics():
    """请求、接受证据、实际 effort 与回退原因不可互相代替。"""
    rows = _table_rows(CONTRACT.read_text(encoding="utf-8"), "每次调用分别记录下列互不混写的字段：")
    by_name = {row["字段"].strip("`"): row["含义"] for row in rows}
    assert set(by_name) == set(EFFORT_FIELD_RULES)
    assert not _effort_semantic_errors(by_name)


def test_effort_field_cross_semantics_mutations_are_rejected():
    """每个字段混入另一个字段的专属语义时，结构化契约必须拒绝。"""
    text = CONTRACT.read_text(encoding="utf-8")
    rows = _table_rows(text, "每次调用分别记录下列互不混写的字段：")
    canonical_by_name = {row["字段"].strip("`"): row["含义"] for row in rows}
    mutations = {
        "requested_effort": ("本轮成功调用", "requested_effort 混入 本轮成功调用"),
        "accepted_request_evidence": ("配置意图", "accepted_request_evidence 混入 配置意图"),
        "effective_effort": ("配置意图", "effective_effort 混入 配置意图"),
        "fallback_reason": ("可信宿主实际元数据", "fallback_reason 混入 可信宿主实际元数据"),
    }
    for field, (foreign_phrase, expected_error) in mutations.items():
        meaning = canonical_by_name[field]
        replacement = f"{meaning} {foreign_phrase}。"
        mutated = text.replace(f"| `{field}` | {meaning} |", f"| `{field}` | {replacement} |", 1)
        rows = _table_rows(mutated, "每次调用分别记录下列互不混写的字段：")
        by_name = {row["字段"].strip("`"): row["含义"] for row in rows}
        assert all(phrase in by_name[field] for phrase in EFFORT_FIELD_RULES[field]["required"]), field
        assert expected_error in _effort_semantic_errors(by_name), field


def test_public_indexes_and_context_register_the_contract():
    """公开规则索引与说明指向同一规则。"""
    sources = (
        ROOT / "sdflow-init/assets/snippets/index-section.md",
        ROOT / "sdflow-init/assets/workflow/workflow.md",
        ROOT / "sdflow-init/assets/workflow/workflow-rules-guide.html",
    )
    for source in sources:
        assert "subagent-dispatch-contract.md" in source.read_text(encoding="utf-8"), source


@needs_full_repo
def test_full_repo_indexes_and_context_register_the_contract():
    """开发仓 ADR、上下文与 INDEX 指向同一规则。"""
    sources = (
        ROOT / "openspec/adr/0046-capacity-bounded-full-roster-dispatch-with-terminal-result-gates.md",
        ROOT / "openspec/CONTEXT.md",
        ROOT / "openspec/INDEX.md",
    )
    for source in sources:
        assert "subagent-dispatch-contract.md" in source.read_text(encoding="utf-8"), source


@needs_full_repo
def test_managed_index_matches_canonical_index_entry():
    """本仓 INDEX 必须经 updater 注入 canonical 规则条目。"""
    source_rows = _table_rows(
        (ROOT / "sdflow-init/assets/snippets/index-section.md").read_text(encoding="utf-8"),
        "## OpenSpec 工作流规则",
    )
    index_rows = _table_rows(
        (ROOT / "openspec/INDEX.md").read_text(encoding="utf-8"),
        "## OpenSpec 工作流规则",
    )
    source_contract = next(row for row in source_rows if row["名称"] == "`subagent-dispatch-contract`")
    index_contract = next((row for row in index_rows if row["名称"] == "`subagent-dispatch-contract`"), None)
    assert index_contract == source_contract
