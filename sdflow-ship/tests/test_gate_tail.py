import subprocess
from conftest import commit_all, mkchange
from test_gate_preflight import run_gate
from test_gate_impl_progress import approved_change, PLAN2

def impl_done(repo):
    d = approved_change(repo, plan=PLAN2)
    commit_all(repo, "checkpoint(task1-a): A")
    commit_all(repo, "checkpoint(task2-b): B")
    return d

def test_cr_missing_run_code_review(repo):
    impl_done(repo)
    _, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_CODE_REVIEW"

def test_cr_blocked_exit4(repo):
    d = impl_done(repo)
    (d / "code-review-report.md").write_text(
        "<!-- ship-gate: code-review=blocked -->\n", encoding="utf-8")
    commit_all(repo, "cr")
    code, js, _ = run_gate(repo)
    assert code == 4 and js["verdict"] == "BLOCKED_UPSTREAM"

def test_verify_fail_exit5(repo):
    d = impl_done(repo)
    (d / "code-review-report.md").write_text(
        "<!-- ship-gate: code-review=pass -->\n", encoding="utf-8")
    (d / "verify-report.md").write_text(
        "<!-- ship-gate: verify=FAIL -->\n", encoding="utf-8")
    commit_all(repo, "cr+verify")
    code, js, _ = run_gate(repo)
    assert code == 5 and js["verdict"] == "VERIFY_FAIL"

def test_full_pass_to_shipped(repo):
    d = impl_done(repo)
    (d / "code-review-report.md").write_text(
        "<!-- ship-gate: code-review=pass -->\n", encoding="utf-8")
    (d / "verify-report.md").write_text(
        "<!-- ship-gate: verify=PASS -->\n", encoding="utf-8")
    (d / "hand-off.md").write_text("交接\n", encoding="utf-8")
    arch = repo / "openspec" / "changes" / "archive" / "2026-07-04-demo"
    arch.mkdir(parents=True)
    (arch / "proposal.md").write_text("归档\n", encoding="utf-8")
    commit_all(repo, "tail")
    code, js, _ = run_gate(repo)   # 沙箱在 main 无 feature 分支 → 视为已并
    assert code == 0 and js["verdict"] == "SHIPPED"

def test_verify_pass_but_no_handoff_run_verify_step(repo):
    d = impl_done(repo)
    (d / "code-review-report.md").write_text(
        "<!-- ship-gate: code-review=pass -->\n", encoding="utf-8")
    (d / "verify-report.md").write_text(
        "<!-- ship-gate: verify=PASS -->\n", encoding="utf-8")
    commit_all(repo, "tail")
    _, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_VERIFY"  # done 未走完（hand-off/archive 缺）
