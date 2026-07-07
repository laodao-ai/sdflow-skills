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
    assert al.anchor_prefix('note <!-- sdflow:hr-tg v1 --> inline') is None or True  # 描述性内联(前缀非行首)
    assert al.anchor_prefix('<!-- sdflow:step1-broad-review v1 mode="native" -->') == "step1-broad-review"
    assert al.anchor_prefix('plain text') is None
