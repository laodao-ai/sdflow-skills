"""Task 4：implement/done 的本轮派发、结果门与门禁职责。"""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
IMPLEMENT = ROOT / "sdflow-implement/SKILL.md"
DONE = ROOT / "sdflow-done/SKILL.md"


def _section(text, heading):
    start = text.index(heading)
    level = len(heading) - len(heading.lstrip("#"))
    tail = text[start + len(heading):]
    offset = 0
    for line in tail.splitlines(keepends=True):
        if line.startswith("#") and len(line) - len(line.lstrip("#")) <= level:
            return text[start:start + len(heading) + offset]
        offset += len(line)
    return text[start:]


def _dispatch_errors(section, required, retired=()):
    return [
        *(f"missing:{token}" for token in required if token not in section),
        *(f"retired:{token}" for token in retired if token in section),
    ]


def _failure_matrix_errors(matrix):
    required_rows = (
        ("解析失败", "硬停。", "修复 resolver 或完整 model/effort 三档后重跑。"),
        ("容量满载 / 容量拒绝", "等待和有界重试。", "刷新终态后按完整清单分批。"),
        ("`failed` / `interrupted` / `cancelled`", "停止当前收尾。", "保留原错误并重跑对应子任务。"),
        ("坏 verify 报告", "不派 archive。", "修复 `verify-report.md` 结构与锚后重跑 verify。"),
        ("旧 archive 结果", "拒绝本轮成功。", "核验本轮 `run_id/task_id` 与 archive 对码后重跑。"),
        ("low` 或 `medium` 门禁请求", "派发前拒绝。", "将 verify effort 改为 high 或更高。"),
    )
    return [
        f"missing-or-changed:{condition}"
        for condition, disposition, recovery in required_rows
        if f"| {condition} | {disposition} | {recovery} |" not in matrix
    ]


def test_implement_dispatch_uses_native_effort_cold_context_and_full_roster():
    section = _section(IMPLEMENT.read_text(encoding="utf-8"), "## 执行模式（`mode=tickets-exec`）")
    required = (
        "完整派发任务清单", "容量只能改变批次", "MUST NOT 删除任务、减少镜数",
        "implementer", "Standards 轴", "Spec 轴", "fix 子代理",
        "host=claude", "subagent_type: sdflow-effort-", "host=codex",
        "reasoning_effort", 'fork_turns: "none"', "MUST NOT 带 `subagent_type`",
        "`completed`", "`result_ref`", "`run_id/task_id`",
    )
    assert not _dispatch_errors(section, required), _dispatch_errors(section, required)


def test_implement_dual_axis_review_dispatch_uses_host_native_parameters():
    section = _section(IMPLEMENT.read_text(encoding="utf-8"), "## 每 ticket 双轴审")
    required = (
        "`host=claude`", "subagent_type: sdflow-effort-$SDFLOW_EFFORT_MID",
        "`host=codex`", 'model: "$SDFLOW_TIER_MID"',
        'reasoning_effort: "$SDFLOW_EFFORT_MID"', 'fork_turns: "none"',
        "MUST NOT 带 `subagent_type`",
    )
    retired = ("`$SDFLOW_EFFORT_MID` 非空时均另附", "为空则不带")
    assert not _dispatch_errors(section, required, retired), _dispatch_errors(
        section, required, retired
    )


def test_review_loop_breaker_records_bug_then_continues_only_after_success():
    section = _section(IMPLEMENT.read_text(encoding="utf-8"), "## 每 ticket 双轴审")
    required = (
        "熔断只停止该 finding 的修复循环", "调用 recorder", "记入 buglist",
        "recorder 成功后", "带已登记缺陷完成", "当前 ticket 的后续动作和后续 frontier",
        "recorder 失败则 fail-loud 硬停", 'model: "$SDFLOW_TIER_STRONG"',
        'reasoning_effort: "$SDFLOW_EFFORT_STRONG"', 'fork_turns: "none"',
    )
    retired = ("进 buglist 并停上抛",)
    assert not _dispatch_errors(section, required, retired), _dispatch_errors(
        section, required, retired
    )


def test_implement_capability_and_terminal_failures_halt_current_ticket():
    text = IMPLEMENT.read_text(encoding="utf-8")
    section = _section(text, "## 本轮 implement 派发与收集")
    required = (
        "子代理机制 `unavailable`", "硬停", "容量满载 / 容量拒绝",
        "等待和有界重试", "MUST NOT 标为 `unavailable`", "`failed` / `interrupted` / `cancelled`",
        "当前票", "MUST NOT 标完成或继续下一票", "`completed` 但缺本轮有效 `result_ref`",
    )
    assert not _dispatch_errors(section, required), _dispatch_errors(section, required)


def test_done_verify_archive_require_current_completed_valid_results_before_next_step():
    text = DONE.read_text(encoding="utf-8")
    section = _section(text, "## 本轮 done 派发与收集")
    required = (
        "verify", "archive", "完整派发任务清单", "容量只能改变批次",
        "`completed`", "本轮", "`result_ref`", "verify-report.md",
        "结构", "锚", "archive 对码", "旧轮结果", "MUST NOT 继续",
        "`failed` / `interrupted` / `cancelled`",
    )
    assert not _dispatch_errors(section, required), _dispatch_errors(section, required)


def test_done_native_parameters_gate_effort_and_main_session_commit():
    text = DONE.read_text(encoding="utf-8")
    dispatch = _section(text, "## 本轮 done 派发与收集")
    required = (
        "host=claude", "subagent_type: sdflow-effort-", "host=codex",
        "reasoning_effort", 'fork_turns: "none"', "MUST NOT 带 `subagent_type`",
        "verify", "请求 effort", "low` 或 `medium`", "派发前拒绝",
        "high` 或更高", "accepted_request_evidence", "effective_effort=unknown",
        "省略 `reasoning_effort`", "最初被拒的 high 请求 MUST NOT",
        "主 session", "commit message", "hand-off", "merge 理由", "最终接受",
    )
    assert not _dispatch_errors(dispatch, required), _dispatch_errors(dispatch, required)
    retired = _section(text, "## 第四步：Git Commit")
    assert "派发 Agent" not in retired
    assert "弱档子 agent" not in retired


def test_done_commit_ownership_is_main_session_in_every_affected_section():
    text = DONE.read_text(encoding="utf-8")
    sections = {
        "opening": text[text.index("将 reconcile"):text.index("## 第零步")],
        "principles": _section(text, "## 设计原则"),
        "model premise": text[text.index("**关键前提**"):text.index("因此 model")],
        "turn cost": text[text.index("注 **turn 数"):text.index("历史取舍")],
    }
    required = "主 session 负责 commit message、提交、hand-off、merge 理由与最终接受"
    for name, section in sections.items():
        assert required in section, f"{name}: missing main-session ownership"
        assert "commit=弱档" not in section, f"{name}: retained weak commit tier"
        assert "弱档-commit" not in section, f"{name}: retained weak commit context"
        assert "commit 机械、弱档" not in section, f"{name}: retained weak commit rationale"
        assert "commit 加冲突处理" not in section, f"{name}: retained weak commit premise"


def test_done_hand_off_is_written_by_main_session_without_delegation():
    text = DONE.read_text(encoding="utf-8")
    assert "主 session 亲自写 hand-off" in text
    assert "或派中档子代理" not in text
    assert "第二步整体交给了中档子代理" not in text


def test_task4_failure_matrix_mutations_are_observable():
    """故障矩阵的每条错误路径都由同一校验器验证。"""
    section = _section(DONE.read_text(encoding="utf-8"), "## 本轮 done 派发与收集")
    matrix = section.split("### 故障矩阵", 1)[1]
    assert not _failure_matrix_errors(matrix), _failure_matrix_errors(matrix)

    mutations = (
        ("删去解析失败行", matrix.replace(
            "| 解析失败 | 硬停。 | 修复 resolver 或完整 model/effort 三档后重跑。 |\n", "", 1
        )),
        ("把容量拒绝改为继续", matrix.replace(
            "| 容量满载 / 容量拒绝 | 等待和有界重试。 | 刷新终态后按完整清单分批。 |",
            "| 容量满载 / 容量拒绝 | 继续下一步。 | 刷新终态后按完整清单分批。 |", 1
        )),
        ("把失败状态改为继续", matrix.replace(
            "| `failed` / `interrupted` / `cancelled` | 停止当前收尾。 | 保留原错误并重跑对应子任务。 |",
            "| `failed` / `interrupted` / `cancelled` | 继续下一步。 | 保留原错误并重跑对应子任务。 |", 1
        )),
        ("删去坏报告行", matrix.replace(
            "| 坏 verify 报告 | 不派 archive。 | 修复 `verify-report.md` 结构与锚后重跑 verify。 |\n", "", 1
        )),
        ("把旧结果改为接受", matrix.replace(
            "| 旧 archive 结果 | 拒绝本轮成功。 | 核验本轮 `run_id/task_id` 与 archive 对码后重跑。 |",
            "| 旧 archive 结果 | 接受本轮成功。 | 核验本轮 `run_id/task_id` 与 archive 对码后重跑。 |", 1
        )),
        ("删去低档请求行", matrix.replace(
            "| low` 或 `medium` 门禁请求 | 派发前拒绝。 | 将 verify effort 改为 high 或更高。 |\n", "", 1
        )),
    )
    for name, mutated in mutations:
        assert _failure_matrix_errors(mutated), name
