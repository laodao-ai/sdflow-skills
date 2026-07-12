import sys, pathlib, pytest
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
import sad_schema as S
from conftest import make_sad

def test_body_lines_skips_fences():
    text = "a\n```\n[假设-9]\n## 1. 目标与质量属性\n```\nb\n"
    lines = [l for _, l in S.body_lines(text)]
    assert lines == ["a", "b"]          # fence 内标记/节锚不进行流

def test_parse_frontmatter_ok():
    fm = S.parse_frontmatter(make_sad(facts={"positioning": "answered",
        "external_systems": "answered", "hard_constraints": "missing"}))
    assert fm["sad_status"] == "draft" and fm["facts"]["hard_constraints"] == "missing"

@pytest.mark.parametrize("mutate,label", [
    (lambda t: t.replace("sad_status: draft", "sad_status: draft\nsad_status: draft"), "duplicate-key"),
    (lambda t: t.replace("assumptions_open", "unknown_key"), "out-of-domain"),
    (lambda t: t.replace("sad_schema: 1", "sad_schema: one"), "bad-type"),
    (lambda t: t.replace("  positioning", "\tpositioning"), "tab-indent"),
    (lambda t: t.replace("facts:\n  positioning: missing\n", "facts: inline\n  positioning: missing\n"), "facts-inline"),
    (lambda t: t.replace("sad_status: draft", "sad_status: approved"), "enum-invalid"),
    (lambda t: t.replace("  positioning: missing", "  color: red"), "facts-unknown-subkey"),
], ids=lambda x: x if isinstance(x, str) else "")
def test_parse_frontmatter_bad_forms_fail_closed(mutate, label):
    with pytest.raises(S.SadParseError):
        S.parse_frontmatter(mutate(make_sad()))

def test_facts_key_missing_means_missing_not_crash():
    text = make_sad().replace("  hard_constraints: missing\n", "")
    fm = S.parse_frontmatter(text)
    assert fm["facts"].get("hard_constraints", "missing") == "missing"

def test_scan_assumptions_and_check():
    ok = make_sad(assumptions=[(1, "接受"), (2, "待校准")], cache=0)
    assert S.check_assumptions(ok) == []
    dup = make_sad(assumptions=[(1, "接受")],
                   extra="[假设-1] 重号内联\n")           # 内联两个1，表一行 → 集合仍相等但重号
    codes = [c for c, _ in S.check_assumptions(dup)]
    assert "assumption-set-mismatch" in codes
    unresolved = make_sad(assumptions=[(1, "未处置")])
    codes = [c for c, _ in S.check_assumptions(unresolved)]
    assert "assumption-unresolved" in codes

def test_scan_subsystems_and_pierce():
    t = make_sad(subsystems=("采集端", "上报端"), slice_section=True, status="skeleton-ready")
    assert S.scan_subsystems(t) == ["采集端", "上报端"]
    assert S.scan_pierce_refs(t) == ["采集端", "上报端"]

def test_every_reason_code_has_next_step():
    for code in ("missing-section", "na-without-reason", "assumption-set-mismatch",
                 "assumption-unresolved", "assumption-cache-mismatch",
                 "quality-attr-order-broken", "schema-version-mismatch",
                 "contract-invariant-violation", "slice-section-missing",
                 "slice-section-stale", "slice-pierce-set-mismatch"):
        assert S.REASON_NEXT_STEP[code].strip()
