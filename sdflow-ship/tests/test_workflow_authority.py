from pathlib import Path

_WFDIR = Path(__file__).resolve().parents[2] / "sdflow-init" / "assets" / "workflow"
WF = _WFDIR / "workflow.md"
# checkpoint 标签格式串的单一源 —— prompt 拆分后它随 step6 搬进了 prompts/（模型取一行
# 不必再读 17KB 的 workflow.md）。守卫跟着搬，别退回去查 workflow.md（那里现在只有指针）。
STEP6 = _WFDIR / "prompts" / "step6-writing-plans.md"

def test_orchestrator_entry_row():
    t = WF.read_text(encoding="utf-8")
    assert "/sdflow-ship" in t and "5.5" in t

def test_decision4_no_self_confidence():
    t = WF.read_text(encoding="utf-8")
    assert "有把握自动选" not in t
    assert "对抗镜复核" in t

def test_step6_tag_contract():
    t = STEP6.read_text(encoding="utf-8")
    # [ship-gate-hardening-2 T32] 主锚契约 = 命名空间格式 <change>:task<N>-（gate 只认当前
    # change 的标签，跨 change stacking 不污染完成集）；裸 task<N>- 旧格式向后兼容仍在文档。
    assert "<change>:task<N>-" in t and "checkpoint-commit.sh" in t
    assert "task<N>-" in t   # 裸格式向后兼容 token（子串，仍在文档）
    assert "implementer" in t or "实现子代理" in t   # D1 注入点：由 implementer 执行


def test_workflow_tag_sample_actually_matches_TAG_RE():
    """⭐ workflow.md 里的格式串样例，MUST 真的被 ship_gate.py 的 TAG_RE 认。

    【为什么不再只查「TAG_RE」这五个字符在不在】（基准 1：能机械判定的别用字符串检查凑）：
    原守卫断言 workflow.md 里出现过 "TAG_RE" 字样，以此代表「标注了权威源」。
    但它【拦不住真正的漂移】——ship_gate.py 的 TAG_RE 改了，workflow.md 的样例纹丝不动，
    那五个字符还在，测试照绿。它守的是「有没有写那句话」，不是「格式对不对」。

    现在直接【拿真 TAG_RE 去认这个样例】：占位符实例化 → 拼成 checkpoint-commit.sh 会产出的
    commit subject → 断言 TAG_RE 匹配且捕获组正确。TAG_RE 一改而样例不跟，当场红。
    """
    import re
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from ship_gate import TAG_RE

    w = STEP6.read_text(encoding="utf-8")
    SAMPLE = "<change>:task<N>-<slug>"
    assert SAMPLE in w, "prompts/step6-writing-plans.md 丢了 checkpoint 标签格式串样例"

    # 把样例的占位符换成真值，拼出 checkpoint-commit.sh 实际产出的 subject
    tag = SAMPLE.replace("<change>", "add-pagination").replace("<N>", "3").replace("<slug>", "schema")
    subject = f"checkpoint({tag}): 实现 schema"

    m = TAG_RE.search(subject)
    assert m, f"step6 prompt 里的样例拼出的 subject 不被 TAG_RE 认：{subject!r}"
    assert m.group(1) == "add-pagination"   # 命名空间组 = change slug（T32：跨 change 不污染）
    assert m.group(2) == "3"                # 任务号组

    # 裸格式向后兼容（T32）—— 无命名空间的旧标签仍须被认
    assert TAG_RE.search("checkpoint(task3-schema): x")


def test_skill_does_not_restate_the_format():
    """单一源：sdflow-ship/SKILL.md 只引用，不复述完整格式串〔T36/SR-4/SR-5〕。"""
    s = (Path(__file__).resolve().parents[1] / "SKILL.md").read_text(encoding="utf-8")
    assert "<change>:task<N>-<slug>" not in s   # 不复述完整格式串
    assert "TAG_RE" in s                        # 改为引用式
