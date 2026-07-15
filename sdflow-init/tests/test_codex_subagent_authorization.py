"""守 Task 9（add-codex-host-support）「消费项目铺设 + fan-out 能力探针」的铺设产物。

【为什么需要机械守】
Codex 宿主默认**不**派子代理（安全默认）——两个评审 SKILL 的多镜 fan-out 要在 Codex 宿主下工作，
必须先有一处**显式**授权（spec `host-adaptive-execution`「子代理不可用时镜数如实降级」Requirement：
「`sdflow-init` 铺给消费项目的 AGENTS.md 段与两个评审 SKILL SHALL 显式声明该授权」）。
授权文字若漏铺（`sdflow-init` 铺设产物里没有）或漏写（SKILL 里没有 fan-out 前的探针协议），
Codex 宿主下的评审要么每次都拿不到子代理权限、要么在没有能力核验的情况下裸 fan-out——
两者都不是本 change 想要的目标态，故须机验存在性。

【探针的诚实边界，本文件同样守住】
探针（trivial 子代理判定"机制活着没"）是**语义核验，非机械门**（ADR-4/adr/0023，§0.0）——
「是否真派出了一次子代理」无可信脚本捕获路径。SKILL.md MUST 显著登记这条边界，MUST NOT
把探针包装成"头号假绿已被事前机械拦截"。这条诚实声明本身也是铺设产物的一部分，漏写 =
把一个语义核验的东西悄悄冒充成机械保证——本文件同样守住这条声明"在不在"。

【mirrors= 词表反漂移】
`anchor_lint.py` 的 `_FANOUT_MIRRORS` 是跨两个评审层共用的固定三 token 词表
（domain/adversarial/grounding），SKILL.md 文档字面量若与它漂移，Codex 宿主下落的锚会被
`anchor_lint` fail-closed 拒收（unknown-token）。本文件直接 import 真实工具、断言 SKILL.md
写的 token 集合是它的**子集**，防止「文档说的」和「工具认的」各写一套。
"""
import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ASSETS = Path(__file__).resolve().parents[1] / "assets"
SNIPPET = ASSETS / "snippets" / "claude-section.md"
AGENTS = REPO / "AGENTS.md"
SPEC_REVIEW_SKILL = REPO / "sdflow-spec-review" / "SKILL.md"
CODE_REVIEW_SKILL = REPO / "sdflow-code-review" / "SKILL.md"
ANCHOR_LINT = ASSETS / "workflow" / "tools" / "anchor_lint.py"


def _anchor_lint_mod():
    spec = importlib.util.spec_from_file_location("anchor_lint", ANCHOR_LINT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ---------- 铺设产物：claude-section.md（单一源） + AGENTS.md（本仓 dogfood 铺设结果）----------

def test_snippet_declares_codex_subagent_authorization():
    """claude-section.md（sdflow-init 铺给消费项目、经 opsx-init 托管块注入 AGENTS.md 的单一源）
    MUST 含 Codex 子代理授权段：授权范围（两个评审 SKILL 的 fan-out）+ spawn_agent 的
    task-specific reason 与 model-tiers 的绑定。"""
    t = SNIPPET.read_text(encoding="utf-8")
    assert "Codex 子代理授权" in t
    assert "spawn_agent" in t
    assert "task-specific reason" in t
    assert "model-tiers.md" in t
    assert "sdflow-spec-review" in t and "sdflow-code-review" in t
    # 授权非无限放开——MUST 显式限定范围，防止被读成"任意 skill 可随便 spawn_agent"
    assert "仅限这两处" in t


def test_snippet_authorization_names_probe_semantic_boundary():
    """授权段紧邻处 MUST 提醒探针是语义核验非机械门——授权和诚实边界不能分离铺设
    （只铺授权、不铺边界，会让读者以为探针=机械保证）。"""
    t = SNIPPET.read_text(encoding="utf-8")
    assert "语义核验" in t
    assert "非机械" in t or "MUST NOT 被当作机械保证" in t
    assert "单镜降级" in t


def test_agents_md_dogfood_mirrors_authorization():
    """本仓 AGENTS.md 的 opsx-init 托管块是 claude-section.md 的铺设结果（dogfood）——
    若只改了源快照、忘了回灌铺设产物，本仓自己的 Codex 宿主评审就拿不到授权
    （dogfood-blind-spot：源仓 config/文档 掩盖消费仓默认态，同一坑）。"""
    t = AGENTS.read_text(encoding="utf-8")
    assert "Codex 子代理授权" in t
    assert "spawn_agent" in t
    assert "task-specific reason" in t
    assert "sdflow-spec-review" in t and "sdflow-code-review" in t
    # AGENTS.md 段落须落在 sdflow-init 维护的 opsx-init 托管块内（不是随手写在托管块外）
    start = t.index("<!-- opsx-init:start")
    end = t.index("<!-- opsx-init:end")
    assert start < t.index("Codex 子代理授权") < end


# ---------- 两评审 SKILL：fan-out 前探针协议 ----------

def _skill_text(path):
    assert path.is_file(), f"缺失：{path}"
    return path.read_text(encoding="utf-8")


def test_both_skills_probe_precedes_fanout_dispatch():
    """探针 MUST 在实际派出 fan-out 子代理之前跑（spec 原文：「fan-out 前跑能力探针」）——
    机验文档顺序：能力探针小节的文本位置须早于 fan-out 派发表格。"""
    for path in (SPEC_REVIEW_SKILL, CODE_REVIEW_SKILL):
        t = _skill_text(path)
        probe_idx = t.index("能力探针")
        fanout_idx = t.index("fan-out（一条消息内全部派出")
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
    评审直接罢工。直接 import 真实工具校验，而非各写一份可能漂移的复制。"""
    al = _anchor_lint_mod()
    vocab = al._FANOUT_MIRRORS
    for path in (SPEC_REVIEW_SKILL, CODE_REVIEW_SKILL):
        t = _skill_text(path)
        # 文档正文出现的 "domain,adversarial,grounding" 字面 token 串
        assert "domain,adversarial,grounding" in t
        tokens = {tok.strip() for tok in "domain,adversarial,grounding".split(",")}
        assert tokens <= vocab, f"{path}: 文档 token 集合 {tokens} 不是 anchor_lint 词表 {vocab} 的子集"


def test_code_review_history_mirror_alias_honestly_documented():
    """code-review 的第三镜叫「历史镜/history」，但 anchor_lint 的 mirrors= 词表是跨层共用的
    固定三 token（domain/adversarial/grounding，无 history）——该skill 借用既有 token
    `grounding` 记录"第三个 fan-out 镜跑了"这件事。这是一处真实的命名不对齐，MUST 在文档里
    诚实注明（非声称"grounding=接地镜"），否则未来读者会误以为 code-review 真有接地镜，
    或误以为 history 镜完全没被 mirrors= 追踪。"""
    t = _skill_text(CODE_REVIEW_SKILL)
    assert "历史镜" in t
    assert "借用既有 token" in t
    assert '`grounding` 记该镜跑过' in t
    assert "非声称" in t
    assert 'lens="history"' in t  # 精确身份仍由 lens-metric 的 lens= 各自记录


def test_fanout_capability_anchor_prefix_matches_real_tool():
    """反漂移锁：SKILL.md 里手写的锚前缀字符串 MUST 与 anchor_lint.ANCHOR_PREFIXES 实际
    识别的 key 一致——防止文档写错前缀（如漏 v1/多空格）导致锚在真实 lint 里不被识别。"""
    al = _anchor_lint_mod()
    assert "<!-- sdflow:fanout-capability v1" in al.ANCHOR_PREFIXES
    for path in (SPEC_REVIEW_SKILL, CODE_REVIEW_SKILL):
        t = _skill_text(path)
        assert "<!-- sdflow:fanout-capability v1" in t
