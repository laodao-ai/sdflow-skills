import subprocess, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
import sad_schema as S
from conftest import make_sad
SCRIPT = pathlib.Path(__file__).parent.parent / "scripts" / "sad_lint.py"

def lint(tmp_path, text):
    p = tmp_path / "sad.md"; p.write_text(text, encoding="utf-8")
    return subprocess.run([sys.executable, str(SCRIPT), "--sad", str(p)],
                          capture_output=True, text=True)

def test_pass_honest_code(tmp_path):
    r = lint(tmp_path, make_sad(assumptions=[(1, "接受")], cache=0))
    assert r.returncode == 0 and r.stdout.splitlines()[0] == S.PASS_CODE
    assert "假设计数: 1" in r.stdout

def test_missing_section_reason_code(tmp_path):
    text = make_sad().replace("## 8. 横切概念\n\nN/A — v1 无横切面\n\n", "")
    r = lint(tmp_path, text)
    assert r.returncode == 1 and "missing-section" in r.stdout and "8" in r.stdout
    assert "next-step:" in r.stdout

def test_na_without_reason(tmp_path):
    r = lint(tmp_path, make_sad().replace("N/A — v1 无横切面", "N/A"))
    assert r.returncode == 1 and "na-without-reason" in r.stdout

def test_duplicate_number_set_reconciliation(tmp_path):
    # 正文两个[假设-1] + 表 假设-1/假设-2 → 计数2==2 但集合对账拦截（REQ-5 场景逐字）
    text = make_sad(assumptions=[(1, "接受"), (2, "接受")], cache=0)
    text = text.replace("[假设-1] [假设-2]", "[假设-1] [假设-1]")
    r = lint(tmp_path, text)
    assert r.returncode == 1 and "assumption-set-mismatch" in r.stdout

def test_cache_mismatch_independent_code(tmp_path):
    r = lint(tmp_path, make_sad(assumptions=[(1, "接受")], cache=5))
    assert r.returncode == 1 and "assumption-cache-mismatch" in r.stdout

def test_quality_attr_order(tmp_path):
    r = lint(tmp_path, make_sad().replace("1. 可靠性\n2. 可维护性", "- 可靠性\n- 可维护性"))
    assert r.returncode == 1 and "quality-attr-order-broken" in r.stdout
    r2 = lint(tmp_path, make_sad().replace("2. 可维护性", "3. 可维护性"))  # 跳号
    assert r2.returncode == 1 and "quality-attr-order-broken" in r2.stdout

def test_schema_version_mismatch_not_fail_closed(tmp_path):
    r = lint(tmp_path, make_sad(schema=0))
    assert r.returncode == 1 and "schema-version-mismatch" in r.stdout   # 独立码+指引
    assert "FAIL" not in r.stderr                                        # 不与损坏共用出口

def test_contract_invariant(tmp_path):
    bad = make_sad(status="validated")  # validated 下残留 contract[draft]
    r = lint(tmp_path, bad)
    assert r.returncode == 1 and "contract-invariant-violation" in r.stdout
    ok = make_sad(status="validated").replace("contract[draft]", "contract[validated]")
    assert lint(tmp_path, ok).returncode == 0

def test_slice_branch_assertions(tmp_path):
    r = lint(tmp_path, make_sad(status="skeleton-ready", slice_section=False,
                                facts={"positioning": "answered", "external_systems": "answered",
                                       "hard_constraints": "answered"}))
    assert r.returncode == 1 and "slice-section-missing" in r.stdout
    r2 = lint(tmp_path, make_sad(status="validated", slice_section=True)
              .replace("contract[draft]", "contract[validated]"))
    assert r2.returncode == 1 and "slice-section-stale" in r2.stdout

def test_bad_input_fail_closed(tmp_path):
    r = lint(tmp_path, "no frontmatter at all\n")
    assert r.returncode == 2 and r.stderr.startswith("[sad_lint] FAIL:") and S.PASS_CODE not in r.stdout
    r2 = subprocess.run([sys.executable, str(SCRIPT), "--sad", str(tmp_path / "nope.md")],
                        capture_output=True, text=True)
    assert r2.returncode == 2 and "[sad_lint] FAIL:" in r2.stderr

def test_enum_invalid_fail_closed(tmp_path):
    r = lint(tmp_path, make_sad().replace("sad_status: draft", "sad_status: approved"))
    assert r.returncode == 2 and "approved" in r.stderr      # REQ-6 场景：stderr 区别于 reason_code

def test_crlf_bom_tolerated(tmp_path):
    text = "﻿" + make_sad(assumptions=[(1, "接受")], cache=0).replace("\n", "\r\n")
    r = lint(tmp_path, text)
    assert r.returncode == 0

def test_fence_inside_markers_not_counted(tmp_path):
    text = make_sad(extra="```\n[假设-7]\n## 11. 假节\n```\n")
    r = lint(tmp_path, text)
    assert r.returncode == 0        # fence 内标记/节锚不计

def test_non_utf8_fail_closed(tmp_path):
    p = tmp_path / "sad.md"
    p.write_bytes(b"---\nsad_schema: 1\nsad_status: draft\n---\nbad \x92 byte\n")
    r = subprocess.run([sys.executable, str(SCRIPT), "--sad", str(p)],
                        capture_output=True, text=True)
    assert r.returncode == 2
    assert r.stderr.startswith("[sad_lint] FAIL:")
    assert "structure-ok" not in r.stdout

def test_slice_pierce_set_mismatch(tmp_path):
    text = make_sad(subsystems=("采集端", "上报端"), status="skeleton-ready", slice_section=True)
    text = text.replace("- 穿越点[上报端]：§5 contract 条目", "")
    r = lint(tmp_path, text)
    assert r.returncode == 1 and "slice-pierce-set-mismatch" in r.stdout

def test_assumption_unresolved_code(tmp_path):
    text = make_sad(assumptions=[(1, "未处置")])
    r = lint(tmp_path, text)
    assert r.returncode == 1
    assert "assumption-unresolved" in r.stdout
    assert "next-step:" in r.stdout

def test_contract_invariant_other_branches_frozen_under_draft(tmp_path):
    # status=draft 但 contract[frozen]——draft/skeleton-ready ⇒ contract∈{planned,draft}
    text_a = make_sad(status="draft").replace("contract[draft]", "contract[frozen]")
    r_a = lint(tmp_path, text_a)
    assert r_a.returncode == 1 and "contract-invariant-violation" in r_a.stdout

def test_contract_invariant_other_branches_unknown_tag(tmp_path):
    # 未知 contract 标签
    text_b = make_sad(status="draft").replace("contract[draft]", "contract[bogus]")
    r_b = lint(tmp_path, text_b)
    assert r_b.returncode == 1 and "contract-invariant-violation" in r_b.stdout
