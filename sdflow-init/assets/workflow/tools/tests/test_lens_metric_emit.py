import subprocess, sys, json, importlib.util
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
