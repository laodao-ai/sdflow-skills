"""retest-review-fixes-and-record-preexisting：「既有问题」记录规则的共享字符串守卫。

本文件集中放该 change 涉及的 SKILL 字符串断言（后续票只往这里追加）。
断言的是 SKILL 指令里的约定字面：前缀、小节名、已移除的旧表述。
它抓不到语义是否自洽，只防字面被误删或旧表述回流。
"""
from pathlib import Path

import pytest

# hack/tests 无 __init__.py，pytest 缺省 prepend 模式把本目录放进 sys.path；
# 时长上限整句与 test_dispatch_contract 共用一份常量，避免两处各写一遍后漂移。
from test_dispatch_contract import ALLOWED_LIMIT_SENTENCES_BY_SKILL

REPO = Path(__file__).resolve().parents[2]
CODE_REVIEW = REPO / "sdflow-code-review" / "SKILL.md"
IMPLEMENT = REPO / "sdflow-implement" / "SKILL.md"


def _read(path):
    return path.read_text(encoding="utf-8")


def _section(text, start_heading, end_heading):
    """取 `start_heading` 所在行到 `end_heading` 所在行之间的文本。"""
    start = text.index(start_heading)
    end = text.index(end_heading, start + 1)
    return text[start:end]


# ── sdflow-code-review ──

def _code_review_step3_preexisting():
    """Step3「既有」裁决条目：从「既有」子项到「溯源三查」子项。"""
    return _section(_read(CODE_REVIEW), "   - **既有**：", "   - **溯源三查")


def test_code_review_has_fullwidth_preexisting_prefix():
    assert "既有问题：" in _code_review_step3_preexisting()


def test_code_review_dismiss_reasons_no_longer_include_preexisting():
    # 不按行匹配：旧表述换行回流时同一行判据会漏拦
    assert "未改动行既有问题" not in _read(CODE_REVIEW)


def test_code_review_step5_records_preexisting_as_defer():
    step5 = _section(_read(CODE_REVIEW), "## 第五步", "## outside-voice helper")
    assert "「既有」" in step5 and "记为 `defer`" in step5


def test_code_review_bug_pool_not_defined_as_change_introduced():
    assert "bug 池=本" not in _read(CODE_REVIEW)


def test_code_review_report_format_has_preexisting_section():
    report_fmt = _section(_read(CODE_REVIEW), "## 报告格式", "## 模型选择")
    assert "### 既有问题" in report_fmt


# ── sdflow-implement ──

def _impl_ticket_close():
    """收尾票契约段：证据 schema（第 5 条）到「收尾票与普通票的三处执行契约差异」。"""
    return _section(_read(IMPLEMENT), "5. **证据 schema", "#### 收尾票与普通票的三处执行契约差异")


def test_implement_closing_ticket_has_preexisting_red_section_and_prefix():
    seg = _impl_ticket_close()
    assert "## 既有红测" in seg
    assert "既有问题：" in seg
    assert "<层> | <失败用例标识> | <issue id>" in seg


def test_implement_closing_ticket_recorder_failure_still_passes():
    seg = _section(_impl_ticket_close(), "6. **四类失败分诊**", "7. 🔴")
    assert "待人工补录" in seg and "照样放行" in seg


def test_implement_off_ticket_sections_have_both_paths():
    text = _read(IMPLEMENT)
    report = _section(text, "🔴 **票外发现上报**", "implementer 状态词表四值处置")
    fold = _section(text, "### 票外发现的 fold/defer", "### 完成信号双写补打")
    for seg in (report, fold):
        assert "无关" in seg and "不走 BASE-18" in seg
    assert "直接按" in report and "入池" in report
    # 按规则名引用，不按条号：条号重排会悬空
    assert "上文第 6 条" not in fold
    assert "按「既有问题记录规则」" in fold


def test_implement_no_longer_calls_postreview_gap_accepted_residual_risk():
    text = _read(IMPLEMENT)
    assert "已知且接受的残余风险" not in text
    assert "**已知且接受**的残余风险" not in text


# ── sdflow-done ──

DONE = REPO / "sdflow-done" / "SKILL.md"


def _done_verify():
    return _section(_read(DONE), "## 第一步：Verify", "### 1.1 verify-report frontmatter")


def _done_handoff():
    return _section(_read(DONE), "## 第二步：产出 hand-off.md", "### 2.1 issues scan 子步")


def test_done_verify_has_rerun_command_shape_and_base_fallbacks():
    seg = _done_verify()
    assert "--root <repo> --base <A> --head HEAD" in seg
    assert "相互独立" in seg and "环境故障 halt" in seg
    assert "收尾票报告头的 `head`" in seg
    assert "git merge-base <默认分支> HEAD" in seg
    # 报告头缺 base 时 SDFLOW_DIFF_BASE 注入回退 A
    assert "SDFLOW_DIFF_BASE=<报告头 base>" in seg and "无 `base` 时注入 A" in seg


def test_done_verify_has_both_no_rerun_phrases_and_tiering():
    seg = _done_verify()
    assert "无代码改动，未触发重跑" in seg
    assert "命中域无自动测试层，未触发重跑" in seg
    assert "`unit` 取 `full`" in seg and "其余层名一律取 `quick`" in seg
    assert "quick 取档只适用于本重跑" in seg
    assert "test-suites.domains" in seg
    for sentence in ALLOWED_LIMIT_SENTENCES_BY_SKILL["sdflow-done"]:
        assert sentence in seg


def test_done_verify_triage_has_four_branches_and_core_gap_fields():
    seg = _done_verify()
    assert "## 既有红测" in seg
    assert "按名单为空" in seg
    for part in ("逐字比对", "flaky", "修复后重跑 `/sdflow-ship`", "临时 worktree",
                 "层内全部失败用例", "base 复跑结果"):
        assert part in seg, part


def test_done_verify_triage_joint_match_base_failure_set_and_worktree_cleanup():
    seg = _done_verify()
    for part in ("(层, 失败用例标识)", "联合逐字匹配", "失败集里同样出现",
                 "git worktree add --detach", "git worktree remove --force",
                 "失败 ⇒ 按第 3 步 halt，不判既有"):
        assert part in seg, part


def test_implement_preexisting_red_row_split_rule():
    assert "第一个与最后一个 `|`" in _impl_ticket_close()


def test_done_no_longer_calls_postreview_gap_accepted_residual_risk():
    text = _read(DONE)
    assert "已知且接受的残余风险" not in text
    assert "已知且接受" not in _done_verify()


def test_done_handoff_groups_by_fullwidth_prefix():
    seg = _done_handoff()
    assert "既有问题：" in seg
    assert "本 change 延后项" in seg
    assert "发现的既有问题（非本 change 引入）" in seg
    assert "已存在" in seg and "待人工补录" in seg and "## 既有红测" in seg
    assert "verify-report" in seg and "按 issue id 去重" in seg
    assert "任一组为空写「无」" in seg


def test_all_three_skills_use_fullwidth_preexisting_prefix_only():
    for path in (CODE_REVIEW, IMPLEMENT, DONE):
        text = _read(path)
        assert "既有问题：" in text, path
        assert "既有问题:" not in text, path


# ── B39：层名级既有红测条目不在第 1 步放行 ──

def _done_triage_step(start, end):
    return _section(_done_verify(), start, end)


def test_done_triage_layer_level_entry_not_passed_at_step1():
    step1 = _done_triage_step("1. (层, 失败用例标识)", "2. 同命令复跑一次即绿")
    assert "**层名级条目不在本步放行**" in step1
    assert "转第 4 步" in step1


def test_done_triage_step4_reuses_layer_level_id_and_splits_env_halt():
    step4 = _done_triage_step("4. 其余 ⇒", "核心缺口条目 MUST 含")
    assert "命中层名级条目的" in step4 and "照录该行 issue id" in step4
    assert "层名级标识按整条层命令比" in step4
    # T470②：环境类原因 halt，其余收集报错判回归
    assert "收集报错整体失败、拿不到该用例结果 ⇒ 判本 change 回归" in step4
    assert "这些是环境类原因，其余收集报错一律按上一条判回归" in step4


def test_done_triage_records_passes_in_verify_report_list():
    seg = _done_verify()
    assert "「重跑放行」小节" in seg
    assert "不用带 id 列的表格" in seg


def test_implement_layer_level_row_and_case_level_base_check():
    seg = _impl_ticket_close()
    assert "层名行在 verify 重跑分诊中不直接放行" in seg
    # T470①：与 sdflow-done 同为用例级口径
    item6 = _section(seg, "6. **四类失败分诊**", "   - **`## 既有红测` 小节**")
    assert "在 base 的失败集里同样出现" in item6
    assert "确认改动前即红" not in item6


IMPL_SPEC = REPO / "openspec" / "specs" / "impl-orchestration" / "spec.md"
needs_specs = pytest.mark.skipif(not IMPL_SPEC.is_file(), reason="发布 clone 不含 openspec/")


@needs_specs
def test_impl_spec_triage_requirement_matches_skill():
    req = _section(_read(IMPL_SPEC), "### Requirement: verify 重跑跑红按四类分诊",
                   "### Requirement: verify 重跑分诊的判定单位与缺口内容")
    assert "层名级条目（标识列为层名的行）MUST NOT 在本步放行" in req
    assert "#### Scenario: 层名级既有红测条目不在第 1 步放行" in req
    assert "base 命令因收集报错整体失败、拿不到该用例结果 ⇒ 判本 change 回归" in req


WF_SPEC = REPO / "openspec" / "specs" / "spec-workflow" / "spec.md"


@needs_specs
def test_workflow_spec_recording_rule_and_source_issue_closure():
    text = _read(WF_SPEC)
    rule = _section(text, "### Requirement: 阶段三既有问题记入 issues 池",
                    "### Requirement: 代码评审报告单列既有问题区")
    assert "`scan --json --all`" in rule and "「已存在：<id>（已关闭）」" in rule
    assert "#### Scenario: 已关闭的同一问题不重复入池" in rule
    assert "### Requirement: sdflow-done 关闭本 change 交付的来源 issue" in text


# ── T469 / T467①：三份记录规则同口径，查重含已关闭项 ──

def _recording_rule_copies():
    return {
        "code-review": _section(_read(CODE_REVIEW), "「既有」条目的入池动作", "   - **溯源三查"),
        "implement": _section(_read(IMPLEMENT), "   - **既有问题记录规则**", "7. 🔴"),
        "done": _section(_done_verify(), "   - **既有问题记录规则**", "5. 判定"),
    }


def test_recording_rule_copies_agree_and_scan_includes_closed():
    for name, seg in _recording_rule_copies().items():
        assert "issues_v2.py scan --json --all" in seg, name
        assert "--status OPEN" not in seg, name
        assert "已关闭项不新增、不重开" in seg, name
        assert "「已存在：<id>（已关闭）」" in seg, name
        assert "待人工补录" in seg, name
        assert "既有问题：" in seg, name


# ── sdflow-done §2.3：关闭本 change 交付的来源 issue ──

def test_done_closes_delivered_source_issues_before_commit():
    text = _read(DONE)
    seg = _section(text, "### 2.3 关闭本 change 交付的来源 issue", "## 第三步")
    for part in ("「来源 issue：」行", "跳过本步", "set-status --id <ID>", "--to DONE", "--to FIXED",
                 '--evidence "{change_name} 归档"', "「已处于终态」⇒ 视为已关，跳过",
                 "未交付的 id 保持 OPEN", "`git add openspec/`"):
        assert part in seg, part
    assert text.index("### 2.3 关闭本 change 交付的来源 issue") < text.index("## 第四步")
