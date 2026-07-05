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
    # SR-6: 子串断言会被"锚行带反引号"或"同行尾注"糊弄过（子串仍命中），
    # 改为逐行 strip 等值比较，并显式断言锚行本身干净（独占裸行、无反引号、无同行尾注）。
    for rel, anchors in PAIRS:
        text = (REPO / rel).read_text(encoding="utf-8")
        lines = text.splitlines()
        for a in anchors:
            assert any(line.strip() == a for line in lines), \
                f"{rel} 模板缺独占裸行锚 {a}（双向钉死破坏，或锚行未独占裸行）"
            assert "`" + a not in text and a + "`" not in text, \
                f"{rel} 锚 {a} 疑似被反引号包裹，未独占裸行"


CR_SKILL = "sdflow-code-review/SKILL.md"

def test_impl_review_exemption_token_bound_to_code_review_step():
    # [spec-review-amendment BR-5] 豁免 token 与 code-review step 名双向钉死。
    # gate 的 is_stale design 域精确式豁免 `checkpoint(impl-review)`；该 subject 由
    # sdflow-code-review 调 checkpoint-commit.sh 的 step 名 `impl-review` 产生。两者
    # 必须一致——step 改名则豁免静默失配（B2 假 REFUSE 重现且无痕），此测试届时变红报警。
    gate = GATE.read_text(encoding="utf-8")
    cr = (REPO / CR_SKILL).read_text(encoding="utf-8")
    assert 'checkpoint(impl-review)' in gate, "gate 缺 impl-review 豁免 token（B2 豁免逻辑被删？）"
    assert 'checkpoint-commit.sh impl-review' in cr, \
        "sdflow-code-review 的 checkpoint step 名与 gate 豁免 token 失配（B2 会静默回归假 REFUSE）"
