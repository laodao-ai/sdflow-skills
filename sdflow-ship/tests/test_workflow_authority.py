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
    # [gate-checkpoint-hardening T36/SR-4/SR-5] checkpoint 标签格式权威源单一化到
    # ship_gate.py 的 TAG_RE：workflow.md 保留一处格式串样例（含权威引用），
    # sdflow-ship/SKILL.md 只引用（TAG_RE/workflow.md），不复述完整格式串。
    wf = Path(__file__).resolve().parents[2] / "sdflow-init" / "assets" / "workflow" / "workflow.md"
    w = wf.read_text(encoding="utf-8")
    assert "<change>:task<N>-<slug>" in w   # 格式源在 workflow.md
    assert "TAG_RE" in w   # workflow.md 标注权威见 ship_gate.py TAG_RE

    skill = Path(__file__).resolve().parents[1] / "SKILL.md"   # parents[1] = sdflow-ship/
    s = skill.read_text(encoding="utf-8")
    assert "<change>:task<N>-<slug>" not in s   # SKILL 不再复述完整格式串
    assert "TAG_RE" in s   # SKILL 改为引用式（引用 workflow.md/TAG_RE）
