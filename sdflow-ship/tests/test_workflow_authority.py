from pathlib import Path

_WFDIR = Path(__file__).resolve().parents[2] / "sdflow-init" / "assets" / "workflow"
WF = _WFDIR / "workflow.md"

def test_orchestrator_entry_row():
    """`/sdflow-ship` 在步骤表中作为阶段三的唯一顶层步骤（步骤 5）。"""
    t = WF.read_text(encoding="utf-8")
    assert "/sdflow-ship" in t
    assert "5.5" not in t, "workflow.md 不该再出现已退役的条件步骤 5.5（embedded-test-sop）"

def test_decision4_no_self_confidence():
    t = WF.read_text(encoding="utf-8")
    assert "有把握自动选" not in t
    assert "对抗镜复核" in t

def test_skill_does_not_restate_the_format():
    """单一源：sdflow-ship/SKILL.md 只引用，不复述完整格式串〔T36/SR-4/SR-5〕。"""
    s = (Path(__file__).resolve().parents[1] / "SKILL.md").read_text(encoding="utf-8")
    assert "<change>:task<N>-<slug>" not in s   # 不复述完整格式串
    assert "TAG_RE" in s                        # 改为引用式
