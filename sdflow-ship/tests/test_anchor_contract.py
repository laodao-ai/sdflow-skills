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
    # 注：本测试对每行 .strip() 后比对——这是有意的粗筛（"字段是否被提及"），**不**覆盖列 0
    # 契约（parse_ship_gate_frontmatter 要求顶层 `ship-gate:` 键不缩进）。列敏感的可解析性验证见
    # 下方 test_producer_frontmatter_parseable，它直接从真实文件字节抽取、不 strip，真正堵住
    #「模板字面缩进导致 parser 静默判 absent」的回归（mlh-p5 cold review Finding 1）。
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


# [mlh-p5 Task4 fix, Finding 2] 从真实 SKILL.md 抽取字面 frontmatter 模板块的核心。
# 提取方式（保持可维护，锚点故意宽松/不要求列 0——若模板重新被缩进破坏，锚点仍应找到块，
# 让下面 parse 调用吃到"坏"的字面文本从而真的判 absent 并让断言变红，而不是让提取器本身
# 因为找不到锚点而以另一种方式静默跳过）：
#   1. 逐行找 `ln.strip() == "ship-gate:"` 的锚点行（HTML/prose 不会写出这个裸行，来自
#      三 SKILL 各自维护的 ship-gate frontmatter 模板，工程上唯一）；
#   2. 从锚点向上找最近一条 `ln.strip() == "---"`（块首栅栏）；
#   3. 从锚点向下找最近一条 `ln.strip() == "---"`（块尾栅栏）；
#   4. 取 [块首, 块尾] 闭区间的**原始行**（不 strip，保留列信息）拼回文本，整段喂给
#      parse_ship_gate_frontmatter——与解析器实际读文件时看到的字节完全一致。
# 一个文件可能含多个块（如 sdflow-done 的 verify PASS/FAIL 两个模板），故返回 list。
def _extract_frontmatter_blocks(text):
    lines = text.splitlines()
    blocks = []
    for i, ln in enumerate(lines):
        if ln.strip() != "ship-gate:":
            continue
        start = next((j for j in range(i - 1, -1, -1) if lines[j].strip() == "---"), None)
        end = next((j for j in range(i + 1, len(lines)) if lines[j].strip() == "---"), None)
        if start is None or end is None:
            continue
        blocks.append("\n".join(lines[start:end + 1]))
    return blocks


def test_producer_frontmatter_parseable():
    # [mlh-p5 Task4 fix, Finding 2] 用真实 SKILL.md 字节喂 parser（而非手写理想化样例字符串）——
    # 若某模板缩进破坏了 parser 要求的顶层 `ship-gate:` 列 0 契约（Finding 1 的原始 bug 形态），
    # 抽取到的块喂给 parse_ship_gate_frontmatter 会返回 ({}, None)（absent），下面
    # `field in state` 断言随之变红，真正堵住"模板字面 = parser 可读"这一不变量的回归。
    for rel, field, value_lines in PRODUCER_FRONTMATTER:
        text = (REPO / rel).read_text(encoding="utf-8")
        blocks = _extract_frontmatter_blocks(text)
        assert blocks, f"{rel} 未找到任何 ---/ship-gate:/--- 字面模板块（结构被整体改写？）"
        for value_line in value_lines:
            _, _, want_raw = value_line.partition(":")
            want_raw = want_raw.strip()
            matching = [b for b in blocks if value_line in b]
            assert matching, \
                f"{rel} 未找到声明 {value_line!r} 的模板块（字段/值漂移，或该模板块整体缺失）"
            for block in matching:
                state, err = ship_gate.parse_ship_gate_frontmatter(block)
                assert err is None, \
                    f"{rel} 声明 {value_line!r} 的模板块解析出错: {err}\n--- 抽取的原始块 ---\n{block}"
                assert field in state, (
                    f"{rel} 模板块声明 {value_line!r} 但 parse_ship_gate_frontmatter 未解析出字段 "
                    f"{field!r}（返回 state={state!r}）——模板缩进很可能破坏了 `ship-gate:` 须列 0 的契约"
                    f"\n--- 抽取的原始块 ---\n{block}"
                )
                want = ship_gate._coerce_ship_gate_value(field, want_raw)
                assert state[field] == want, \
                    f"{rel} 解析出的 {field}={state[field]!r} 与模板声明 {value_line!r} 不符"


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
