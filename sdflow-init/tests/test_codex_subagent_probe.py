"""守 Task 9（add-codex-host-support）的 fan-out 能力探针。

【为什么需要机械守】
两个评审 SKILL 明确要求 fan-out，仍须保留派发前的能力探针与诚实降级协议。

【探针的诚实边界，本文件同样守住】
探针（trivial 子代理判定"机制活着没"）是**语义核验，非机械门**（ADR-4/adr/0023，§0.0）——
「是否真派出了一次子代理」无可信脚本捕获路径。SKILL.md MUST 显著登记这条边界，MUST NOT
把探针包装成"头号假绿已被事前机械拦截"。这条诚实声明本身也是铺设产物的一部分，漏写 =
把一个语义核验的东西悄悄冒充成机械保证——本文件同样守住这条声明"在不在"。

【mirrors= 词表反漂移】
`anchor_lint.py` 的 `_FANOUT_MIRRORS` 是跨两个评审层共用的固定四 token 词表
（domain/adversarial/grounding/history），SKILL.md 文档字面量若与它漂移，Codex 宿主下落的锚会被
`anchor_lint` fail-closed 拒收（unknown-token）。本文件直接 import 真实工具、断言 SKILL.md
写的 token 集合是它的**子集**，防止「文档说的」和「工具认的」各写一套。两份 SKILL 的第三镜身份
不同——spec-review 是接地镜（`grounding`），code-review 是历史镜（`history`，T148 真名替换后不再
借用 `grounding`）——故按文件区分预期 token 串。
"""
import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
ASSETS = Path(__file__).resolve().parents[1] / "assets"
SPEC_REVIEW_SKILL = REPO / "sdflow-spec-review" / "SKILL.md"
CODE_REVIEW_SKILL = REPO / "sdflow-code-review" / "SKILL.md"
ANCHOR_LINT = ASSETS / "workflow" / "tools" / "anchor_lint.py"
PUBLIC_DELEGATION_POLICY_CARRIER = ASSETS / "snippets" / "claude-section.md"
HUMAN_DELEGATION_POLICY_CARRIERS = (
    REPO / "AGENTS.md",
    REPO / "CLAUDE.md",
)
needs_human_carriers = pytest.mark.skipif(
    not all(path.is_file() for path in HUMAN_DELEGATION_POLICY_CARRIERS),
    reason="本门核对项目人读载体中的 Codex 派发策略；发布 clone 不含 AGENTS.md / CLAUDE.md",
)
DELEGATION_POLICY_FORBIDDEN = (
    "## Codex 子代理授权",
    "Codex 宿主默认不派子代理",
    "仅限这三处",
)


def _anchor_lint_mod():
    spec = importlib.util.spec_from_file_location("anchor_lint", ANCHOR_LINT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ---------- 两评审 SKILL：fan-out 前探针协议 ----------

def _skill_text(path):
    assert path.is_file(), f"缺失：{path}"
    return path.read_text(encoding="utf-8")


def _assert_no_codex_delegation_policy(paths):
    for path in paths:
        text = _skill_text(path)
        for phrase in DELEGATION_POLICY_FORBIDDEN:
            assert phrase not in text, f"{path}: 不应包含项目级子代理规则：{phrase}"


def test_public_template_does_not_add_codex_delegation_policy():
    """公开项目模板不设置 Codex 子代理授权、白名单或默认禁用规则。"""
    _assert_no_codex_delegation_policy((PUBLIC_DELEGATION_POLICY_CARRIER,))


@needs_human_carriers
def test_project_instructions_do_not_add_codex_delegation_policy():
    """开发仓项目说明不设置 Codex 子代理授权、白名单或默认禁用规则。"""
    _assert_no_codex_delegation_policy(HUMAN_DELEGATION_POLICY_CARRIERS)


def test_both_skills_probe_precedes_fanout_dispatch():
    """探针 MUST 在实际派出 fan-out 子代理之前跑——
    机验文档顺序：能力探针小节的文本位置须早于 fan-out 派发表格。
    两份评审 SKILL 都用当前稳定的完整 roster 容量分批文案，且两处均位于能力探针之后。"""
    fanout_needles = {
        SPEC_REVIEW_SKILL: "完整 roster 分批 dispatch",
        CODE_REVIEW_SKILL: "fan-out（完整 roster 按容量分批派出",
    }
    for path in (SPEC_REVIEW_SKILL, CODE_REVIEW_SKILL):
        t = _skill_text(path)
        probe_idx = t.index("能力探针")
        fanout_idx = t.index(fanout_needles[path])
        assert probe_idx < fanout_idx, f"{path}: 探针小节须在 fan-out 派发表格之前"


def test_both_skills_declare_capability_anchor_and_host_branches():
    """两个评审 SKILL MUST 各自声明：claude 免探恒 available / unknown 不 fan-out /
    codex MUST 探 + 落 `sdflow:fanout-capability` 锚（Task 2 anchor_lint 的判据源）。"""
    for path in (SPEC_REVIEW_SKILL, CODE_REVIEW_SKILL):
        t = _skill_text(path)
        assert '$SDFLOW_HOST="claude"' in t and "免探" in t
        assert '$SDFLOW_HOST="unknown"' in t and "不 fan-out" in t
        assert '$SDFLOW_HOST="codex"' in t and "MUST" in t
        assert "<!-- sdflow:fanout-capability v1" in t
        assert 'subagents="available|unavailable"' in t


def test_both_skills_declare_honest_probe_boundary():
    """§0.0 诚实边界：探针值是主 session 自报，无可信脚本捕获路径——MUST NOT 声称机械门，
    MUST NOT 声称"头号假绿已被事前机械拦截"（一致性 lint 只拦机制死的自相矛盾，不拦机制活时的偷懒自代）。"""
    for path in (SPEC_REVIEW_SKILL, CODE_REVIEW_SKILL):
        t = _skill_text(path)
        assert "MUST NOT 声称这是机械门" in t
        assert '头号假绿（多镜静默退化）已被事前机械拦截' in t
        assert "MUST NOT 声称" in t
        assert "无机械守，残余语义层" in t


def test_both_skills_shrink_roster_when_unavailable():
    """探针判 unavailable ⇒ MUST 缩 roster 到实跑镜 + 报告显著标注单镜降级
    （spec「子代理不可用则缩 roster」Scenario：roster 只含实际独立完成的行键）。"""
    for path in (SPEC_REVIEW_SKILL, CODE_REVIEW_SKILL):
        t = _skill_text(path)
        assert 'subagents="unavailable"' in t
        assert "缩 roster 到主 session 实际独立完成的镜" in t
        assert "单镜降级（子代理不可用，host=codex）" in t
        assert "MUST NOT 为未独立跑过的镜落锚" in t


def test_mirrors_field_not_coupled_to_metrics():
    """GC-3：mirrors= 由 SKILL 直接落、不经 emitter/lens-metric、不读 config.metrics
    （一致性 lint 的判据源须 always-on，不受 metrics 开关门控）。"""
    for path in (SPEC_REVIEW_SKILL, CODE_REVIEW_SKILL):
        t = _skill_text(path)
        assert "不经 emitter/lens-metric、不读" in t
        assert "config.metrics" in t


def test_mirrors_tokens_are_subset_of_anchor_lint_vocabulary():
    """反漂移锁：SKILL.md 文档字面写的 mirrors= token 集合 MUST 是 anchor_lint._FANOUT_MIRRORS
    的子集——否则 Codex 宿主真落锚时会被 anchor_lint 判 unknown-token fail-closed，
    评审直接罢工。直接 import 真实工具校验，而非各写一份可能漂移的复制。

    两份 SKILL 的第三镜身份不同（spec-review=接地镜/grounding，code-review=历史镜/history，
    真名替换后 T148），故按文件区分预期 token 串，而非共享同一个字面量循环。"""
    al = _anchor_lint_mod()
    vocab = al._FANOUT_MIRRORS
    expected = {
        SPEC_REVIEW_SKILL: "domain,adversarial,grounding",
        CODE_REVIEW_SKILL: "domain,adversarial,history",
    }
    for path, literal in expected.items():
        t = _skill_text(path)
        assert literal in t
        tokens = {tok.strip() for tok in literal.split(",")}
        assert tokens <= vocab, f"{path}: 文档 token 集合 {tokens} 不是 anchor_lint 词表 {vocab} 的子集"


def test_code_review_history_mirror_alias_honestly_documented():
    """code-review 的第三镜是历史镜/history——T148 后 anchor_lint._FANOUT_MIRRORS 已扩至
    四 token（domain/adversarial/grounding/history），code-review 不再需要借用 `grounding`
    这个不属于自己的 token 来记录"第三个 fan-out 镜跑了"。本测试断言 mirrors= 字面已改为真名
    `history`，且旧的借用措辞（"借用既有 token"）不再出现——防止真名替换后残留过期的借用叙事。"""
    t = _skill_text(CODE_REVIEW_SKILL)
    assert 'mirrors="domain,adversarial,history' in t
    assert "借用既有 token" not in t


def test_fanout_capability_anchor_prefix_matches_real_tool():
    """反漂移锁：SKILL.md 里手写的锚前缀字符串 MUST 与 anchor_lint.ANCHOR_PREFIXES 实际
    识别的 key 一致——防止文档写错前缀（如漏 v1/多空格）导致锚在真实 lint 里不被识别。"""
    al = _anchor_lint_mod()
    assert "<!-- sdflow:fanout-capability v1" in al.ANCHOR_PREFIXES
    for path in (SPEC_REVIEW_SKILL, CODE_REVIEW_SKILL):
        t = _skill_text(path)
        assert "<!-- sdflow:fanout-capability v1" in t
