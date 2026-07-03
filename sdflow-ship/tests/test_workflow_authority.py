from pathlib import Path

WF = Path(__file__).resolve().parents[2] / "sdflow-init" / "assets" / "workflow" / "workflow.md"

def test_orchestrator_entry_row():
    t = WF.read_text(encoding="utf-8")
    assert "/sdflow-ship" in t and "5.5" in t

def test_decision4_no_self_confidence():
    t = WF.read_text(encoding="utf-8")
    assert "有把握自动选" not in t
    assert "对抗镜复核" in t

def test_step6_tag_contract():
    t = WF.read_text(encoding="utf-8")
    assert "task<N>-" in t and "checkpoint-commit.sh" in t
    assert "implementer" in t or "实现子代理" in t   # D1 注入点：由 implementer 执行
