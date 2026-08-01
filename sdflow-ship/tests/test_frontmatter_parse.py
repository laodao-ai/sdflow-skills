import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from ship_gate import parse_ship_gate_frontmatter as P

def test_clean_verify_pass():
    state, err = P("---\nship-gate:\n  verify: PASS\n---\n# 报告正文\n")
    assert state == {"verify": "PASS"} and err is None

def test_clean_design_approved_bool():
    state, err = P("---\nship-gate:\n  design_approved: true\n---\n")
    assert state == {"design_approved": True} and err is None

def test_absent_no_frontmatter():          # 无首行 --- = absent（非坏）
    state, err = P("# 报告\n正文\n")
    assert state == {} and err is None

def test_body_dashes_not_frontmatter():    # D2：正文中部 --- 块不当 frontmatter
    txt = "# 报告\n\n## 综述\n\n---\nship-gate:\n  verify: PASS\n---\n正文"
    state, err = P(txt)
    assert state == {} and err is None      # 首行非 ---，absent

def test_bom_stripped():                   # D2：去 BOM
    state, err = P("﻿---\nship-gate:\n  verify: PASS\n---\n")
    assert state == {"verify": "PASS"} and err is None

def test_unclosed_frontmatter_is_absent():   # [T74] 首行 --- 无闭合 → absent（首块不成立，非坏）
    state, err = P("---\nship-gate:\n  verify: PASS\n")
    assert state == {} and err is None


def test_unclosed_frontmatter_first_line_only():
    # [T74] 首行 --- + 全文无第二个 --- → 首块不闭合 → absent（走既有无锚语义），非旧错误类别
    state, err = P("---\n随便正文，没有闭合横线\nship-gate 也不在块内\n")
    assert state == {} and err is None

def test_duplicate_field_key_error():      # D5：重复键 → 坏（不取最后一个）
    state, err = P("---\nship-gate:\n  verify: PASS\n  verify: FAIL\n---\n")
    assert err is not None and err[1] == "duplicate-key"

def test_duplicate_toplevel_key_error():   # [mlh-p5 Task5 补 Task1 遗留覆盖缺口]
    # 顶层 `ship-gate:` 键本身重复两次（非字段级重复）→ 坏，category == "duplicate-key"，
    # 且 err[0] 点名的是键名本身 "ship-gate"（与字段级重复的 err[0]=字段名区分）。
    state, err = P("---\nship-gate:\n  verify: PASS\nship-gate:\n  code_review: pass\n---\n")
    assert state == {} and err is not None
    assert err[0] == "ship-gate" and err[1] == "duplicate-key"

def test_out_of_domain_error():            # 越域
    state, err = P("---\nship-gate:\n  verify: MAYBE\n---\n")
    assert err is not None and err[0] == "verify" and err[1] == "out-of-domain"

def test_bad_bool_type_error():            # design_approved 非 bool
    state, err = P("---\nship-gate:\n  design_approved: yes\n---\n")
    assert err is not None and err[1] == "bad-type"

def test_tab_indent_error():               # tab 缩进 → 坏
    state, err = P("---\nship-gate:\n\tverify: PASS\n---\n")
    assert err is not None and err[1] == "tab-indent"

def test_crlf_stripped():                  # CRLF 值不残留 \r
    state, err = P("---\r\nship-gate:\r\n  verify: PASS\r\n---\r\n")
    assert state == {"verify": "PASS"} and err is None


# ─── [impl-review-fix] 冷主审 whole-branch findings ───────────────────────────

def test_nested_field_not_accepted():
    # [impl-review-fix FIX-1] 嵌套在 note: 下的 design_approved 不得被当直接字段接受（假过设计门）。
    # 只认 ship-gate 直接子键：深于直接层级的行是嵌套子树，跳过不扫。
    state, err = P("---\nship-gate:\n  note:\n    design_approved: true\n---\n")
    assert state == {} and err is None      # absent，不假过门
    # 同理 verify / code_review 嵌套亦不被采纳
    state, err = P("---\nship-gate:\n  note:\n    verify: PASS\n---\n")
    assert state == {} and err is None
    state, err = P("---\nship-gate:\n  note:\n    code_review: pass\n---\n")
    assert state == {} and err is None


def test_nested_deep_ignored_direct_kept():
    # [impl-review-fix FIX-1] 直接子键正常采纳，其下嵌套子树被跳过（不污染、不误坏）。
    state, err = P("---\nship-gate:\n  verify: PASS\n  note:\n    design_approved: true\n---\n")
    assert state == {"verify": "PASS"} and err is None


def test_toplevel_ship_gate_scalar_is_bad():
    # [impl-review-fix FIX-2] 顶层 ship-gate 带内联标量/inline 值 → bad-type（非 absent）。
    for scalar in ("[]", "true", "{verify: PASS}", "null"):
        state, err = P(f"---\nship-gate: {scalar}\n---\n")
        assert state == {} and err == ("ship-gate", "bad-type"), scalar


def test_toplevel_tab_indent():
    # [impl-review-fix FIX-4] tab 缩进的顶层 ship-gate: 行判 tab-indent 坏（与字段行 tab 检测对称）。
    state, err = P("---\n\tship-gate:\n  verify: PASS\n---\n")
    assert err is not None and err[1] == "tab-indent"


def test_comment_line_skipped():
    # [impl-review-fix FIX-3a] 块内独占注释行（strip 后以 # 起始）跳过，不误判 bad-type。
    state, err = P("---\nship-gate:\n  # 待复核\n  verify: PASS\n---\n")
    assert state == {"verify": "PASS"} and err is None


def test_trailing_comment_on_value():
    # [impl-review-fix FIX-3b] 值行尾部 # 注释在枚举比对前剥离。
    state, err = P("---\nship-gate:\n  verify: PASS  # confirmed\n---\n")
    assert state == {"verify": "PASS"} and err is None


def test_quoted_value_now_equivalent_to_bare_under_yq():
    # [shared-yaml-subset-parser] 取值改委托 yq 真 YAML 解析后，`verify: "PASS"` 与
    # `verify: PASS` 语义等价（真解析器天然剥引号）——旧断言 test_quoted_value_is_strict
    # 断言的「引号即坏」是手搓扫描器（不做引号剥离）的副作用，非业务不变量，随本次迁移
    # 接受为已知行为变化（design.md Compliance 段已登记）。
    state, err = P('---\nship-gate:\n  verify: "PASS"\n---\n')
    assert state == {"verify": "PASS"} and err is None


def test_second_frontmatter_block_ignored_by_design():
    # [impl-review-fix FIX-6 A1] D2「只认首块」自指免疫：首块 PASS + 正文第二块 FAIL → 读首块 PASS。
    # 有意的自指免疫权衡（报告正文可含 ship-gate frontmatter 示例块），MUST NOT 改为「第二块→fail」。
    txt = ("---\nship-gate:\n  verify: PASS\n---\n# 报告正文\n\n"
           "示例第二块：\n---\nship-gate:\n  verify: FAIL\n---\n")
    state, err = P(txt)
    assert state == {"verify": "PASS"} and err is None
