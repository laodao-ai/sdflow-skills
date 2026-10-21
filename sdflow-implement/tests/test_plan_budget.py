"""pytest for impl_route.py `plan-budget`（T249：出票预算计量口径）。

口径：预算票 = 全部票 − 合规迁移批次 − 唯一「R-ID: all」收尾票，预算票数 ≤ BUDGET_MAX。
迁移批次豁免须机读声明（批次票 `Migration-of: <expand 号>`，expand 票 `Transform: <变换>`），
且结构合规（批次 Blocked-by 恰为 {expand}；存在 contract 票 Blocked-by ⊇ 全部批次），否则报违规。
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "impl_route.py"
sys.path.insert(0, str(SCRIPT.parent))
import impl_route as ir  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
ADR_ARCHIVE_TICKETS = (REPO_ROOT / "openspec" / "changes" / "archive"
                       / "2026-09-25-add-sdflow-adr" / "tickets.md")
needs_full_repo = pytest.mark.skipif(
    not ADR_ARCHIVE_TICKETS.is_file(),
    reason="被测语料是本仓 openspec/ 归档；发布 clone 不含 openspec/")


def _task(n, title, blocked_by, r_id="R1", extra=""):
    return (f"### Task {n}: {title}\n\n**Blocked-by:** {blocked_by}\n**R-ID:** {r_id}\n"
            f"{extra}\n- [ ] x\n\n")


def _closing(n, deps):
    return (f"### Task {n}: 实现验证（收尾）\n\n**Blocked-by:** {deps}\n**R-ID:** all\n\n"
            "按聚合套件发现契约运行。\n\n- [ ] x\n")


def _plan(*parts):
    return "---\nimpl-pipeline: tickets\n---\n\n" + "".join(parts)


def _functional_chain(count):
    parts = [_task(1, "A", "none")]
    for i in range(2, count + 1):
        parts.append(_task(i, f"T{i}", str(i - 1)))
    return parts


def test_plan_budget_within_budget_passes():
    text = _plan(*_functional_chain(4), _closing(5, "1, 2, 3, 4"))
    res = ir.plan_budget(text)
    assert res["violations"] == []
    assert res["budgeted"] == [1, 2, 3, 4]
    assert res["closing"] == [5]
    assert res["migration_batches"] == []


def test_plan_budget_over_budget_without_markers_fails():
    text = _plan(*_functional_chain(7), _closing(8, "1, 2, 3, 4, 5, 6, 7"))
    res = ir.plan_budget(text)
    assert res["budgeted"] == [1, 2, 3, 4, 5, 6, 7]
    assert any("超出" in v for v in res["violations"])


def _expand_contract_plan(batch_blocked_by="1", transform=True, with_contract=True):
    expand_extra = "**Transform:** 把共享函数 foo 改名为 bar（新旧并存）" if transform else ""
    parts = [_task(1, "expand", "none", extra=expand_extra)]
    batches = list(range(2, 10))   # 8 张批次，超过预算上限也合法
    for b in batches:
        parts.append(_task(b, f"迁移批次 {b}", batch_blocked_by, extra="**Migration-of:** 1"))
    nxt = 10
    if with_contract:
        parts.append(_task(nxt, "contract", ", ".join(str(b) for b in batches)))
        nxt += 1
    parts.append(_task(nxt, "独立功能", "none"))
    deps = ", ".join(str(i) for i in range(1, nxt + 1))
    parts.append(_closing(nxt + 1, deps))
    return _plan(*parts)


def test_plan_budget_valid_expand_contract_exempts_batches():
    res = ir.plan_budget(_expand_contract_plan())
    assert res["violations"] == []
    assert res["migration_batches"] == [2, 3, 4, 5, 6, 7, 8, 9]
    assert res["budgeted"] == [1, 10, 11]


def test_plan_budget_batch_blocked_by_not_exactly_expand_fails():
    res = ir.plan_budget(_expand_contract_plan(batch_blocked_by="none"))
    assert any("Task 2" in v and "Blocked-by" in v for v in res["violations"])


def test_plan_budget_expand_without_transform_fails():
    res = ir.plan_budget(_expand_contract_plan(transform=False))
    assert any("Transform" in v for v in res["violations"])


def test_plan_budget_missing_contract_fails():
    res = ir.plan_budget(_expand_contract_plan(with_contract=False))
    assert any("contract" in v for v in res["violations"])


def test_plan_budget_migration_of_unknown_task_fails():
    text = _plan(_task(1, "A", "none"),
                 _task(2, "批次", "1", extra="**Migration-of:** 9"),
                 _closing(3, "1, 2"))
    res = ir.plan_budget(text)
    assert any("Task 2" in v and "9" in v for v in res["violations"])


def test_plan_budget_marker_inside_fence_ignored():
    # fenced 示例里的 Migration-of 不得生效（口径同 parse_blocked_by 的 fence-aware）
    text = _plan(_task(1, "A", "none", extra="```\n**Migration-of:** 1\n```"),
                 _closing(2, "1"))
    res = ir.plan_budget(text)
    assert res["migration_batches"] == []
    assert res["violations"] == []


@needs_full_repo
def test_plan_budget_rejects_add_sdflow_adr_archive_shape():
    """回看：add-sdflow-adr 的审计批次无 expand / Transform / Migration-of，Blocked-by 是 2,3,4，
    在新口径下 10 张功能票全部计入预算 ⇒ 超限被拦。"""
    res = ir.plan_budget(ADR_ARCHIVE_TICKETS.read_text(encoding="utf-8"))
    assert res["closing"] == [11]
    assert res["budgeted"] == list(range(1, 11))
    assert any("超出" in v for v in res["violations"])


def _run_cli(plan_path):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "plan-budget", "--plan", str(plan_path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace")


def test_cli_plan_budget_ok_exit0(tmp_path):
    p = tmp_path / "tickets.md"
    p.write_text(_plan(*_functional_chain(3), _closing(4, "1, 2, 3")), encoding="utf-8")
    r = _run_cli(p)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["violations"] == []


def test_cli_plan_budget_violation_exit1(tmp_path):
    p = tmp_path / "tickets.md"
    p.write_text(_plan(*_functional_chain(7), _closing(8, "1, 2, 3, 4, 5, 6, 7")),
                 encoding="utf-8")
    r = _run_cli(p)
    assert r.returncode == 1
    assert json.loads(r.stdout)["violations"]
    assert "超出" in r.stderr


def test_cli_plan_budget_topo_error_exit6(tmp_path):
    p = tmp_path / "tickets.md"
    p.write_text(_plan("### Task 1: A\n**R-ID:** R1\n- [ ] x\n"), encoding="utf-8")
    r = _run_cli(p)
    assert r.returncode == 6
