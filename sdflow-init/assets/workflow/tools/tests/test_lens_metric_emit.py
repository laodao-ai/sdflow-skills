import subprocess, sys, json, importlib.util, pytest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
SCRIPT = TOOLS / "lens_metric_emit.py"
CONTRACT = TOOLS.parent / "lens-metric-contract.md"

def _mod():
    spec = importlib.util.spec_from_file_location("lens_metric_emit", SCRIPT)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def test_load_enums_real_contract():
    e = _mod().load_enums(CONTRACT)
    assert e["layer"] == {"spec-review", "code-review"}
    assert e["lens"] == {"domain","adversarial","grounding","history","outside-voice","broad"}
    assert e["runner"] == {"claude","codex","claude-fallback"}
    assert e["sev_levels"] == ("致","高","中","低")
    assert e["sev_re"].match("致1/高2/中0/低3") and not e["sev_re"].match("致1/高2/中0")

def test_load_fold_real_contract():
    m = _mod(); e = m.load_enums(CONTRACT); fold = m.load_fold(CONTRACT, e)
    assert fold["对抗镜1"] == "adversarial" and fold["codex"] == "outside-voice"
    assert all(v in e["lens"] for v in fold.values())        # codomain ⊆ lens enum
    assert "domain" not in fold                              # 恒等项不列块

def test_load_enums_missing_block(tmp_path):
    m = _mod(); bad = tmp_path/"c.md"; bad.write_text("# no blocks", encoding="utf-8")
    import pytest
    with pytest.raises(m.EmitError): m.load_enums(bad)

def test_load_fold_dup_key_fail_closed(tmp_path):
    m = _mod(); e = m.load_enums(CONTRACT)
    c = tmp_path/"c.md"
    c.write_text("```lens-metric-fold\n对抗镜1: adversarial\n对抗镜1: broad\n```\n", encoding="utf-8")
    import pytest
    with pytest.raises(m.EmitError): m.load_fold(c, e)

def test_load_fold_codomain_out_of_enum_fail_closed(tmp_path):
    m = _mod(); e = m.load_enums(CONTRACT)
    c = tmp_path/"c.md"
    c.write_text("```lens-metric-fold\n某镜: newlens\n```\n", encoding="utf-8")
    import pytest
    with pytest.raises(m.EmitError): m.load_fold(c, e)

def test_fold_hit_identity_passthrough():
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e)
    assert m.fold_hit({"raw":"domain"}, e, f) == ("domain","claude","—")

def test_fold_hit_nonidentity_map():
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e)
    assert m.fold_hit({"raw":"对抗镜2"}, e, f) == ("adversarial","claude","—")

def test_fold_hit_outside_voice_needs_runner_site():
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e)
    assert m.fold_hit({"raw":"codex","runner":"codex","site":"hr-tg"}, e, f) == ("outside-voice","codex","hr-tg")
    import pytest
    with pytest.raises(m.EmitError): m.fold_hit({"raw":"codex"}, e, f)      # 缺 runner/site

def test_fold_hit_unknown_raw_fail_closed_not_broad():
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e)
    import pytest
    with pytest.raises(m.EmitError): m.fold_hit({"raw":"神秘镜"}, e, f)     # SR-E 不塞 broad

def test_fold_hit_site_injection_fail_closed():
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e)
    import pytest
    with pytest.raises(m.EmitError): m.fold_hit({"raw":"codex","runner":"codex","site":'a"b'}, e, f)

def _ef():
    m = _mod(); e = m.load_enums(CONTRACT); f = m.load_fold(CONTRACT, e); return m, e, f

def test_reduce_single_accepted():
    m, e, f = _ef()
    roster = [{"lens":"domain","runner":"claude","site":"—"},
              {"lens":"broad","runner":"claude","site":"—"},
              {"lens":"outside-voice","runner":"codex","site":"design-voice"}]
    findings = [{"hits":[{"raw":"domain"}], "verdict":"采纳", "sev":"高"}]
    lines = m.reduce(roster, findings, "spec-review", e, f)
    dom = [l for l in lines if 'lens="domain"' in l][0]
    assert 'findings="1"' in dom and '采纳="1"' in dom and '独立="1"' in dom
    assert 'sev="致0/高1/中0/低0"' in dom
    # 零-finding 行全零
    ov = [l for l in lines if 'lens="outside-voice"' in l][0]
    assert 'findings="0"' in ov and 'sev="致0/高0/中0/低0"' in ov and 'site="design-voice"' in ov

def test_reduce_coreport_no_independent():
    m, e, f = _ef()
    roster = [{"lens":"domain","runner":"claude","site":"—"},
              {"lens":"outside-voice","runner":"codex","site":"hr-tg"},
              {"lens":"broad","runner":"claude","site":"—"}]
    findings = [{"hits":[{"raw":"domain"},{"raw":"codex","runner":"codex","site":"hr-tg"}],
                 "verdict":"采纳","sev":"中"}]
    lines = m.reduce(roster, findings, "spec-review", e, f)
    for lens in ("domain","outside-voice"):
        row = [l for l in lines if f'lens="{lens}"' in l][0]
        assert '采纳="1"' in row and '独立="0"' in row     # 共抓：各记采纳、均不独立

def test_reduce_same_type_multi_instance_independent():
    m, e, f = _ef()
    roster = [{"lens":"adversarial","runner":"claude","site":"—"},
              {"lens":"broad","runner":"claude","site":"—"},
              {"lens":"outside-voice","runner":"codex","site":"hr-tg"}]
    findings = [{"hits":[{"raw":"对抗镜1"},{"raw":"对抗镜2"}], "verdict":"采纳","sev":"致"}]
    adv = [l for l in m.reduce(roster, findings, "spec-review", e, f) if 'lens="adversarial"' in l][0]
    assert '采纳="1"' in adv and '独立="1"' in adv and 'sev="致1/高0/中0/低0"' in adv

def _base_roster():
    return [{"lens":"broad","runner":"claude","site":"—"},
            {"lens":"outside-voice","runner":"codex","site":"hr-tg"}]

def test_reduce_empty_hits_fail_closed():
    m, e, f = _ef()
    with pytest.raises(m.EmitError):
        m.reduce(_base_roster(), [{"hits":[], "verdict":"采纳","sev":"高"}], "spec-review", e, f)

def test_reduce_accepted_missing_sev_fail_closed():
    m, e, f = _ef()
    with pytest.raises(m.EmitError):
        m.reduce(_base_roster(), [{"hits":[{"raw":"broad"}], "verdict":"采纳"}], "spec-review", e, f)

def test_reduce_bad_verdict_fail_closed():
    m, e, f = _ef()
    with pytest.raises(m.EmitError):
        m.reduce(_base_roster(), [{"hits":[{"raw":"broad"}], "verdict":"通过","sev":"高"}], "spec-review", e, f)

def test_reduce_bad_layer_fail_closed():
    m, e, f = _ef()
    with pytest.raises(m.EmitError):
        m.reduce(_base_roster(), [], "review", e, f)

def test_reduce_finding_lens_not_in_roster_fail_closed():
    m, e, f = _ef()
    with pytest.raises(m.EmitError):              # C4：domain 不在 roster
        m.reduce(_base_roster(), [{"hits":[{"raw":"domain"}], "verdict":"采纳","sev":"高"}], "spec-review", e, f)

def test_reduce_roster_missing_mandatory_fail_closed():
    m, e, f = _ef()
    with pytest.raises(m.EmitError):              # 缺 outside-voice
        m.reduce([{"lens":"broad","runner":"claude","site":"—"}], [], "spec-review", e, f)

def test_reduce_roster_dup_key_fail_closed():
    m, e, f = _ef()
    r = _base_roster() + [{"lens":"broad","runner":"claude","site":"—"}]
    with pytest.raises(m.EmitError):
        m.reduce(r, [], "spec-review", e, f)


def _run(inp_path, layer="spec-review"):
    return subprocess.run([sys.executable, str(SCRIPT), "--layer", layer, "--input", str(inp_path)],
                          capture_output=True, text=True)


def test_cli_valid_emits(tmp_path):
    inp = tmp_path/"in.json"
    inp.write_text(json.dumps({
        "roster":[{"lens":"broad","runner":"claude","site":"—"},
                  {"lens":"outside-voice","runner":"codex","site":"hr-tg"}],
        "findings":[{"hits":[{"raw":"broad"}], "verdict":"采纳","sev":"高"}]}, ensure_ascii=False), encoding="utf-8")
    r = _run(inp)
    assert r.returncode == 0
    assert r.stdout.count("<!-- sdflow:lens-metric v1") == 2


def test_cli_bad_json_exit1_no_stdout(tmp_path):
    inp = tmp_path/"in.json"; inp.write_text("{not json", encoding="utf-8")
    r = _run(inp)
    assert r.returncode == 1 and "<!-- sdflow:lens-metric" not in r.stdout and r.stderr.strip()


def test_cli_partial_fail_no_partial_anchor(tmp_path):
    # 第 2 条 finding 坏（采纳缺 sev）→ 全失败、stdout 无任何锚（all-or-nothing）
    inp = tmp_path/"in.json"
    inp.write_text(json.dumps({
        "roster":[{"lens":"broad","runner":"claude","site":"—"},
                  {"lens":"outside-voice","runner":"codex","site":"hr-tg"}],
        "findings":[{"hits":[{"raw":"broad"}],"verdict":"采纳","sev":"高"},
                    {"hits":[{"raw":"broad"}],"verdict":"采纳"}]}, ensure_ascii=False), encoding="utf-8")
    r = _run(inp)
    assert r.returncode == 1 and "<!-- sdflow:lens-metric" not in r.stdout


def test_cli_idempotent_cross_process(tmp_path):
    inp = tmp_path/"in.json"
    inp.write_text(json.dumps({
        "roster":[{"lens":"broad","runner":"claude","site":"—"},
                  {"lens":"domain","runner":"claude","site":"—"},
                  {"lens":"outside-voice","runner":"codex","site":"hr-tg"}],
        "findings":[{"hits":[{"raw":"domain"}],"verdict":"采纳","sev":"中"}]}, ensure_ascii=False), encoding="utf-8")
    import os
    env0 = dict(os.environ, PYTHONHASHSEED="0"); env1 = dict(os.environ, PYTHONHASHSEED="1")
    a = subprocess.run([sys.executable, str(SCRIPT),"--layer","spec-review","--input",str(inp)],
                       capture_output=True, text=True, env=env0).stdout
    b = subprocess.run([sys.executable, str(SCRIPT),"--layer","spec-review","--input",str(inp)],
                       capture_output=True, text=True, env=env1).stdout
    assert a == b and a.count("lens-metric v1") == 3      # 跨 hashseed 字节一致


def test_cli_null_roster_clean_fail(tmp_path):
    inp = tmp_path/"in.json"
    inp.write_text('{"roster": null, "findings": []}', encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT),"--layer","spec-review","--input",str(inp)],
                       capture_output=True, text=True)
    assert r.returncode == 1 and r.stdout == "" and "FAIL" in r.stderr and "Traceback" not in r.stderr


# --- 产出↔校验/聚合一致性守卫（跨模块单一源；importlib 加载真实模块，非脚本 import） ---

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mm = importlib.util.module_from_spec(spec); spec.loader.exec_module(mm); return mm

AL = TOOLS / "anchor_lint.py"
# repo_root/sdflow-retro/scripts/lens_metric_aggregate.py — TOOLS =
# .../sdflow-init/assets/workflow/tools，需 4 层 .parent 才到 repo root
# （brief 草稿写 3 层算错，落到 sdflow-init/sdflow-retro/... 不存在；已按真实目录改正）。
AGG = TOOLS.parent.parent.parent.parent / "sdflow-retro" / "scripts" / "lens_metric_aggregate.py"

def test_emit_then_check_lens_metric_clean(tmp_path):
    m, e, f = _ef()
    roster = [{"lens":"broad","runner":"claude","site":"—"},
              {"lens":"outside-voice","runner":"codex","site":"hr-tg"}]
    lines = m.reduce(roster, [{"hits":[{"raw":"broad"}],"verdict":"采纳","sev":"高"}], "spec-review", e, f)
    al = _load("anchor_lint", AL); enums = al.load_enums(CONTRACT)
    report = "\n".join(lines) + "\n"
    assert al.check_lens_metric(report, "spec-review", enums) == []   # 无违规（C5 精确口径）

def test_load_enums_equivalence():
    m = _mod(); al = _load("anchor_lint", AL)
    me, ae = m.load_enums(CONTRACT), al.load_enums(CONTRACT)
    for k in ("layer","lens","runner"):
        assert me[k] == ae[k]
    assert me["sev_re"].pattern == ae["sev_re"].pattern       # C10 逐字段等价

def test_fold_codomain_subset_lens_enum():
    m = _mod(); e = m.load_enums(CONTRACT); fold = m.load_fold(CONTRACT, e)
    assert set(fold.values()) <= e["lens"]                   # C3

def test_aggregator_enum_matches_contract():
    m = _mod(); e = m.load_enums(CONTRACT); agg = _load("lens_metric_aggregate", AGG)
    assert agg.LENS_ENUM == e["lens"] and agg.LAYER_ENUM == e["layer"]   # C23

def test_min_lens_rows_matches_anchor_lint():
    m = _mod(); al = _load("anchor_lint", AL)
    assert set(m.MANDATORY_LENS) == set(al.MIN_LENS_ROWS)     # C17 分叉①=B
