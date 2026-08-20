import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GATE = REPO / "sdflow-ship" / "scripts" / "ship_gate.py"

sys.path.insert(0, str(GATE.parent))
import ship_gate  # noqa: E402  [mlh-p5 Task4] 直接 import 解析器，断言模板与解析器同源

# 〔sweep-pool-debt D3/D4〕三 producer 头部 frontmatter 契约的**载体已变**：迁移前/迁移后
# （mlh-p5）三 SKILL 都在文档里手写一份字面 `reviewed_sha: <40-hex 示例>` 模板供人照抄；
# 现在锚从「commit-sha 把手」改为「监视域内容 manifest 的 sha256 + manifest 本身」，两字段
# 由 `anchor_writeback.py` 权威计算、**MUST NOT 手写**——三 SKILL.md 不再嵌入字面锚值模板，
# 而是指示调用该脚本（`--domain` + `--set field=value`）。本文件的契约测试相应从「字面模板
# 逐字比对」改为「SKILL.md 是否正确指示调用脚本、且不再残留手写锚值模板/旧 inline 锚字面」。
PRODUCER_FRONTMATTER = [
    ("sdflow-spec-review/SKILL.md", "design_approved", "design",
     ["--set design_approved=true"]),
    ("sdflow-done/SKILL.md", "verify", "code",
     ["--set verify=PASS", "--set verify=FAIL"]),
    ("sdflow-code-review/SKILL.md", "code_review", "code",
     ["--set code_review=pass", "--set code_review=blocked"]),
]


def test_producer_invokes_anchor_writeback_script():
    # 三 producer MUST 指示调用权威写锚脚本，而非手写/手抄锚值。
    for rel, _field, _domain, _set_flags in PRODUCER_FRONTMATTER:
        text = (REPO / rel).read_text(encoding="utf-8")
        assert "anchor_writeback.py" in text, \
            f"{rel} 未指示调用 anchor_writeback.py（仍可能手写/手抄锚值）"


def test_producer_declares_correct_domain():
    # spec-review 写的是 design 域报告（spec-review-report.md）；code-review/done 写的是
    # code 域报告（各自 report），--domain 参数须与其监视域对应，否则脚本算出的锚与
    # ship_gate.py 的 is_stale 判据口径不一致（读写两侧域不同源）。
    for rel, _field, domain, _set_flags in PRODUCER_FRONTMATTER:
        text = (REPO / rel).read_text(encoding="utf-8")
        assert f"--domain {domain}" in text, \
            f"{rel} 未见 `--domain {domain}`（producer 报告归属域与脚本调用参数须一致）"


def test_producer_set_flags_cover_both_conclusion_branches():
    # 每个 producer 的正/负两种结论分支都须各自示范一次 `--set field=value` 调用，
    # 否则负面半场（FAIL/blocked）落地时无据可依、容易漏写。
    for rel, _field, _domain, set_flags in PRODUCER_FRONTMATTER:
        text = (REPO / rel).read_text(encoding="utf-8")
        for flag in set_flags:
            assert flag in text, f"{rel} 缺少 `{flag}` 的调用示范"


def test_producer_frontmatter_fields():
    # 字段名 ∈ FIELD_ENUMS（精确下划线，非连字符），且三 SKILL 确实各自在 `--set` 调用里
    # 声明了该字段（粗筛：字段是否被提及，不做列敏感可解析性验证——那类验证现由
    # `anchor_writeback.py` 的产物做实际落盘校验，SKILL.md 侧不再嵌入可供 parser 直接吃的
    # 字面 frontmatter 块）。
    for rel, field, _domain, _set_flags in PRODUCER_FRONTMATTER:
        assert field in ship_gate.FIELD_ENUMS, f"{field} 不在 ship_gate.FIELD_ENUMS（读写两侧字段名漂移）"
        assert "code-review" not in ship_gate.FIELD_ENUMS, "FIELD_ENUMS 不应含连字符字段名"
        text = (REPO / rel).read_text(encoding="utf-8")
        assert f"{field}=" in text, f"{rel} 未见 `{field}=` 的 --set 调用（字段名漂移或迁移未完成）"


def test_reviewed_sha_and_manifest_registered_in_validators():
    assert "reviewed_sha" in ship_gate.FIELD_VALIDATORS, \
        "解析器未注册 reviewed_sha —— producer 写了也读不到（新锚永远读不到）"
    assert "reviewed_manifest" in ship_gate.FIELD_VALIDATORS, \
        "解析器未注册 reviewed_manifest —— 双字段互锁的另一半读不到"
    assert "reviewed_sha" not in ship_gate.FIELD_ENUMS, \
        "reviewed_sha 的值域是 40|64 位 hex，不该塞进有限枚举表"


def test_no_hyphenated_field_name_in_producer_templates():
    # [防漂移] 三 SKILL 模板不得残留旧连字符字段名（design-approved / code-review 作为
    # frontmatter 字段名，而非历史 prose 提及），杜绝下划线/连字符两套并存混淆机判。
    for rel, _field, _domain, _set_flags in PRODUCER_FRONTMATTER:
        text = (REPO / rel).read_text(encoding="utf-8")
        lines = [ln.strip() for ln in text.splitlines()]
        assert not any(ln.startswith("design-approved:") for ln in lines), \
            f"{rel} 残留连字符字段名 design-approved:（应为 design_approved:）"
        assert not any(ln.startswith("code-review:") for ln in lines), \
            f"{rel} 残留连字符字段名 code-review:（应为 code_review:）"


def test_no_inline_anchor_literal_in_producer_templates():
    # 迁移后三 SKILL 模板不应再指示 producer 写旧 inline HTML 注释锚
    # （ship_gate.py 侧仍保留 ANCHOR_VERIFY_* 常量以兼容归档旧报告 dual-read，属预期，
    # 不在此断言范围）。
    old_inline_anchors = [
        "<!-- ship-gate: design-approved -->",
        "<!-- ship-gate: verify=PASS -->",
        "<!-- ship-gate: verify=FAIL -->",
        "<!-- ship-gate: code-review=pass -->",
        "<!-- ship-gate: code-review=blocked -->",
    ]
    for rel, _field, _domain, _set_flags in PRODUCER_FRONTMATTER:
        text = (REPO / rel).read_text(encoding="utf-8")
        for anchor in old_inline_anchors:
            assert anchor not in text, f"{rel} 仍残留旧 inline 锚 {anchor}（迁移未完成）"


def test_no_hand_written_anchor_value_template():
    # 〔sweep-pool-debt D3/D4〕MUST NOT 残留可供直接照抄的字面 40-hex commit-sha 模板值——
    # 那正是本 change 要消灭的"LLM 手抄锚值"路径。64-hex 全零值也不允许（同样是可照抄的
    # 字面锚值，即便格式已改）。
    for rel, _field, _domain, _set_flags in PRODUCER_FRONTMATTER:
        text = (REPO / rel).read_text(encoding="utf-8")
        assert "0123456789abcdef0123456789abcdef01234567" not in text, \
            f"{rel} 残留旧 40-hex 字面锚值模板（producer MUST NOT 手写锚值）"


def test_frontmatter_prepend_instruction_present():
    # D8/D9: 三 SKILL 模板须明确指示「头部 prepend」而非「追加末尾」，防未来编辑把指令误写回追加式。
    for rel, _field, _domain, _set_flags in PRODUCER_FRONTMATTER:
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


def test_anchor_writeback_script_exists_and_reuses_ship_gate_fingerprint():
    # DT-3：写锚脚本 MUST import ship_gate 复用同一份指纹实现（物理同源，防两端口径漂移）。
    script = REPO / "sdflow-ship" / "scripts" / "anchor_writeback.py"
    assert script.is_file(), "anchor_writeback.py 缺失"
    text = script.read_text(encoding="utf-8")
    assert "import ship_gate" in text
    assert "fingerprint_entries" in text
