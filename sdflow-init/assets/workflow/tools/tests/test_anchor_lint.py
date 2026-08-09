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
    # async-outside-voice §3.5：site 默认取 code-voice（e2e 夹具多为 code-review 层，per-site 核按层比对期望集）
    base = dict(site="code-voice", host="claude", runner="codex", reason_code="ok")
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

def test_load_enums_unclosed_block_raises(tmp_path):
    """T86：块开了但 EOF 前无匹配闭合围栏 ⇒ 后续正文被当枚举吞进来，取值域不可信 ⇒ fail-closed。
    MUST NOT 静默按「读到 EOF 为止」当合法块处理。"""
    al = _mod()
    # 各键齐全（否则 §解析空/缺项 那道门会先红 ⇒ 本用例变恒真、测不到未闭合这条）
    bad = tmp_path / "c.md"
    bad.write_text("```lens-metric-enums\nlayer: spec-review,code-review\nlens: domain\n"
                   "host: claude\nrunner: claude\nreason_code: ok\nsev-format: 致N/高N/中N/低N\n"
                   "\n## 后面的散文正文（没有闭合围栏）\n", encoding="utf-8")
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
    al = _mod(); assert al._metrics_enabled(tmp_path) is False        # ① 无文件

def test_metrics_no_block_false(tmp_path):                                # ② 消费仓常态
    al = _mod(); root = _write_config(tmp_path, "schema: spec-driven\ncontext: |\n  x\n")
    assert al._metrics_enabled(root) is False

def test_metrics_block_illegal_raises(tmp_path):                          # ③ 块在值非法
    al = _mod(); root = _write_config(tmp_path, "metrics:\n  enabled: yes\n")
    import pytest
    with pytest.raises(al.MetricsError):
        al._metrics_enabled(root)

def test_metrics_true(tmp_path):                                          # ④
    al = _mod(); root = _write_config(tmp_path, "metrics:\n  enabled: true\n")
    assert al._metrics_enabled(root) is True

def test_metrics_block_boundary(tmp_path):                                # 块边界：另一段的 enabled 不误读
    al = _mod(); root = _write_config(tmp_path, "metrics:\n  enabled: false\nother:\n  enabled: true\n")
    assert al._metrics_enabled(root) is False

def test_metrics_top_comment_between(tmp_path):        # [impl-review-fix] F3 补测：顶层注释/空行不误判块边界
    al = _mod(); root = _write_config(tmp_path, "metrics:\n# 注释\n  enabled: true\n")
    assert al._metrics_enabled(root) is True


# --- shared-yaml-subset-parser Task 2：`_yq()` 薄封装（design.md §1 参考实现）------------------

def test_yq_reads_scalar_true(tmp_path):
    al = _mod()
    p = tmp_path / "c.yaml"; p.write_text("metrics:\n  enabled: true\n", encoding="utf-8")
    assert al._yq(".metrics.enabled", p, default=False) is True

def test_yq_default_for_null(tmp_path):                # 键不存在 → stdout=null exit0 → default 参数返回
    al = _mod()
    p = tmp_path / "c.yaml"; p.write_text("other: 1\n", encoding="utf-8")
    assert al._yq(".metrics.enabled", p, default="sentinel") == "sentinel"

def test_yq_raises_on_nonzero_exit(tmp_path):           # YAML 语法错误 → exit≠0 → raise，不吞
    al = _mod()
    p = tmp_path / "bad.yaml"; p.write_text('a: "unterminated\n', encoding="utf-8")
    with pytest.raises(RuntimeError):
        al._yq(".a", p, default=None)

def test_yq_not_installed_fails_loud(monkeypatch, tmp_path):
    al = _mod()
    monkeypatch.setattr(al.shutil, "which", lambda name: None)
    p = tmp_path / "c.yaml"; p.write_text("a: 1\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="yq 未安装"):
        al._yq(".a", p, default=None)

def test_yq_identity_check_rejects_non_mikefarah(monkeypatch, tmp_path):
    al = _mod()
    monkeypatch.setattr(al.shutil, "which", lambda name: "/usr/bin/yq")
    class _FakeResult:
        def __init__(self, stdout): self.stdout, self.stderr, self.returncode = stdout, "", 0
    def fake_run(cmd, **kw):
        assert "--version" in cmd, "身份校验须先于业务调用"
        return _FakeResult("yq (https://github.com/kislyuk/yq/) version 3.5.1")
    monkeypatch.setattr(al.subprocess, "run", fake_run)
    p = tmp_path / "c.yaml"; p.write_text("a: 1\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="不是 mikefarah/yq"):
        al._yq(".a", p, default=None)

def test_yq_version_check_runs_once_then_cached(tmp_path):
    al = _mod()
    calls = {"version": 0}
    orig_run = al.subprocess.run
    def spy_run(cmd, **kw):
        if "--version" in cmd:
            calls["version"] += 1
        return orig_run(cmd, **kw)
    al.subprocess.run = spy_run
    p = tmp_path / "c.yaml"; p.write_text("a: 1\nb: 2\n", encoding="utf-8")
    al._yq(".a", p, default=None)
    al._yq(".b", p, default=None)
    assert calls["version"] == 1


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
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


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
           '<!-- sdflow:step1-broad-review v1 mode="native" -->\n'
           '<!-- sdflow:declared-sites v1 declared="code-voice" -->\n')
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


# 🔴 B1 回归：outside-voice lens-metric 行此前**完全脱离**校验（check_lens_metric 显式 lens!="outside-voice" 才校）
# → 手写/emitter-bypass 的三类矛盾锚被放行、经 aggregator 汇入 retro 价值表。面治覆盖 OV 行完整不变量集：
#   ① runner="none"（无执行）⇒ findings MUST=0；② host="unknown"（无 voice 目标）⇒ runner MUST="none"；
#   ③ OV 行 runner 域收紧 ∈{claude,codex,none}，MUST NOT="unknown"（unknown 只属非-ov 普通镜行，契约「跨模型性」段）。
def test_ov_lens_row_runner_none_nonzero_findings_blocked():   # ① runner=none 却 findings>0 → 拦
    al = _mod()
    v = al.check_lens_metric(_lm(host="codex", lens="outside-voice", runner="none", findings="5", site="code-voice"),
                             "code-review", _enums())
    assert _has(v, "ov-runner-none-nonzero-findings")

def test_ov_lens_row_unknown_host_runner_not_none_blocked():   # ② host=unknown 却 runner≠none → 拦
    al = _mod()
    v = al.check_lens_metric(_lm(host="unknown", lens="outside-voice", runner="claude", findings="0", site="code-voice"),
                             "code-review", _enums())
    assert _has(v, "ov-unknown-host-runner")

def test_ov_lens_row_runner_unknown_blocked():                 # ③ OV 行 runner=unknown（越 OV 域）→ 拦
    al = _mod()
    v = al.check_lens_metric(_lm(host="unknown", lens="outside-voice", runner="unknown", findings="0", site="code-voice"),
                             "code-review", _enums())
    assert _has(v, "ov-runner-unknown")

def test_ov_lens_row_no_exec_legal_clean():                    # 合法无执行 OV 行：host=unknown runner=none findings=0 → clean
    al = _mod()
    v = al.check_lens_metric(_lm(host="unknown", lens="outside-voice", runner="none", findings="0",
                                 采纳="0", 裁掉="0", 独立="0", sev="致0/高0/中0/低0", site="code-voice"),
                             "code-review", _enums())
    assert v == []

def test_ov_lens_row_same_family_fallback_legal_clean():       # 合法同族 fallback OV 行：host=claude runner=claude → clean
    al = _mod()
    v = al.check_lens_metric(_lm(host="claude", lens="outside-voice", runner="claude", findings="2", site="code-voice"),
                             "code-review", _enums())
    assert v == []


# --- Step 6：🔒 边界锁——anchor_lint 不判宿主（ADR-1），MUST NOT import/调 resolve-models.sh -------

def test_anchor_lint_does_not_reference_resolve_models():
    """ADR-1：宿主判定只在产出侧需要；anchor_lint 只校验锚行内部一致性（host/runner/reason_code 都写在锚里）。
    MUST NOT import/调 resolve-models.sh（否则把宿主判定双实现进校验器，与 ADR-1 冲突）。
    锁**代码**（剥注释后）——注释里为解释 ADR-1 而提及文件名不算违规。
    [shared-yaml-subset-parser Task 2 更新] `subprocess` 已合法引入（`_yq()` 起 yq 子进程读 YAML，
    非判宿主）——旧断言「根本不起子进程」的字面检查随之失真，改为锁住真正的 ADR-1 意图：
    subprocess 调用的第一个参数只能是 `yq`/`_yq_bin`，MUST NOT 出现 resolve-models.sh 的调用形态。"""
    code_only = "\n".join(ln.split("#", 1)[0] for ln in SCRIPT.read_text(encoding="utf-8").splitlines())
    assert "resolve-models" not in code_only          # 无 shell-out 调宿主脚本
    assert "resolve_models" not in code_only          # 无 python 双实现
    assert "subprocess.run([yq" in code_only or "subprocess.run([_yq_bin" in code_only  # 唯一起子进程点=起 yq
    import re as _re
    subprocess_run_calls = _re.findall(r'subprocess\.run\(\[([^\]]*)', code_only)
    assert subprocess_run_calls, "预期至少一处 subprocess.run([...] 调用（_yq 内部）"
    for call_args in subprocess_run_calls:
        assert "resolve-models" not in call_args and "resolve_models" not in call_args


# --- Step 7：fan-out always-on 一致性 lint（读 mirrors=，MUST NOT 数 lens-metric 行）------------

def test_fanout_unavailable_multi_mirror_blocked():            # unavailable + mirrors 列 3 镜 → dead-fanout-multi-mirror
    al = _mod()
    r = _fc(host="codex", subagents="unavailable", mirrors="domain,adversarial,grounding") + "\n"
    assert _has(al.check_fanout_consistency(r), "dead-fanout-multi-mirror")

def test_parse_mirrors_history_token_valid():                  # history 是合法 mirror token，非 unknown-token
    al = _mod()
    tokens, err = al._parse_mirrors("history")
    assert err is None
    assert tokens == ["history"]

def test_fanout_unavailable_history_multi_mirror_blocked():    # unavailable + mirrors="domain,history" → dead-fanout-multi-mirror
    al = _mod()
    r = _fc(host="codex", subagents="unavailable", mirrors="domain,history") + "\n"
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


# --- absorb-gstack-review Task 1：mirrors 合法 token 集扩 broad，不污染 dead-fanout 计数集 --------

def test_mirrors_legal_and_fanout_constants_split():
    """🔒 design.md §2 钉死常量名：合法集 `_MIRRORS_LEGAL` 含 broad，计数集 `_FANOUT_MIRRORS` 不含 broad——
    两者必须是不同对象，防止未来把 broad 直接塞回 `_FANOUT_MIRRORS` 顺带污染计数域。"""
    al = _mod()
    assert "broad" in al._MIRRORS_LEGAL
    assert "broad" not in al._FANOUT_MIRRORS
    assert al._MIRRORS_LEGAL != al._FANOUT_MIRRORS

def test_parse_mirrors_broad_token_valid():                    # broad 是合法 mirrors token
    al = _mod()
    tokens, err = al._parse_mirrors("broad")
    assert err is None
    assert tokens == ["broad"]

def test_fanout_unavailable_broad_history_not_dead_fanout():
    """unavailable + mirrors="broad,history" → broad 不进计数集，去重计数域只剩 history（1 个）→ 不触发。"""
    al = _mod()
    r = _fc(host="codex", subagents="unavailable", mirrors="broad,history") + "\n"
    assert al.check_fanout_consistency(r) == []

def test_fanout_unavailable_broad_domain_history_still_dead_fanout():
    """unavailable + mirrors="broad,domain,history" → 计数域仍是 {domain,history}（2 个）→ 触发，broad 未被误算但也未误免责。"""
    al = _mod()
    r = _fc(host="codex", subagents="unavailable", mirrors="broad,domain,history") + "\n"
    assert _has(al.check_fanout_consistency(r), "dead-fanout-multi-mirror")

def test_step1_broad_review_mode_subagent_lint_passes():
    """🔒 锁定「lint 不校验 step1-broad-review 的 mode 值」不变量：新枚举值 mode="subagent" 不应触发任何
    与 mode 相关的校验（只校验锚族存在性）。"""
    al = _mod()
    r = ('<!-- sdflow:step1-broad-review v1 mode="subagent" -->\n'
         + _ov(host="claude", runner="codex", reason_code="ok") + "\n"
         + '<!-- sdflow:hr-tg v1 hit="none" -->\n')
    assert al.check_existence(r, "code-review", metrics_on=False) == []

def test_fanout_mirrors_unknown_token_hint_mentions_setup_sh():
    """mirrors-unknown-token 报错须自带可操作指引：旧版 bundle 遇到未来新增 token 时不应让人对着陌生
    token 名发呆——文案须提示回运行 checkout 跑 `bash setup.sh`（absorb-gstack-autoplan：`sdflow-init update`
    指引已随 adr/0039 真实部署模型退役——消费仓规则经全局 canonical 实时解析，不再有本地 bundle 副本
    靠 update 刷新；真正过时的是运行 checkout 未 pull+setup，见 design.md「Risks」版本 skew 段）。"""
    al = _mod()
    r = _fc(host="codex", subagents="unavailable", mirrors="domain,bogus") + "\n"
    v = al.check_fanout_consistency(r)
    hit = [x for x in v if x["kind"] == "mirrors-unknown-token"]
    assert hit and "bash setup.sh" in hit[0].get("detail", "")
    assert "sdflow-init update" not in hit[0].get("detail", "")


# --- absorb-gstack-autoplan Task 1：spec-review 广审自持化(strategy+plan-eng→broad)新形态 + mode 新枚举值 ---

def test_fanout_spec_review_single_batch_mirrors_broad_scenario():
    """DD1 单批 dispatch:spec-review 的 strategy/plan-eng 两广审镜随领域/对抗/接地镜一次性 fan-out——
    `mirrors=` 单行同时含 broad 与其余镜 token（两广审镜折叠为同一 `broad` token，枚举零改动，
    只补覆盖新形态）。host=codex subagents=available 时应合法放行。"""
    al = _mod()
    r = (_lm(layer="spec-review", lens="broad", host="codex", runner="codex") + "\n"
         + _fc(host="codex", subagents="available",
               mirrors="broad,domain,adversarial,grounding,history") + "\n")
    assert al.check_fanout_consistency(r) == []

def test_fanout_spec_review_unavailable_mirrors_broad_alone_ok():
    """spec-review 广审在子代理不可用时降级为主 session 亲做（DD3 恒跑守卫）——mirrors="broad" 单独
    出现于 unavailable 场景须合法放行（broad 不进 dead-fanout 计数集）。"""
    al = _mod()
    r = (_lm(layer="spec-review", lens="broad", host="codex", runner="codex") + "\n"
         + _fc(host="codex", subagents="unavailable", mirrors="broad") + "\n")
    assert al.check_fanout_consistency(r) == []

def test_step1_broad_review_mode_main_session_lint_passes():
    """🔒 同 test_step1_broad_review_mode_subagent_lint_passes：新枚举值 mode="main-session"（DD3 探针判
    子代理不可用时广审镜由主 session 亲做的降级路径）同样不应触发任何与 mode 相关的校验（只校验锚族
    存在性，mode 值为主 session 自报、无机械枚举校验，design.md DD3 诚实边界）。"""
    al = _mod()
    r = ('<!-- sdflow:step1-broad-review v1 mode="main-session" -->\n'
         + _ov(host="claude", runner="codex", reason_code="ok") + "\n"
         + '<!-- sdflow:hr-tg v1 hit="none" -->\n')
    assert al.check_existence(r, "code-review", metrics_on=False) == []


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
           '<!-- sdflow:step1-broad-review v1 mode="native" -->\n'
           '<!-- sdflow:declared-sites v1 declared="code-voice" -->\n')
    rpt_path = tmp_path / "r.md"; rpt_path.write_text(rpt, encoding="utf-8")
    r = _run(rpt_path, "code-review", root)
    assert r.returncode == 0, r.stderr


# --- async-outside-voice §3.5（F-C）：declared-sites per-site 完整性机械核 -----------------
# 家族级门（"outside-voice" 有 ≥1 行即过）放过「并发 2 站点漏收一个」。本组测 per-site 核：
# declared-sites 锚声明「本层应有锚站点集」，脚本重算期望集（layer + HR-TG∩）并与实落 site= 集比对。

def _ds(declared):
    return f'<!-- sdflow:declared-sites v1 declared="{declared}" -->'

_HR_TG_EMPTY = '<!-- sdflow:hr-tg v1 hit="none" declared="" -->'
# HR-TG∩≠∅（TG-04 在 _HR_TG_SUBSET 内）
_HR_TG_HIT = '<!-- sdflow:hr-tg v1 hit="TG-04" declared="TG-04" evidence="x" -->'


def _dsv(report, layer="code-review", subset=None):
    al = _mod()
    return al.check_declared_sites(report, layer, subset if subset is not None else _HR_TG_SUBSET)


def test_ds_ok_code_review_no_hrtg():
    """正例：code-review + HR-TG∩=∅ → 期望 {code-voice}，declared 与实落均相符 → 零违规。"""
    rpt = _ov(site="code-voice") + "\n" + _HR_TG_EMPTY + "\n" + _ds("code-voice") + "\n"
    assert _dsv(rpt) == []


def test_ds_ok_spec_review_with_hrtg():
    """正例：spec-review + HR-TG∩≠∅ → 期望 {design-voice,hr-tg}，两锚俱在 → 零违规。"""
    rpt = (_ov(site="design-voice") + "\n" + _ov(site="hr-tg") + "\n"
           + _HR_TG_HIT + "\n" + _ds("design-voice,hr-tg") + "\n")
    assert _dsv(rpt, layer="spec-review") == []


def test_ds_declared_more_than_actual_is_red():
    """🔴 本票核心失效模式：并发 2 站点漏收一个——declared 有 hr-tg 但报告无该锚 → site-missing-anchor。"""
    rpt = _ov(site="design-voice") + "\n" + _HR_TG_HIT + "\n" + _ds("design-voice,hr-tg") + "\n"
    v = _dsv(rpt, layer="spec-review")
    assert any(x["kind"] == "site-missing-anchor" and x["detail"] == "hr-tg" for x in v)


def test_ds_declared_fewer_than_actual_is_red():
    """declared 少一个站点（实落多一条锚）→ site-unexpected-anchor；且缩水的 declared 同时违反公式。"""
    rpt = (_ov(site="design-voice") + "\n" + _ov(site="hr-tg") + "\n"
           + _HR_TG_HIT + "\n" + _ds("design-voice") + "\n")
    v = _dsv(rpt, layer="spec-review")
    assert any(x["kind"] == "site-unexpected-anchor" and x["detail"] == "hr-tg" for x in v)
    assert any(x["kind"] == "declared-not-expected" for x in v)


def test_ds_declared_empty_string_is_red():
    """declared="" （合法空串→空集）MUST 判红：空集永不等于期望集（该层恒有一个 base 站点）。

    行为本已 fail-closed，此处锁死，防后续把空串误当「本层无需站点」的合法豁免。
    """
    rpt = _ov(site="design-voice") + "\n" + _HR_TG_EMPTY + "\n" + _ds("") + "\n"
    v = _dsv(rpt, layer="spec-review")
    assert any(x["kind"] == "declared-not-expected" for x in v)
    assert any(x["kind"] == "site-unexpected-anchor" for x in v)


def test_ds_declared_shrink_and_drop_anchor_still_red():
    """🔴 反规避：模型同时缩 declared 又不落锚（两边自洽）——公式重算仍判红，不放行。"""
    rpt = _ov(site="design-voice") + "\n" + _HR_TG_HIT + "\n" + _ds("design-voice") + "\n"
    v = _dsv(rpt, layer="spec-review")
    assert [x["kind"] for x in v] == ["declared-not-expected"]


def test_ds_layer_base_site_is_layer_specific():
    """按层区分：code-review 层 declared 写 design-voice → declared-not-expected（站点集非站点无关）。"""
    rpt = _ov(site="design-voice") + "\n" + _HR_TG_EMPTY + "\n" + _ds("design-voice") + "\n"
    v = _dsv(rpt, layer="code-review")
    assert any(x["kind"] == "declared-not-expected" for x in v)


def test_ds_reuse_state_design_voice_no_dispatch_still_green():
    """🔴 G1：复用态 design-voice（guard=none、未 dispatch）照样落锚 → 期望集按「应有锚」定义，判绿。
    若按「应 dispatch 集」定义，此最常见路径会假红。"""
    rpt = (_ov(site="design-voice", guard="none", host="claude", runner="codex", reason_code="ok") + "\n"
           + _HR_TG_EMPTY + "\n" + _ds("design-voice") + "\n")
    assert _dsv(rpt, layer="spec-review") == []


def test_ds_missing_anchor_is_violation_not_silent_pass():
    """declared-sites 锚缺失 MUST NOT 静默放行（否则整个门可由省略绕过）。"""
    rpt = _ov(site="code-voice") + "\n" + _HR_TG_EMPTY + "\n"
    v = _dsv(rpt)
    assert any(x["kind"] == "missing-declared-sites" for x in v)


def test_ds_multiple_anchors_fail_closed():
    """≥2 条 declared-sites 锚 → fail-closed，MUST NOT 静默取首。"""
    rpt = (_ov(site="code-voice") + "\n" + _HR_TG_EMPTY + "\n"
           + _ds("code-voice") + "\n" + _ds("code-voice,hr-tg") + "\n")
    v = _dsv(rpt)
    assert any(x["kind"] == "multi-declared-sites" for x in v)


def test_ds_missing_declared_field():
    rpt = (_ov(site="code-voice") + "\n" + _HR_TG_EMPTY + "\n"
           + '<!-- sdflow:declared-sites v1 -->' + "\n")
    v = _dsv(rpt)
    assert any(x["kind"] == "missing-field" and x["field"] == "declared" for x in v)


def test_ds_dup_key_fail_closed():
    """重复 declared= → dup-key 且不进比对（镜像 check_legal_combo 的末值胜防线）。"""
    rpt = (_ov(site="code-voice") + "\n" + _HR_TG_EMPTY + "\n"
           + '<!-- sdflow:declared-sites v1 declared="code-voice" declared="code-voice,hr-tg" -->' + "\n")
    v = _dsv(rpt)
    assert any(x["kind"] == "dup-key" and x["field"] == "declared" for x in v)


def test_ds_malformed_site_csv():
    """域外站点记号 / 空 cell → malformed-site-csv（fail-closed，不宽松抽取）。"""
    for bad in ("code-voice,bogus-site", "code-voice,,hr-tg", ",code-voice"):
        rpt = _ov(site="code-voice") + "\n" + _HR_TG_EMPTY + "\n" + _ds(bad) + "\n"
        v = _dsv(rpt)
        assert any(x["kind"] == "malformed-site-csv" for x in v), bad


def test_ds_duplicate_and_order():
    rpt = _ov(site="code-voice") + "\n" + _ov(site="hr-tg") + "\n" + _HR_TG_HIT + "\n"
    v_dup = _dsv(rpt + _ds("code-voice,code-voice,hr-tg") + "\n")
    assert any(x["kind"] == "declared-sites-duplicate" for x in v_dup)
    v_ord = _dsv(rpt + _ds("hr-tg,code-voice") + "\n")
    assert any(x["kind"] == "declared-sites-not-canonical-order" for x in v_ord)


def test_ds_outside_voice_missing_site_field():
    """outside-voice 锚缺 site= → 无从归站点，报 missing-field（矩阵必填字段集未被修改）。"""
    al = _mod()
    ov_nosite = '<!-- sdflow:outside-voice v1 host="claude" runner="codex" reason_code="ok" -->'
    rpt = ov_nosite + "\n" + _HR_TG_EMPTY + "\n" + _ds("code-voice") + "\n"
    v = _dsv(rpt)
    assert any(x["kind"] == "missing-field" and x["field"] == "site" for x in v)
    assert al.OUTSIDE_VOICE_REQUIRED_FIELDS == ("host", "runner", "reason_code")   # 矩阵必填集未动


def test_ds_duplicate_site_anchors():
    """同站点两条 outside-voice 锚 → duplicate-site-anchor（集合会吞掉歧义，须显式拦）。"""
    rpt = (_ov(site="code-voice") + "\n" + _ov(site="code-voice") + "\n"
           + _HR_TG_EMPTY + "\n" + _ds("code-voice") + "\n")
    v = _dsv(rpt)
    assert any(x["kind"] == "duplicate-site-anchor" for x in v)


def test_ds_hr_tg_unresolved_fail_closed():
    """HR-TG∩ 算不出（hr-tg 锚缺失 / 非唯一 / declared 畸形）→ hr-tg-unresolved，MUST NOT 猜期望集。"""
    base = _ov(site="code-voice") + "\n" + _ds("code-voice") + "\n"
    assert any(x["kind"] == "hr-tg-unresolved" for x in _dsv(base))                       # 缺
    assert any(x["kind"] == "hr-tg-unresolved"
               for x in _dsv(base + _HR_TG_EMPTY + "\n" + _HR_TG_HIT + "\n"))             # 非唯一
    assert any(x["kind"] == "hr-tg-unresolved"
               for x in _dsv(base + '<!-- sdflow:hr-tg v1 hit="none" declared="TG-,x" -->' + "\n"))


def test_ds_fenced_template_anchors_no_false_positive():
    """🔴 G4 核心：报告正文围栏内的模版/示例锚（本 change 报告自身即在讨论锚格式）MUST NOT 被计入。
    围栏内放「相反的」declared-sites + 多余 outside-voice 模版锚，真锚在围栏外 → 仍判绿。"""
    rpt = (
        "# 报告\n\n"
        "锚模版如下：\n\n"
        "```\n"
        + _ov(site="design-voice") + "\n"
        + _ov(site="hr-tg") + "\n"
        + _ds("design-voice,hr-tg") + "\n"
        + '<!-- sdflow:hr-tg v1 hit="TG-04" declared="TG-04" evidence="示例" -->' + "\n"
        "```\n\n"
        "~~~\n" + _ov(site="hr-tg") + "\n~~~\n\n"
        + _ov(site="code-voice") + "\n" + _HR_TG_EMPTY + "\n" + _ds("code-voice") + "\n"
    )
    assert _dsv(rpt) == []


def test_ds_reuses_fence_outside_lines_no_bare_grep():
    """实现须复用本文件既有 fence 口径：给 fence_outside_lines 打桩（只放行第一行）后，
    check_declared_sites 的可见行随之变化 → 证明它走的是该函数、而非另起裸 grep 解析路径。"""
    al = _mod()
    rpt = _ov(site="code-voice") + "\n" + _HR_TG_EMPTY + "\n" + _ds("code-voice") + "\n"
    assert al.check_declared_sites(rpt, "code-review", _HR_TG_SUBSET) == []
    orig = al.fence_outside_lines
    al.fence_outside_lines = lambda text: iter(text.splitlines()[:1])
    try:
        v = al.check_declared_sites(rpt, "code-review", _HR_TG_SUBSET)
    finally:
        al.fence_outside_lines = orig
    assert any(x["kind"] == "missing-declared-sites" for x in v)


def test_ds_self_referential_real_report_no_false_positive():
    """🔴 自指测试：拿本 change 自己的 spec-review-report.md（真实文件，正文在讨论锚格式）跑，
    补上应有的 declared-sites 锚 + 围栏内模版锚后 MUST 零违规（裸 grep 实现必在此假阳）。"""
    # 归档后 active 路径消失 ⇒ 回落到 archive/ 找同名报告，否则本用例会在归档当天起【永久跳过】、
    # 自指覆盖面静默归零（与它自己要防的 dogfood 盲区同型）。
    root = Path(__file__).resolve().parents[5]
    real = root / "openspec/changes/async-outside-voice/spec-review-report.md"
    if not real.exists():
        cands = sorted(root.glob("openspec/changes/archive/*-async-outside-voice/spec-review-report.md"))
        real = cands[-1] if cands else real
    if not real.exists():
        pytest.skip(f"真实报告不在 active 也不在 archive: {real}")
    text = real.read_text(encoding="utf-8")
    # 该报告 hr-tg 锚 hit=TG-09,TG-17,TG-26 ⇒ HR-TG∩≠∅；实落 site=design-voice + hr-tg
    subset = {"TG-09", "TG-17", "TG-26"}
    augmented = (text + "\n" + _ds("design-voice,hr-tg") + "\n\n"
                 + "```\n" + _ov(site="code-voice") + "\n" + _ds("code-voice") + "\n```\n")
    al = _mod()
    v = al.check_declared_sites(augmented, "spec-review", subset)
    assert v == [], v


def test_ds_cli_end_to_end_violation(tmp_path):
    """端到端：main() 接入 per-site 核——漏收一个站点 → returncode 1 + JSON 含 site-missing-anchor。"""
    root = _write_config(tmp_path, "metrics:\n  enabled: false\n")
    rpt = (_ov(site="code-voice") + "\n"
           + '<!-- sdflow:hr-tg v1 hit="TG-04" declared="TG-04" evidence="x" -->\n'
           '<!-- sdflow:step1-broad-review v1 mode="native" -->\n'
           + _ds("code-voice,hr-tg") + "\n")
    rpt_path = tmp_path / "r.md"; rpt_path.write_text(rpt, encoding="utf-8")
    r = _run(rpt_path, "code-review", root)
    assert r.returncode == 1, r.stderr
    assert any(x["kind"] == "site-missing-anchor" for x in json.loads(r.stdout)["violations"])


def test_ds_cli_end_to_end_clean(tmp_path):
    """端到端正例：站点集自洽 → CLEAN（exit 0）。"""
    root = _write_config(tmp_path, "metrics:\n  enabled: false\n")
    rpt = (_ov(site="code-voice") + "\n" + _ov(site="hr-tg") + "\n"
           + '<!-- sdflow:hr-tg v1 hit="TG-04" declared="TG-04" evidence="x" -->\n'
           '<!-- sdflow:step1-broad-review v1 mode="native" -->\n'
           + _ds("code-voice,hr-tg") + "\n")
    rpt_path = tmp_path / "r.md"; rpt_path.write_text(rpt, encoding="utf-8")
    r = _run(rpt_path, "code-review", root)
    assert r.returncode == 0, r.stderr
