"""retest-review-fixes-and-record-preexisting：「既有问题」记录规则的共享字符串守卫。

本文件集中放该 change 涉及的 SKILL 字符串断言（后续票只往这里追加）。
断言的是 SKILL 指令里的约定字面：前缀、小节名、已移除的旧表述。
它抓不到语义是否自洽，只防字面被误删或旧表述回流。
"""
from pathlib import Path

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

def test_code_review_has_fullwidth_preexisting_prefix():
    assert "既有问题：" in _read(CODE_REVIEW)


def test_code_review_dismiss_reasons_no_longer_include_preexisting():
    offenders = [ln for ln in _read(CODE_REVIEW).splitlines()
                 if "裁掉" in ln and "未改动行既有问题" in ln]
    assert offenders == []


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
        assert "无关" in seg and "BASE-18" in seg
    assert "直接按" in report and "入池" in report
    assert "不走 BASE-18" in fold


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
    assert "180 分钟" in seg


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
    assert "无" in seg


def test_all_three_skills_use_fullwidth_preexisting_prefix_only():
    for path in (CODE_REVIEW, IMPLEMENT, DONE):
        text = _read(path)
        assert "既有问题：" in text, path
        assert "既有问题:" not in text, path
