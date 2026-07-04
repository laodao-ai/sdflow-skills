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
    # [ship-gate-hardening-2 T32] 主锚契约 = 命名空间格式 <change>:task<N>-（gate 只认当前
    # change 的标签，跨 change stacking 不污染完成集）；裸 task<N>- 旧格式向后兼容仍在文档。
    assert "<change>:task<N>-" in t and "checkpoint-commit.sh" in t
    assert "task<N>-" in t   # 裸格式向后兼容 token（子串，仍在文档）
    assert "implementer" in t or "实现子代理" in t   # D1 注入点：由 implementer 执行


def test_skill_producer_arg_namespaced():
    # [ship-gate-hardening-2 T32/G1] 消费引用 SKILL.md 与权威源同批改齐为命名空间格式
    skill = Path(__file__).resolve().parents[1] / "SKILL.md"   # parents[1] = sdflow-ship/
    s = skill.read_text(encoding="utf-8")
    assert "<change>:task<N>-<slug>" in s
