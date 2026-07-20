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


# [harden-gate-git-layer Task1 · tasks 1.4] 三个 producer 的锚字段模板 MUST 逐字对齐
# design.md ADR-1 的 YAML 示例：字段名、挂载层级（顶层 `ship-gate:` 的**直接子键**，与结论
# 字段同层）、示例值形态。某处写成独立顶层键或改了字段名 ⇒ 该 producer 的锚永远读不到。
#
# [fix1 · F3-minor] 该行 MUST 从 design.md 的 ADR-1 YAML 示例**抽取**，不硬编码——「逐字对齐
# ADR-1」这句承诺的单一源就是 ADR-1 本身。硬编码时 ADR-1 改了示例值/字段名，本文件不会变红，
# 三个模板照旧对齐着一份已不存在的规格。
CHANGE_NAME = "harden-gate-git-layer"


def _design_md_path():
    """定位本 change 的 design.md——active 与 archive 两处都找（归档后路径会搬走）。

    写死 active 路径正是本仓踩过的坑：archive 之后机械门当场 FileNotFoundError 崩掉。
    """
    candidates = [REPO / "openspec" / "changes" / CHANGE_NAME / "design.md"]
    candidates += sorted(
        (REPO / "openspec" / "changes" / "archive").glob(f"*{CHANGE_NAME}*/design.md"))
    for p in candidates:
        if p.is_file():
            return p
    raise AssertionError(
        f"未找到 {CHANGE_NAME} 的 design.md（active 与 archive 均无）——锚行单一源丢失")


def _adr1_anchor_line():
    """抽 design.md ADR-1 节内 YAML 示例块里的 `reviewed_sha:` 裸行。

    有界解析（基准 5）：Markdown 章节标题 + ``` 围栏，形态数得完，故可手写。
    """
    lines = _design_md_path().read_text(encoding="utf-8").splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.strip().startswith("### ADR-1")), None)
    assert start is not None, "design.md 找不到 `### ADR-1` 节（锚行单一源丢失）"
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].startswith("### ")), len(lines))
    hits = [ln.strip() for ln in lines[start:end] if ln.strip().startswith("reviewed_sha:")]
    assert len(hits) == 1, \
        f"design.md ADR-1 节内 `reviewed_sha:` 示例行须恰好一条，实得 {len(hits)} 条：{hits}"
    return hits[0]


ADR1_ANCHOR_LINE = _adr1_anchor_line()


def test_producer_templates_declare_reviewed_sha_verbatim():
    # [fix1 · F3] 粒度 MUST 是**每个结论模板块**，不是「每文件出现过一次即可」。
    # 原实现只查文件级存在性 ⇒ 5 个结论模板块里，`verify: FAIL` 与 `code_review: blocked`
    # 两块（正是 FAIL/blocked 半场）删掉锚行也全绿——评审方实做变异证实。
    # 后果不是纸面的：负面结论块少了 reviewed_sha，producer 照模板落盘就写不出锚，
    # reader 侧 anchor-missing → UNKNOWN(6)，负面半场整个走不通。
    #
    # [fix2] 遍历范畴 MUST 是 `_extract_frontmatter_blocks` 抽出的**全部块**，不是硬编码的
    # PRODUCER_FRONTMATTER.value_lines。上一版按 value_lines 反查块，粒度只降到「每已知枚举
    # 值」——将来 producer 新增一个结论块（如 `design_approved: false`，它是 FIELD_ENUMS 里
    # 合法的目标态取值）而漏写锚行，仍然全绿，原样重演刚修掉的那个 bug。
    # 两层检查互补，缺一不可：
    #   (A) 全块遍历——**任何**块都不许漏锚（覆盖将来新增的块）；
    #   (B) value_lines 存在性——5 个已知结论块必须都在场（防某块被整体删掉而静默缩面）。
    for rel, _field, value_lines in PRODUCER_FRONTMATTER:
        text = (REPO / rel).read_text(encoding="utf-8")
        blocks = _extract_frontmatter_blocks(text)
        assert blocks, f"{rel} 未找到任何 ---/ship-gate:/--- 字面模板块（结构被整体改写？）"
        # (A) 全块遍历
        for block in blocks:
            block_lines = [ln.strip() for ln in block.splitlines()]
            assert ADR1_ANCHOR_LINE in block_lines, (
                f"{rel} 存在缺锚字段裸行 {ADR1_ANCHOR_LINE!r} 的 ship-gate 模板块"
                f"（与 design.md ADR-1 示例逐字对齐；锚 MUST 与结论字段同块同次落盘）"
                f"\n--- 抽取的原始块 ---\n{block}"
            )
        # (B) 已知结论块存在性
        for value_line in value_lines:
            assert any(value_line in b for b in blocks), \
                f"{rel} 未找到声明 {value_line!r} 的 frontmatter 模板块"


def test_producer_anchor_is_direct_child_of_ship_gate():
    # 列敏感验证：抽真实字节的模板块喂 parser——锚若被挂成独立顶层键 / 嵌套更深一层，
    # parse 解不出 reviewed_sha，本断言变红。
    #
    # [fix2] MUST NOT 按「含锚」过滤块。旧版 `if ADR1_ANCHOR_LINE in b` 让本用例的覆盖面
    # 随守卫放宽而静默缩小：一个漏锚的块会被过滤掉、从而两个用例都不管它。改为遍历全部块，
    # 与上面的全块守卫同范畴。
    for rel, field, value_lines in PRODUCER_FRONTMATTER:
        text = (REPO / rel).read_text(encoding="utf-8")
        blocks = _extract_frontmatter_blocks(text)
        assert blocks, f"{rel} 未找到 ship-gate frontmatter 模板块"
        for block in blocks:
            state, err = ship_gate.parse_ship_gate_frontmatter(block)
            assert err is None, f"{rel} 含锚模板块解析出错: {err}\n{block}"
            assert "reviewed_sha" in state, \
                f"{rel} 锚字段未被解析出（挂载层级错？须是顶层 ship-gate: 的直接子键）\n{block}"
            assert field in state, \
                f"{rel} 锚与结论字段 {field!r} 须同层同块（ADR-1：同一次写入落盘）\n{block}"


def test_reviewed_sha_registered_in_validators():
    assert "reviewed_sha" in ship_gate.FIELD_VALIDATORS, \
        "解析器未注册 reviewed_sha —— producer 写了也读不到（新锚永远读不到）"
    assert "reviewed_sha" not in ship_gate.FIELD_ENUMS, \
        "reviewed_sha 的值域是任意 40 位 hex，不该塞进有限枚举表"


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
