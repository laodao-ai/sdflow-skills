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
        # 不用 zip(strict=True)：它要 3.10+，而 CI 下限是 3.9
        assert len(cells) == len(headers), line
        rows.append(dict(zip(headers, cells)))
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


def row_line(text, name):
    return next(ln for ln in text.splitlines() if ln.startswith("| " + name))


def test_effort_fallback_diagnostic_keeps_task_model_prompt_and_runner():
    """失败矩阵 effort-fallback 行的恢复动作须声明保留同一任务、model、prompt 与 runner。"""
    rows = _table_rows(CONTRACT.read_text(encoding="utf-8"), "## 运行诊断与恢复")
    row = next(row for row in rows if row["诊断"] == "`effort-fallback`")
    assert "保留同一任务、model、prompt 与 runner" in row["可执行恢复动作"]
    full = CONTRACT.read_text(encoding="utf-8")
    # 先定位目标句：变异点不存在时测试自身红，而不是 replace 空转后误判
    target = "、prompt 与 runner。 |"
    assert full.count(target) >= 1 and target in row_line(full, "`effort-fallback`"), "变异目标句不在 effort-fallback 行"
    mutated = full.replace(target, "、prompt。 |", 1)
    mutated_row = next(r for r in _table_rows(mutated, "## 运行诊断与恢复") if r["诊断"] == "`effort-fallback`")
    assert "runner" not in mutated_row["可执行恢复动作"]


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


TASK_NAME_RE = re.compile(r"^[a-z0-9_]+$")


def test_task_name_convention_documented_with_valid_charset_and_batch_uniqueness():
    """implement-optimize-codex-workflow-p2-pull · Task 3.3 / HAE-01：`task_name` 约定一行
    存在，字符集合法（`[a-z0-9_]`），且契约里给出的同批示例互不重复。
    """
    text = CONTRACT.read_text(encoding="utf-8")
    assert "## Codex 派发的 task_name" in text
    assert "task_name" in text
    assert "<skill>_<role>[_<n>]" in text
    assert "[a-z0-9_]" in text
    assert "agent_path=/root/<task_name>" in text

    section = text.split("## Codex 派发的 task_name", 1)[1].split("## Codex effort 回退与门禁", 1)[0]
    examples = re.findall(r"`([a-z0-9_]+)`", section)
    examples = [e for e in examples if "_" in e]  # 排除 `task_name` 本身等非示例反引号词
    assert len(examples) >= 3, examples
    for name in examples:
        assert TASK_NAME_RE.match(name), f"示例 {name!r} 字符集不合法"
    assert len(examples) == len(set(examples)), f"同批示例存在重复：{examples}"


def test_task_name_charset_mutation_is_rejected():
    """字符集校验不是空判断——注入一个含非法字符的名字必须让上面的正则断言失败。"""
    assert not TASK_NAME_RE.match("Spec-Review/Strategy")
    assert not TASK_NAME_RE.match("spec review")
    assert TASK_NAME_RE.match("spec_review_strategy")


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


# ---- Codex 结果收集（HAE-14 / HAE-15 / HAE-18）----
COLLECTION_HEADING = "## Codex 结果收集"
COLLECTION_REFERENCERS = (
    "sdflow-implement",
    "sdflow-done",
    "sdflow-roadmap",
    "sdflow-adr",
    "sdflow-architecture",
    "sdflow-devenv",
)
BARRIER_LINES = (
    ("sdflow-spec-review", "进合并去重前 MUST 先完成 outside-voice collect barrier"),
    ("sdflow-code-review", "进汇总去重前 MUST 先完成 outside-voice collect barrier"),
)


def _collection_section(text=None):
    text = CONTRACT.read_text(encoding="utf-8") if text is None else text
    assert COLLECTION_HEADING in text
    body = text.split(COLLECTION_HEADING, 1)[1]
    return body.split("\n## ", 1)[0]


def _barrier_line(skill, anchor):
    text = (ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
    lines = [ln for ln in text.splitlines() if anchor in ln]
    assert len(lines) == 1, (skill, lines)
    return lines[0]


COLLECTION_REQUIRED_TERMS = (
    "wait_agent",  # 1 同回合循环
    "list_agents",
    "date -u +%s",  # 2 单子代理计时
    "interrupt_agent",  # 3 超限处置
    "interrupted",
    "未确认停止",
    "N - 1 - A",  # 4 名额
    "send_message",
    "followup_task",
    "close_agent",
    "thread limit reached",  # 5 名额耗尽
    "等它们进入终态后重试一次",
    "不再重试",
    "需新开会话",
    "MUST NOT 结束回合",
)
# 各入口引用「Codex 结果收集」节的原句片段
COLLECTION_REFERENCE_SENTENCES = {
    "sdflow-implement": "Codex 宿主按其「Codex 结果收集」节在同一回合内收齐结果",
    "sdflow-done": "Codex 宿主按其「Codex 结果收集」节在同一回合内收齐结果",
    "sdflow-roadmap": "Codex 宿主按其「Codex 结果收集」节在同一回合内收齐结果",
    "sdflow-adr": "Codex 宿主按其「Codex 结果收集」节在同一回合内收齐结果",
    "sdflow-architecture": "Codex 宿主按其「Codex 结果收集」节在同一回合内收齐结果",
    "sdflow-devenv": "Codex 宿主按其「Codex 结果收集」节在同一回合内收齐结果",
}


def _missing_collection_terms(text=None):
    section = _collection_section(text)
    return [term for term in COLLECTION_REQUIRED_TERMS if term not in section]


def test_contract_has_codex_collection_section_with_five_points():
    assert _missing_collection_terms() == []


def test_collection_section_does_not_lock_wait_agent_return_fields():
    section = _collection_section()
    for field in ("status", "result", "agent_id", "timed_out"):
        assert f"`{field}`" not in section, field


def test_collection_section_mutation_is_rejected():
    mutated = CONTRACT.read_text(encoding="utf-8").replace("thread limit reached", "XX")
    assert "thread limit reached" in _missing_collection_terms(mutated)


def test_six_entrypoints_reference_collection_section():
    assert set(COLLECTION_REFERENCE_SENTENCES) == set(COLLECTION_REFERENCERS)
    for skill, sentence in COLLECTION_REFERENCE_SENTENCES.items():
        text = (ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
        assert sentence in text, skill
        assert "subagent-dispatch-contract.md" in text, skill


def test_implement_declares_180_minute_limit():
    text = (ROOT / "sdflow-implement/SKILL.md").read_text(encoding="utf-8")
    assert "本入口的 implementer、fix 子代理时长上限 180 分钟（要跑测试），Standards 轴与 Spec 轴按契约表 60 分钟。" in text
    assert "60 分钟（implementer" not in text


def test_review_barrier_summary_is_split_by_host():
    for skill, anchor in BARRIER_LINES:
        line = _barrier_line(skill, anchor)
        claude_side, codex_side = line.split("Codex 宿主", 1)
        assert "Claude 宿主等完成通知" in claude_side, skill
        assert "让出轮次等通知" not in codex_side, skill
        assert "等通知" not in codex_side, skill
        assert "有界 `await`" in codex_side, skill
        assert "⑥ codex-host" in codex_side, skill


# ---- 子代理时长上限 / Claude 结果收集（HAE-20 / HAE-21）----
LIMIT_HEADING = "## 子代理时长上限"
CLAUDE_COLLECTION_HEADING = "## Claude 结果收集"
RECORD_HEADING = "## 每轮任务记录"
EIGHT_ENTRIES = (
    "sdflow-spec-review",
    "sdflow-code-review",
    "sdflow-implement",
    "sdflow-done",
    "sdflow-roadmap",
    "sdflow-adr",
    "sdflow-architecture",
    "sdflow-devenv",
)
# 禁用词清单：契约不得用这些词描述"空闲阈值 / 输出文件判定"。
# 覆盖边界：只拦清单内的字面词；换一种说法描述同一判定不会被这条断言发现。
FORBIDDEN_IDLE_TERMS = (
    "空闲阈值",
    "空闲时长",
    "静默时长",
    "静默阈值",
    "无输出时长",
    "输出文件判定",
    "输出文件的修改时间",
    "输出文件未更新",
    "活动判定",
    "活动信号",
    "mtime",
    "idle",
    "stall",
)


def _section(heading, text=None):
    text = CONTRACT.read_text(encoding="utf-8") if text is None else text
    assert heading in text, heading
    return text.split(heading, 1)[1].split("\n## ", 1)[0]


def test_contract_has_time_limit_section():
    section = _section(LIMIT_HEADING)
    for term in ("60 分钟", "180 分钟", "implementer", "fix", "评审镜", "verify", "archive",
                 "更长的上限", "主 session 自己的计时"):
        assert term in section, term


def test_time_limit_section_mutation_is_rejected():
    mutated = CONTRACT.read_text(encoding="utf-8").replace("180 分钟", "XX 分钟")
    assert "180 分钟" not in _section(LIMIT_HEADING, mutated)


CLAUDE_COLLECTION_REQUIRED_TERMS = (
    "TaskStop",
    "run_in_background",
    "date +%s; sleep",
    "截止时刻",
    "闹钟任务 ID",
    "最早的截止时刻",
    "忽略",  # 任务 ID 不符的闹钟通知
    "闹钟异常重起",
    "休眠",
    "120 秒",
    "顺延",
    "interrupted",
    "超过时长上限 N 分钟",
    "未确认停止，可能仍在写入",
    "MUST NOT 重派",
    "MUST NOT 撤销其改动",
    "HAE-18",
    "停止后才到达的完成通知",
    "记账丢失",
    "按上限表中最长的一档重新计时",
    "outside-voice",
    "不起闹钟",
)


def test_contract_has_claude_collection_section_with_all_nine_rules():
    section = _section(CLAUDE_COLLECTION_HEADING)
    missing = [term for term in CLAUDE_COLLECTION_REQUIRED_TERMS if term not in section]
    assert missing == []
    numbered = re.findall(r"^(\d)\. \*\*", section, flags=re.M)
    assert numbered == [str(i) for i in range(1, 10)], numbered


def test_claude_collection_clamps_alarm_seconds_and_handles_already_finished_stop():
    section = _section(CLAUDE_COLLECTION_HEADING)
    assert "差值不足 60 时取 60" in section
    assert "任务已结束" in section
    assert "不再计入在途、不记 `interrupted`" in section


def test_done_adr_sync_interrupted_branch_does_not_revert():
    text = (ROOT / "sdflow-done/SKILL.md").read_text(encoding="utf-8")
    flow = text[text.index("## 第 1.5 步：ADR 同步"):text.index("## 第二步：产出 hand-off.md")]
    assert "子代理 interrupted（超过时长上限被停）" in flow
    assert "MUST NOT 撤销" in flow
    assert "ADR 同步超时未完成：改动保留待人工核对" in flow
    assert "/sdflow-adr sync" in flow


def test_no_entry_lists_interrupted_with_revert_for_adr_sync():
    # done、adr 正文与 sync-prompt 都不得再把 interrupted 与撤销并列
    # 空白先归一化：断言不依赖 Markdown 折行位置
    def flat(text):
        return re.sub(r"\s+", "", text)

    done = flat((ROOT / "sdflow-done/SKILL.md").read_text(encoding="utf-8"))
    adr = (ROOT / "sdflow-adr/SKILL.md").read_text(encoding="utf-8")
    prompt = flat((ROOT / "sdflow-adr/references/sync-prompt.md").read_text(encoding="utf-8"))
    assert flat("`failed`/`interrupted`/`cancelled` 一律按第 1.5 步") not in done
    assert flat("`interrupted`（超时被停）不撤销") in done
    step4 = flat(adr[adr.index("4. **任何终态后对实际改动集跑 lint**"):adr.index("5. sync **不做全目录 lint**")])
    assert flat("子代理 `interrupted`（超过时长上限被停）→ MUST NOT 撤销") in step4
    assert flat("子代理非 `completed`") not in step4
    assert flat("非 `completed` 终态") not in prompt
    assert flat("`interrupted`（超过时长上限被停）不撤销") in prompt


def test_task_record_section_has_deadline_and_alarm_id_fields():
    section = _section(RECORD_HEADING)
    assert "截止时刻" in section
    assert "闹钟任务 ID" in section


def _idle_term_hits(text):
    # 英文词按词边界匹配，避免 "install" 之类含 "stall" 的词误命中；中文词按子串匹配。
    hits = []
    for term in FORBIDDEN_IDLE_TERMS:
        if term.isascii():
            pattern = r"(?<![A-Za-z0-9_])" + re.escape(term) + r"(?![A-Za-z0-9_])"
        else:
            pattern = re.escape(term)
        if re.search(pattern, text, flags=re.I):
            hits.append(term)
    return hits


def test_contract_has_no_idle_threshold_or_output_file_judgement():
    text = CONTRACT.read_text(encoding="utf-8")
    assert _idle_term_hits(text) == []


def test_forbidden_idle_terms_check_detects_injection():
    text = CONTRACT.read_text(encoding="utf-8") + "\n按空闲阈值判定。\n"
    assert _idle_term_hits(text) == ["空闲阈值"]
    assert _idle_term_hits("the stall timer and mtime check") == ["mtime", "stall"]


def test_forbidden_idle_terms_ignore_words_that_merely_contain_a_term():
    assert _idle_term_hits("先 install 再 reinstall，idle_timeout 不算 idle") == ["idle"]
    assert _idle_term_hits("先 install 再 reinstall，installation 完成") == []


def test_codex_collection_section_points_to_claude_section_and_limit_table():
    section = _section(COLLECTION_HEADING)
    # 开头说明段：从节首到第一条编号项之前，不依赖空行分段数。
    assert "\n1. " in section, "Codex 结果收集节应有编号项"
    intro = section.split("\n1. ", 1)[0]
    assert "「Claude 结果收集」节" in intro
    assert "Claude 宿主等完成通知，不适用本节" not in section
    assert "「子代理时长上限」节" in section
    for stale in ("30 分钟", "60 分钟", "180 分钟"):
        assert stale not in section, stale


def test_eight_entrypoints_reference_limit_and_claude_collection_sections():
    for skill in EIGHT_ENTRIES:
        text = (ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
        assert "「子代理时长上限」节" in text, skill
        assert "「Claude 结果收集」节" in text, skill
        assert "subagent-dispatch-contract.md" in text, skill


# 入口声明的时长上限整句允许清单：只有 implement 入口可以写数字，其余入口引用契约上限表。
ALLOWED_LIMIT_SENTENCES = (
    "本入口的 implementer、fix 子代理时长上限 180 分钟（要跑测试），Standards 轴与 Spec 轴按契约表 60 分钟。",
)
LIMIT_LITERAL = re.compile(r"\d+\s*分钟")


def _hardcoded_limits(text, skill="sdflow-implement"):
    # 整句允许清单只对 implement 入口生效；其他入口写了同句也算硬编码
    if skill == "sdflow-implement":
        for sentence in ALLOWED_LIMIT_SENTENCES:
            text = text.replace(sentence, "")
    return LIMIT_LITERAL.findall(text)


def test_entrypoints_do_not_hardcode_default_limit():
    for skill in EIGHT_ENTRIES:
        text = (ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
        assert "时长上限取缺省" not in text, skill
        assert "缺省 30 分钟" not in text, skill
        assert _hardcoded_limits(text, skill) == [], skill


def test_hardcoded_limit_guard_rejects_injected_number_and_allows_implement_sentence():
    implement = (ROOT / "sdflow-implement/SKILL.md").read_text(encoding="utf-8")
    assert _hardcoded_limits(implement) == []
    assert _hardcoded_limits(implement + "\n子代理时长上限 60 分钟。\n") == ["60 分钟"]
    assert _hardcoded_limits("评审镜上限 90分钟") == ["90分钟"]
    # 允许句只对 implement 入口豁免，其他入口出现同句仍判硬编码
    assert _hardcoded_limits(ALLOWED_LIMIT_SENTENCES[0], "sdflow-done") != []


def test_review_barrier_summary_claude_side_mentions_alarm_fallback():
    for skill, anchor in BARRIER_LINES:
        line = _barrier_line(skill, anchor)
        claude_side = line.split("Codex 宿主", 1)[0]
        assert "Agent 子代理（含 outside-voice 的 fallback 子代理）起闹钟" in claude_side, skill
        assert "outside-voice 的后台 Bash 不起" in claude_side, skill
        assert "outside-voice 站点不起闹钟" not in claude_side, skill
        assert "「Claude 结果收集」节" in claude_side, skill


# HAE-27：被拒处理说明只写在契约一处。特征短语取说明的主语加谓语，足够独特，不会出现在其他 SKILL.md。
DENIAL_PHRASE = "权限确认可能被全局 hook 直接拒绝"
DENIAL_POINTS = ("跳过", "报告", "未完成")


def _denial_paragraph(text):
    """返回含特征短语的那一行（说明写成单行段落）；没有则返回空串。"""
    for line in text.splitlines():
        if DENIAL_PHRASE in line:
            return line
    return ""


def _skills_containing_denial_phrase(skill_texts):
    return sorted(name for name, text in skill_texts.items() if DENIAL_PHRASE in text)


def _top_level_skill_texts():
    return {
        p.parent.name: p.read_text(encoding="utf-8")
        for p in sorted(ROOT.glob("*/SKILL.md"))
    }


def test_contract_states_permission_denial_handling():
    paragraph = _denial_paragraph(CONTRACT.read_text(encoding="utf-8"))
    assert paragraph, "契约缺少被拒处理说明（说明须写成单行，_denial_paragraph 按行匹配）"
    for point in DENIAL_POINTS:
        assert point in paragraph, point


def test_top_level_skills_do_not_repeat_permission_denial_note():
    texts = _top_level_skill_texts()
    assert texts, "未发现任何顶层 SKILL.md"
    assert _skills_containing_denial_phrase(texts) == []


def test_denial_phrase_scanner_detects_injected_phrase():
    # 扫描器自检：注入特征短语后能被发现
    assert _skills_containing_denial_phrase({"x": "前文\n" + DENIAL_PHRASE + "\n"}) == ["x"]
