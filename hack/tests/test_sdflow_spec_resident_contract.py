"""`sdflow-spec` 薄入口的公开契约门。

被测 seam 是安装后用户与宿主实际读取的 `sdflow-spec/SKILL.md`，以及入口按条件路由到的
versioned references。测试只观察这组公开 Markdown 契约，不解析实现私有结构。
"""

import re
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "sdflow-spec" / "SKILL.md"


RESIDENT_CONTRACT = {
    "frontmatter": ("name: sdflow-spec", "disable-model-invocation: true"),
    "principles": (
        "<!-- sdflow:principles:start",
        "### ① 能查的自己查，能调研的自己调研",
        "### ② 不确定的方案，先调研再给推荐",
        "### ③ 以最终目标为准",
        "### ④ 方案尽量简化",
        "<!-- sdflow:principles:end -->",
    ),
    "phase-0": ("## 第零步", "openspec --version", "openspec list", "### 0.3 重入探测"),
    "phase-a": ("## 相位 A", "一次只问一个问题", "收束进的是 B，不是 C"),
    "phase-b": ("## 相位 B", "## 承重约束", "sdflow-spec-grill"),
    "phase-c": (
        "## 相位 C",
        "openspec instructions <artifact>",
        "resolvedOutputPath",
        "`context` / 当前 artifact 的 `rules`",
        "作为生成约束",
        "MUST NOT 复制进产物",
        "resolve-workflow.sh",
    ),
    "c1-four-verdicts": (
        "### C.1 起手核验纪要（四判，缺一即拒）",
        "`decision-memo.md` **存在**",
        "`## 拍板决策` 与 `## 承重约束` **非空**",
        "**身份字段匹配当前盘面**",
        "**`decision_hash` 重算后匹配**",
    ),
    "final-review": (
        "## 终审",
        "整个 change 目录",
        "decision-memo.md",
        "design ↔ specs",
        "非平凡 design 至少一张",
        "TG-18 tasks 含测试覆盖图",
    ),
    "strict-validate": ("openspec validate", "--strict", "validate --strict"),
    "checkpoints": ("sdflow-spec-grill", "sdflow-spec-generate"),
    "exit-sequence": (
        "## 出口序列",
        "1. /clear",
        "2. 切换到评审档模型",
        "3. /sdflow-spec-review",
    ),
}


REFERENCE_ROUTES = {
    "delegation": {
        "path": "references/delegation-protocol.md",
        "condition": "仅在人明确要求重新评估或启用外派时读取",
        "tokens": ("# 未启用外派协议", "sdflow-local-researcher", "secret-scan", "MUST NOT 用通用子代理"),
    },
    "diagnostics": {
        "path": "references/degradation-ladder.md",
        "condition": "仅在发生失败、降级或需要诊断时读取",
        "tokens": ("# 降级阶梯", "problem + cause + fix", "## 4. 失败模式表"),
    },
    "evolution": {
        "path": "references/evolution-notes.md",
        "condition": "仅在审计历史依据或设计未来 T132 gate 时读取",
        "tokens": (
            "# 演进依据与未来门契约",
            "分支 A",
            "checkpoint(sdflow-spec-grill)",
            "分支 B",
            "checkpoint(grill)",
            "sdflow:grill-done",
            "T132 保持 OPEN",
        ),
    },
}


DELEGATION_PROPAGATION_CONTRACT = (
    "每一次派发的 prompt",
    "`sdflow:principles` 从 `start` 到 `end`",
    "原文整段复制进去",
    "MUST NOT 依赖 agent 定义中的副本",
)


def _text(path: Path = SKILL) -> str:
    return path.read_text(encoding="utf-8")


def test_entry_is_within_unicode_character_budget():
    text = _text()
    assert len(text) <= 18_000, f"sdflow-spec/SKILL.md 有 {len(text)} 个 Unicode 字符，超过 18,000"


def test_frontmatter_is_the_real_document_frontmatter():
    match = re.match(r"\A---\n(?P<body>.*?)\n---\n", _text(), flags=re.DOTALL)
    assert match, "入口缺 YAML frontmatter"
    frontmatter = match.group("body")
    assert re.search(r"^name:\s*sdflow-spec$", frontmatter, flags=re.MULTILINE)
    assert re.search(r"^disable-model-invocation:\s*true$", frontmatter, flags=re.MULTILINE)
    assert re.search(r"^description:\s*>$", frontmatter, flags=re.MULTILINE)


def test_resident_contract_tokens_have_substantive_semantics():
    text = _text()
    for capability, tokens in RESIDENT_CONTRACT.items():
        missing = [token for token in tokens if token not in text]
        assert not missing, f"常驻契约 {capability} 缺少实质语义锚：{missing}"


def _assert_reference_routes(entry: str) -> None:
    for category, contract in REFERENCE_ROUTES.items():
        path = contract["path"]
        condition = contract["condition"]
        route = re.compile(
            rf"(?m)^- {re.escape(condition)}\s+"
            rf"\[`{re.escape(path)}`\]\({re.escape(path)}\)"
        )
        assert route.search(entry), (
            f"{category} reference 必须由同一列表项中的加载条件和非空标签相对链接共同路由"
        )

        target = SKILL.parent / path
        assert target.is_file(), f"{category} reference 不可达：{target}"
        content = _text(target)
        headings = re.findall(r"^#{1,6}\s+\S.*$", content, flags=re.MULTILINE)
        assert len(headings) >= 2, f"{category} reference 只有空标题或无实质结构"
        for token in contract["tokens"]:
            assert token in content, f"{category} reference 缺语义锚：{token}"


def test_three_on_demand_references_have_conditions_paths_and_content():
    _assert_reference_routes(_text())


@pytest.mark.parametrize(
    "degraded_route",
    (
        "- 仅在人明确要求重新评估或启用外派时读取\n  [](references/delegation-protocol.md)",
        "- 仅在人明确要求重新评估或启用外派时读取\n  其它文字\n"
        "  [`references/delegation-protocol.md`](references/delegation-protocol.md)",
    ),
)
def test_reference_route_rejects_bare_or_detached_links(degraded_route):
    entry = _text()
    valid_route = (
        "- 仅在人明确要求重新评估或启用外派时读取\n"
        "  [`references/delegation-protocol.md`](references/delegation-protocol.md)"
    )
    with pytest.raises(AssertionError, match="delegation reference"):
        _assert_reference_routes(entry.replace(valid_route, degraded_route, 1))


def test_delegation_requires_verbatim_principles_in_every_dispatched_prompt():
    delegation = _text(SKILL.parent / "references/delegation-protocol.md")
    for token in DELEGATION_PROPAGATION_CONTRACT:
        assert token in delegation, f"外派协议缺传播纪律锚：{token}"


def test_codex_claim_is_limited_to_observed_user_trigger():
    text = _text()
    assert "Codex 当前只观察到用户显式触发已被接受" in text
    assert "没有本 session 可调用的 Skill 执行面" in text
    assert "MUST NOT 把接口缺席写成模型调用已被拒绝" in text


def test_final_review_accepts_change_directory_traceability():
    text = _text()
    assert "追溯边界是整个 change 目录" in text
    assert "只在 `decision-memo.md` 中保留被砍候选与理由也合法" in text
    assert "design.md` 的一行纪要指针是合法路径" in text


def test_t132_contract_is_documented_but_not_implemented():
    entry = _text()
    notes = _text(SKILL.parent / "references/evolution-notes.md")
    assert "T132 未来 gate 尚未实现，保持 OPEN" in entry
    assert "A 需要身份、hash、必填节有效的 `decision-memo.md`" in notes
    assert "B 需要既有 `checkpoint(grill)` 或未来 gate 明确认可的 `sdflow:grill-done` 锚" in notes
    assert "本 reference 不实现 gate" in notes
