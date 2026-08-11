from conftest import commit_all, mkchange, head_sha, write_report
from test_gate_preflight import run_gate
from test_gate_impl_progress import approved_change, PLAN2_TICKETS

def impl_done(repo):
    # [remove-superpowers-pipeline Task2] 单名 tickets.md 下第四道校验无条件生效——
    # 需带合法收尾 ticket 的 plan 才能推进到 RUN_CODE_REVIEW，故用 PLAN2_TICKETS
    # 取代裸 PLAN2（本 helper 被 test_gate_freshness.py 等多个文件重用）。
    d = approved_change(repo, plan=PLAN2_TICKETS)
    commit_all(repo, "checkpoint(task1-a): A")
    commit_all(repo, "checkpoint(task2-b): B")
    return d

def test_cr_missing_run_code_review(repo):
    impl_done(repo)
    _, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_CODE_REVIEW"

def test_cr_blocked_exit4(repo):
    d = impl_done(repo)
    # [mlh-p5 Task5] live 迁 frontmatter
    (d / "code-review-report.md").write_text(
        f"---\nship-gate:\n  code_review: blocked\n  reviewed_sha: {head_sha(repo)}\n---\n# 代码审报告\n", encoding="utf-8")
    commit_all(repo, "cr")
    code, js, _ = run_gate(repo)
    assert code == 4 and js["verdict"] == "BLOCKED_UPSTREAM"

def test_verify_fail_exit5(repo):
    d = impl_done(repo)
    # [mlh-p5 Task5] live 迁 frontmatter
    (d / "code-review-report.md").write_text(
        f"---\nship-gate:\n  code_review: pass\n  reviewed_sha: {head_sha(repo)}\n---\n# 代码审报告\n", encoding="utf-8")
    (d / "verify-report.md").write_text(
        f"---\nship-gate:\n  verify: FAIL\n  reviewed_sha: {head_sha(repo)}\n---\n# 验证报告\n", encoding="utf-8")
    commit_all(repo, "cr+verify")
    code, js, _ = run_gate(repo)
    assert code == 5 and js["verdict"] == "VERIFY_FAIL"

def test_verify_pass_active_present_run_verify(repo):
    # 〔H1/HRTG-1〕active 目录仍在 = archive 尚未发生 → 恒 RUN_VERIFY，绝不 SHIPPED
    # （即便有旧同名 archive dir）。真 SHIPPED（归档后 active 缺席）见 test_gate_terminal.py。
    d = impl_done(repo)
    # [mlh-p5 Task5] live 迁 frontmatter
    (d / "code-review-report.md").write_text(
        f"---\nship-gate:\n  code_review: pass\n  reviewed_sha: {head_sha(repo)}\n---\n# 代码审报告\n", encoding="utf-8")
    (d / "verify-report.md").write_text(
        f"---\nship-gate:\n  verify: PASS\n  reviewed_sha: {head_sha(repo)}\n---\n# 验证报告\n", encoding="utf-8")
    (d / "hand-off.md").write_text("交接\n", encoding="utf-8")
    arch = repo / "openspec" / "changes" / "archive" / "2026-07-04-demo"
    arch.mkdir(parents=True)
    (arch / "proposal.md").write_text("归档\n", encoding="utf-8")
    commit_all(repo, "tail")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "RUN_VERIFY"   # active 存在 → 不 SHIPPED（H1）

def test_cr_report_no_anchor_in_progress(repo):
    d = impl_done(repo)
    (d / "code-review-report.md").write_text(
        "# 报告\n审查中…\n", encoding="utf-8")
    commit_all(repo, "cr-in-progress")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "STEP_IN_PROGRESS" and js["next"] == "sdflow-code-review"

def test_verify_report_no_anchor_in_progress(repo):
    d = impl_done(repo)
    # [mlh-p5 Task5] live 迁 frontmatter（verify-report.md 保持无锚正文不变——本用例本就测「无锚」）
    (d / "code-review-report.md").write_text(
        f"---\nship-gate:\n  code_review: pass\n  reviewed_sha: {head_sha(repo)}\n---\n# 代码审报告\n", encoding="utf-8")
    (d / "verify-report.md").write_text(
        "# 报告\n验证中…\n", encoding="utf-8")
    commit_all(repo, "verify-in-progress")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "STEP_IN_PROGRESS" and js["next"] == "sdflow-done"

def test_verify_pass_but_no_handoff_run_verify_step(repo):
    d = impl_done(repo)
    # [mlh-p5 Task5] live 迁 frontmatter
    (d / "code-review-report.md").write_text(
        f"---\nship-gate:\n  code_review: pass\n  reviewed_sha: {head_sha(repo)}\n---\n# 代码审报告\n", encoding="utf-8")
    (d / "verify-report.md").write_text(
        f"---\nship-gate:\n  verify: PASS\n  reviewed_sha: {head_sha(repo)}\n---\n# 验证报告\n", encoding="utf-8")
    commit_all(repo, "tail")
    _, js, _ = run_gate(repo)
    assert js["verdict"] == "RUN_VERIFY"  # done 未走完（hand-off/archive 缺）
