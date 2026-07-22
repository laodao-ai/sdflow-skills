"""守「ff 之后是 grill，不是 spec-review」这条交棒规则。

【为什么需要机械守】
`grill-with-docs` 是 `disable-model-invocation: true` 的第三方 skill —— **模型唤不起它**，
只能把 prompt 贴给人、由人手敲。而它在消费仓 CLAUDE.md 里【原本一次都没出现过】，
于是 ff 跑完，模型自然跳到它唯一看得见的下一个 skill = /sdflow-spec-review。

结果：一份**没被拷问过**的设计直接进设计审。而 spec-review 的多镜是在**已有设计的框架内**
找问题——**它不会替你质疑这个框架本身**。这正是 07 的教训（18 面镜全在废弃分支里做优化）。

∴ 两件事都得守：
  1. 消费仓 CLAUDE.md 托管块里，这条交棒规则在不在
  2. 它指向的那段 grill prompt，在 workflow.md 里还在不在（指针不能悬空）
"""
from pathlib import Path

ASSETS = Path(__file__).resolve().parents[1] / "assets"
SNIPPET = ASSETS / "snippets" / "claude-section.md"
WORKFLOW = ASSETS / "workflow" / "workflow.md"
PROMPTS = ASSETS / "workflow" / "prompts"


def test_snippet_routes_ff_to_grill_not_spec_review():
    """CLAUDE.md 托管块 MUST 写死：ff 之后是 grill，且 MUST 贴 prompt。"""
    t = SNIPPET.read_text(encoding="utf-8")
    assert "ff 之后是 grill" in t
    assert "grill-with-docs" in t
    assert "MUST NOT 直接跳到" in t and "sdflow-spec-review" in t
    # 光说「下一步跑 grill」没用 —— 必须把 prompt 贴出来（它唤不起，只能人敲）
    assert "原样贴出来" in t
    assert "只能人手动触发" in t


def test_grill_prompt_pointer_is_not_dangling():
    """托管块让人去 workflow.md 步骤 3 取 prompt —— 那段 prompt MUST 真的在那里。

    指针悬空 = 模型取不到 → 只能凭记忆重写 → 而托管块明令 MUST NOT 凭记忆重写
    → 死锁，实际结果就是静默跳过 grill。
    """
    assert "workflow/prompts/step3-grill.md" in SNIPPET.read_text(encoding="utf-8")
    f = PROMPTS / "step3-grill.md"
    assert f.is_file(), "指针悬空：prompts/step3-grill.md 不存在"
    assert f.read_text(encoding="utf-8").startswith("/grill-with-docs 死磕")


def test_grill_prompt_carries_the_principles_landing():
    """grill 是通则③（拿现状反驳目标）的最高发场景 —— prompt MUST 当场点名。

    通则正文（CLAUDE.md 托管块）是通用表述；grill 场景下它有特定形态：
    「现在代码不是这么写的，所以这个设计不对」。
    而 grill 手边唯一的实证材料就是现状代码 ⇒ 这是它的【默认失效模式】，不是偶发。
    """
    assert "现状只用来核事实，不用来定对错" in (PROMPTS / "step3-grill.md").read_text(encoding="utf-8")


def test_grill_is_always_full_depth():
    """grill 是独立审视 —— MUST NOT 因上游（explore / wayfinder 已决）就瘦跑。

    拿上游产出给自己松绑，二次审视就退化成盖章。
    回归：`wayfinder-resolved:` 锚曾被用作「grill 瘦跑判据」，已废除（锚只剩溯源用途）。
    """
    w = WORKFLOW.read_text(encoding="utf-8")
    assert "一律全深度" in w

    ff = (ASSETS / "workflow" / "ff-generation-constraints.md").read_text(encoding="utf-8")
    assert "锚的用途只有溯源" in ff
    assert "瘦跑以该前缀为唯一判据" not in ff   # 死条款已清


# ---------- superpowers 的 task-brief 断口（靠读第三方源码才发现的）----------

def test_plan_constraints_land_where_implementer_can_see_them():
    """⭐ 领域约束 MUST 落在【每个 Task 段内】，不能只写 plan 头部的 Global Constraints。

    【这个洞是怎么发现的】（读 superpowers 6.1.1 源码）：
      - `subagent-driven-development/scripts/task-brief` 的 awk 【只抽 `### Task N` 那一段】；
      - 其 SKILL.md dispatch 契约白纸黑字：brief 是 "the single source of requirements"，
        且 "Exact values … appear **only in the brief**"，五项必含里【没有 Global Constraints】；
      - 而 `writing-plans` 的模版却写着 "Every task's requirements **implicitly** include
        this section" —— **这个 implicitly 在 subagent-dev 的执行路径上是假的**。

    ⇒ 「把 design 的领域约束逐字写进 Global Constraints」曾是一条【悬空的 MUST】：
       写进去了，implementer 一个字都看不到（同 07 附录 A22 那类病 —— MUST 无承载）。

    ⚠️ 这条断口在 superpowers 侧，我们改不了；只能让 plan 把约束【也】写进 Task 段。
       升级 superpowers 后若 task-brief 改成抽全文，本测试可以放宽 —— 但【先去读它的源码再放宽】。
    """
    s6 = (PROMPTS / "step6-writing-plans.md").read_text(encoding="utf-8")
    assert "每个 Task 段内复述" in s6
    assert "task-brief" in s6 and "不进 brief" in s6


def test_dispatch_sites_carry_the_principles():
    """两条实现管线的 dispatch 点，都 MUST 点名「原文携带四条通则」。

    子代理 fresh context —— 看不见 CLAUDE.md，也看不见 SKILL.md。
    通则块自带传播纪律，但【声明在通则里】拦不住【dispatch 那一行忘了带】——
    所以每个 dispatch 站点上都要点名（同 spec-review / code-review 的 fan-out）。
    """
    w = WORKFLOW.read_text(encoding="utf-8")
    assert "dispatch prompt MUST 原文携带四条通则" in w        # superpowers 路径（步骤 7）

    impl = (Path(__file__).resolve().parents[2] / "sdflow-implement" / "SKILL.md") \
        .read_text(encoding="utf-8")
    assert "「四条通则」区块全文" in impl                        # tickets 路径
