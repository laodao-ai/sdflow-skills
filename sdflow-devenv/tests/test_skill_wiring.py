"""SKILL.md 接线测试：命令示例可直接复制执行。只做子串 / 逐行检查，不解析 Markdown。"""
import re
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"
REFS = SKILL.parent / "references"


def _read(path):
    return path.read_text(encoding="utf-8")


def test_skill_md_has_no_undefined_skill_dir_variable():
    assert "$SKILL_DIR" not in _read(SKILL)


def test_every_devenv_lint_call_passes_root():
    """只看以 python3 开头的命令行；正文里提到脚本名的句子不是调用。"""
    calls = [ln for ln in _read(SKILL).splitlines()
             if ln.startswith("python3 ") and "devenv_lint.py" in ln]
    assert calls, "SKILL.md 里一条 devenv_lint.py 调用都没有，检查被打破了"
    missing = [ln for ln in calls if "--root" not in ln]
    assert not missing, f"缺 --root 的调用: {missing}"


def test_every_devenv_scaffold_call_passes_root():
    calls = [ln for ln in _read(SKILL).splitlines() if "devenv_scaffold.py" in ln]
    assert calls, "SKILL.md 里一条 devenv_scaffold.py 调用都没有，检查被打破了"
    missing = [ln for ln in calls if "--root" not in ln]
    assert not missing, f"缺 --root 的调用: {missing}"


REAL_HW = "需真机（按 SOP 人工执行后 confirm-lane）"


def test_skill_and_lane_patterns_name_real_hardware_sop_and_planned():
    """SKILL.md 与 lane-patterns.md 都写：真机泳道 SOP 已落地 → scaffolded + 固定句，未落地 → planned。"""
    for path in (SKILL, REFS / "lane-patterns.md"):
        text = _read(path)
        assert REAL_HW in text, path.name
        assert "未落地 → `planned`" in text, path.name


def test_no_direct_scaffolded_for_real_hardware():
    """带反引号与不带反引号两种写法都不许出现。"""
    for path in (SKILL, REFS / "lane-patterns.md"):
        text = _read(path)
        for phrase in ("直接 `scaffolded`", "直接 scaffolded"):
            assert phrase not in text, (path.name, phrase)


def test_review_dispatch_template_points_at_contract_without_inlining():
    text = _read(REFS / "review-dispatch-template.md")
    assert "subagent-dispatch-contract.md" in text
    assert "prefix-version" not in text
    assert "--untracked-files=all" in text


def test_review_lenses_has_no_tier_column_words():
    text = _read(REFS / "review-lenses.md")
    assert "中档" not in text
    assert "弱档" not in text


PROVENANCE_MARK = "[推断]"


def _slot_section(text, heading_prefix):
    """取以 heading_prefix 开头的 ## / ### 标题到下一个 ## / ### 标题之前的文本。"""
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.startswith(heading_prefix)), None)
    assert start is not None, f"找不到标题 {heading_prefix!r}"
    end = next((i for i in range(start + 1, len(lines))
                if re.match(r"#{2,3} ", lines[i])), len(lines))
    return "\n".join(lines[start:end])


def test_fact_claim_provenance_marker_required_per_slot():
    """逐槽检查：environments-template 槽 3.1–3.5 与 testing-framework 槽 ⑥ 各自带出处标记要求。"""
    env = _read(REFS / "environments-template.md")
    for n in range(1, 6):
        section = _slot_section(env, f"### 槽 3.{n} ")
        assert PROVENANCE_MARK in section, f"environments-template 槽 3.{n}"
    framework = _read(REFS / "testing-framework.md")
    assert PROVENANCE_MARK in _slot_section(framework, "### 槽⑥"), "testing-framework 槽⑥"
