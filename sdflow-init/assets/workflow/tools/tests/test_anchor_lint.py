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


# --- add-codex-host-support：v2 锚构造夹具 ---------------------------------------------------

def _ov(**kw):
    """outside-voice 锚构造器（矩阵测试用）。默认合法跨模型：host=claude runner=codex reason_code=ok。"""
    base = dict(site="x", host="claude", runner="codex", reason_code="ok")
    base.update(kw)
    return "<!-- sdflow:outside-voice v1 " + " ".join(f'{k}="{v}"' for k, v in base.items()) + " -->"

# 合法跨模型 outside-voice 锚（e2e 报告需一条 mandatory outside-voice 锚且不触矩阵违规时用）
_OV_XM = _ov()

def _fc(**kw):
    """fanout-capability 锚构造器。默认 host=codex subagents=unavailable mirrors=domain。"""
    base = dict(host="codex", subagents="unavailable", mirrors="domain")
    base.update(kw)
    return "<!-- sdflow:fanout-capability v1 " + " ".join(f'{k}="{v}"' for k, v in base.items()) + " -->"

def test_load_enums_from_real_contract():
    al = _mod()
    e = al.load_enums(CONTRACT)
    assert e["layer"] == {"spec-review", "code-review"}
    assert e["lens"] == {"domain", "adversarial", "grounding", "history", "outside-voice", "broad"}
    # add-codex-host-support：runner 加 none/unknown、废弃 claude-fallback；新增 host / reason_code 域（从契约块读）
    assert e["runner"] == {"claude", "codex", "none", "unknown"}
    assert e["host"] == {"claude", "codex", "unknown"}
    assert e["reason_code"] == {"ok", "not-installed", "preflight-error", "timeout", "exec-error",
                                "host-unknown", "secret-hit", "fallback-unavailable"}
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
    # add-codex-host-support：base 含 host="claude"（v2 必填），普通镜 runner==host
    base = dict(layer="code-review", lens="domain", host="claude", runner="claude",
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


# --- F2 整行严格解析拒重复键（mlh-p4 Task5：防跨消费者 lint 末值胜 vs sdflow-retro 取首分歧）-----

def test_parse_kv_strict_detects_dup():
    al = _mod()
    kv, dup = al.parse_kv_strict('hit="none" hit="TG-04" declared=""')
    assert dup == ["hit"]
    assert kv["hit"] == "TG-04"                              # 末值胜，与 parse_kv 同口径（续算用同一确定值）

def test_parse_kv_strict_no_dup_empty_list():
    al = _mod()
    kv, dup = al.parse_kv_strict('hit="none" declared=""')
    assert dup == []

def test_f2_duplicate_key_violation():                       # 重复 hit= → dup-key violation
    al = _mod()
    r = '<!-- sdflow:hr-tg v1 hit="none" hit="TG-04" declared="" -->\n'
    v = al.check_hr_tg(r, _HR_TG_SUBSET, _ALL_TG_SET)
    assert any(x["kind"] == "dup-key" and x["field"] == "hit" for x in v)

def test_f2_duplicate_key_collect_not_raise_continues_m1():  # dup-key 不中断，其余校验（M1 缺字段等）仍续算
    al = _mod()
    r = '<!-- sdflow:hr-tg v1 declared="" declared="" -->\n'   # 重复 declared= 且缺 hit=
    v = al.check_hr_tg(r, _HR_TG_SUBSET, _ALL_TG_SET)
    assert any(x["kind"] == "dup-key" and x["field"] == "declared" for x in v)
    assert any(x["kind"] == "missing-field" and x["field"] == "hit" for x in v)


# --- [impl-review-fix] F-A/F-B/F-C：anchor_lint 本地重实现的 catalog 解析同样加固（非仅赖 F3 golden）---

def _catalog_body(all_tg_table, hr_tg_members, decoy_section="", prose_extra=""):
    return (
        "# 触发目录\n\n"
        f"{decoy_section}"
        "## 三、触发词目录\n\n"
        "| ID | 触发 |\n|---|---|\n" + all_tg_table + "\n"
        f"{prose_extra}"
        "## 七、HR-TG 子集（评审 cross-model 层单一源）\n\n"
        f"> 成员：**{hr_tg_members}**\n"
    )


def test_famember_line_rejects_suffixed_token_anchor_lint(tmp_path):
    al = _mod()
    body = _catalog_body("| TG-04 | x |\n", "TG-04x")
    cat = tmp_path / "trigger-catalog.md"; cat.write_text(body, encoding="utf-8")
    with pytest.raises(al.EmitError):
        al.load_hr_tg_subset(cat)


def test_fb_ambiguous_section_heading_fail_closed_anchor_lint(tmp_path):
    al = _mod()
    decoy = "## 零、触发词目录草案（历史存档）\n\n| ID | 触发 |\n|---|---|\n| TG-77 | x |\n\n"
    body = _catalog_body("| TG-04 | x |\n| TG-16 | x |\n", "TG-04, TG-16", decoy_section=decoy)
    cat = tmp_path / "trigger-catalog.md"; cat.write_text(body, encoding="utf-8")
    with pytest.raises(al.EmitError):
        al.load_all_tg_set(cat)


def test_fc_fence_aware_catalog_parsing_anchor_lint(tmp_path):
    al = _mod()
    prose = "```\n| TG-88 | 仅示例 |\n```\n\n"
    body = _catalog_body("| TG-04 | x |\n| TG-16 | x |\n", "TG-04, TG-16", prose_extra=prose)
    cat = tmp_path / "trigger-catalog.md"; cat.write_text(body, encoding="utf-8")
    all_tg = al.load_all_tg_set(cat)
    assert "TG-88" not in all_tg
    assert {"TG-04", "TG-16"} <= all_tg


# --- [impl-review-fix] F-D：hr-tg 锚行须严格边界闭合（未闭合注释 / -->后残留 → violation）---

def test_fd_unterminated_anchor_violation():
    al = _mod()
    r = '<!-- sdflow:hr-tg v1 hit="none" declared="" trailing\n'
    v = al.check_hr_tg(r, _HR_TG_SUBSET, _ALL_TG_SET)
    assert any(x["kind"] in ("unterminated-anchor", "malformed-anchor") for x in v)


def test_fd_trailing_residue_after_close_violation():
    al = _mod()
    r = '<!-- sdflow:hr-tg v1 hit="none" declared="" --> trailing junk\n'
    v = al.check_hr_tg(r, _HR_TG_SUBSET, _ALL_TG_SET)
    assert any(x["kind"] in ("unterminated-anchor", "malformed-anchor") for x in v)


def test_fd_normal_closed_anchor_ok():
    al = _mod()
    r = '<!-- sdflow:hr-tg v1 hit="none" declared="" -->\n'
    assert al.check_hr_tg(r, _HR_TG_SUBSET, _ALL_TG_SET) == []


# --- [impl-review-fix] F-E：hit=/declared= 须原始序=numeric canonical 序、无重复元素 ---

def test_fe_hit_out_of_order_violation():
    al = _mod()
    r = '<!-- sdflow:hr-tg v1 hit="TG-16,TG-04" declared="TG-04,TG-16" evidence="x" -->\n'
    v = al.check_hr_tg(r, _HR_TG_SUBSET, _ALL_TG_SET)
    assert any(x["kind"] == "hit-not-canonical-order" for x in v)


def test_fe_hit_duplicate_violation():
    al = _mod()
    r = '<!-- sdflow:hr-tg v1 hit="TG-04,TG-04" declared="TG-04" evidence="x" -->\n'
    v = al.check_hr_tg(r, _HR_TG_SUBSET, _ALL_TG_SET)
    assert any(x["kind"] == "hit-duplicate" for x in v)


def test_fe_normal_canonical_order_ok():
    al = _mod()
    r = '<!-- sdflow:hr-tg v1 hit="TG-04,TG-16" declared="TG-04,TG-16" evidence="x" -->\n'
    assert al.check_hr_tg(r, _HR_TG_SUBSET, _ALL_TG_SET) == []


def test_fe_s1_still_passes_with_order_checks():
    """S1 诚实边界不因 F-E 新增序校验倒退：hit="none" declared="" 仍必须过。"""
    al = _mod()
    r = '<!-- sdflow:hr-tg v1 hit="none" declared="" -->\n'
    assert al.check_hr_tg(r, _HR_TG_SUBSET, _ALL_TG_SET) == []


# --- [impl-review-fix] F-F：declared/hit 各自独立 try/except，一侧畸形不吞另一侧已判定违规 ---

def test_ff_declared_and_hit_violations_both_collected_independently():
    al = _mod()
    r = '<!-- sdflow:hr-tg v1 hit="TG-04,,TG-16" declared="TG-04,TG-77" evidence="x" -->\n'
    v = al.check_hr_tg(r, _HR_TG_SUBSET, _ALL_TG_SET)
    kinds = [(x["field"], x["kind"]) for x in v]
    assert ("declared", "tg-not-in-catalog") in kinds
    assert ("hit", "malformed-tg-csv") in kinds
    assert len(v) == 2


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
    rpt = (_OV_XM + '\n<!-- sdflow:hr-tg v1 hit="none" declared="" -->\n'
           '<!-- sdflow:step1-broad-review v1 mode="native" -->\n')
    rpt_path = tmp_path / "r.md"; rpt_path.write_text(rpt, encoding="utf-8")
    r = _run(rpt_path, "code-review", root); assert r.returncode == 0, r.stderr

def test_hr_tg_missing_declared_exit1(tmp_path):            # 完整报告但 hr-tg 缺 declared= → VIOLATION（端到端）
    root = _write_config(tmp_path, "metrics:\n  enabled: false\n")
    rpt = (_OV_XM + '\n<!-- sdflow:hr-tg v1 hit="none" -->\n'
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


def test_f9_cli_malformed_csv_returncode1_valid_json(tmp_path):
    """F9 CLI 级回归（fold，Task4 审留 Minor）：畸形 hit= CSV（连续逗号→空 cell）经 main() 子进程跑到底，
    须 returncode==1（VIOLATION，非 2/ERROR）且 stdout 仍是合法 JSON（json.loads 不抛——collect-not-raise
    契约在 CLI 边界仍成立，不泄漏 traceback、不中断双输出），并含 kind=malformed-tg-csv。"""
    root = _write_config(tmp_path, "metrics:\n  enabled: false\n")
    rpt = (_OV_XM + '\n'
           '<!-- sdflow:hr-tg v1 hit="TG-04,,TG-16" declared="TG-04,TG-16" evidence="x" -->\n'
           '<!-- sdflow:step1-broad-review v1 mode="native" -->\n')
    rpt_path = tmp_path / "r.md"; rpt_path.write_text(rpt, encoding="utf-8")
    r = _run(rpt_path, "code-review", root)
    assert r.returncode == 1, r.stderr
    payload = json.loads(r.stdout)                            # 不抛 = F9 契约核心断言
    assert payload["result"] == "VIOLATION"
    assert any(x["kind"] == "malformed-tg-csv" for x in payload["violations"])


# =========================================================================================
# add-codex-host-support Task 2：host 必填 + 合法组合矩阵（自审红线）+ fan-out 一致性 lint
#   + 普通镜行级校验 + 不判宿主边界锁
# =========================================================================================

# --- Step 1/2：REQUIRED_FIELDS 含 host；缺 host / host 越域 / runner 废弃值越域 -----------------

def test_required_fields_includes_host():
    al = _mod()
    assert "host" in al.REQUIRED_FIELDS

def test_lens_metric_missing_host_violation():
    al = _mod()
    anchor = '<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" runner="claude" -->'  # 缺 host
    v = al.check_lens_metric(anchor, "code-review", _enums())
    assert any(x["field"] == "host" and x["kind"] == "missing-field" for x in v)

def test_lens_metric_host_out_of_enum():
    al = _mod()
    v = al.check_lens_metric(_lm(host="mistral"), "code-review", _enums())
    assert any(x["field"] == "host" and x["kind"] == "out-of-enum" for x in v)

def test_lens_metric_runner_deprecated_claude_fallback_out_of_enum():
    al = _mod()  # claude-fallback 已废弃、不在 runner 域 → out-of-enum
    v = al.check_lens_metric(_lm(runner="claude-fallback"), "code-review", _enums())
    assert any(x["field"] == "runner" and x["kind"] == "out-of-enum" for x in v)


# --- Step 3/4：合法组合矩阵（🔴 自审红线单一源）绑到 outside-voice 锚 -----------------------------

def _has(v, kind):
    return any(x["kind"] == kind for x in v)

def test_matrix_cross_model_legal():                        # ① 跨模型合法：host=claude runner=codex reason_code=ok
    al = _mod()
    assert al.check_legal_combo(_ov(host="claude", runner="codex", reason_code="ok") + "\n", _enums()) == []

def test_matrix_same_family_legal():                        # ② 同族降级合法：runner==host + 降级码
    al = _mod()
    assert al.check_legal_combo(_ov(host="codex", runner="codex", reason_code="not-installed") + "\n", _enums()) == []

def test_matrix_preflight_error_mapped_from_missing_deps_legal():
    """task 8.6/D7（tasks 7.8 补测）：outside-voice.sh preflight stdout=`missing-deps` 由调用 SKILL
    映射为锚 reason_code="preflight-error"（合法同族降级码集内）后 MUST 放行——这是「诚实同族 fallback」
    路径，不得被矩阵拦。"""
    al = _mod()
    a = _ov(host="codex", runner="codex", reason_code="preflight-error") + "\n"
    assert al.check_legal_combo(a, _enums()) == []

def test_matrix_raw_missing_deps_reason_code_rejected():
    """反例锁：`reason_code="missing-deps"` 原样落锚（未按 D7 映射为 preflight-error）MUST 被拒——
    `missing-deps` 不在契约 reason_code 8 值域内，越域即报错，防止调用方漏映射而假绿放行。"""
    al = _mod()
    a = _ov(host="codex", runner="codex", reason_code="missing-deps") + "\n"
    v = al.check_legal_combo(a, _enums())
    assert any(x["field"] == "reason_code" and x["kind"] == "out-of-enum" for x in v)

def test_matrix_noexec_legal():                             # ③ 无执行合法：runner=none findings=0 host-unknown
    al = _mod()
    a = _ov(host="unknown", runner="none", reason_code="host-unknown", findings="0") + "\n"
    assert al.check_legal_combo(a, _enums()) == []

def test_matrix_noexec_secret_hit_legal():                  # ③ 无执行合法：host∈{claude,codex}∧secret-hit
    al = _mod()
    a = _ov(host="claude", runner="none", reason_code="secret-hit", findings="0") + "\n"
    assert al.check_legal_combo(a, _enums()) == []

def test_matrix_runner_none_with_findings_blocked():        # runner=none findings=5 → 拦
    al = _mod()
    a = _ov(host="claude", runner="none", reason_code="secret-hit", findings="5") + "\n"
    assert _has(al.check_legal_combo(a, _enums()), "illegal-combo")

def test_matrix_host_unknown_runner_claude_blocked():       # host=unknown runner=claude → 拦（catch-all）
    al = _mod()
    a = _ov(host="unknown", runner="claude", reason_code="ok") + "\n"
    assert _has(al.check_legal_combo(a, _enums()), "illegal-combo")

def test_matrix_self_review_runner_eq_host_reason_ok():     # 🔴 runner==host reason_code=ok → 自审
    al = _mod()
    a = _ov(host="claude", runner="claude", reason_code="ok") + "\n"
    assert _has(al.check_legal_combo(a, _enums()), "self-review")

def test_matrix_self_review_same_family_bad_code():         # runner==host 但 reason_code 非降级码（host-unknown）→ 自审
    al = _mod()
    a = _ov(host="codex", runner="codex", reason_code="host-unknown") + "\n"
    assert _has(al.check_legal_combo(a, _enums()), "self-review")

def test_matrix_catch_all_outside_voice_runner_unknown():   # 🔒 catch-all 显式回归锁：outside-voice runner=unknown → 拦
    al = _mod()  # runner='unknown' 在共享 runner 枚举域内、第一层域校验放行，MUST 由矩阵 catch-all（显式 else）拦住
    a = _ov(host="claude", runner="unknown", reason_code="ok") + "\n"
    assert _has(al.check_legal_combo(a, _enums()), "illegal-combo")

def test_matrix_cross_model_wrong_reason_code_blocked():    # runner≠host 但 reason_code≠ok → 拦
    al = _mod()
    a = _ov(host="claude", runner="codex", reason_code="timeout") + "\n"
    assert _has(al.check_legal_combo(a, _enums()), "illegal-combo")

def test_matrix_outside_voice_missing_reason_code():        # Step 3：outside-voice 锚缺 reason_code → missing-field
    al = _mod()
    a = '<!-- sdflow:outside-voice v1 site="x" host="claude" runner="codex" -->\n'
    v = al.check_legal_combo(a, _enums())
    assert any(x["field"] == "reason_code" and x["kind"] == "missing-field" for x in v)

def test_matrix_bound_to_outside_voice_not_lens_metric():
    """🔒 反例锁：F6 红线绑到 outside-voice 锚、非 lens-metric 锚。lens-metric 锚无 reason_code——
    绑错会让红线读不到 reason_code 而静默永不触发=假绿。验：① 一条 runner==host 的 lens-metric 锚
    （普通镜正常态）MUST NOT 被矩阵判自审（矩阵不碰 lens-metric 锚）；② 同样 runner==host 落在
    outside-voice 锚上 MUST 被判自审——证明红线确实绑在 outside-voice 锚。"""
    al = _mod()
    lm = ('<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" host="claude" runner="claude" '
          'site="—" findings="0" 采纳="0" 裁掉="0" defer="0" 独立="0" sev="致0/高0/中0/低0" -->\n')
    assert al.check_legal_combo(lm, _enums()) == []          # 矩阵忽略 lens-metric 锚
    ov = _ov(host="claude", runner="claude", reason_code="ok") + "\n"
    assert _has(al.check_legal_combo(ov, _enums()), "self-review")  # 绑在 outside-voice 锚 → 触发


def test_matrix_dup_key_fail_closed_not_reclassified_as_cross_model():
    """🔴 红线 fail-open 锁（Important #1）：重复 runner= 键 MUST NOT 让 parse_kv 末值胜把自审翻成跨模型放行。
    锚 host=claude runner=claude reason_code=ok runner=codex —— first-value(runner=claude)=自审、
    last-value(runner=codex)=跨模型。严格解析须报 dup-key 且 fail-closed（在 classify_combo 之前跳过分类），
    NOT clean（v 非空），MUST NOT 被误判为合法跨模型放行（clean）。"""
    al = _mod()
    a = ('<!-- sdflow:outside-voice v1 site="x" host="claude" runner="claude" '
         'reason_code="ok" runner="codex" -->\n')
    v = al.check_legal_combo(a, _enums())
    assert _has(v, "dup-key") and v != []               # 报 dup-key、NOT clean
    assert any(x["field"] == "runner" and x["kind"] == "dup-key" for x in v)
    # 因 dup 时 continue 跳过分类 → 不产生 self-review/illegal-combo（重复键先 fail-closed，末值胜 kv 不进矩阵）
    assert not _has(v, "self-review") and not _has(v, "illegal-combo")


def test_matrix_single_key_still_classifies_after_strict_parse():
    """对照：改 parse_kv_strict 后正常单键锚仍正确分类——自审仍判 self-review、跨模型仍 clean、无 dup-key。"""
    al = _mod()
    v_self = al.check_legal_combo(_ov(host="claude", runner="claude", reason_code="ok") + "\n", _enums())
    assert _has(v_self, "self-review") and not _has(v_self, "dup-key")
    v_xm = al.check_legal_combo(_ov(host="claude", runner="codex", reason_code="ok") + "\n", _enums())
    assert v_xm == []                                   # 合法跨模型仍 clean


# --- Step 5：lens-metric 普通镜行级校验 -----------------------------------------------------

def test_ordinary_mirror_runner_unknown_host_known_blocked():   # host=claude lens=domain runner=unknown → 拦
    al = _mod()
    v = al.check_lens_metric(_lm(host="claude", lens="domain", runner="unknown"), "code-review", _enums())
    assert _has(v, "ordinary-runner-host-mismatch")

def test_ordinary_mirror_runner_unknown_host_unknown_ok():      # host=unknown lens=domain runner=unknown → 放行
    al = _mod()
    v = al.check_lens_metric(_lm(host="unknown", lens="domain", runner="unknown"), "code-review", _enums())
    assert not _has(v, "ordinary-runner-host-mismatch")

def test_ordinary_mirror_runner_none_blocked():                # 普通镜 runner=none → 拦（none 仅 outside-voice 无执行）
    al = _mod()
    v = al.check_lens_metric(_lm(host="claude", lens="domain", runner="none"), "code-review", _enums())
    assert _has(v, "ordinary-runner-host-mismatch")

def test_ordinary_mirror_runner_eq_host_ok():                  # host=codex lens=domain runner=codex → 放行
    al = _mod()
    v = al.check_lens_metric(_lm(layer="code-review", host="codex", lens="domain", runner="codex"), "code-review", _enums())
    assert not _has(v, "ordinary-runner-host-mismatch")

def test_outside_voice_lens_row_cross_model_not_flagged():     # lens=outside-voice 行 runner≠host 合法，不套普通镜规则
    al = _mod()
    v = al.check_lens_metric(_lm(host="claude", lens="outside-voice", runner="codex", site="code-voice"),
                             "code-review", _enums())
    assert not _has(v, "ordinary-runner-host-mismatch")


# --- Step 6：🔒 边界锁——anchor_lint 不判宿主（ADR-1），MUST NOT import/调 resolve-models.sh -------

def test_anchor_lint_does_not_reference_resolve_models():
    """ADR-1：宿主判定只在产出侧需要；anchor_lint 只校验锚行内部一致性（host/runner/reason_code 都写在锚里）。
    MUST NOT import/调 resolve-models.sh（否则把宿主判定双实现进校验器，与 ADR-1 冲突）。
    锁**代码**（剥注释后）——注释里为解释 ADR-1 而提及文件名不算违规。"""
    code_only = "\n".join(ln.split("#", 1)[0] for ln in SCRIPT.read_text(encoding="utf-8").splitlines())
    assert "resolve-models" not in code_only          # 无 shell-out 调宿主脚本
    assert "resolve_models" not in code_only          # 无 python 双实现
    assert "subprocess" not in code_only              # anchor_lint 纯解析、根本不起子进程（无处调宿主脚本）


# --- Step 7：fan-out always-on 一致性 lint（读 mirrors=，MUST NOT 数 lens-metric 行）------------

def test_fanout_unavailable_multi_mirror_blocked():            # unavailable + mirrors 列 3 镜 → dead-fanout-multi-mirror
    al = _mod()
    r = _fc(host="codex", subagents="unavailable", mirrors="domain,adversarial,grounding") + "\n"
    assert _has(al.check_fanout_consistency(r), "dead-fanout-multi-mirror")

def test_fanout_unavailable_single_mirror_ok():               # unavailable + 1 镜 → 放行
    al = _mod()
    r = _fc(host="codex", subagents="unavailable", mirrors="domain") + "\n"
    assert al.check_fanout_consistency(r) == []

def test_fanout_available_multi_mirror_ok():                  # available + N 镜 → 放行（残余留语义层，不拦偷懒自代）
    al = _mod()
    r = _fc(host="codex", subagents="available", mirrors="domain,adversarial,grounding") + "\n"
    assert al.check_fanout_consistency(r) == []

def test_fanout_mirrors_sentinel_ok():                        # mirrors="—"（未 fan-out）+ unavailable → 放行
    al = _mod()
    r = _fc(host="codex", subagents="unavailable", mirrors="—") + "\n"
    assert al.check_fanout_consistency(r) == []

def test_fanout_reads_mirrors_not_lens_metric_rows():
    """🔒 C2 反例锁：判据 MUST 读 mirrors=、MUST NOT 数 lens-metric 行。构造 unavailable + mirrors 单镜
    但报告里另有 3 条 domain/adversarial/grounding lens-metric 行——若误数 lens-metric 行会误报 >1，读 mirrors= 则放行。"""
    al = _mod()
    r = (_fc(host="codex", subagents="unavailable", mirrors="domain") + "\n"
         + _lm(host="codex", lens="domain", runner="codex") + "\n"
         + _lm(host="codex", lens="adversarial", runner="codex") + "\n"
         + _lm(host="codex", lens="grounding", runner="codex") + "\n")
    assert al.check_fanout_consistency(r) == []              # 只数 mirrors=（1 镜），不数 lens-metric 行

# fail-closed 分支
def test_fanout_subagents_empty_fail_closed():
    al = _mod()
    r = _fc(host="codex", subagents="", mirrors="domain") + "\n"
    assert _has(al.check_fanout_consistency(r), "bad-subagents")

def test_fanout_subagents_unknown_fail_closed():
    al = _mod()
    r = _fc(host="codex", subagents="maybe", mirrors="domain") + "\n"
    assert _has(al.check_fanout_consistency(r), "bad-subagents")

def test_fanout_subagents_missing_fail_closed():
    al = _mod()
    r = '<!-- sdflow:fanout-capability v1 host="codex" mirrors="domain" -->\n'
    assert _has(al.check_fanout_consistency(r), "bad-subagents")

def test_fanout_bad_subagents_not_bypassed_by_multi_mirror():
    """🔒 r3-narrow #5：坏 subagents 值携多镜 MUST NOT 因不等于 'unavailable' 而绕过——须 fail-closed。"""
    al = _mod()
    r = _fc(host="codex", subagents="", mirrors="domain,adversarial,grounding") + "\n"
    assert _has(al.check_fanout_consistency(r), "bad-subagents")

def test_fanout_mirrors_missing_host_codex_fail_closed():
    al = _mod()
    r = '<!-- sdflow:fanout-capability v1 host="codex" subagents="unavailable" -->\n'
    assert _has(al.check_fanout_consistency(r), "mirrors-missing")

def test_fanout_mirrors_empty_fail_closed():
    al = _mod()
    r = _fc(host="codex", subagents="unavailable", mirrors="") + "\n"
    assert _has(al.check_fanout_consistency(r), "mirrors-empty")

def test_fanout_mirrors_unknown_token_fail_closed():
    al = _mod()
    r = _fc(host="codex", subagents="unavailable", mirrors="domain,bogus") + "\n"
    assert _has(al.check_fanout_consistency(r), "mirrors-unknown-token")

def test_fanout_mirrors_dup_token_fail_closed():
    al = _mod()
    r = _fc(host="codex", subagents="unavailable", mirrors="domain,domain") + "\n"
    assert _has(al.check_fanout_consistency(r), "mirrors-dup-token")

def test_fanout_duplicate_anchor_fail_closed():
    al = _mod()
    r = (_fc(host="codex", subagents="available", mirrors="domain") + "\n"
         + _fc(host="codex", subagents="unavailable", mirrors="domain") + "\n")
    assert _has(al.check_fanout_consistency(r), "duplicate-fanout-anchor")

def test_fanout_host_mismatch_fail_closed():
    al = _mod()  # capability 锚 host=claude 混入 host=codex 报告（outside-voice host=codex）
    r = (_ov(host="codex", runner="claude", reason_code="ok") + "\n"
         + _fc(host="claude", subagents="unavailable", mirrors="domain") + "\n")
    assert _has(al.check_fanout_consistency(r), "fanout-host-mismatch")

def test_fanout_host_codex_missing_anchor_blocked():
    al = _mod()  # host=codex 报告（从 outside-voice host 读到）缺 fanout-capability 锚 → 报错
    r = _ov(host="codex", runner="claude", reason_code="ok") + "\n"
    assert _has(al.check_fanout_consistency(r), "missing-fanout-anchor")

def test_fanout_host_claude_no_anchor_ok():                   # host=claude 免探、无 capability 锚合法
    al = _mod()
    r = _ov(host="claude", runner="codex", reason_code="ok") + "\n"
    assert al.check_fanout_consistency(r) == []

def test_fanout_kv_duplicate_key_fail_closed():
    al = _mod()
    r = '<!-- sdflow:fanout-capability v1 host="codex" host="claude" subagents="unavailable" mirrors="domain" -->\n'
    assert _has(al.check_fanout_consistency(r), "dup-key")

def test_fanout_conflicting_report_host_fail_closed():
    """🔒 Minor #2：报告含 ≥2 个不同真 host（outside-voice host=codex + host=claude）→ 原 report_host
    塌成 None，missing-fanout-anchor / host-mismatch 静默失效。须 fail-closed 报 conflicting-report-host。
    此处**无** fanout-capability 锚——若不硬停，host=codex 缺探针锚会被 report_host=None 偷渡放行。"""
    al = _mod()
    r = (_ov(host="codex", runner="claude", reason_code="ok") + "\n"
         + _ov(host="claude", runner="codex", reason_code="ok") + "\n")
    v = al.check_fanout_consistency(r)
    assert _has(v, "conflicting-report-host")
    assert not _has(v, "missing-fanout-anchor")         # 硬停在前，不再走缺锚判定（避免双噪声）

def test_fanout_unknown_mixed_single_real_host_not_conflict():
    """对照：unknown 与单一真 host 混合非冲突（去 unknown 后仅 1 个真 host=codex）→ 不报 conflicting-report-host，
    且 report_host 仍取真 host（codex），探针锚在场且一致 → 全程 clean。"""
    al = _mod()
    r = (_ov(host="codex", runner="claude", reason_code="ok") + "\n"
         + _lm(host="unknown", lens="domain", runner="unknown") + "\n"
         + _fc(host="codex", subagents="unavailable", mirrors="domain") + "\n")
    v = al.check_fanout_consistency(r)
    assert not _has(v, "conflicting-report-host")
    assert v == []

def test_fanout_in_fence_not_checked():                       # fence 内示例锚不校验
    al = _mod()
    r = 'real\n```\n' + _fc(host="codex", subagents="unavailable", mirrors="domain,adversarial") + '\n```\n'
    assert al.check_fanout_consistency(r) == []


# --- 解耦锁（metrics=false 时矩阵红线 + 一致性 lint 仍生效，端到端）------------------------------

def test_matrix_self_review_blocks_when_metrics_off(tmp_path):
    """🔒 解耦锁：metrics.enabled=false（默认消费仓、无 lens-metric 行）时，矩阵自审红线仍端到端拦截。"""
    root = _write_config(tmp_path, "metrics:\n  enabled: false\n")
    rpt = (_ov(host="claude", runner="claude", reason_code="ok") + "\n"   # 自审
           + '<!-- sdflow:hr-tg v1 hit="none" declared="" -->\n'
           '<!-- sdflow:step1-broad-review v1 mode="native" -->\n')
    rpt_path = tmp_path / "r.md"; rpt_path.write_text(rpt, encoding="utf-8")
    r = _run(rpt_path, "code-review", root)
    assert r.returncode == 1, r.stderr
    assert any(x["kind"] == "self-review" for x in json.loads(r.stdout)["violations"])

def test_fanout_dead_multi_mirror_blocks_when_metrics_off(tmp_path):
    """🔒 解耦锁（C2）：metrics=false 且无 lens-metric 行时，一致性 lint 仍读 mirrors= 端到端拦截。"""
    root = _write_config(tmp_path, "metrics:\n  enabled: false\n")
    rpt = (_ov(host="codex", runner="claude", reason_code="ok") + "\n"    # host=codex 跨模型，合法
           + _fc(host="codex", subagents="unavailable", mirrors="domain,adversarial,grounding") + "\n"
           + '<!-- sdflow:hr-tg v1 hit="none" declared="" -->\n'
           '<!-- sdflow:step1-broad-review v1 mode="native" -->\n')
    rpt_path = tmp_path / "r.md"; rpt_path.write_text(rpt, encoding="utf-8")
    r = _run(rpt_path, "code-review", root)
    assert r.returncode == 1, r.stderr
    assert any(x["kind"] == "dead-fanout-multi-mirror" for x in json.loads(r.stdout)["violations"])

def test_clean_v2_report_with_fanout_exit0(tmp_path):
    """正例端到端：host=codex 合法跨模型 + fanout available 多镜 + mandatory 锚齐 → CLEAN。"""
    root = _write_config(tmp_path, "metrics:\n  enabled: false\n")
    rpt = (_ov(host="codex", runner="claude", reason_code="ok") + "\n"
           + _fc(host="codex", subagents="available", mirrors="domain,adversarial,grounding") + "\n"
           + '<!-- sdflow:hr-tg v1 hit="none" declared="" -->\n'
           '<!-- sdflow:step1-broad-review v1 mode="native" -->\n')
    rpt_path = tmp_path / "r.md"; rpt_path.write_text(rpt, encoding="utf-8")
    r = _run(rpt_path, "code-review", root)
    assert r.returncode == 0, r.stderr
