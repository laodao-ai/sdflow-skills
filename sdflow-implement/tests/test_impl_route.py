"""pytest for sdflow-implement/scripts/impl_route.py

覆盖 plan Task 2 Step 1 的完整矩阵（TDD 先写，后实现）：
- read_config_pipeline：缺失/空值/tickets/superpowers/拼错值/带引号值
- read_plan_marker：缺文件/无 frontmatter/合法单键/键重复→停/非法值→停/未闭合 frontmatter→停
- CLI route：PIPELINE_RECEIPT 行格式（含在途锁定 vs 首跳 config 的路由合成规则）
- parse_blocked_by/next_ready：线性链/菱形/环→错/自环→错/缺依赖号→错/done 集过滤
- CLI frontier：next-ready 号列 + TopoError 退出码

[impl-review-fix] 补充矩阵（code-review 裁决修复，TDD 先写后实现）：
- BOM 剥离：read_config_pipeline / read_plan_marker
- 键匹配容忍冒号前空格：`impl-pipeline : tickets`（config 与 frontmatter 两处）
- 损坏引号值 fail-closed：未闭合引号 / 闭合引号后跟垃圾字符（config→unknown-value，marker→RouteStop）
- parse_blocked_by fence-aware + 标题正则收紧（对 sdflow-ship golden fixtures 的跨脚本一致性回归）
- Blocked-by 三态 fail-closed：缺失/重复/大小写变体/全角冒号 → TopoError
- CLI route：显式 marker=superpowers 折叠显示（锁现行 display 行为）
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


def _write_config(root: Path, body: str):
    cfg_dir = root / "openspec"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "config.yaml").write_text(body, encoding="utf-8")


def _mkchange(root: Path, name: str = "demo") -> Path:
    d = root / "openspec" / "changes" / name
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# read_config_pipeline
# ---------------------------------------------------------------------------

def test_config_missing_file(tmp_path):
    assert ir.read_config_pipeline(tmp_path) == ("superpowers", "absent")


def test_config_missing_key(tmp_path):
    _write_config(tmp_path, "schema: spec-driven\nmetrics:\n  enabled: true\n")
    assert ir.read_config_pipeline(tmp_path) == ("superpowers", "absent")


def test_config_empty_value(tmp_path):
    _write_config(tmp_path, "impl-pipeline:\nmetrics:\n  enabled: true\n")
    assert ir.read_config_pipeline(tmp_path) == ("superpowers", "absent")


def test_config_value_tickets(tmp_path):
    _write_config(tmp_path, "impl-pipeline: tickets\n")
    assert ir.read_config_pipeline(tmp_path) == ("tickets", "ok")


def test_config_value_superpowers(tmp_path):
    _write_config(tmp_path, "impl-pipeline: superpowers\n")
    assert ir.read_config_pipeline(tmp_path) == ("superpowers", "ok")


def test_config_value_typo(tmp_path):
    _write_config(tmp_path, "impl-pipeline: tikets\n")
    pipeline, note = ir.read_config_pipeline(tmp_path)
    assert pipeline == "superpowers"
    assert note == "unknown-value:tikets"


def test_config_value_quoted_double(tmp_path):
    _write_config(tmp_path, 'impl-pipeline: "tickets"\n')
    assert ir.read_config_pipeline(tmp_path) == ("tickets", "ok")


def test_config_value_quoted_single(tmp_path):
    _write_config(tmp_path, "impl-pipeline: 'superpowers'\n")
    assert ir.read_config_pipeline(tmp_path) == ("superpowers", "ok")


def test_config_commented_line_ignored(tmp_path):
    # 模板注释态（config.template.yaml 先例）：`# impl-pipeline: tickets` 不应被当真键读到
    _write_config(tmp_path, "# impl-pipeline: tickets\nschema: spec-driven\n")
    assert ir.read_config_pipeline(tmp_path) == ("superpowers", "absent")


def test_config_indented_mention_not_matched(tmp_path):
    # 非顶层（缩进）出现的同名文本不应误判为键命中（如 context 块标量内提及）
    _write_config(tmp_path, "context: |\n  聊到 impl-pipeline: tickets 只是举例\n")
    assert ir.read_config_pipeline(tmp_path) == ("superpowers", "absent")


# ---------------------------------------------------------------------------
# [impl-review-fix] BOM 剥离
# ---------------------------------------------------------------------------

def test_config_bom_prefix_legal_value(tmp_path):
    # BOM + 合法 frontmatter/键值：剥 BOM 前会被误判「无键命中」，静默锁错管线
    _write_config(tmp_path, "﻿impl-pipeline: tickets\n")
    assert ir.read_config_pipeline(tmp_path) == ("tickets", "ok")


def test_marker_bom_prefix_tickets(tmp_path):
    p = tmp_path / "plan.md"
    p.write_text("﻿---\nimpl-pipeline: tickets\n---\n### Task 1: A\nBlocked-by: none\n",
                 encoding="utf-8")
    assert ir.read_plan_marker(p) == "tickets"


# ---------------------------------------------------------------------------
# [impl-review-fix] 键匹配容忍冒号前空格
# ---------------------------------------------------------------------------

def test_config_key_space_before_colon(tmp_path):
    _write_config(tmp_path, "impl-pipeline : tickets\n")
    assert ir.read_config_pipeline(tmp_path) == ("tickets", "ok")


def test_marker_key_space_before_colon(tmp_path):
    p = tmp_path / "plan.md"
    p.write_text("---\nimpl-pipeline : tickets\n---\n### Task 1: A\nBlocked-by: none\n",
                 encoding="utf-8")
    assert ir.read_plan_marker(p) == "tickets"


# ---------------------------------------------------------------------------
# [impl-review-fix] 损坏引号值 fail-closed（未闭合引号 / 闭合引号后跟垃圾字符）
# ---------------------------------------------------------------------------

def test_config_value_quoted_unclosed_damaged(tmp_path):
    _write_config(tmp_path, 'impl-pipeline: "tickets\n')
    pipeline, note = ir.read_config_pipeline(tmp_path)
    assert pipeline == "superpowers"
    assert note.startswith("unknown-value:")


def test_config_value_quoted_trailing_junk_damaged(tmp_path):
    _write_config(tmp_path, 'impl-pipeline: "tickets" junk\n')
    pipeline, note = ir.read_config_pipeline(tmp_path)
    assert pipeline == "superpowers"
    assert note.startswith("unknown-value:")


def test_marker_quoted_unclosed_stops(tmp_path):
    p = tmp_path / "plan.md"
    p.write_text('---\nimpl-pipeline: "tickets\n---\n### Task 1: A\nBlocked-by: none\n',
                 encoding="utf-8")
    with pytest.raises(ir.RouteStop):
        ir.read_plan_marker(p)


def test_marker_quoted_trailing_junk_stops(tmp_path):
    p = tmp_path / "plan.md"
    p.write_text('---\nimpl-pipeline: "tickets" junk\n---\n### Task 1: A\nBlocked-by: none\n',
                 encoding="utf-8")
    with pytest.raises(ir.RouteStop):
        ir.read_plan_marker(p)


# ---------------------------------------------------------------------------
# read_plan_marker
# ---------------------------------------------------------------------------

def test_marker_file_missing(tmp_path):
    assert ir.read_plan_marker(tmp_path / "superpowers-plan.md") is None


def test_marker_no_frontmatter(tmp_path):
    p = tmp_path / "plan.md"
    p.write_text("### Task 1: A\n- [ ] x\n", encoding="utf-8")
    assert ir.read_plan_marker(p) == "superpowers"


def test_marker_empty_file(tmp_path):
    p = tmp_path / "plan.md"
    p.write_text("", encoding="utf-8")
    assert ir.read_plan_marker(p) == "superpowers"


def test_marker_frontmatter_no_key(tmp_path):
    p = tmp_path / "plan.md"
    p.write_text("---\ntitle: x\n---\n### Task 1: A\n", encoding="utf-8")
    assert ir.read_plan_marker(p) == "superpowers"


def test_marker_valid_single_key_tickets(tmp_path):
    p = tmp_path / "plan.md"
    p.write_text("---\nimpl-pipeline: tickets\n---\n### Task 1: A\n", encoding="utf-8")
    assert ir.read_plan_marker(p) == "tickets"


def test_marker_valid_single_key_superpowers(tmp_path):
    p = tmp_path / "plan.md"
    p.write_text("---\nimpl-pipeline: superpowers\n---\n### Task 1: A\n", encoding="utf-8")
    assert ir.read_plan_marker(p) == "superpowers"


def test_marker_duplicate_key_stops(tmp_path):
    p = tmp_path / "plan.md"
    p.write_text(
        "---\nimpl-pipeline: tickets\nimpl-pipeline: superpowers\n---\n### Task 1: A\n",
        encoding="utf-8")
    with pytest.raises(ir.RouteStop):
        ir.read_plan_marker(p)


def test_marker_illegal_value_stops(tmp_path):
    p = tmp_path / "plan.md"
    p.write_text("---\nimpl-pipeline: bogus\n---\n### Task 1: A\n", encoding="utf-8")
    with pytest.raises(ir.RouteStop):
        ir.read_plan_marker(p)


def test_marker_unclosed_frontmatter_stops(tmp_path):
    p = tmp_path / "plan.md"
    p.write_text("---\nimpl-pipeline: tickets\n### Task 1: A\n", encoding="utf-8")
    with pytest.raises(ir.RouteStop):
        ir.read_plan_marker(p)


# ---------------------------------------------------------------------------
# CLI: route → PIPELINE_RECEIPT（路由合成规则 + receipt 行格式）
# ---------------------------------------------------------------------------

def _run_route(root, change):
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "route", "--root", str(root), "--change", change],
        capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def test_cli_route_absent_absent_defaults_superpowers(tmp_path):
    _mkchange(tmp_path)
    code, out, _ = _run_route(tmp_path, "demo")
    assert code == 0
    assert out == ("PIPELINE_RECEIPT change=demo config=absent marker=absent "
                    "pipeline=superpowers plan_sha=-")


def test_cli_route_config_tickets_plan_missing_first_jump(tmp_path):
    # marker 缺席（plan 文件不存在）→ 用 config 值（首跳）
    _mkchange(tmp_path)
    _write_config(tmp_path, "impl-pipeline: tickets\n")
    code, out, _ = _run_route(tmp_path, "demo")
    assert code == 0
    assert "config=tickets" in out
    assert "marker=absent" in out
    assert "pipeline=tickets" in out


def test_cli_route_marker_locks_over_config_change(tmp_path):
    # marker 存在（tickets）时 marker 优先——事后把 config 改回 superpowers 不影响在途 change
    d = _mkchange(tmp_path)
    (d / "superpowers-plan.md").write_text(
        "---\nimpl-pipeline: tickets\n---\n### Task 1: A\n", encoding="utf-8")
    _write_config(tmp_path, "impl-pipeline: superpowers\n")
    code, out, _ = _run_route(tmp_path, "demo")
    assert code == 0
    assert "marker=tickets" in out
    assert "pipeline=tickets" in out


def test_cli_route_marker_implicit_superpowers_locks_over_config(tmp_path):
    # marker 存在但无显式声明（旧管线产物，隐式 superpowers）——同样锁定，不因 config 现在
    # 说 tickets 就切换（防两管线混跑）
    d = _mkchange(tmp_path)
    (d / "superpowers-plan.md").write_text("### Task 1: A\n- [ ] x\n", encoding="utf-8")
    _write_config(tmp_path, "impl-pipeline: tickets\n")
    code, out, _ = _run_route(tmp_path, "demo")
    assert code == 0
    assert "marker=none" in out
    assert "pipeline=superpowers" in out


def test_cli_route_marker_explicit_superpowers_displays_none(tmp_path):
    # [impl-review-fix 补测 7] 现行折叠行为：显式 marker=superpowers 与隐式缺省（无
    # frontmatter/无键）在 receipt 里显示相同（marker=none）——read_plan_marker 两种情形返回
    # 同一个字符串 "superpowers"，receipt 无法区分（display 改进已 defer），本用例锁定现状。
    d = _mkchange(tmp_path)
    (d / "superpowers-plan.md").write_text(
        "---\nimpl-pipeline: superpowers\n---\n### Task 1: A\nBlocked-by: none\n",
        encoding="utf-8")
    code, out, _ = _run_route(tmp_path, "demo")
    assert code == 0
    assert "marker=none" in out
    assert "pipeline=superpowers" in out


def test_cli_route_stop_on_bad_marker(tmp_path):
    d = _mkchange(tmp_path)
    (d / "superpowers-plan.md").write_text(
        "---\nimpl-pipeline: tickets\nimpl-pipeline: superpowers\n---\n### Task 1: A\n",
        encoding="utf-8")
    code, out, err = _run_route(tmp_path, "demo")
    assert code == 6
    assert out == ""
    assert err  # stderr 原因非空


def test_cli_route_unknown_config_value_echoed(tmp_path):
    _mkchange(tmp_path)
    _write_config(tmp_path, "impl-pipeline: tikets\n")
    code, out, _ = _run_route(tmp_path, "demo")
    assert code == 0
    assert "config=tikets" in out
    assert "pipeline=superpowers" in out


def test_cli_route_plan_sha_dash_when_no_plan(tmp_path):
    _mkchange(tmp_path)
    code, out, _ = _run_route(tmp_path, "demo")
    assert code == 0
    assert "plan_sha=-" in out


def test_cli_route_plan_sha_present_when_committed(tmp_path):
    d = _mkchange(tmp_path)
    (d / "superpowers-plan.md").write_text(
        "---\nimpl-pipeline: tickets\n---\n### Task 1: A\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)],
                    check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "t"],
                    check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "t@t"],
                    check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"],
                    check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-q", "-m", "seed"],
                    check=True, capture_output=True, text=True)
    code, out, _ = _run_route(tmp_path, "demo")
    assert code == 0
    sha_field = [seg for seg in out.split() if seg.startswith("plan_sha=")][0]
    sha = sha_field.split("=", 1)[1]
    assert sha != "-"
    assert len(sha) == 7
    assert all(c in "0123456789abcdef" for c in sha)


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
    # golden fixture 三张票均有 canonical Blocked-by 行——三态契约收紧后 golden 仍须全绿。
    text = (SHIP_FIXTURES / "tickets_plan_golden.md").read_text(encoding="utf-8")
    deps = ir.parse_blocked_by(text)
    assert deps == {1: set(), 2: {1}, 3: {1, 2}}


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
        capture_output=True, text=True)
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
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def test_cli_task_text_default_out_path_under_impl_reports(tmp_path):
    change_dir = tmp_path / "openspec" / "changes" / "demo"
    change_dir.mkdir(parents=True)
    plan = change_dir / "superpowers-plan.md"
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
