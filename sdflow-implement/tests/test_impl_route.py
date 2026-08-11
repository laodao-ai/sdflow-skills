"""pytest for sdflow-implement/scripts/impl_route.py（tickets 调度 helper：frontier /
task-text 子命令 + Blocked-by 拓扑解析）

覆盖保留半场（frontier / task-text / parse_blocked_by / next_ready / extract_task_text /
TopoError / BLOCKED_BY_RE）的完整矩阵：
- parse_blocked_by/next_ready：线性链/菱形/环→错/自环→错/缺依赖号→错/done 集过滤
- CLI frontier：next-ready 号列 + TopoError 退出码
- parse_blocked_by fence-aware + 标题正则收紧（对 sdflow-ship golden fixtures 的跨脚本一致性回归）
- Blocked-by 三态 fail-closed：缺失/重复/大小写变体/全角冒号 → TopoError
- 围栏词法单一源 = ship_gate.FenceTracker（跨脚本一致性）
- extract_task_text：单张 Task 原文机械抠取 + CLI task-text

[remove-superpowers-pipeline Task 1] route/config/marker 参照系用例已随 impl_route.py 路由
半场一并退役——那些用例断言的是本文件已不存在的行为（`route` 子命令、`read_config_pipeline`
/ `read_plan_marker` / `resolve_pipeline` / `RouteStop` / `_get_plan_sha` / `_yq` /
`_resolve_plan_path` 单一源核验，见 openspec/changes/remove-superpowers-pipeline/design.md）。
保留半场接口与行为逐字不变，本文件即回归网。
"""
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "impl_route.py"
sys.path.insert(0, str(SCRIPT.parent))
import impl_route as ir  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
SHIP_FIXTURES = REPO_ROOT / "sdflow-ship" / "tests" / "fixtures"


# ---------------------------------------------------------------------------
# parse_blocked_by / next_ready（拓扑）
# ---------------------------------------------------------------------------

def test_parse_linear_chain():
    text = (
        "### Task 1: A\n**Blocked-by:** none\n- [ ] x\n"
        "### Task 2: B\n**Blocked-by:** 1\n- [ ] x\n"
        "### Task 3: C\n**Blocked-by:** 2\n- [ ] x\n"
    )
    deps = ir.parse_blocked_by(text)
    assert deps == {1: set(), 2: {1}, 3: {2}}
    assert ir.next_ready(deps, set()) == [1]
    assert ir.next_ready(deps, {1}) == [2]
    assert ir.next_ready(deps, {1, 2}) == [3]
    assert ir.next_ready(deps, {1, 2, 3}) == []


def test_parse_diamond():
    text = (
        "### Task 1: A\nBlocked-by: none\n"
        "### Task 2: B\nBlocked-by: 1\n"
        "### Task 3: C\nBlocked-by: 1\n"
        "### Task 4: D\nBlocked-by: 2,3\n"
    )
    deps = ir.parse_blocked_by(text)
    assert deps == {1: set(), 2: {1}, 3: {1}, 4: {2, 3}}
    assert ir.next_ready(deps, {1}) == [2, 3]
    assert ir.next_ready(deps, {1, 2}) == [3]
    assert ir.next_ready(deps, {1, 2, 3}) == [4]


def test_cycle_raises_topoerror():
    text = "### Task 1: A\nBlocked-by: 2\n### Task 2: B\nBlocked-by: 1\n"
    with pytest.raises(ir.TopoError):
        ir.parse_blocked_by(text)


def test_self_loop_raises_topoerror():
    text = "### Task 1: A\nBlocked-by: 1\n"
    with pytest.raises(ir.TopoError):
        ir.parse_blocked_by(text)


def test_missing_dep_ref_raises_topoerror():
    text = "### Task 1: A\nBlocked-by: 5\n"
    with pytest.raises(ir.TopoError):
        ir.parse_blocked_by(text)


def test_done_set_filters_ready():
    text = "### Task 1: A\nBlocked-by: none\n### Task 2: B\nBlocked-by: 1\n"
    deps = ir.parse_blocked_by(text)
    assert ir.next_ready(deps, {1}) == [2]
    assert 1 not in ir.next_ready(deps, {1})
    assert ir.next_ready(deps, {1, 2}) == []


# ---------------------------------------------------------------------------
# [impl-review-fix] parse_blocked_by：fence-aware 解析 + 标题正则收紧
# ---------------------------------------------------------------------------

def test_task_header_no_space_after_hashes_not_counted():
    # `###Task 1:`（### 与 Task 间无空格）不匹配收紧后的标题正则——与 gate TASK_TITLE_RE 一致
    text = "###Task 1: A\nBlocked-by: none\n"
    assert ir.parse_blocked_by(text) == {}


def test_task_header_double_space_not_counted():
    # `### Task  1:`（Task 与号之间两个空格）同样不计——排版漂移，与 gate 一致
    text = "### Task  1: A\nBlocked-by: none\n"
    assert ir.parse_blocked_by(text) == {}


def test_fenced_header_does_not_leak_task_id_cross_script_golden():
    # 跨脚本一致性回归：sdflow-ship golden fixture 里 fence 内的伪 `### Task 9:` 对
    # parse_blocked_by 同样不可见（与 ship_gate.plan_task_ids 口径一致）。
    text = (SHIP_FIXTURES / "tickets_plan_fenced_header.md").read_text(encoding="utf-8")
    deps = ir.parse_blocked_by(text)
    assert set(deps.keys()) == {1, 2, 3}
    assert deps == {1: set(), 2: {1}, 3: {1, 2}}


def test_fence_dangling_raises_topoerror_cross_script_golden():
    # 悬空 fence（EOF 未闭合）→ TopoError，fail-closed 同向 gate 的 UNKNOWN 判定。
    text = (SHIP_FIXTURES / "tickets_plan_fence_dangling.md").read_text(encoding="utf-8")
    with pytest.raises(ir.TopoError):
        ir.parse_blocked_by(text)


def test_golden_plan_parses_cleanly_cross_script():
    # golden fixture 四张票（含收尾票 T250）均有 canonical Blocked-by 行——三态契约收紧后 golden 仍须全绿。
    text = (SHIP_FIXTURES / "tickets_plan_golden.md").read_text(encoding="utf-8")
    deps = ir.parse_blocked_by(text)
    assert deps == {1: set(), 2: {1}, 3: {1, 2}, 4: {1, 2, 3}}


# ---------------------------------------------------------------------------
# [impl-review-fix] Blocked-by 三态 fail-closed：缺失/重复/大小写变体/全角冒号
# ---------------------------------------------------------------------------

def test_blocked_by_missing_raises_topoerror():
    text = "### Task 1: A\n- [ ] x\n"
    with pytest.raises(ir.TopoError):
        ir.parse_blocked_by(text)


def test_blocked_by_duplicate_raises_topoerror():
    text = "### Task 1: A\nBlocked-by: none\nBlocked-by: none\n"
    with pytest.raises(ir.TopoError):
        ir.parse_blocked_by(text)


def test_blocked_by_lowercase_variant_raises_topoerror():
    text = "### Task 1: A\nblocked-by: none\n"
    with pytest.raises(ir.TopoError):
        ir.parse_blocked_by(text)


def test_blocked_by_fullwidth_colon_variant_raises_topoerror():
    text = "### Task 1: A\nBlocked-by：none\n"
    with pytest.raises(ir.TopoError):
        ir.parse_blocked_by(text)


def test_blocked_by_inline_form_still_matches_canonical():
    # 行内形态（如 golden fixture 的 R-ID 前缀写法变体）仍应被 canonical 正则命中，
    # 非仅独占一行才算数。
    text = "### Task 1: A\nR-ID: 1.1 · Blocked-by: none\n"
    deps = ir.parse_blocked_by(text)
    assert deps == {1: set()}


# ---------------------------------------------------------------------------
# CLI: frontier
# ---------------------------------------------------------------------------

def _run_frontier(plan_path, done):
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "frontier", "--plan", str(plan_path), "--done", done],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def test_cli_frontier_prints_ready_list(tmp_path):
    p = tmp_path / "plan.md"
    p.write_text(
        "### Task 1: A\nBlocked-by: none\n"
        "### Task 2: B\nBlocked-by: 1\n"
        "### Task 3: C\nBlocked-by: 1\n", encoding="utf-8")
    code, out, _ = _run_frontier(p, "1")
    assert code == 0
    assert out == "2 3"


def test_cli_frontier_done_none_literal(tmp_path):
    p = tmp_path / "plan.md"
    p.write_text("### Task 1: A\nBlocked-by: none\n", encoding="utf-8")
    code, out, _ = _run_frontier(p, "none")
    assert code == 0
    assert out == "1"


def test_cli_frontier_topoerror_exit6(tmp_path):
    p = tmp_path / "plan.md"
    p.write_text("### Task 1: A\nBlocked-by: 1\n", encoding="utf-8")
    code, out, err = _run_frontier(p, "none")
    assert code == 6
    assert out == ""
    assert err


def test_cli_frontier_blocked_by_missing_exit6(tmp_path):
    p = tmp_path / "plan.md"
    p.write_text("### Task 1: A\n- [ ] x\n", encoding="utf-8")
    code, out, err = _run_frontier(p, "none")
    assert code == 6
    assert out == ""
    assert err


def test_cli_frontier_blocked_by_duplicate_exit6(tmp_path):
    p = tmp_path / "plan.md"
    p.write_text("### Task 1: A\nBlocked-by: none\nBlocked-by: none\n", encoding="utf-8")
    code, out, err = _run_frontier(p, "none")
    assert code == 6
    assert out == ""
    assert err


def test_cli_frontier_blocked_by_lowercase_variant_exit6(tmp_path):
    p = tmp_path / "plan.md"
    p.write_text("### Task 1: A\nblocked-by: none\n", encoding="utf-8")
    code, out, err = _run_frontier(p, "none")
    assert code == 6
    assert out == ""
    assert err


def test_cli_frontier_blocked_by_fullwidth_colon_variant_exit6(tmp_path):
    p = tmp_path / "plan.md"
    p.write_text("### Task 1: A\nBlocked-by：none\n", encoding="utf-8")
    code, out, err = _run_frontier(p, "none")
    assert code == 6
    assert out == ""
    assert err


# ---------------------------------------------------------------------------
# [impl-review-fix] CLI frontier × sdflow-ship golden fixtures（手工复核对应用例）
# ---------------------------------------------------------------------------

def test_cli_frontier_fenced_header_done1_outputs_2():
    plan = SHIP_FIXTURES / "tickets_plan_fenced_header.md"
    code, out, _ = _run_frontier(plan, "1")
    assert code == 0
    assert out == "2"


def test_cli_frontier_fence_dangling_exit6():
    plan = SHIP_FIXTURES / "tickets_plan_fence_dangling.md"
    code, out, err = _run_frontier(plan, "none")
    assert code == 6
    assert out == ""
    assert err


# ══════════════════════════════════════════════════════════════════════════
# [impl-review-fix F4] 围栏词法单一源 = ship_gate.FenceTracker
#
# 旧状态：本文件手抄 `line.lstrip().startswith("```")`，注释却声称「口径与
# ship_gate._parse_plan 一致」——gate 侧已收敛到 FenceTracker（同种 + 长度 ≥ 开启符
# + 尾部校验），手抄副本没跟上 ⇒ 那句注释是假的，两个解析器对同一 plan 给出不同
# 段落边界；被隐藏的行若恰是唯一未勾项，完成判据侧假 ✅。
# ══════════════════════════════════════════════════════════════════════════

NESTED_FENCE_FIXTURE = SHIP_FIXTURES / "tickets_plan_nested_fence.md"


def test_fence_lexer_is_the_single_source_from_ship_gate():
    # 机械守单一源关系：手抄一份副本回来 ⇒ 本例转红
    sys.path.insert(0, str(REPO_ROOT / "sdflow-ship" / "scripts"))
    import ship_gate as sg  # noqa: E402

    assert ir._FenceTracker is sg.FenceTracker


def test_nested_example_fence_agrees_with_gate_cross_script():
    # 判别性 fixture：外层 ````markdown 内嵌 ```text 示例块。旧手抄口径会被内层 ```
    # 提前关掉外层围栏 ⇒ 多认一个伪 `### Task 9:` 段（与 gate 分叉）。
    sys.path.insert(0, str(REPO_ROOT / "sdflow-ship" / "scripts"))
    import ship_gate as sg  # noqa: E402

    text = NESTED_FENCE_FIXTURE.read_text(encoding="utf-8")
    gate_ids = {int(i) for i in sg._parse_plan(text)[0]}
    route_ids = set(ir.parse_blocked_by(text).keys())
    assert gate_ids == route_ids == {1, 2}      # 伪 Task 9 两侧都不可见


# ---------------------------------------------------------------------------
# extract_task_text：单张 Task 原文机械抠取（供 task-text CLI）
# ---------------------------------------------------------------------------

def test_extract_task_text_basic():
    text = (SHIP_FIXTURES / "tickets_plan_golden.md").read_text(encoding="utf-8")
    out = ir.extract_task_text(text, 2)
    assert out.startswith("### Task 2: 通知节流窗口可配置")
    assert "调整配置项后" in out
    assert "### Task 3:" not in out          # 不越界收下一段
    assert "### Task 1:" not in out          # 不倒收前一段


def test_extract_task_text_missing_task_returns_none():
    text = (SHIP_FIXTURES / "tickets_plan_golden.md").read_text(encoding="utf-8")
    assert ir.extract_task_text(text, 99) is None


def test_extract_task_text_fenced_pseudo_header_not_boundary_and_content_preserved():
    # 判别性 fixture：Task 2 段内嵌一个 fenced 示例，里面写着假的 `### Task 9:`。
    # 要求：①假标题不切段（Task 2 抠取不提前止步、也不被误认成 Task 9）；
    # ②fenced 内容本身原样保留在抠出结果里（这是 Task 2 的真实正文，不是噪音——
    # 与 parse_blocked_by 整段跳过 fenced 行的口径有意不同）。
    text = (SHIP_FIXTURES / "tickets_plan_fenced_header.md").read_text(encoding="utf-8")
    out = ir.extract_task_text(text, 2)
    assert out.startswith("### Task 2: 通知节流窗口可配置")
    assert "### Task 9: 直接改" in out        # fenced 内容保留
    assert "### Task 3:" not in out           # 真实下一段未被误收


def test_extract_task_text_dangling_fence_raises_topoerror():
    text = (SHIP_FIXTURES / "tickets_plan_fence_dangling.md").read_text(encoding="utf-8")
    with pytest.raises(ir.TopoError):
        ir.extract_task_text(text, 1)


# ---------------------------------------------------------------------------
# CLI: task-text
# ---------------------------------------------------------------------------

def _run_task_text(plan_path, task, out=None):
    cmd = [sys.executable, str(SCRIPT), "task-text", "--plan", str(plan_path),
           "--task", str(task)]
    if out is not None:
        cmd += ["--out", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def test_cli_task_text_default_out_path_under_impl_reports(tmp_path):
    change_dir = tmp_path / "openspec" / "changes" / "demo"
    change_dir.mkdir(parents=True)
    plan = change_dir / "tickets.md"
    plan.write_text(
        "### Task 1: A\nBlocked-by: none\n- [ ] x\n"
        "### Task 2: B\nBlocked-by: 1\n- [ ] y\n", encoding="utf-8")

    code, out, err = _run_task_text(plan, 1)
    assert code == 0, err
    default_out = change_dir / "impl-reports" / "task1-brief.md"
    assert default_out.is_file()
    content = default_out.read_text(encoding="utf-8")
    assert content.startswith("### Task 1: A")
    assert "### Task 2:" not in content


def test_cli_task_text_explicit_out_path(tmp_path):
    plan = tmp_path / "plan.md"
    plan.write_text("### Task 1: A\nBlocked-by: none\n- [ ] x\n", encoding="utf-8")
    out_path = tmp_path / "custom" / "brief.md"

    code, out, err = _run_task_text(plan, 1, out=out_path)
    assert code == 0, err
    assert out_path.is_file()
    assert out_path.read_text(encoding="utf-8").startswith("### Task 1: A")


def test_cli_task_text_missing_task_exit6(tmp_path):
    plan = tmp_path / "plan.md"
    plan.write_text("### Task 1: A\nBlocked-by: none\n- [ ] x\n", encoding="utf-8")
    code, out, err = _run_task_text(plan, 9)
    assert code == 6
    assert out == ""
    assert err


def test_cli_task_text_plan_missing_exit6(tmp_path):
    code, out, err = _run_task_text(tmp_path / "no-such-plan.md", 1)
    assert code == 6
    assert out == ""
    assert err
