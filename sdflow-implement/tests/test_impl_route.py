"""pytest for sdflow-implement/scripts/impl_route.py

覆盖 plan Task 2 Step 1 的完整矩阵（TDD 先写，后实现）：
- read_config_pipeline：缺失/空值/tickets/superpowers/拼错值/带引号值
- read_plan_marker：缺文件/无 frontmatter/合法单键/键重复→停/非法值→停/未闭合 frontmatter→停
- CLI route：PIPELINE_RECEIPT 行格式（含在途锁定 vs 首跳 config 的路由合成规则）
- parse_blocked_by/next_ready：线性链/菱形/环→错/自环→错/缺依赖号→错/done 集过滤
- CLI frontier：next-ready 号列 + TopoError 退出码
"""
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "impl_route.py"
sys.path.insert(0, str(SCRIPT.parent))
import impl_route as ir  # noqa: E402


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
