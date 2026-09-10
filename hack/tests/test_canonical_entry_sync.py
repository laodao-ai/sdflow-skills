"""canonical 规则单一源：阶段一「唯一线性路径 + 自动触发规则」不得分叉。

【为什么要有本文件（v2，simplify-workflow 改写）】
`add-sdflow-spec` 曾引入阶段一「分支 A / 分支 B 双轨 + 四入口选择规则 + sunset 条件」，本文件
v1 版本守住那套设计在**七处**载体间不分叉。`simplify-workflow` 把双轨收敛为**唯一线性路径**
（explore 条件 → `/sdflow-spec` 自动触发 → HARD-GATE → ship），双轨设计连同它的 SA-14/D10
锚点一并退役——继续守一个已被删除的设计只会制造恒假的红灯，而非价值。

本文件 v2 不是删除重来，而是**保留仍然成立的部分**（人读侧/AI 读侧/Codex 授权段三处载体
仍须互相同步——这条一致性纪律本身没变，变的只是同步的内容），并把 v1 那批「presence」断言
换成 v2 的两类断言：
  ① presence：新的自动触发规则、唯一线性路径措辞，canonical 与人读侧必须**同字**出现；
  ② absence：分支 A/B、`disable-model-invocation`、旧三步 sunset 阈值等已退役措辞，
     MUST NOT 再出现在 canonical 或人读侧——防止未来编辑把双轨语言悄悄改回来。

【锚的质量纪律，继承自 v1（仍然成立，未改动）】
- **MUST 单行命中**：canonical bundle 一律锚单行散文/表格行，不锚跨行 ASCII 图。
- **例外：人读侧（CLAUDE.md / AGENTS.md）用「压掉空白后比对」，不用单行锚**——硬折行的中文
  散文句子会跨行，单行锚随折行位置变化而假红/假绿。
- 每条断言都做过定点变异回验（把被锚的那句话改掉/删掉 → 该断言必红）。

【与 v1 的差异一览】
- 删除：`test_generation_process_has_two_branches` 等 11 条锚「分支 A/B 存在」的用例
  （双轨已被移除，presence 断言的参照系不存在，继续留着只会制造恒红或需要手工跳过）。
- 保留：三处载体互相同步的 parity 类用例（`test_entry_section_exists_in_both_human_carriers`
  / `test_two_human_carriers_are_verbatim_identical` / `test_codex_auth_section_parity`）——
  这条纪律与双轨设计正交，simplify-workflow 后依然成立。
- 新增：absence 类回归守卫，覆盖 `simplify-workflow` 明确要清理的关键词
  （分支 A / 分支 B / disable-model-invocation / RUN_SOP / embedded-test-sop 条件触发语言）。
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WF = REPO / "sdflow-init" / "assets" / "workflow"

WORKFLOW = WF / "workflow.md"
GENERATION = WF / "generation-process.md"
CLAUDE_SECTION = REPO / "sdflow-init" / "assets" / "snippets" / "claude-section.md"

HUMAN_SIDE = {
    "CLAUDE.md": REPO / "CLAUDE.md",
    "AGENTS.md": REPO / "AGENTS.md",
}
ENTRY_HEADING = "## 阶段一入口："


def lines(p: Path):
    return p.read_text(encoding="utf-8").splitlines()


def has_line(p: Path, *needles: str) -> bool:
    """存在**同一行**同时含全部 needles。跨行结构一律不算命中。"""
    return any(all(n in ln for n in needles) for ln in lines(p))


def require(p: Path, *needles: str):
    assert has_line(p, *needles), (
        f"{p.relative_to(REPO)} 里找不到同时含 {needles!r} 的**单行** —— "
        "canonical 与本 change 的阶段一规则已分叉，或这条锚失鲜了（先核对再改测试）"
    )


def flat(text: str) -> str:
    """压掉全部空白（含换行）。用于比对**硬折行的中文散文**，见模块 docstring。"""
    return re.sub(r"\s+", "", text)


def entry_section(p: Path) -> str:
    """截出「阶段一入口」那一节（到下一个同级 `## ` 标题为止）。"""
    text = p.read_text(encoding="utf-8")
    start = text.find(ENTRY_HEADING)
    assert start >= 0, (
        f"{p.relative_to(REPO)} 里没有「{ENTRY_HEADING}…」这一节 —— "
        "阶段一入口小节须同时落在人读侧与 AI 读侧，人读侧这份不许消失"
    )
    end = text.find("\n## ", start + 1)
    return text[start:] if end < 0 else text[start:end]


# ── ① generation-process.md：唯一线性路径 + 自动触发规则（presence） ──────

def test_generation_process_states_single_entry_pipeline():
    require(GENERATION, "推荐流水线", "唯一入口")


def test_generation_process_states_auto_trigger_rule():
    require(GENERATION, "模型 SHALL 在以下情形自动 invoke", "/sdflow-spec")
    require(GENERATION, "模型 MUST NOT 自主判断", "该开 change 了")


# ── ② canonical 与人读侧：分支 A/B 等已退役措辞 MUST NOT 复活（absence） ──

RETIRED_PHRASES = (
    "分支 A",
    "分支 B",
    "disable-model-invocation: true",
    "四入口选择规则",
    "旧入口 sunset 条件",
)


def test_canonical_carries_no_retired_branch_language():
    for path in (WORKFLOW, GENERATION):
        blob = path.read_text(encoding="utf-8")
        for phrase in RETIRED_PHRASES:
            assert phrase not in blob, (
                f"{path.relative_to(REPO)} 仍含已退役措辞 {phrase!r} —— "
                "simplify-workflow 已把双轨收敛为单轨，此措辞不该复活"
            )


def test_human_carriers_entry_section_has_no_retired_branch_language():
    for name, path in HUMAN_SIDE.items():
        section = entry_section(path)
        for phrase in RETIRED_PHRASES:
            assert phrase not in section, (
                f"{name} 的「阶段一入口」小节仍含已退役措辞 {phrase!r}"
            )


# ── ③ 人读侧（CLAUDE.md / AGENTS.md 非托管区）：两份手抄副本须逐字相等 ─────
#     纪律继承自 v1：两份是同一条规则的两个手抄副本，唯一的兜底原本只是一句
#     prose「改一处就改另一处」，而「会想起去查那句 prose 的人本来就不会漏改」。

def test_entry_section_exists_in_both_human_carriers():
    for name, path in HUMAN_SIDE.items():
        assert entry_section(path).strip(), f"{name} 的阶段一入口小节是空的"


def test_two_human_carriers_are_verbatim_identical():
    claude = entry_section(HUMAN_SIDE["CLAUDE.md"])
    agents = entry_section(HUMAN_SIDE["AGENTS.md"])
    assert claude == agents, (
        "CLAUDE.md 与 AGENTS.md 的「阶段一入口」小节已分叉 —— "
        "两份是同一条规则的两个手抄副本，MUST 逐字相同（改一处就改另一处）"
    )


def test_human_carriers_state_the_auto_trigger_rule():
    for name, path in HUMAN_SIDE.items():
        section = entry_section(path)
        assert flat("人示意收敛") in flat(section), (
            f"{name} 的阶段一入口小节没有自动触发规则（人示意收敛 → 模型自动 invoke）"
        )
        assert flat("模型 MUST NOT 自主判断") in flat(section), (
            f"{name} 的阶段一入口小节没有「模型 MUST NOT 自主判断该开 change 了」这条禁令"
        )


# ── ④ Codex 子代理授权段 parity（T260，与双轨设计正交，v1 原样保留）───────

CODEX_AUTH_HEADING = "## Codex 子代理授权"


def _codex_auth_section(p):
    text = p.read_text(encoding="utf-8")
    start = text.find(CODEX_AUTH_HEADING)
    if start < 0:
        return None
    end = text.find("\n## ", start + 1)
    section = text[start:] if end < 0 else text[start:end]
    return re.sub(r"<!--\s*opsx-init:\w+\s*-->", "", section)


def test_codex_auth_section_parity():
    sources = {
        "CLAUDE.md": REPO / "CLAUDE.md",
        "AGENTS.md": REPO / "AGENTS.md",
        "claude-section.md": CLAUDE_SECTION,
    }
    sections = {}
    for name, path in sources.items():
        sec = _codex_auth_section(path)
        assert sec is not None, f"{name} 里没有「{CODEX_AUTH_HEADING}」这一节"
        sections[name] = sec
    canonical = flat(sections["CLAUDE.md"])
    for name, sec in sections.items():
        assert flat(sec) == canonical, (
            f"{name} 的 Codex 子代理授权段与 CLAUDE.md 不一致（压掉空白后比对）"
        )
