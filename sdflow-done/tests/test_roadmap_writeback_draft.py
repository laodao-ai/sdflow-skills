import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import roadmap_writeback_draft as rwd


def test_parse_prefix_real_change_name():
    # 真实归档样本：implement-mechanical-layer-hardening-p4-lens-metric-emit
    assert rwd.parse_prefix(
        "implement-mechanical-layer-hardening-p4-lens-metric-emit"
    ) == ("mechanical-layer-hardening", "4")


def test_parse_prefix_no_suffix():
    assert rwd.parse_prefix("implement-workflow-cost-optimization-p2") == (
        "workflow-cost-optimization",
        "2",
    )


def test_parse_prefix_non_matching_returns_none():
    assert rwd.parse_prefix("done-roadmap-writeback") is None
    assert rwd.parse_prefix("add-user-auth") is None
    assert rwd.parse_prefix("implement-foo") is None  # 无 -pN


def test_detect_markers_solo_line():
    text = "前言\n<!-- roadmap: mechanical-layer-hardening#4 -->\n后文"
    assert rwd.detect_markers(text) == [("mechanical-layer-hardening", "4")]


def test_detect_markers_self_ref_defense():
    # P-5: marker 串在行内 code(反引号) / 散文中 → 不误检测（本 change 自身即如此）
    prose = "- change 声明关联：一行 `<!-- roadmap: {name}#{phase} -->`（或 done --roadmap）"
    assert rwd.detect_markers(prose) == []


def test_detect_markers_inside_code_fence_ignored():
    text = "```\n<!-- roadmap: foo#1 -->\n```\n正文"
    assert rwd.detect_markers(text) == []


def test_detect_markers_indented_code_block_ignored():
    text = "正文\n    <!-- roadmap: foo#1 -->\n更多"
    assert rwd.detect_markers(text) == []


def test_detect_markers_placeholder_name_not_matched():
    # 字面占位 {name} 非 [a-z0-9-] → 不匹配
    text = "<!-- roadmap: {name}#{phase} -->"
    assert rwd.detect_markers(text) == []


def test_resolve_prefix_only():
    a = rwd.resolve_association(
        "implement-mechanical-layer-hardening-p4-x", "", "", None
    )
    assert a["roadmap"] == "mechanical-layer-hardening"
    assert a["phase"] == "4"
    assert a["source"] == "prefix"
    assert a["warnings"] == []


def test_resolve_flag_overrides_prefix_with_warning():
    a = rwd.resolve_association(
        "implement-foo-p1-x", "", "", "bar#2"
    )
    assert (a["roadmap"], a["phase"], a["source"]) == ("bar", "2", "flag")
    assert len(a["warnings"]) == 1  # foo#1(prefix) vs bar#2(flag) 不一致 warn


def test_resolve_marker_fallback_when_prefix_absent():
    proposal = "<!-- roadmap: wco#3 -->"
    a = rwd.resolve_association("done-roadmap-writeback", proposal, "", None)
    assert (a["roadmap"], a["phase"], a["source"]) == ("wco", "3", "marker")


def test_resolve_none_when_no_signal():
    assert rwd.resolve_association("done-roadmap-writeback", "散文无 marker", "", None) is None


def _write(tmp_path, name, content):
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_verify_state_good_pass(tmp_path):
    _write(tmp_path, "verify-report.md", "---\nship-gate:\n  verify: PASS\n---\n# r\n")
    assert rwd.read_verify_state(tmp_path) == ("good", "PASS")


def test_verify_state_absent_when_missing(tmp_path):
    assert rwd.read_verify_state(tmp_path) == ("absent", None)


def test_verify_state_absent_when_no_frontmatter(tmp_path):
    _write(tmp_path, "verify-report.md", "# 无 frontmatter\nPASS\n")
    assert rwd.read_verify_state(tmp_path) == ("absent", None)


def test_verify_state_malformed_unclosed(tmp_path):
    _write(tmp_path, "verify-report.md", "---\nship-gate:\n  verify: PASS\n")
    assert rwd.read_verify_state(tmp_path) == ("malformed", None)


def test_verify_state_malformed_duplicate_key(tmp_path):
    _write(tmp_path, "verify-report.md",
           "---\nverify: PASS\nverify: FAIL\n---\n")
    assert rwd.read_verify_state(tmp_path) == ("malformed", None)


def test_verify_state_malformed_bad_enum(tmp_path):
    _write(tmp_path, "verify-report.md", "---\nverify: MAYBE\n---\n")
    assert rwd.read_verify_state(tmp_path) == ("malformed", None)


def test_tasks_completion_counts(tmp_path):
    _write(tmp_path, "tasks.md", "- [x] a\n- [x] b\n- [ ] c\n普通行\n")
    assert rwd.read_tasks_completion(tmp_path) == (2, 3)


CHECKBOX_ROADMAP = (
    "- [x] 1.A.1 done item\n"
    "- [ ] 4.A.1 phase4 待办甲\n"
    "- [x] 4.C.1 phase4 已交付\n"
    "- [ ] 4.D.1 phase4 待办乙\n"
    "- [ ] 5.A.1 phase5 待办\n"
)
TABLE_ROADMAP = (
    "| **P1** · x | Leg 1 | — | ✅ 已交付 |\n"
    "| **P2** · y | Leg 2 | P0 | 🔄 |\n"
    "- 脚本：散文 bullet 无复选框\n"
)


def test_probe_format_checkbox():
    assert rwd.probe_format(CHECKBOX_ROADMAP) == "checkbox"


def test_probe_format_table_prose():
    assert rwd.probe_format(TABLE_ROADMAP) == "table-prose"


def test_locate_phase_rows_only_unchecked_of_phase():
    rows = rwd.locate_phase_rows(CHECKBOX_ROADMAP, "4")
    assert rows == ["- [ ] 4.A.1 phase4 待办甲", "- [ ] 4.D.1 phase4 待办乙"]
    # 已勾 4.C.1 不入候选; 别的 phase(1/5) 不入


def test_locate_phase_rows_empty_when_none():
    assert rwd.locate_phase_rows(CHECKBOX_ROADMAP, "9") == []


def _assoc(source="prefix", warnings=None):
    return {"roadmap": "mlh", "phase": "4", "source": source, "warnings": warnings or []}


def test_assemble_draft_checkbox_has_mechanical_anchors_and_placeholders():
    out = rwd.assemble_draft(
        _assoc(), "PASS", 5, 5, "implement-mlh-p4-x", "feat/x",
        "checkbox", ["- [ ] 4.A.1 甲"], pytest_count=39
    )
    assert "change: `implement-mlh-p4-x`" in out
    assert "verify: PASS" in out
    assert "5/5" in out
    assert "pytest: 39" in out
    assert "- [ ] 4.A.1 甲" in out  # 候选行集
    # P-1: archive/merge 占位不预填当前日期
    assert "<待归档后由人补>" in out
    assert "<待 merge 后由人补>" in out
    # P-2: 不产 per-行"建议勾"(措辞), 只列候选行集供人判
    assert "建议勾" not in out


def test_assemble_draft_table_prose_fail_loud():
    out = rwd.assemble_draft(
        _assoc(), "PASS", 3, 3, "implement-wco-p2-y", "feat/y",
        "table-prose", [], pytest_count=None
    )
    assert "fail-loud" in out or "非复选框格式" in out
    assert "pytest: N/A" in out


def test_assemble_draft_warnings_surfaced():
    out = rwd.assemble_draft(
        _assoc(source="flag", warnings=["关联不一致: prefix=a#1 vs 采纳 flag=b#2"]),
        "PASS", 1, 1, "c", "b", "checkbox", [], None
    )
    assert "关联不一致" in out


def test_assemble_draft_deterministic():
    args = (_assoc(), "PASS", 2, 2, "c", "b", "checkbox", ["- [ ] 4.A.1 甲"], 10)
    assert rwd.assemble_draft(*args) == rwd.assemble_draft(*args)  # 同输入同输出


import subprocess

SCRIPT = str(Path(__file__).resolve().parent.parent / "scripts" / "roadmap_writeback_draft.py")


def _run(root, change, extra=None):
    cmd = ["python3", SCRIPT, "--change", change, "--root", str(root), "--branch", "feat/t"]
    if extra:
        cmd += extra
    return subprocess.run(cmd, capture_output=True, text=True)


def _mk_change(root, name, verify="PASS", proposal="", tasks="- [x] a\n- [ ] b\n"):
    d = root / "openspec" / "changes" / name
    d.mkdir(parents=True)
    if verify is not None:
        (d / "verify-report.md").write_text(
            "---\nship-gate:\n  verify: %s\n---\n" % verify, encoding="utf-8")
    (d / "proposal.md").write_text(proposal, encoding="utf-8")
    (d / "tasks.md").write_text(tasks, encoding="utf-8")
    return d


def _mk_roadmap(root, name, text):
    d = root / "openspec" / "roadmaps" / name
    d.mkdir(parents=True)
    (d / "roadmap.md").write_text(text, encoding="utf-8")


def test_main_happy_checkbox(tmp_path):
    _mk_change(tmp_path, "implement-mlh-p4-x")
    _mk_roadmap(tmp_path, "mlh", CHECKBOX_ROADMAP)
    r = _run(tmp_path, "implement-mlh-p4-x")
    assert r.returncode == 0
    assert "roadmap 回填草稿" in r.stdout
    assert "- [ ] 4.A.1" in r.stdout


def test_main_no_association_returns_3(tmp_path):
    # dogfood 自指: change 名非 implement-* 前缀 + proposal 内 marker 仅在散文/行内 code
    _mk_change(tmp_path, "done-roadmap-writeback",
               proposal="轻量标记 `<!-- roadmap: {name}#{phase} -->` 兜底")
    r = _run(tmp_path, "done-roadmap-writeback")
    assert r.returncode == 3  # 无关联 → 退现状(P-5 fence-aware 未误检测)


def test_main_table_prose_fail_loud_still_exit0(tmp_path):
    _mk_change(tmp_path, "implement-wco-p2-y")
    _mk_roadmap(tmp_path, "wco", TABLE_ROADMAP)
    r = _run(tmp_path, "implement-wco-p2-y")
    assert r.returncode == 0
    assert "fail-loud" in r.stdout or "非复选框格式" in r.stdout


def test_main_malformed_board_returns_5(tmp_path):
    d = _mk_change(tmp_path, "implement-mlh-p4-z", verify=None)
    (d / "verify-report.md").write_text("---\nverify: MAYBE\n---\n", encoding="utf-8")
    _mk_roadmap(tmp_path, "mlh", CHECKBOX_ROADMAP)
    r = _run(tmp_path, "implement-mlh-p4-z")
    assert r.returncode == 5


def test_main_verify_fail_returns_6(tmp_path):
    _mk_change(tmp_path, "implement-mlh-p4-w", verify="FAIL")
    _mk_roadmap(tmp_path, "mlh", CHECKBOX_ROADMAP)
    r = _run(tmp_path, "implement-mlh-p4-w")
    assert r.returncode == 6


def test_main_board_absent_returns_4(tmp_path):
    _mk_change(tmp_path, "implement-mlh-p4-v", verify=None)  # 无 verify-report
    _mk_roadmap(tmp_path, "mlh", CHECKBOX_ROADMAP)
    r = _run(tmp_path, "implement-mlh-p4-v")
    assert r.returncode == 4
