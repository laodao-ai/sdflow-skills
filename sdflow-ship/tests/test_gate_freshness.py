from conftest import commit_all, mkchange
from test_gate_preflight import run_gate
from test_gate_impl_progress import approved_change, PLAN2
from test_gate_tail import impl_done

def tail_ok(repo):
    d = impl_done(repo)
    (d / "code-review-report.md").write_text(
        "<!-- ship-gate: code-review=pass -->\n", encoding="utf-8")
    (d / "verify-report.md").write_text(
        "<!-- ship-gate: verify=PASS -->\n", encoding="utf-8")
    commit_all(repo, "reports")
    return d

def touch_code(repo, name="src.py"):
    (repo / name).write_text("# code\n", encoding="utf-8")
    commit_all(repo, "code change")

def test_stale_pass_reruns_not_ship(repo):
    tail_ok(repo)
    touch_code(repo)             # 报告后有 openspec/ 外提交
    _, js, _ = run_gate(repo)
    assert js["verdict"] == "RERUN_STALE" and js["next"] == "sdflow-code-review"

def test_stale_fail_reruns_not_exit5(repo):
    d = impl_done(repo)
    (d / "code-review-report.md").write_text(
        "<!-- ship-gate: code-review=pass -->\n", encoding="utf-8")
    (d / "verify-report.md").write_text(
        "<!-- ship-gate: verify=FAIL -->\n", encoding="utf-8")
    commit_all(repo, "reports")
    touch_code(repo)             # FAIL 之后修了代码 → 重验不卡死
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "RERUN_STALE" and js["next"] == "sdflow-done"

def test_design_anchor_survives_impl_commits(repo):
    # Q1=B 断言①：实现提交不令 design-approved 失鲜
    approved_change(repo, plan=PLAN2)
    touch_code(repo)
    _, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL"   # 而非 REFUSE_START（链自锁反例）

def test_design_anchor_stale_on_design_edit(repo):
    # Q1=B 断言②：四件套被改 → design-approved 失鲜
    d = approved_change(repo, plan=PLAN2)
    (d / "design.md").write_text("# 拍板后又改了设计\n", encoding="utf-8")
    commit_all(repo, "edit design after approval")
    code, js, _ = run_gate(repo)
    assert code == 3 and "重审" in js["reason"]

def test_uncommitted_report_is_fresh(repo):
    # Q3=A：报告从未提交 → fresh + freshness=uncommitted
    d = tail_ok(repo)
    (d / "hand-off.md").write_text("x", encoding="utf-8")
    arch = repo / "openspec" / "changes" / "archive" / "2026-07-04-demo"
    arch.mkdir(parents=True); (arch / "p.md").write_text("a", encoding="utf-8")
    commit_all(repo, "tail")
    # 用未提交的新 verify 报告覆盖（工作区改动不提交）
    (d / "verify-report.md").write_text(
        "<!-- ship-gate: verify=PASS -->\n新一轮手写\n", encoding="utf-8")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "SHIPPED"

def test_openspec_only_commits_keep_fresh(repo):
    d = tail_ok(repo)
    (d / "hand-off.md").write_text("x", encoding="utf-8")
    commit_all(repo, "handoff only touches openspec")   # 正常尾流不误伤
    _, js, _ = run_gate(repo)
    assert js["verdict"] in ("RUN_VERIFY", "SHIPPED")   # 不得 RERUN_STALE

def test_cr_stale_verify_fresh_fail_carries_cr_note(repo):
    # F1 fix 轮：cr 陈旧 + verify 自身新鲜且 FAIL → VERIFY_FAIL 携带 cr 陈旧提示
    d = impl_done(repo)
    (d / "code-review-report.md").write_text(
        "<!-- ship-gate: code-review=pass -->\n", encoding="utf-8")
    commit_all(repo, "cr alone")
    touch_code(repo)             # 触及 src.py → cr 变陈旧
    (d / "verify-report.md").write_text(
        "<!-- ship-gate: verify=FAIL -->\n", encoding="utf-8")
    commit_all(repo, "verify alone")   # verify 本身新鲜（其后无提交）
    code, js, _ = run_gate(repo)
    assert code == 5 and js["verdict"] == "VERIFY_FAIL"
    assert js.get("cr_freshness") == "stale"
    assert "code-review 结论亦已陈旧" in js["reason"]
