"""锚检测行锚定 + fence-aware（B4）：anchors_in / _line_scoped_hits。"""
import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
_gate_path = REPO / "sdflow-ship" / "scripts" / "ship_gate.py"
_spec = importlib.util.spec_from_file_location("ship_gate", _gate_path)
_sg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sg)   # __main__ 守卫，加载无副作用

DESIGN = "<!-- ship-gate: design-approved -->"
VPASS = "<!-- ship-gate: verify=PASS -->"
VFAIL = "<!-- ship-gate: verify=FAIL -->"


def test_inline_mention_not_hit(tmp_path):
    # B4 活体复现：锚内联在描述句中（行内反引号），非独占一行 → 不命中
    f = tmp_path / "spec-review-report.md"
    f.write_text(f"拍板后才写 `{DESIGN}`（当前未获批）。\n", encoding="utf-8")
    assert _sg.anchors_in(f, [DESIGN]) == []


def test_fenced_anchor_not_hit(tmp_path):
    # 锚独占一行但在 ``` 代码块内作文档示例 → 不命中（ADR-2）
    f = tmp_path / "spec-review-report.md"
    f.write_text(f"结论区\n```\n{DESIGN}\n```\n正文无真锚\n", encoding="utf-8")
    assert _sg.anchors_in(f, [DESIGN]) == []


def test_standalone_anchor_hit(tmp_path):
    # 独占一行的真锚（前后可有空白）→ 命中
    f = tmp_path / "spec-review-report.md"
    f.write_text(f"结论\n\n   {DESIGN}   \n", encoding="utf-8")
    assert _sg.anchors_in(f, [DESIGN]) == [DESIGN]


def test_conflict_multi_hit(tmp_path):
    # PASS 与 FAIL 各独占一行并存 → 两者皆命中（保 ADR-3 多命中）
    f = tmp_path / "verify-report.md"
    f.write_text(f"{VPASS}\n{VFAIL}\n", encoding="utf-8")
    got = _sg.anchors_in(f, [VPASS, VFAIL])
    assert VPASS in got and VFAIL in got
