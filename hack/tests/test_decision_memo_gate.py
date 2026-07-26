"""`sdflow-spec` 的两道机械门。

【门 1 · 决策纪要】`decision-memo.md` 缺失 / 必填小节为空 ⇒ 红。
    纪要是 `/sdflow-spec` 相位 B 的**承重件**（`/clear` 无损这条不变式全靠它）。
    它是这条管线上**唯一有确定性信号的东西** —— 文件在不在、两个必填小节有没有正文，
    都是逐行字面量可判的（语法面有界，基准 5）。围栏 / HTML 注释块的识别**复用
    `ship_gate.py` 的单一源**，MUST NOT 在此手抄一份（见下方 import 处注释）。
    🔴 **诚实边界**：本门只证明「纪要存在且这两节非空」，**MUST NOT** 被表述成
    「证明发生过对抗拷问」。拷问是管线的内建默认路径，不是机械保证。

【门 2 · 存在态 ≠ 合格态】被截断的产物 ⇒ `openspec validate --strict` 判红。
    `openspec status` 的完成判据是**文件存在性**（CLI `dist/core/artifact-graph/state.js:25-29`）
    ⇒ 半截产物照样报 done，叠加「不重写已完成产物」后永久锁死。SA-05 因此要求两者分开判。
    本门用真的 `openspec` CLI 跑一遍，证明这条判据**真的挡得住**。

    ⚠️ **覆盖边界（实测钉住，见 `test_validate_strict_only_covers_delta_specs`）**：
    CLI 1.5.0 的 `validate <change> --strict` **只校验 `specs/*/spec.md` 的 delta 结构**——
    `proposal.md` / `design.md` / `tasks.md` 的内容它**根本不读**（proposal.md 整份删掉
    照样报 valid）。故「半截 design.md」这一形态**无机械门**，只能靠终审人判。
    该事实由本文件机械钉住 —— openspec 哪天扩了覆盖面，那条用例会红，提示回来改文档。
"""
import importlib.util
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]

# ── fenced code block / HTML 注释块的识别口径：**复用本仓单一源**，MUST NOT 手抄 ──────────
# 单一源 = `sdflow-ship/scripts/ship_gate.py:568-579` 那一组（`fence_delim` / `FenceTracker` /
# `HtmlCommentTracker`），原文即写着「MUST NOT 再各自手抄 `line.lstrip().startswith("```")`」。
# 手抄的口径只认 ``` ⇒ `~~~` / 四 backtick 开的块内的 `## 标题` 会被当成真标题（本门里 = 假绿）。
# 从**文件路径**加载而非 `import`：目录名含 `-`（非合法包名），且 MUST NOT 动 sys.path/sys.modules
# 污染全套件 —— 与 `sdflow-ship/tests/test_gate_breaker.py:13-16` 同一 idiom。
# ⇒ 两处**是同一份实现**，不是两份拷贝，∴ 结构上不存在漂移面，无需再加漂移守卫。
_GATE_PATH = REPO / "sdflow-ship" / "scripts" / "ship_gate.py"
_gate_spec = importlib.util.spec_from_file_location("_ship_gate_for_memo_gate", _GATE_PATH)
_ship_gate = importlib.util.module_from_spec(_gate_spec)
_gate_spec.loader.exec_module(_ship_gate)
FenceTracker = _ship_gate.FenceTracker
HtmlCommentTracker = _ship_gate.HtmlCommentTracker

# 纪要格式的真相源 —— 小节名从这里来，改名两边一起改（下方 test_schema_doc_and_gate_agree 守）
MEMO_SCHEMA_DOC = REPO / "sdflow-spec" / "references" / "decision-memo-schema.md"

# 小节名的**第三处消费者**：skill 指令本体（C.1 起手核验逐字引用这两个标题）。
# 只守「门 ↔ schema 文档」两处 ⇒ 改名漏改 SKILL.md 仍全绿（基准 3：同片一致性面一次扫全）。
MEMO_SECTION_CONSUMERS = (
    MEMO_SCHEMA_DOC,
    REPO / "sdflow-spec" / "SKILL.md",
)

MEMO_FILENAME = "decision-memo.md"

# 必填且必须非空的小节（SA-01 Scenario「纪要缺失拒绝生成」逐字点名的两项）
REQUIRED_SECTIONS = ("## 拍板决策", "## 承重约束")


# ---------------------------------------------------------------- 门 1 的判据本体

_ATX_RE = re.compile(r"^ {0,3}(#{1,6})(?:\s|$)")


def _atx_level(line):
    """ATX 标题行 → 级数 1–6；不是标题行 → None。

    口径 = CommonMark ATX 的**有界**词法（数得完，故可手写；基准 5）：行首 ≤3 个空格
    + 1–6 个 `#` + 空白或行尾。缩进 ≥4 列的行按定义是缩进代码块、**不是标题**，
    ∴ 这条正则同时把「缩进代码块里的 `## X`」挡在外面，无需另设追踪器。
    """
    m = _ATX_RE.match(line)
    return len(m.group(1)) if m else None


def _visible_flags(lines):
    """逐行 → 该行是否是「可当标题看」的行：既不在 fenced code block 内、也不在 HTML 注释块内。

    围栏行与注释块内的行本身也算不可见（它们不是正文结构）。
    两个追踪器都从 `ship_gate.py` 复用（本仓单一源），MUST NOT 手抄。
    """
    fence, comment = FenceTracker(), HtmlCommentTracker()
    flags = []
    for l in lines:
        is_fence_line = fence.feed(l)
        in_comment = comment.feed(l)
        flags.append(not is_fence_line and not fence.inside and not in_comment)
    return flags


def _section_body(text, heading):
    """取 `heading` 这一行到下一个**同级或更高级** ATX 标题（或 EOF）之间的正文。

    两条口径，都落在**有界**语法面上（基准 5），MUST NOT 演化成「解析 Markdown 结构」：
    - **级数**：`##` 只被 `##` / `#` 终止 —— `### D1 …` 子标题**属于本节正文**
      （决策纪要必然用 `###` 列决策，任何 `#` 都断 = 假红）；
    - **可见性**：fenced code block 与 HTML 注释块内的行不参与标题判定
      （纪要引用 schema 模板时，代码块内必然出现 `## 承重约束` 字面量 —— 当真即假绿）。
    """
    level = _atx_level(heading)
    lines = text.splitlines()
    visible = _visible_flags(lines)
    start = next((i for i, l in enumerate(lines)
                  if visible[i] and _atx_level(l) == level and l.strip() == heading), None)
    if start is None:
        return None
    body = []
    for i in range(start + 1, len(lines)):
        lv = _atx_level(lines[i])
        if visible[i] and lv is not None and lv <= level:
            break
        body.append(lines[i])
    return "\n".join(body)


def _strip_noise(body):
    """去掉 HTML 注释与空白 —— 只留「人真的写了字」的部分。"""
    return re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL).strip()


def check_decision_memo(change_dir):
    """→ [] 表示过门；否则返回违规原因列表（每条都指名道姓，可直接照做）。"""
    memo = Path(change_dir) / MEMO_FILENAME
    if not memo.is_file():
        return [f"{memo} 不存在 —— 相位 B 未产出决策纪要，MUST NOT 进入相位 C"]

    text = memo.read_text(encoding="utf-8")
    problems = []
    for heading in REQUIRED_SECTIONS:
        body = _section_body(text, heading)
        if body is None:
            problems.append(f"{memo}: 缺必填小节「{heading}」")
        elif not _strip_noise(body):
            problems.append(f"{memo}: 必填小节「{heading}」为空")
    return problems


# ---------------------------------------------------------------- 门 1 的用例

def _write_memo(tmp_path, decisions, constraints):
    d = tmp_path / "changes" / "demo"
    d.mkdir(parents=True)
    (d / MEMO_FILENAME).write_text(
        "---\nschema_version: 1\nchange: demo\nbranch: feat/demo\n---\n\n"
        "# 决策纪要 · demo\n\n## 目标态\n\n一句话。\n\n"
        f"## 拍板决策\n\n{decisions}\n\n## 承重约束\n\n{constraints}\n",
        encoding="utf-8",
    )
    return d


def test_missing_memo_is_red(tmp_path):
    """⭐ 纪要文件不存在 ⇒ 判红。"""
    d = tmp_path / "changes" / "demo"
    d.mkdir(parents=True)
    problems = check_decision_memo(d)
    assert problems, "纪要缺失却判绿 —— 门是空的"
    assert MEMO_FILENAME in problems[0]


def test_empty_required_section_is_red(tmp_path):
    """⭐ 必填小节存在但没有正文 ⇒ 判红（占位标题不算数）。"""
    d = _write_memo(tmp_path, decisions="- **D1 …**", constraints="")
    problems = check_decision_memo(d)
    assert len(problems) == 1, problems
    assert "承重约束" in problems[0] and "为空" in problems[0]


def test_comment_only_section_is_red(tmp_path):
    """⭐ 小节里只有模板注释 ⇒ 仍判空（把模板原样交上来不算写过）。"""
    d = _write_memo(tmp_path, decisions="<!-- 待填 -->", constraints="- **C1 …** 证据锚：a.py:1")
    problems = check_decision_memo(d)
    assert len(problems) == 1, problems
    assert "拍板决策" in problems[0]


def test_both_sections_missing_reports_both(tmp_path):
    """两节都缺 ⇒ 两条都报出来，不在第一条就短路（人一次改完）。"""
    d = tmp_path / "changes" / "demo"
    d.mkdir(parents=True)
    (d / MEMO_FILENAME).write_text("# 决策纪要 · demo\n\n## 目标态\n\n一句话。\n", encoding="utf-8")
    problems = check_decision_memo(d)
    assert len(problems) == 2, problems


def test_complete_memo_is_green(tmp_path):
    """⭐ 反向锚：填齐了必须判绿 —— 否则本门是个恒红的假门，同样没有信息量。"""
    d = _write_memo(
        tmp_path,
        decisions="- **D1 拷问前置** — 依据：改想法比改四份成文便宜；砍掉的候选：先生成后拷问（锚定效应）",
        constraints="- **C1 CLI 无 rename change** — 验证方式：`openspec new --help`；证据锚：实跑输出仅 change 子命令",
    )
    assert check_decision_memo(d) == []


def test_subheading_does_not_end_the_section(tmp_path):
    """⭐ `###` 子标题**属于本节正文**，MUST NOT 终止 `##` 小节。

    决策纪要必然用 `### D1 …` 列决策 —— 若任何 `#` 开头的行都断，这类纪要会被判「为空」= 假红。
    """
    d = _write_memo(
        tmp_path,
        decisions="### D1 拷问前置\n\n依据：改想法比改四份成文便宜。",
        constraints="### C1 CLI 无 rename change\n\n证据锚：`openspec new --help` 实跑输出。",
    )
    assert check_decision_memo(d) == []


def test_heading_inside_fenced_block_is_not_a_real_heading(tmp_path):
    """⭐⭐ **本门的 dogfood 自指坑**：纪要在「拍板决策」里引用 schema 模板，
    而模板的代码块内含 `## 承重约束` 字面量 —— 若围栏无感，门会把它当成真小节，
    于是**真正空着的** `## 承重约束` 反而判绿（假绿，`/sdflow-spec` 在本仓自跑必然命中）。

    三族围栏各来一发（``` / ~~~ / 四 backtick）——CommonMark 的**有界**变体，数得完（基准 5）。
    """
    for n, fence in enumerate(("```markdown", "~~~markdown", "````markdown")):
        close = fence.split("markdown")[0]
        d = _write_memo(
            tmp_path / f"case{n}",
            decisions=f"- **D1 纪要格式照 schema** — 模板：\n\n{fence}\n## 承重约束\n\n- **C1 …**\n{close}\n",
            constraints="",
        )
        problems = check_decision_memo(d)
        assert len(problems) == 1, f"{fence}: {problems}"
        assert "承重约束" in problems[0] and "为空" in problems[0], f"{fence}: {problems}"


def test_fenced_heading_neither_truncates_nor_relocates_the_section():
    """⭐ 同一个洞的另外两侧（直接打 `_section_body` 这个判据本体）：

    ① 围栏内的 `## X` MUST NOT **截断**本节正文（否则围栏之后的内容整段丢失）；
    ② 真正的 `## X` 小节 MUST 被定位到**围栏外**那一处（否则取到的是模板里的假小节）。
    """
    text = ("## 拍板决策\n\n```markdown\n## 承重约束\n<模板占位>\n```\n\n- **D1 真决策**\n\n"
            "## 承重约束\n\n- **C1 真约束**\n")
    body = _section_body(text, "## 拍板决策")
    assert "D1 真决策" in body, f"围栏内的标题截断了本节正文：{body!r}"
    assert _section_body(text, "## 承重约束").strip().startswith("- **C1"), "定位到了围栏内的假小节"


def test_heading_hidden_in_html_comment_block_is_red(tmp_path):
    """⭐ 把整节注释掉（多行 `<!-- … -->`）⇒ 那个标题不算数，仍判缺失/为空。

    与 `_strip_noise` 是**两件事**：那条管「小节里只有注释」，这条管「标题本身被注释掉」。
    注释块无感 ⇒ 注释里的 `## 承重约束` 被当真小节、`-->` 被当正文 ⇒ 假绿。
    """
    d = tmp_path / "changes" / "demo"
    d.mkdir(parents=True)
    (d / MEMO_FILENAME).write_text(
        "# 决策纪要 · demo\n\n## 拍板决策\n\n- **D1 …**\n\n"
        "<!--\n## 承重约束\n\n- **C1 …**\n-->\n",
        encoding="utf-8",
    )
    problems = check_decision_memo(d)
    assert len(problems) == 1, problems
    assert "承重约束" in problems[0]


def test_schema_doc_and_gate_agree():
    """⭐ 小节名是**共享字符串**：门与**全部**消费者 MUST 逐字一致。

    消费者三处（`grep -rn "## 承重约束"` 全量扫，不加 `--include`）：本门 · schema 文档 ·
    `sdflow-spec/SKILL.md` 的 C.1 起手核验。少守一处 ⇒ 改名漏改那一处仍全绿（基准 3：面治）。

    🔴 **判据必须带右界**（本仓「gate 子串检测自指坑」的同形）：裸 `heading in doc` 下
    `## 承重约束` 是 `## 承重约束项` 的**前缀** ⇒ 改名成后者，守卫照样绿（实测：变异 M5 不红）。
    故要求紧跟其后的字符 ∈ {空白, 反引号, 竖线} 或已到文末 —— 覆盖三种真实出现形态：
    代码块里独占一行、行内 `` `## 承重约束` ``、表格单元格 `| ## 承重约束 |`。
    """
    for path in MEMO_SECTION_CONSUMERS:
        doc = path.read_text(encoding="utf-8")
        for heading in REQUIRED_SECTIONS:
            assert re.search(re.escape(heading) + r"(?![^\s`|])", doc), (
                f"{path.relative_to(REPO)} 里找不到小节「{heading}」（须整名出现，前缀不算）"
                "——门与消费者已漂移")
    assert MEMO_FILENAME in MEMO_SCHEMA_DOC.read_text(encoding="utf-8")


def test_repo_memos_all_pass_the_gate():
    """本仓 `openspec/changes/*/` 下**已存在的**纪要逐份过门。

    ⚠️ **诚实边界**：本仓当前尚无任何 change 由 `/sdflow-spec` 产出 ⇒ 这条现在扫到 0 份，
    是**目标态**的面级守卫（第一份纪要落盘即生效），不是当下就在挡什么。
    非空断言留给上面的 fixture 用例，本条 MUST NOT 被当作「门已在守」的证据。
    """
    memos = sorted((REPO / "openspec" / "changes").glob("*/" + MEMO_FILENAME))
    problems = [p for m in memos for p in check_decision_memo(m.parent)]
    assert problems == [], "\n".join(problems)


# ---------------------------------------------------------------- 门 2：存在态 vs 合格态

openspec_cli = pytest.mark.skipif(
    shutil.which("openspec") is None,
    reason="openspec CLI 未安装 —— 本门需要真跑 CLI（MUST NOT 手搓 Markdown 解析器顶替）",
)

_GOOD_PROPOSAL = """# Demo Proposal

## Why
需要一个能跑的最小 change 来验证门。

## What Changes
- 加一个 foo

## Impact
- specs/foo
"""

_GOOD_SPEC = """# foo Delta Specification

## ADDED Requirements

### Requirement: Foo SHALL work
Foo SHALL work.

#### Scenario: works
- **WHEN** 触发
- **THEN** 有结果
"""

_GOOD_DESIGN = """# Demo Design

## Context
背景。

## Goals / Non-Goals
**Goals:** 让门跑起来。

## Decisions
D1：见 decision-memo.md。

## Risks / Trade-offs
无。

## Migration Plan
无。

## Open Questions
无。
"""


def _make_change(root, *, proposal=_GOOD_PROPOSAL, spec=_GOOD_SPEC, design=_GOOD_DESIGN):
    """在 `root` 下造一个最小可 validate 的 openspec 仓，返回 change 目录。"""
    change = root / "openspec" / "changes" / "demo"
    (change / "specs" / "foo").mkdir(parents=True)
    (root / "openspec" / "config.yaml").write_text(
        "schema: spec-driven\ncontext: |\n  gate fixture\n", encoding="utf-8")
    (change / "proposal.md").write_text(proposal, encoding="utf-8")
    (change / "specs" / "foo" / "spec.md").write_text(spec, encoding="utf-8")
    (change / "design.md").write_text(design, encoding="utf-8")
    (change / "tasks.md").write_text("# Tasks\n\n## 1. 组\n\n- [ ] 1.1 做\n", encoding="utf-8")
    return change


# 外部 CLI 一律带 timeout：挂起时本用例自己红（TimeoutExpired），
# 而不是把 CI job 拖到 workflow 级超时才被杀（那时红的是整条泳道，看不出是哪一条）。
_CLI_TIMEOUT_S = 60


def _validate(root):
    return subprocess.run(
        ["openspec", "validate", "demo", "--strict", "--type", "change"],
        cwd=str(root), capture_output=True, text=True, timeout=_CLI_TIMEOUT_S)


def _status_is_complete(root):
    out = subprocess.run(
        ["openspec", "status", "--change", "demo", "--json"],
        cwd=str(root), capture_output=True, text=True, check=True,
        timeout=_CLI_TIMEOUT_S).stdout
    import json
    return json.loads(out)["isComplete"]


@openspec_cli
def test_intact_change_passes_strict_validate(tmp_path):
    """反向锚：完好的四件套必须绿 —— 否则下面的红说明不了任何事。"""
    _make_change(tmp_path)
    r = _validate(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr


@openspec_cli
def test_truncated_spec_delta_is_caught_by_strict_validate(tmp_path):
    """⭐ 门 2 本体：产物写到一半（Requirement 后被截断）⇒ `validate --strict` 判红。

    这正是 SA-05「半截产物不被判完成」要挡的形态：写 specs 时命中输出上限，
    文件落盘但 Scenario 没写完。
    """
    truncated = "# foo Delta Specification\n\n## ADDED Requirements\n\n### Requirement: Foo SHALL work\nFoo SHALL wo"
    _make_change(tmp_path, spec=truncated)
    r = _validate(tmp_path)
    assert r.returncode != 0, "半截 spec delta 竟然过了 strict validate"
    assert "scenario" in (r.stdout + r.stderr).lower()


@openspec_cli
def test_status_says_done_while_validate_says_red(tmp_path):
    """⭐⭐ 「存在态 ≠ 合格态」的正面证明 —— 同一份盘面，两个判据结论相反。

    `status` 只看文件在不在（CLI `artifact-graph/state.js:25-29`）⇒ 半截产物报 done。
    ∴ SKILL.md 的写后核验 MUST 两个都跑，MUST NOT 只跑 status。
    """
    truncated = "# foo Delta Specification\n\n## ADDED Requirements\n\n### Requirement: Foo SHALL work\nFoo SHALL wo"
    _make_change(tmp_path, spec=truncated)
    assert _status_is_complete(tmp_path) is True, "status 的判据若已不是文件存在性，本门的前提要重写"
    assert _validate(tmp_path).returncode != 0


@openspec_cli
@pytest.mark.parametrize("kind, kwargs", [
    ("半截 design.md", {"design": "# Demo Design\n\n## Context\n背景写到一半"}),
    ("半截 proposal.md", {"proposal": "# Demo Proposal\n\n## Why\n理由写到一半"}),
    ("空 proposal.md", {"proposal": ""}),
])
def test_validate_strict_only_covers_delta_specs(tmp_path, kind, kwargs):
    """⭐ **覆盖边界钉子**：`validate --strict` 只校验 `specs/*/spec.md` 的 delta 结构。

    实证（CLI 1.5.0）：`dist/core/validation/validator.js` 全文无 `design` 字样；
    change 路径实际只跑 `validateChangeDeltaSpecs`——`proposal.md` 整份删掉照样报 valid。

    ⇒ SA-05 Scenario「生成 design.md 命中输出上限 → validate 不过」**对 design.md 不成立**；
    proposal.md / tasks.md 同样无覆盖。这三份的「未截断」只能由终审人判，
    SKILL.md C.4 与 `references/degradation-ladder.md` §5 已如实声明该残余。

    本条**不是**在为缺陷背书 —— 它让这个事实可机械追踪：openspec 哪天扩了覆盖面，
    本条会红，提示回来收紧那两处诚实边界声明。
    """
    _make_change(tmp_path, **kwargs)
    r = _validate(tmp_path)
    assert r.returncode == 0, (
        f"openspec 开始校验 {kind} 了 —— 请更新 sdflow-spec/SKILL.md C.4 与 "
        "references/degradation-ladder.md §5 的覆盖边界声明\n" + r.stdout + r.stderr)
