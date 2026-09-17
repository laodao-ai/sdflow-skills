"""Task 3：三个评审入口的 roster、宿主参数和终态收集契约。"""
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
ENTRIES = {
    "spec": ROOT / "sdflow-spec-review/SKILL.md",
    "code": ROOT / "sdflow-code-review/SKILL.md",
    "roadmap": ROOT / "sdflow-roadmap/SKILL.md",
}
REVIEW_ENTRIES = (ENTRIES["spec"], ENTRIES["code"])
DISPATCH_HEADINGS = {
    "spec": "## 第一步：能力探针 + 规划镜头 + 完整 roster 容量分批 dispatch（广审双镜 + 领域镜 + 对抗镜 + 接地镜 + design-voice）",
    "code": "## 第二步：规划镜头 + 并行 fan-out 子代理（本项目清单）",
    "roadmap": "### 双镜派发（恒跑，不分档）",
}


def _text(entry):
    return entry.read_text(encoding="utf-8")


def _section(text, heading):
    """取 heading 到下一个同级或更高层标题，避免全文关键词假绿。"""
    start = text.index(heading)
    level = len(heading) - len(heading.lstrip("#"))
    tail = text[start + len(heading):]
    position = 0
    for line in tail.splitlines(keepends=True):
        if line.startswith("#") and len(line) - len(line.lstrip("#")) <= level:
            return text[start:start + len(heading) + position]
        position += len(line)
    return text[start:]


def _dispatch_section(name):
    return _section(_text(ENTRIES[name]), DISPATCH_HEADINGS[name])


def _tier_segment(entry):
    text = _text(entry)
    start = text.index("<!-- sdflow:tier-resolution:start ")
    end = text.index("<!-- sdflow:tier-resolution:end -->", start)
    return text[start:end]


def _failure_rows(section):
    table = _section(section, "### 故障矩阵")
    rows = []
    for line in table.splitlines():
        if line.startswith("|") and "---" not in line:
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if cells[0] != "状态 / 条件":
                rows.append(cells)
    return rows


def _failure_matrix_errors(rows):
    by_status = {row[0]: row[1:] for row in rows if len(row) == 3}
    required = {
        "子代理机制 `unavailable`": "既定",
        "探针容量满载 / 容量拒绝": "等待和有界重试",
        "容量重试耗尽": "MUST NOT 标为 `unavailable`",
        "`completed` 但缺本轮有效 `result_ref`": "旧轮结果",
        "`failed` / `interrupted` / `cancelled`": "未审待恢复",
    }
    return [
        status for status, expected in required.items()
        if status not in by_status or not any(expected in cell for cell in by_status[status])
    ]


def _dispatch_errors(section):
    required = (
        "完整派发任务清单", "容量只能改变批次", "MUST NOT 删除任务、减少镜数",
        "host=claude", "subagent_type: sdflow-effort-", "host=codex",
        "reasoning_effort", 'fork_turns: "none"', "MUST NOT 带 `subagent_type`",
    )
    retired = ("单批 dispatch", "单批全并行", "同批一条消息内", "一条消息内并行派出")
    return [
        *(f"missing:{token}" for token in required if token not in section),
        *(f"retired:{token}" for token in retired if token in section),
    ]


def _tier_errors(segment):
    required = "host≠unknown 时三 `$SDFLOW_TIER_*` 与三 `$SDFLOW_EFFORT_*` MUST 非空"
    errors = []
    if required not in segment:
        errors.append("missing:known-host-model-effort-validation")
    if "空值即回落" in segment:
        errors.append("forbidden:empty-effort-fallback")
    return errors


def _roadmap_resolution_segment():
    return _section(_text(ENTRIES["roadmap"]), "### 双镜派发（恒跑，不分档）")


def _effort_policy(segment):
    """从入口的真实校验指令解析 host 对应枚举，供行为测试执行。"""
    match = re.search(
        r"`host=claude` 时三 `\$SDFLOW_EFFORT_\*` MUST 分别精确 ∈ \{([^}]+)\}，"
        r"`host=codex` 时 MUST 分别精确 ∈ \{([^}]+)\}，"
        r"任何非空非法值 MUST 在派发前 fail-closed",
        segment,
    )
    if not match:
        raise ValueError("missing host effort validator")
    return {
        "claude": frozenset(match.group(1).split(",")),
        "codex": frozenset(match.group(2).split(",")),
    }


def _validate_efforts(segment, host, efforts):
    """执行文档规定的派发前 validator；三档必须全部非空且属于该 host 枚举。"""
    if host not in {"claude", "codex", "unknown"}:
        return False
    if host == "unknown":
        return True
    allowed = _effort_policy(segment)[host]
    return len(efforts) == 3 and all(value and value in allowed for value in efforts)


def _capability_section(name):
    text = _text(ENTRIES[name])
    if name == "spec":
        return _dispatch_section(name)
    start = text.index("5. **能力探针")
    end = text.index("## 第一步：", start)
    return text[start:end]


def _capability_errors(section):
    required = (
        "派不出/机制报错 → `subagents=\"unavailable\"`",
        "容量满载 / 容量拒绝不属于机制错误",
        "MUST NOT 写为 `subagents=\"unavailable\"` 或缩 roster",
    )
    return [f"missing:{token}" for token in required if token not in section]


def test_review_dispatch_details_use_full_roster_batches_and_native_parameters():
    """删掉详细派发段的容量、宿主分支或冷上下文参数必须红。"""
    for name in ENTRIES:
        assert not _dispatch_errors(_dispatch_section(name)), name


def test_review_dispatch_details_reject_legacy_single_batch_mutation():
    """详细派发段回灌旧单批指令时，结构守卫必须拒绝。"""
    for name in ENTRIES:
        mutated = _dispatch_section(name) + "\n单批 dispatch（一条消息内并行派出全部镜）\n"
        assert any(error.startswith("retired:") for error in _dispatch_errors(mutated))


def test_known_hosts_require_complete_model_and_effort_tiers_at_all_four_sites():
    """四站点任一已知宿主放过空 effort 都必须红。"""
    sites = (
        ROOT / "sdflow-implement/SKILL.md", ROOT / "sdflow-done/SKILL.md",
        ROOT / "sdflow-code-review/SKILL.md", ROOT / "sdflow-spec-review/SKILL.md",
    )
    required = "host≠unknown 时三 `$SDFLOW_TIER_*` 与三 `$SDFLOW_EFFORT_*` MUST 非空"
    for site in sites:
        segment = _tier_segment(site)
        assert not _tier_errors(segment), site
        mutated = segment.replace(required, "host≠unknown 时三 `$SDFLOW_TIER_*` MUST 非空")
        assert "missing:known-host-model-effort-validation" in _tier_errors(mutated)


def test_host_effort_enums_are_executed_at_all_task3_sites():
    """真实 validator：Claude 拒 ultra，Codex 接受 ultra，双方拒绝未知值。"""
    segments = [
        _tier_segment(ROOT / "sdflow-implement/SKILL.md"),
        _tier_segment(ROOT / "sdflow-done/SKILL.md"),
        _tier_segment(ROOT / "sdflow-code-review/SKILL.md"),
        _tier_segment(ROOT / "sdflow-spec-review/SKILL.md"),
        _roadmap_resolution_segment(),
    ]
    for segment in segments:
        assert not _validate_efforts(segment, "claude", ("high", "ultra", "low"))
        assert _validate_efforts(segment, "codex", ("high", "ultra", "low"))
        assert not _validate_efforts(segment, "claude", ("high", "bogus", "low"))
        assert not _validate_efforts(segment, "codex", ("high", "bogus", "low"))


def test_effort_enum_mutation_enters_real_validator():
    """删掉 Codex 的 ultra 后，执行同一个 validator 必须拒绝原本合法的三档输入。"""
    for entry in (
        ROOT / "sdflow-implement/SKILL.md", ROOT / "sdflow-done/SKILL.md",
        ROOT / "sdflow-code-review/SKILL.md", ROOT / "sdflow-spec-review/SKILL.md",
    ):
        segment = _tier_segment(entry)
        mutated = segment.replace("{low,medium,high,xhigh,max,ultra}", "{low,medium,high,xhigh,max}")
        assert not _validate_efforts(mutated, "codex", ("high", "ultra", "low"))
    roadmap = _roadmap_resolution_segment()
    mutated = roadmap.replace("{low,medium,high,xhigh,max,ultra}", "{low,medium,high,xhigh,max}")
    assert not _validate_efforts(mutated, "codex", ("high", "ultra", "low"))


@pytest.mark.parametrize("name", ("spec", "code"))
def test_capability_unavailable_is_distinct_from_capacity_exhaustion(name):
    """能力不可用可降级；容量拒绝必须等待重试，耗尽后不得伪装成不可用。"""
    section = _capability_section(name)
    assert not _capability_errors(section), name
    mutated = section.replace(
        "容量满载 / 容量拒绝不属于机制错误",
        "容量满载 / 容量拒绝属于机制错误",
    )
    assert "missing:容量满载 / 容量拒绝不属于机制错误" in _capability_errors(mutated)


@pytest.mark.parametrize("entry", ENTRIES.values(), ids=ENTRIES)
def test_failure_matrix_preserves_terminal_result_and_capacity_paths(entry):
    """每条故障路径都有不同处置；删去一项会让矩阵验证失败。"""
    rows = _failure_rows(_section(_text(entry), "## 本轮"))
    assert not _failure_matrix_errors(rows), entry
    for status in (
        "子代理机制 `unavailable`", "探针容量满载 / 容量拒绝", "容量重试耗尽",
        "`completed` 但缺本轮有效 `result_ref`", "`failed` / `interrupted` / `cancelled`",
    ):
        mutated = [row for row in rows if row[0] != status]
        assert status in _failure_matrix_errors(mutated), (entry, status)


@pytest.mark.parametrize("entry", ENTRIES.values(), ids=ENTRIES)
def test_effort_fallback_is_bounded_without_changing_dispatch_identity(entry):
    """只允许两级 effort 回退，不能换 model、prompt、runner 或缩 roster。"""
    section = _section(_text(entry), "## 本轮")
    for required in (
        "canonical 默认", "省略 `reasoning_effort`",
        "不得改变 model、任务、prompt、runner 或完整派发任务清单",
    ):
        assert required in section, (entry, required)


def test_roadmap_keeps_review_pending_when_dispatch_or_recovery_fails():
    """roadmap 双镜失败与 voice fallback 失败都不得进入收尾。"""
    text = _text(ENTRIES["roadmap"])
    section = _section(text, "## 本轮 roadmap review 派发与收集")
    assert "未审待恢复" in section
    failure_section = _section(text, "### 双镜派发失败 / voice 失败时不静默，且阻塞收尾")
    assert "未审待恢复" in failure_section
    assert "包状态为 `未审待恢复` 时" in failure_section
