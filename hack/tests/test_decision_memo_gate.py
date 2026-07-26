"""`sdflow-spec` 的两道机械门。

【门 1 · 决策纪要】`decision-memo.md` 缺失 / 必填小节为空 ⇒ 红。
    纪要是 `/sdflow-spec` 相位 B 的**承重件**（`/clear` 无损这条不变式全靠它）。
    它是这条管线上**唯一有确定性信号的东西** —— 文件在不在、两个必填小节有没有正文，
    都是逐行字面量可判的（语法面有界，基准 5）。
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
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]

# 纪要格式的真相源 —— 小节名从这里来，改名两边一起改（下方 test_schema_doc_and_gate_agree 守）
MEMO_SCHEMA_DOC = REPO / "sdflow-spec" / "references" / "decision-memo-schema.md"

MEMO_FILENAME = "decision-memo.md"

# 必填且必须非空的小节（SA-01 Scenario「纪要缺失拒绝生成」逐字点名的两项）
REQUIRED_SECTIONS = ("## 拍板决策", "## 承重约束")


# ---------------------------------------------------------------- 门 1 的判据本体

def _section_body(text, heading):
    """取 `heading` 这一行到下一个同级/更高级 ATX 标题（或 EOF）之间的正文。

    【语法面有界】只做两件事：逐行字面量比对标题行、逐行看是否以 `#` 开头。
    MUST NOT 演化成「解析 Markdown 结构」（基准 5）。
    """
    lines = text.splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == heading)
    except StopIteration:
        return None
    body = []
    for l in lines[start + 1:]:
        if l.startswith("#"):
            break
        body.append(l)
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


def test_schema_doc_and_gate_agree():
    """⭐ 小节名是**共享字符串**：门与格式真相源 MUST 逐字一致。

    改了 `references/decision-memo-schema.md` 里的标题却忘了改本门（或反之）⇒ 这里红。
    """
    doc = MEMO_SCHEMA_DOC.read_text(encoding="utf-8")
    for heading in REQUIRED_SECTIONS:
        assert heading in doc, f"{MEMO_SCHEMA_DOC.name} 里找不到小节「{heading}」——门与真相源已漂移"
    assert MEMO_FILENAME in doc


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


def _validate(root):
    return subprocess.run(
        ["openspec", "validate", "demo", "--strict", "--type", "change"],
        cwd=str(root), capture_output=True, text=True)


def _status_is_complete(root):
    out = subprocess.run(
        ["openspec", "status", "--change", "demo", "--json"],
        cwd=str(root), capture_output=True, text=True, check=True).stdout
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
