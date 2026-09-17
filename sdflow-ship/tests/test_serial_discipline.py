from pathlib import Path

SR = Path(__file__).resolve().parents[2] / "sdflow-spec-review" / "SKILL.md"


def test_t20_serial_discipline_retired_single_batch_dispatch():
    """T20 的 checkpoint 串行分治已退役。完整 roster 按容量分批派发；容量只改变批次，
    不恢复 Step1 后才派领域/对抗镜的依赖，也不删除镜。各镜仍互不依赖。
    """
    t = SR.read_text(encoding="utf-8")
    assert "MUST 待 Step1 checkpoint 完成后才 fan-out" not in t
    assert "接地镜 MAY 与 Step1 并行起跑" not in t
    assert "SHALL NOT 自动补跑接地镜" not in t
    assert "完整 roster 分批 dispatch" in t
    assert "按容量逐批派完" in t
    assert "互不依赖" in t
