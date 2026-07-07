from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"

def text():
    return SKILL.read_text(encoding="utf-8")

def test_gate_discipline_present():
    t = text()
    assert "每步前后" in t and "ship_gate" in t
    assert "MUST" in t and "prose" in t.lower() or "步序" in t

def test_zero_git_and_passthrough():
    t = text()
    assert "不 commit" in t or "零 git" in t
    assert "透传" in t and "push" in t

def test_fuse_and_resume():
    t = text()
    # T26/SR-1；mlh-p5 Task6 D11：熔断判据 = 该步 frontmatter 状态集合是否变化（inline 锚随
    # live 读点退役，不再参与），非 HEAD/mtime；见 test_gate_breaker.py 的 anchor_set/
    # breaker_no_progress 单测（本处只钉 SKILL 文案含新判据关键词，非重复逻辑测试）。
    assert "状态集合" in t and "无净变化" in t and "UNKNOWN" in t     # D5 熔断（迁 frontmatter 状态集）
    assert "HEAD 移动" in t and "文件修改时间戳" in t and "MUST NOT 作免疫信号" in t
    assert "重调" in t and "勿重派" in t                  # D9 resume

def test_trigger_words_scoped():
    t = text()
    assert "/sdflow-ship" in t and "ship 这个 change" in t
    head = t.split("---", 2)[1]   # frontmatter
    assert "发布" not in head      # 避让裸词（D9 撞车）
