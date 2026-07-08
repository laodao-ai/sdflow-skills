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
