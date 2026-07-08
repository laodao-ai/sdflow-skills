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
