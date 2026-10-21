"""checklists 注册一致性（T284）：domains/*.md 文件集 ↔ README 领域注册表 ↔ 前缀表 ↔ 文件内规则 ID。

新增 / 删除 domain 时要手工同步两侧 README 的两张表，漏一处就失鲜（add-frontend-checklists
评审实证 4 处）。Markdown 表格行的语法面有界，手写解析即可。
"""
import re
from pathlib import Path

import pytest

WORKFLOW = Path(__file__).resolve().parents[1] / "assets" / "workflow"
SIDES = ["spec-checklists", "code-checklists"]

ROW_RE = re.compile(r"^\|(.+)\|\s*$")
RULE_ID_RE = re.compile(r"^\|\s*\*{0,2}([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-)\d+\b")
EXTENDS_RE = re.compile(r"`extends:\s*([a-z0-9-]+)`")
PREFIX_TOKEN_RE = re.compile(r"`([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-)NN`")


def _cells(line):
    m = ROW_RE.match(line.strip())
    return [c.strip() for c in m.group(1).split("|")] if m else None


def _registry(side):
    """README 领域注册表 → {文件名: (extends, ID 前缀)}"""
    rows = {}
    for line in (WORKFLOW / side / "README.md").read_text(encoding="utf-8").splitlines():
        cells = _cells(line)
        if not cells or len(cells) < 4:
            continue
        m = re.fullmatch(r"`domains/([a-z0-9-]+\.md)`", cells[0])
        if m:
            rows[m.group(1)] = (cells[1], cells[3].strip("`"))
    return rows


def _prefix_table(side):
    """README 前缀表里登记的全部前缀（`X-NN` 形态）。"""
    text = (WORKFLOW / side / "README.md").read_text(encoding="utf-8")
    return set(PREFIX_TOKEN_RE.findall(text))


@pytest.mark.parametrize("side", SIDES)
def test_registry_lists_exactly_the_domain_files(side):
    files = {p.name for p in (WORKFLOW / side / "domains").glob("*.md")}
    registry = set(_registry(side))
    assert files, f"{side}/domains 下一个领域文件都没有——扫描面坏了"
    assert registry == files, (
        f"{side}/README.md 领域注册表与 domains/ 不一致："
        f"有文件未登记 {sorted(files - registry)}，有登记无文件 {sorted(registry - files)}")


@pytest.mark.parametrize("side", SIDES)
def test_every_registered_prefix_is_in_prefix_table(side):
    missing = sorted({prefix for _, prefix in _registry(side).values()} - _prefix_table(side))
    assert not missing, f"{side}/README.md 前缀表缺少：{missing}（每个领域前缀都要以 `X-NN` 形态登记）"


@pytest.mark.parametrize("side", SIDES)
def test_domain_rule_ids_use_registered_prefix(side):
    for name, (_, prefix) in _registry(side).items():
        lines = (WORKFLOW / side / "domains" / name).read_text(encoding="utf-8").splitlines()
        ids = [m.group(1) for m in (RULE_ID_RE.match(l) for l in lines) if m]
        assert ids, f"{side}/domains/{name} 里没找到任何规则 ID 行"
        wrong = sorted(set(ids) - {prefix})
        assert not wrong, f"{side}/domains/{name} 的规则 ID 前缀 {wrong} 与注册表登记的 {prefix} 不符"


@pytest.mark.parametrize("side", SIDES)
def test_domain_extends_matches_registry(side):
    registry = _registry(side)
    stems = {n[:-3] for n in registry} | {"base"}
    for name, (extends, _) in registry.items():
        assert extends in stems, f"{side}/README.md 里 {name} 的 extends={extends!r} 不是 base 或已登记领域"
        declared = EXTENDS_RE.findall((WORKFLOW / side / "domains" / name).read_text(encoding="utf-8"))
        assert declared and declared[0] == extends, (
            f"{side}/domains/{name} 声明 extends={declared[:1]}，注册表写的是 {extends!r}")
