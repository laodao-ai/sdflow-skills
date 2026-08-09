from pathlib import Path

SR = Path(__file__).resolve().parents[2] / "sdflow-spec-review" / "SKILL.md"


def test_t20_serial_discipline_retired_single_batch_dispatch():
    """absorb-gstack-autoplan DD1：T20「领域/对抗镜须待 Step1 checkpoint 完成后才 fan-out」的
    串行分治条款随旧两段 dispatch 结构一并退役——广审双镜（strategy/plan-eng）不再是外部工具产
    amendment 再等其余镜跟进的两段结构，而是与领域镜/对抗镜/接地镜/design-voice 同批一条消息内
    并行派出、互不依赖。本用例反向验证旧串行措辞已清零、新单批措辞已到位（同 test_step2_serial_
    must_sentence 的反面，见 git blame：旧用例断言的三句话本身就是本次要删除的内容）。
    """
    t = SR.read_text(encoding="utf-8")
    assert "MUST 待 Step1 checkpoint 完成后才 fan-out" not in t
    assert "接地镜 MAY 与 Step1 并行起跑" not in t
    assert "SHALL NOT 自动补跑接地镜" not in t
    assert "单批全并行 dispatch" in t
    assert "互不依赖" in t
