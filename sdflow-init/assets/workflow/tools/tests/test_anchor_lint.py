import json, subprocess, sys, importlib.util
from pathlib import Path
import pytest

TOOLS = Path(__file__).resolve().parent.parent          # .../workflow/tools
SCRIPT = TOOLS / "anchor_lint.py"
CONTRACT = TOOLS.parent / "lens-metric-contract.md"     # .../workflow/lens-metric-contract.md

def _mod():
    spec = importlib.util.spec_from_file_location("anchor_lint", SCRIPT)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


# --- 最小 trigger-catalog 夹具（HR-TG 段 + 触发词目录全集表段），供 check_hr_tg 三参签名 / _run 用 ---

_HR_TG_SUBSET = {"TG-04", "TG-16"}
_ALL_TG_SET = {"TG-04", "TG-16", "TG-19"}

def _write_catalog(dest_dir, members="TG-04, TG-16"):
    body = (
        "# 触发目录\n\n"
        "## 三、触发词目录\n\n"
        "| ID | 触发 |\n|---|---|\n"
        "| TG-04 | x |\n| TG-16 | x |\n| TG-19 | x |\n\n"
        "## 七、HR-TG 子集（评审 cross-model 层单一源）\n\n"
        "> 高风险触发子集——命中任一 → 单开领域 cross-model。\n"
        f"> 成员：**{members}**\n"
    )
    p = Path(dest_dir) / "trigger-catalog.md"
    p.write_text(body, encoding="utf-8")
    return p

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


# --- hr-tg 锚 declared= 字段 schema（mlh-p4 T81：承「依据模型判定」）---------

def test_hr_tg_declared_present_ok():                       # hit=+declared=+evidence= 齐、M2 自洽 → 无违规
    al = _mod()
    report = '<!-- sdflow:hr-tg v1 hit="TG-04,TG-16" declared="TG-04,TG-16,TG-19" evidence="x" -->\n'
    assert al.check_hr_tg(report, _HR_TG_SUBSET, _ALL_TG_SET) == []

def test_hr_tg_none_with_declared_ok():                     # none 态 declared="" 亦合规（空集显式可见）
    al = _mod()
    report = '<!-- sdflow:hr-tg v1 hit="none" declared="" -->\n'
    assert al.check_hr_tg(report, _HR_TG_SUBSET, _ALL_TG_SET) == []

def test_hr_tg_missing_declared_violation():                # 缺 declared= → 违规（新 schema 强制该字段在场）
    al = _mod()
    report = '<!-- sdflow:hr-tg v1 hit="none" -->\n'
    v = al.check_hr_tg(report, _HR_TG_SUBSET, _ALL_TG_SET)
    assert any(x["field"] == "declared" and x["kind"] == "missing-field" for x in v)

def test_hr_tg_missing_hit_violation():                     # 缺 hit= → 违规
    al = _mod()
    report = '<!-- sdflow:hr-tg v1 declared="TG-04" -->\n'
    v = al.check_hr_tg(report, _HR_TG_SUBSET, _ALL_TG_SET)
    assert any(x["field"] == "hit" and x["kind"] == "missing-field" for x in v)

def test_hr_tg_malformed_csv_collect_not_raise():           # F9：非 TG-<num> 记号就地转 violation，不 raise
    """Task4 前旧断言"字段值任意不校验"已被 M2/M-new 取代——CSV 语法与目录归属现受检；
    仍不受检的仅"declared 是否=真命中集"（语义残余，S1，见 test_m2_consistent_but_wrong_still_passes）。"""
    al = _mod()
    report = '<!-- sdflow:hr-tg v1 hit="whatever" declared="anything" -->\n'
    v = al.check_hr_tg(report, _HR_TG_SUBSET, _ALL_TG_SET)   # 不 raise（F9 collect-not-raise）
    assert any(x["kind"] == "malformed-tg-csv" for x in v)

# --- M2 重算 / M4 evidence / M-new lint / F1 sentinel（mlh-p4 Task4）--------------------------

def test_m2_hit_recompute_mismatch_violation():             # hit≠declared∩HR-TG → hit-declared-mismatch
    al = _mod()
    r = '<!-- sdflow:hr-tg v1 hit="TG-04" declared="TG-19" evidence="x" -->\n'   # TG-19 非 HR-TG→expect_hits=[]≠[TG-04]
    v = al.check_hr_tg(r, _HR_TG_SUBSET, _ALL_TG_SET)
    assert any(x["kind"] == "hit-declared-mismatch" for x in v)

def test_m2_consistent_but_wrong_still_passes():
    """诚实边界（S1）：hit="none" declared="" 内部自洽（M2 只堵一致性，堵不住"是否漏判真命中"）→ 必须过。"""
    al = _mod()
    r = '<!-- sdflow:hr-tg v1 hit="none" declared="" -->\n'
    assert al.check_hr_tg(r, _HR_TG_SUBSET, _ALL_TG_SET) == []

def test_m4_evidence_missing_when_hit():                    # hit≠none 缺/纯空白 evidence → evidence-missing
    al = _mod()
    r = '<!-- sdflow:hr-tg v1 hit="TG-04" declared="TG-04" evidence="   " -->\n'
    v = al.check_hr_tg(r, _HR_TG_SUBSET, _ALL_TG_SET)
    assert any(x["kind"] == "evidence-missing" for x in v)

def test_m4_evidence_present_when_hit_ok():                 # 正例：hit≠none 且 evidence 非空白 → 无 evidence-missing
    al = _mod()
    r = '<!-- sdflow:hr-tg v1 hit="TG-04" declared="TG-04" evidence="见 x 行" -->\n'
    v = al.check_hr_tg(r, _HR_TG_SUBSET, _ALL_TG_SET)
    assert not any(x["kind"] == "evidence-missing" for x in v)

def test_f1_declared_none_literal_is_violation():           # F1：declared="none" 字面（应为 ""）→ 违规
    al = _mod()
    r = '<!-- sdflow:hr-tg v1 hit="none" declared="none" -->\n'
    v = al.check_hr_tg(r, _HR_TG_SUBSET, _ALL_TG_SET)
    assert any(x["kind"] == "declared-none-literal" for x in v)

def test_f1_hit_empty_string_is_violation():                # F1：hit=""（应为 "none"）→ 违规
    al = _mod()
    r = '<!-- sdflow:hr-tg v1 hit="" declared="" -->\n'
    v = al.check_hr_tg(r, _HR_TG_SUBSET, _ALL_TG_SET)
    assert any(x["kind"] == "hit-empty-not-none" for x in v)

def test_mnew_lint_tg_not_in_catalog():                     # M-new lint 侧：declared 含全集外 TG → 违规
    al = _mod()
    r = '<!-- sdflow:hr-tg v1 hit="none" declared="TG-77" -->\n'
    v = al.check_hr_tg(r, _HR_TG_SUBSET, _ALL_TG_SET)
    assert any(x["kind"] == "tg-not-in-catalog" for x in v)

def test_mnew_lint_hit_tg_not_in_catalog():                 # M-new lint 侧：hit 含全集外 TG 亦违规（非仅 declared）
    al = _mod()
    r = '<!-- sdflow:hr-tg v1 hit="TG-77" declared="TG-77" -->\n'
    v = al.check_hr_tg(r, _HR_TG_SUBSET, _ALL_TG_SET)
    assert any(x["kind"] == "tg-not-in-catalog" and x["field"] == "hit" for x in v)

def test_hr_tg_in_fence_not_checked():                      # fence 内示例锚不校验（同 lens-metric 口径）
    al = _mod()
    report = 'real\n```\n<!-- sdflow:hr-tg v1 hit="none" -->\n```\n'
    assert al.check_hr_tg(report, _HR_TG_SUBSET, _ALL_TG_SET) == []


def _run(report_path, layer, root=None, catalog=None):
    if catalog is None:
        catalog = _write_catalog(Path(report_path).parent)  # 最小合法 catalog，自动落在 report 同目录
    cmd = [sys.executable, str(SCRIPT), "--report", str(report_path), "--layer", layer,
           "--trigger-catalog", str(catalog)]
    if root: cmd += ["--root", str(root)]
    return subprocess.run(cmd, capture_output=True, text=True)


def test_anchor_lint_missing_catalog_fail_closed(tmp_path):
    """未传 --trigger-catalog → argparse required 缺参 SystemExit(2)（fail-closed），MUST NOT WARN 放行。"""
    al = _mod()
    rpt = tmp_path / "r.md"
    rpt.write_text('<!-- sdflow:hr-tg v1 hit="none" declared="" -->\n', encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        al.main(["--report", str(rpt), "--layer", "spec-review"])
    assert e.value.code == 2


def test_catalog_bad_exit2_reason(tmp_path):
    """--trigger-catalog 指向损坏单一源（无 HR-TG 段）→ exit2 且原因码 catalog-bad（非只 returncode==2）。"""
    root = _write_config(tmp_path, "metrics:\n  enabled: false\n")
    rpt = tmp_path / "r.md"
    rpt.write_text('<!-- sdflow:outside-voice v1 site="x" -->\n<!-- sdflow:hr-tg v1 hit="none" declared="" -->\n'
                   '<!-- sdflow:step1-broad-review v1 mode="native" -->\n', encoding="utf-8")
    bad_catalog = tmp_path / "bad-catalog.md"
    bad_catalog.write_text("# no HR-TG section here\n", encoding="utf-8")
    r = _run(rpt, "code-review", root, catalog=bad_catalog)
    assert r.returncode == 2
    assert json.loads(r.stdout)["reason"] == "catalog-bad"

def test_clean_report_exit0(tmp_path):
    root = _write_config(tmp_path, "metrics:\n  enabled: false\n")
    rpt = ('<!-- sdflow:outside-voice v1 site="x" -->\n<!-- sdflow:hr-tg v1 hit="none" declared="" -->\n'
           '<!-- sdflow:step1-broad-review v1 mode="native" -->\n')
    rpt_path = tmp_path / "r.md"; rpt_path.write_text(rpt, encoding="utf-8")
    r = _run(rpt_path, "code-review", root); assert r.returncode == 0, r.stderr

def test_hr_tg_missing_declared_exit1(tmp_path):            # 完整报告但 hr-tg 缺 declared= → VIOLATION（端到端）
    root = _write_config(tmp_path, "metrics:\n  enabled: false\n")
    rpt = ('<!-- sdflow:outside-voice v1 site="x" -->\n<!-- sdflow:hr-tg v1 hit="none" -->\n'
           '<!-- sdflow:step1-broad-review v1 mode="native" -->\n')
    rpt_path = tmp_path / "r.md"; rpt_path.write_text(rpt, encoding="utf-8")
    r = _run(rpt_path, "code-review", root); assert r.returncode == 1, r.stderr

def test_missing_report_error_exit2(tmp_path):              # F6：断言原因码，防 argparse 缺参撞码假绿
    r = _run(tmp_path / "nope.md", "code-review", tmp_path)
    assert r.returncode == 2
    assert json.loads(r.stdout)["reason"] == "report-unreadable"

def test_violation_exit1(tmp_path):
    root = _write_config(tmp_path, "metrics:\n  enabled: false\n")
    rpt_path = tmp_path / "r.md"; rpt_path.write_text("<!-- sdflow:hr-tg v1 hit=\"none\" -->\n", encoding="utf-8")
    r = _run(rpt_path, "code-review", root); assert r.returncode == 1
    assert '"' in r.stdout or r.stdout.strip()              # JSON 输出

def test_config_bad_block_exit2(tmp_path):                   # F6：断言原因码，防 argparse 缺参撞码假绿
    root = _write_config(tmp_path, "metrics:\n  enabled: yes\n")
    rpt_path = tmp_path / "r.md"
    rpt_path.write_text('<!-- sdflow:outside-voice v1 site="x" -->\n<!-- sdflow:hr-tg v1 hit="none" -->\n'
                        '<!-- sdflow:step1-broad-review v1 mode="native" -->\n', encoding="utf-8")
    r = _run(rpt_path, "code-review", root)
    assert r.returncode == 2
    assert json.loads(r.stdout)["reason"] == "metrics-block-bad"
