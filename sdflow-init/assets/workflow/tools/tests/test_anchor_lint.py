import subprocess, sys, importlib.util
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent          # .../workflow/tools
SCRIPT = TOOLS / "anchor_lint.py"
CONTRACT = TOOLS.parent / "lens-metric-contract.md"     # .../workflow/lens-metric-contract.md

def _mod():
    spec = importlib.util.spec_from_file_location("anchor_lint", SCRIPT)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def test_load_enums_from_real_contract():
    al = _mod()
    e = al.load_enums(CONTRACT)
    assert e["layer"] == {"spec-review", "code-review"}
    assert e["lens"] == {"domain", "adversarial", "grounding", "history", "outside-voice", "broad"}
    assert e["runner"] == {"claude", "codex", "claude-fallback"}
    assert e["sev_re"].match("致1/高2/中0/低3")
    assert not e["sev_re"].match("致1/高2/中0")

def test_load_enums_missing_block_raises(tmp_path):
    al = _mod()
    bad = tmp_path / "c.md"; bad.write_text("# no machine block here\n", encoding="utf-8")
    import pytest
    with pytest.raises(al.EnumsError):
        al.load_enums(bad)

def test_fence_outside_excludes_demo_anchor():
    al = _mod()
    text = "real\n<!-- sdflow:lens-metric v1 layer=\"x\" -->\n```\n<!-- sdflow:lens-metric v1 layer=\"demo\" -->\n```\n"
    outside = list(al.fence_outside_lines(text))
    hits = [ln for ln in outside if al.anchor_prefix(ln) == "lens-metric"]
    assert len(hits) == 1 and 'layer="x"' in hits[0]        # fence 内 demo 不计

def test_anchor_prefix_four_families():
    al = _mod()
    assert al.anchor_prefix('<!-- sdflow:hr-tg v1 hit="none" -->') == "hr-tg"
    assert al.anchor_prefix('note <!-- sdflow:hr-tg v1 --> inline') is None  # [impl-review-fix] F7 去恒真
    assert al.anchor_prefix('<!-- sdflow:step1-broad-review v1 mode="native" -->') == "step1-broad-review"
    assert al.anchor_prefix('plain text') is None

def test_version_token_boundary():                     # [impl-review-fix] F5 补测：v10 不当 v1
    al = _mod()
    assert al.anchor_prefix('<!-- sdflow:lens-metric v10 layer="x" -->') is None


def _write_config(tmp_path, body):
    d = tmp_path / "openspec"; d.mkdir(parents=True, exist_ok=True)
    (d / "config.yaml").write_text(body, encoding="utf-8"); return tmp_path

def test_metrics_file_absent_false(tmp_path):
    al = _mod(); assert al.read_metrics_enabled(tmp_path) is False        # ① 无文件

def test_metrics_no_block_false(tmp_path):                                # ② 消费仓常态
    al = _mod(); root = _write_config(tmp_path, "schema: spec-driven\ncontext: |\n  x\n")
    assert al.read_metrics_enabled(root) is False

def test_metrics_block_illegal_raises(tmp_path):                          # ③ 块在值非法
    al = _mod(); root = _write_config(tmp_path, "metrics:\n  enabled: yes\n")
    import pytest
    with pytest.raises(al.MetricsError):
        al.read_metrics_enabled(root)

def test_metrics_true(tmp_path):                                          # ④
    al = _mod(); root = _write_config(tmp_path, "metrics:\n  enabled: true\n")
    assert al.read_metrics_enabled(root) is True

def test_metrics_block_boundary(tmp_path):                                # 块边界：另一段的 enabled 不误读
    al = _mod(); root = _write_config(tmp_path, "metrics:\n  enabled: false\nother:\n  enabled: true\n")
    assert al.read_metrics_enabled(root) is False

def test_metrics_top_comment_between(tmp_path):        # [impl-review-fix] F3 补测：顶层注释/空行不误判块边界
    al = _mod(); root = _write_config(tmp_path, "metrics:\n# 注释\n  enabled: true\n")
    assert al.read_metrics_enabled(root) is True


def test_existence_missing_mandatory(tmp_path):
    al = _mod()
    report = '<!-- sdflow:hr-tg v1 hit="none" -->\n<!-- sdflow:step1-broad-review v1 mode="native" -->\n'  # 缺 outside-voice
    v = al.check_existence(report, "code-review", metrics_on=False)
    assert any(x["kind"] == "missing-anchor" and "outside-voice" in x["detail"] for x in v)

def test_existence_min_required_rows(tmp_path):
    al = _mod()
    # metrics 开：有 domain lens-metric 但缺 broad+outside-voice 行
    report = ('<!-- sdflow:outside-voice v1 site="x" -->\n<!-- sdflow:hr-tg v1 hit="none" -->\n'
              '<!-- sdflow:step1-broad-review v1 mode="native" -->\n'
              '<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" runner="claude" -->\n')
    v = al.check_existence(report, "code-review", metrics_on=True)
    kinds = {x["detail"] for x in v if x["kind"] == "missing-lens-row"}
    assert "broad" in " ".join(kinds) and "outside-voice" in " ".join(kinds)


def _lm(**kw):
    base = dict(layer="code-review", lens="domain", runner="claude",
               findings="2", 采纳="1", 裁掉="1", defer="0", 独立="0", sev="致0/高1/中0/低0")
    base.update(kw)
    return "<!-- sdflow:lens-metric v1 " + " ".join(f'{k}="{v}"' for k, v in base.items()) + " -->"

def _enums():
    return _mod().load_enums(CONTRACT)

def test_lens_enum_out_of_domain():
    al = _mod(); v = al.check_lens_metric(_lm(lens="bogus"), "code-review", _enums())
    assert any(x["field"] == "lens" for x in v)

def test_layer_must_equal_cli():
    al = _mod(); v = al.check_lens_metric(_lm(layer="spec-review"), "code-review", _enums())
    assert any(x["field"] == "layer" and "cli" in x["kind"] for x in v)

def test_bad_sev():
    al = _mod(); v = al.check_lens_metric(_lm(sev="致0/高1/中0"), "code-review", _enums())
    assert any(x["field"] == "sev" for x in v)

def test_count_not_nonneg_int():
    al = _mod()
    for bad in ("-1", "1.5", "", "三"):
        v = al.check_lens_metric(_lm(findings=bad), "code-review", _enums())
        assert any(x["field"] == "findings" for x in v), bad

def test_site_not_checked():
    al = _mod(); v = al.check_lens_metric(_lm(site="weird-value"), "code-review", _enums())
    assert v == []                                          # site 任意值合法

def test_missing_required_field():
    al = _mod()
    anchor = '<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" -->'  # 缺多字段
    v = al.check_lens_metric(anchor, "code-review", _enums())
    assert any(x["field"] == "runner" for x in v)

def test_empty_field_rejected():                            # [impl-review-fix] F1 补测：空串须落违规
    al = _mod(); enums = _enums()
    assert any(x["field"] == "layer" for x in al.check_lens_metric(_lm(layer=""), "code-review", enums))
    assert any(x["field"] == "lens" for x in al.check_lens_metric(_lm(lens=""), "code-review", enums))
    assert any(x["field"] == "runner" for x in al.check_lens_metric(_lm(runner=""), "code-review", enums))
    assert any(x["field"] == "sev" for x in al.check_lens_metric(_lm(sev=""), "code-review", enums))

def test_numeric_consistency_not_checked():                 # [impl-review-fix] F9 诚实边界：数值一致性脚本不兜
    al = _mod()
    v = al.check_lens_metric(_lm(findings="99"), "code-review", _enums())  # findings 与"实收数"不符也合法
    assert v == []

def test_min_required_both_present_ok():                    # [impl-review-fix] F11 正例：broad+outside-voice 都在
    al = _mod()
    report = ('<!-- sdflow:outside-voice v1 site="x" -->\n<!-- sdflow:hr-tg v1 hit="none" -->\n'
              '<!-- sdflow:step1-broad-review v1 mode="native" -->\n'
              '<!-- sdflow:lens-metric v1 layer="code-review" lens="broad" runner="claude" -->\n'
              '<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="claude" -->\n')
    v = al.check_existence(report, "code-review", metrics_on=True)
    assert not any(x["kind"] == "missing-lens-row" for x in v)

def test_min_required_single_missing():                     # [impl-review-fix] F11 单缺：只缺 broad
    al = _mod()
    report = ('<!-- sdflow:outside-voice v1 site="x" -->\n<!-- sdflow:hr-tg v1 hit="none" -->\n'
              '<!-- sdflow:step1-broad-review v1 mode="native" -->\n'
              '<!-- sdflow:lens-metric v1 layer="code-review" lens="outside-voice" runner="claude" -->\n')
    v = al.check_existence(report, "code-review", metrics_on=True)
    missing = {x["detail"] for x in v if x["kind"] == "missing-lens-row"}
    assert missing == {"broad"}


def _run(report_path, layer, root=None):
    cmd = [sys.executable, str(SCRIPT), "--report", str(report_path), "--layer", layer]
    if root: cmd += ["--root", str(root)]
    return subprocess.run(cmd, capture_output=True, text=True)

def test_clean_report_exit0(tmp_path):
    root = _write_config(tmp_path, "metrics:\n  enabled: false\n")
    rpt = ('<!-- sdflow:outside-voice v1 site="x" -->\n<!-- sdflow:hr-tg v1 hit="none" -->\n'
           '<!-- sdflow:step1-broad-review v1 mode="native" -->\n')
    rpt_path = tmp_path / "r.md"; rpt_path.write_text(rpt, encoding="utf-8")
    r = _run(rpt_path, "code-review", root); assert r.returncode == 0, r.stderr

def test_missing_report_error_exit2(tmp_path):
    r = _run(tmp_path / "nope.md", "code-review", tmp_path); assert r.returncode == 2

def test_violation_exit1(tmp_path):
    root = _write_config(tmp_path, "metrics:\n  enabled: false\n")
    rpt_path = tmp_path / "r.md"; rpt_path.write_text("<!-- sdflow:hr-tg v1 hit=\"none\" -->\n", encoding="utf-8")
    r = _run(rpt_path, "code-review", root); assert r.returncode == 1
    assert '"' in r.stdout or r.stdout.strip()              # JSON 输出

def test_config_bad_block_exit2(tmp_path):
    root = _write_config(tmp_path, "metrics:\n  enabled: yes\n")
    rpt_path = tmp_path / "r.md"
    rpt_path.write_text('<!-- sdflow:outside-voice v1 site="x" -->\n<!-- sdflow:hr-tg v1 hit="none" -->\n'
                        '<!-- sdflow:step1-broad-review v1 mode="native" -->\n', encoding="utf-8")
    r = _run(rpt_path, "code-review", root); assert r.returncode == 2
