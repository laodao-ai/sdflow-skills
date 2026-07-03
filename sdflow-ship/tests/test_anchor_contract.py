from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GATE = REPO / "sdflow-ship" / "scripts" / "ship_gate.py"

PAIRS = [
    ("sdflow-spec-review/SKILL.md", ["<!-- ship-gate: design-approved -->"]),
    ("sdflow-done/SKILL.md", ["<!-- ship-gate: verify=PASS -->",
                              "<!-- ship-gate: verify=FAIL -->"]),
    ("sdflow-code-review/SKILL.md", ["<!-- ship-gate: code-review=pass -->",
                                     "<!-- ship-gate: code-review=blocked -->"]),
]

def test_gate_header_lists_all_anchors():
    text = GATE.read_text(encoding="utf-8")
    for _, anchors in PAIRS:
        for a in anchors:
            assert a in text, f"gate 头注释缺锚行 {a}"

def test_skill_templates_carry_same_literals():
    for rel, anchors in PAIRS:
        text = (REPO / rel).read_text(encoding="utf-8")
        for a in anchors:
            assert a in text, f"{rel} 模板缺锚行 {a}（双向钉死破坏）"
