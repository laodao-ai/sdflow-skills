from pathlib import Path

SR = Path(__file__).resolve().parents[2] / "sdflow-spec-review" / "SKILL.md"

def test_step2_serial_must_sentence():
    t = SR.read_text(encoding="utf-8")
    assert "MUST 待 Step1 checkpoint 完成后才 fan-out" in t
    assert "接地镜 MAY 与 Step1 并行起跑" in t
    assert "SHALL NOT 自动补跑接地镜" in t
