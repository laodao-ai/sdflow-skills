from pathlib import Path

SR = Path(__file__).resolve().parents[2] / "sdflow-spec-review" / "SKILL.md"

def test_step2_serial_must_sentence():
    t = SR.read_text(encoding="utf-8")
    assert "MUST 待 Step1" in t and "checkpoint 完成后才 fan-out" in t
    assert "禁止与 Step1 并行" in t
    assert "增量核对" in t   # 历史并行补救句
