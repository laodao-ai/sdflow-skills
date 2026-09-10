"""SKILL.md 文案机械守（同 sdflow-ship/tests/test_skill_text.py 惯例：只钉关键词在场，不重复逻辑测试）。

本文件守 IO-1（implementer dispatch 携带信号权威归属声明，change fix-design-gate-freshness-proxy）：
dispatch 契约的必填槽须含信号权威表，且表内归属与 ship_gate.py 实际消费的完成判据一致。
"""
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"


def text():
    return SKILL.read_text(encoding="utf-8")


def test_dispatch_carries_signal_authority_table():
    """IO-1 Scenario①：dispatch prompt 必含槽里有信号权威表（正面陈述，非禁令清单）。"""
    t = text()
    assert "信号权威表" in t
    # 必填槽定位：权威表须落在「每 ticket 派 fresh implementer」的 `dispatch prompt 必含：` 列表内，
    # 不能只是文末某处泛泛提一句。
    head = t.split("dispatch prompt 必含：", 1)
    assert len(head) == 2, "dispatch 必含槽列表锚点缺失"
    slot = head[1].split("\n## ", 1)[0]
    assert "信号权威表" in slot, "信号权威表不在 dispatch 必含槽内"
    # 正面陈述：表格形式列归属（范畴 → 权威在哪 → 谁写），而非「不许碰 X」的禁令清单。
    assert "权威在哪" in slot and "范畴" in slot


def test_authority_table_matches_gate_consumed_criteria():
    """IO-1 Scenario①的 AND 子句：表内容与 ship_gate.py 实际消费的完成判据一致。

    gate 完成集 = checkpoint 标签通道（TAG_RE，窗口 [plan 首次提交 sha, HEAD] 闭区间）
                ∪ 复选框通道（_parse_plan 按 `### Task <n>:` 分段绑定、段内全勾）。
    设计域失鲜监视集 = proposal / design / tasks.md / specs/。
    """
    t = text()
    slot = t.split("dispatch prompt 必含：", 1)[1].split("\n## ", 1)[0]
    # 完成信号两通道都在场
    assert "验收复选框" in slot
    assert "checkpoint(<change>:task<N>-<slug>)" in slot
    # 完成信号的写入时机（双轴审通过后由执行模式补打，implementer 不自行写）
    assert "双轴审通过后" in slot
    # 设计工件四件套全在场（gate design 域监视集）
    for artifact in ("proposal.md", "design.md", "specs/", "tasks.md"):
        assert artifact in slot, f"设计工件 {artifact} 未在权威表中声明归属"
    # 与 gate 消费面对齐的显式锚（防表内声明 gate 不读取的信号源）
    assert "ship_gate.py" in slot


def test_fix_dispatch_also_carries_authority_table():
    """IO-1：fix 轮次子代理同为 fresh context，dispatch 同样必带权威表。"""
    t = text()
    assert "fix 子代理的 dispatch prompt 同样 MUST 原文携带" in t
    # 切到下一个段落边界再断言邻近性——用固定字符窗口（如 [:200]）会因措辞增删而脆
    tail = t.split("fix 子代理的 dispatch prompt 同样 MUST 原文携带", 1)[1]
    assert "信号权威表" in tail.split("\n\n", 1)[0]


def test_authority_table_absence_not_silently_degraded():
    """IO-1 Scenario②：权威表缺席 MUST 显式停，不得以「gate 已兜住」为由静默放行。"""
    t = text()
    assert "权威表缺席不得静默降级" in t
    tail = t.split("权威表缺席不得静默降级", 1)[1][:600]
    assert "MUST 显式停" in tail or "显式停并报告" in tail
    # 独立成立声明：不因 gate 侧防线在场而可省
    assert "各自独立成立" in tail
