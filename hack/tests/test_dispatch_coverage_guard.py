"""派发覆盖面守卫（HAE-17）与长编排 SKILL 的完成产物 / 停点声明（SW-03）。

守什么：
1. 每个顶层 SKILL.md 恰好在「派发清单」或「非派发清单」之一；新增 skill 未归类即红。
   「是否派发」由本文件内的显式清单决定，不扫自然语言字样（词表无界）。
2. 派发清单内的 skill 都引用 `resolve-models.sh` 与 `SDFLOW_EFFORT_`。
3. adr / architecture / devenv 的档位、宿主参数与 Codex 分支文本契约。
4. spec-review / code-review / implement 在通则块之后、第零步之前声明完成产物、
   允许停下的情形、循环上限；声明里的停点都能在正文找到对应出口。
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

DISPATCHING = (
    "sdflow-spec-review",
    "sdflow-code-review",
    "sdflow-implement",
    "sdflow-done",
    "sdflow-roadmap",
    "sdflow-adr",
    "sdflow-architecture",
    "sdflow-devenv",
)
# sdflow-spec：角色定义派发由 SA-07 管；sdflow-ship：自身不派发（经 Skill inline 调 implement）。
NON_DISPATCHING = (
    "sdflow-init",
    "sdflow-issues",
    "sdflow-retro",
    "sdflow-spec",
    "sdflow-ship",
    "sdflow-upgrade",
)

PRINCIPLES_END = "<!-- sdflow:principles:end -->"


def _skill(name):
    return (ROOT / name / "SKILL.md").read_text(encoding="utf-8")


def _top_level_skills():
    return sorted(p.parent.name for p in ROOT.glob("*/SKILL.md"))


def _between(text, start, end):
    i = text.index(start)
    j = text.index(end, i + len(start))
    return text[i:j]


# ── 清单守卫 ─────────────────────────────────────────────────

def test_lists_are_disjoint():
    assert not set(DISPATCHING) & set(NON_DISPATCHING)


def test_every_top_level_skill_is_in_exactly_one_list():
    classified = set(DISPATCHING) | set(NON_DISPATCHING)
    unclassified = [s for s in _top_level_skills() if s not in classified]
    assert not unclassified, f"未归入派发 / 非派发清单：{unclassified}"
    stale = [s for s in classified if s not in _top_level_skills()]
    assert not stale, f"清单里的 skill 已不存在：{stale}"


@pytest.mark.parametrize("name", DISPATCHING)
def test_dispatching_skill_resolves_model_and_effort(name):
    text = _skill(name)
    assert "resolve-models.sh" in text, f"{name} 未引用 resolve-models.sh"
    assert "SDFLOW_EFFORT_" in text, f"{name} 未引用 SDFLOW_EFFORT_"


# ── adr / architecture / devenv 文本契约 ──────────────────────

def test_adr_sync_uses_mid_and_audit_uses_strong():
    text = _skill("sdflow-adr")
    sync = _between(text, "## sync 模式", "## audit 模式")
    audit = text[text.index("## audit 模式"):text.index("## 脚本定位")]
    assert "$SDFLOW_TIER_MID" in sync and "$SDFLOW_EFFORT_MID" in sync
    assert "$SDFLOW_TIER_STRONG" in audit and "$SDFLOW_EFFORT_STRONG" in audit
    assert "不低于 high" in audit, "audit 是门禁性质，请求 effort 须声明不低于 high"


def test_adr_sync_reuses_done_variables_and_done_declares_it():
    adr = _skill("sdflow-adr")
    done = _skill("sdflow-done")
    assert "复用 done 已导出的变量" in adr
    step = done[done.index("## 第 1.5 步"):]
    step = step[:step.index("\n## ", 5)]
    assert "复用本轮第 0.4 步已导出的变量" in step
    assert "SDFLOW_TIER_MID" in step


def test_adr_standalone_runs_four_step_resolution():
    text = _skill("sdflow-adr")
    assert "<!-- sdflow:tier-resolution:start v1 -->" in text
    assert "独立调用" in text


@pytest.mark.parametrize("name", ("sdflow-adr", "sdflow-architecture", "sdflow-devenv"))
def test_codex_branch_uses_native_params_and_collection_section(name):
    text = _skill(name)
    assert "reasoning_effort" in text
    assert 'fork_turns: "none"' in text
    assert "「Codex 结果收集」" in text
    assert "`subagent_type: sdflow-effort-" in text


@pytest.mark.parametrize("name", ("sdflow-architecture", "sdflow-devenv"))
def test_architecture_and_devenv_dispatch_strong(name):
    text = _skill(name)
    assert "$SDFLOW_TIER_STRONG" in text
    assert "$SDFLOW_EFFORT_STRONG" in text


def test_architecture_degrades_only_on_unknown_host_and_codex_uses_spawn_agent():
    text = _skill("sdflow-architecture")
    assert "spawn_agent" in text
    assert "无 fresh 子代理原语" not in text, "旧的 Codex 宿主降级前提还在"
    marker = "walkthrough=self-review-degraded"
    paragraphs = [p for p in re.split(r"\n\s*\n", text) if marker in p]
    assert paragraphs, "降级留痕段不存在"
    head = paragraphs[0]
    assert "host=unknown" in head
    assert "host=codex" not in head and "Codex CLI" not in head


def test_devenv_cold_review_is_strong_and_gate_effort_floor_declared():
    text = _skill("sdflow-devenv")
    assert "不低于 high" in text


# ── SW-03：完成产物与停点声明 ────────────────────────────────

LONG_SKILLS = {
    "sdflow-spec-review": {
        "stops": (
            "resolve-models.sh 未安装",
            "run 目录未被 git 忽略",
            "未审待恢复",
            "HARD-GATE",
        ),
        "loops": ("同一镜重派一次",),
        "artifacts": ("spec-review-report.md", "锚行自检", "checkpoint"),
    },
    "sdflow-code-review": {
        "stops": (
            "resolve-models.sh 未安装",
            "run 目录未被 git 忽略",
            "容量重试耗尽",
            "fail-loud 拒写",
        ),
        "loops": ("同一镜重派一次", "硬上限 2 轮"),
        "artifacts": ("code-review-report.md", "自动修复", "checkpoint"),
    },
    "sdflow-implement": {
        "stops": (
            "resolve-models.sh 未安装",
            "Codex 宿主下子代理机制不可用",
            "halt envelope",
            "BLOCKED",
        ),
        "loops": ("同一任务重派一次", "连续 2 轮", "≥3 轮"),
        "artifacts": ("ticket 落盘", "checkpoint", "frontier"),
    },
}
ZERO_STEP = "\n## 第零步"


def _declaration(name):
    text = _skill(name)
    after_principles = text[text.index(PRINCIPLES_END) + len(PRINCIPLES_END):]
    head = after_principles[:after_principles.index(ZERO_STEP)]
    decl = head[head.index("## 完成标准与停点"):]
    # 正文 = 去掉声明段的整份 SKILL：故障矩阵等出口可能在通则块之前。
    return decl, text.replace(decl, "")


@pytest.mark.parametrize("name", LONG_SKILLS)
def test_declaration_sits_between_principles_and_zero_step_with_three_items(name):
    decl, _ = _declaration(name)
    for label in ("**完成产物**", "**允许停下的情形**", "**循环上限**"):
        assert label in decl, f"{name} 声明段缺 {label}"
    assert "检查通过就继续，不做未要求的改进" in decl


@pytest.mark.parametrize("name", LONG_SKILLS)
def test_declaration_artifacts_and_loops(name):
    decl, _ = _declaration(name)
    for token in LONG_SKILLS[name]["artifacts"] + LONG_SKILLS[name]["loops"]:
        assert token in decl, f"{name} 声明段缺 {token!r}"


@pytest.mark.parametrize("name", LONG_SKILLS)
def test_declared_stops_exist_in_body(name):
    decl, body = _declaration(name)
    for stop in LONG_SKILLS[name]["stops"]:
        assert stop in decl, f"{name} 声明段缺停点 {stop!r}"
        assert stop in body, f"{name} 声明的停点 {stop!r} 在正文找不到对应出口"
