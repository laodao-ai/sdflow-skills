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

def test_unterminated_is_error():          # --- 不配对 → 坏
    state, err = P("---\nship-gate:\n  verify: PASS\n")
    assert err is not None and err[1] == "unterminated"

def test_duplicate_field_key_error():      # D5：重复键 → 坏（不取最后一个）
    state, err = P("---\nship-gate:\n  verify: PASS\n  verify: FAIL\n---\n")
    assert err is not None and err[1] == "duplicate-key"

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
