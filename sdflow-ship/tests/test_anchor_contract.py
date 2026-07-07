import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GATE = REPO / "sdflow-ship" / "scripts" / "ship_gate.py"

sys.path.insert(0, str(GATE.parent))
import ship_gate  # noqa: E402  [mlh-p5 Task4] 直接 import 解析器，断言模板与解析器同源

# [mlh-p5 Task4] 三 producer 头部 frontmatter 契约（迁移前 inline 锚 → 迁移后 frontmatter 字段）。
# 字段名精确下划线（防 code_review vs code-review 连字符漂移）；每项列 (SKILL 相对路径,
# 字段名, 该 SKILL 模板里应出现的裸行集合——每行 "field: value" 精确 strip 等值)。
PRODUCER_FRONTMATTER = [
    ("sdflow-spec-review/SKILL.md", "design_approved", ["design_approved: true"]),
    ("sdflow-done/SKILL.md", "verify", ["verify: PASS", "verify: FAIL"]),
    ("sdflow-code-review/SKILL.md", "code_review", ["code_review: pass", "code_review: blocked"]),
]


def test_producer_frontmatter_fields():
    # 字段名 ∈ FIELD_ENUMS（精确下划线，非连字符）+ 三 SKILL 模板确实各自声明了该字段。
    for rel, field, value_lines in PRODUCER_FRONTMATTER:
        assert field in ship_gate.FIELD_ENUMS, f"{field} 不在 ship_gate.FIELD_ENUMS（读写两侧字段名漂移）"
        assert "code-review" not in ship_gate.FIELD_ENUMS, "FIELD_ENUMS 不应含连字符字段名"
        text = (REPO / rel).read_text(encoding="utf-8")
        lines = [ln.strip() for ln in text.splitlines()]
        assert "ship-gate:" in lines, f"{rel} 缺 frontmatter 顶层 `ship-gate:` 键裸行"
        for value_line in value_lines:
            assert value_line in lines, \
                f"{rel} 模板缺 frontmatter 字段裸行 {value_line!r}（迁移未完成或字段名/值漂移）"
        # 枚举值须在 FIELD_ENUMS 定义域内（双向钉死：模板值不可越出解析器承认的域）
        for value_line in value_lines:
            _, _, raw = value_line.partition(":")
            raw = raw.strip()
            coerced = ship_gate._coerce_ship_gate_value(field, raw)
            assert coerced in ship_gate.FIELD_ENUMS[field], \
                f"{rel} 模板值 {raw!r} 不在 {field} 的 FIELD_ENUMS 定义域 {ship_gate.FIELD_ENUMS[field]}"


def test_producer_frontmatter_parseable():
    # 断言 parse_ship_gate_frontmatter 真能读出三 SKILL 模板声明的字段（非只字符串巧合命中）。
    samples = {
        "design_approved": "---\nship-gate:\n  design_approved: true\n---\n",
        "verify": "---\nship-gate:\n  verify: PASS\n---\n",
        "code_review": "---\nship-gate:\n  code_review: pass\n---\n",
    }
    for field, text in samples.items():
        state, err = ship_gate.parse_ship_gate_frontmatter(text)
        assert err is None, f"{field} 样例 frontmatter 解析出错: {err}"
        assert field in state, f"{field} 样例 frontmatter 未被解析出（解析器与模板字段名脱节）"


def test_no_hyphenated_field_name_in_producer_templates():
    # [防漂移] 三 SKILL 模板不得残留旧连字符字段名（design-approved / code-review 作为
    # frontmatter 字段名，而非历史 prose 提及），杜绝下划线/连字符两套并存混淆机判。
    for rel, _field, _value_lines in PRODUCER_FRONTMATTER:
        text = (REPO / rel).read_text(encoding="utf-8")
        lines = [ln.strip() for ln in text.splitlines()]
        assert not any(ln.startswith("design-approved:") for ln in lines), \
            f"{rel} 残留连字符字段名 design-approved:（应为 design_approved:）"
        assert not any(ln.startswith("code-review:") for ln in lines), \
            f"{rel} 残留连字符字段名 code-review:（应为 code_review:）"


def test_no_inline_anchor_literal_in_producer_templates():
    # 迁移后三 SKILL 模板不应再指示 producer 写旧 inline HTML 注释锚
    # （ship_gate.py 侧仍保留 ANCHOR_* 常量以兼容归档旧报告 / 过渡期回退，属预期，不在此断言范围）。
    old_inline_anchors = [
        "<!-- ship-gate: design-approved -->",
        "<!-- ship-gate: verify=PASS -->",
        "<!-- ship-gate: verify=FAIL -->",
        "<!-- ship-gate: code-review=pass -->",
        "<!-- ship-gate: code-review=blocked -->",
    ]
    for rel, _field, _value_lines in PRODUCER_FRONTMATTER:
        text = (REPO / rel).read_text(encoding="utf-8")
        for anchor in old_inline_anchors:
            assert anchor not in text, f"{rel} 仍残留旧 inline 锚 {anchor}（迁移未完成）"


def test_frontmatter_prepend_instruction_present():
    # D8/D9: 三 SKILL 模板须明确指示「头部 prepend」而非「追加末尾」，防未来编辑把指令误写回追加式。
    for rel, _field, _value_lines in PRODUCER_FRONTMATTER:
        text = (REPO / rel).read_text(encoding="utf-8")
        assert "prepend" in text, f"{rel} 缺 prepend（头部写入）措辞，防漂移回追加末尾"


def test_no_import_yaml():
    # 零依赖不变量：frontmatter 手写 stdlib 解析，不得引入 PyYAML。
    # 用 ast 解析真实 import 语句（非裸子串）——docstring 里本就有一句「手写 stdlib，
    # 不 import yaml」的说明性注释，裸子串断言会被这句自我描述文字误判失败。
    src = GATE.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(GATE))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(alias.name.split(".")[0] == "yaml" for alias in node.names), \
                "ship_gate.py 引入了 import yaml，违反零依赖不变量"
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] != "yaml", \
                "ship_gate.py 引入了 from yaml import ...，违反零依赖不变量"


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
