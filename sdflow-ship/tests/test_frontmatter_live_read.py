# [mlh-p5 Task2] live 读点 dual-read（frontmatter 优先→absent 回退 inline，坏→UNKNOWN 不回退）。
# 沿用 test_gate_*.py 的 fixture 构造法：写 openspec/changes/{c}/ 报告 + 跑 decide，断言退出码/verdict。
from conftest import commit_all, mkchange
from test_gate_preflight import run_gate
from test_gate_tail import impl_done


def test_live_verify_frontmatter_pass(repo):
    # verify-report frontmatter verify: PASS → 走 frontmatter 读出 PASS → 正常推进（RUN_VERIFY 收尾）
    d = impl_done(repo)
    d.joinpath("code-review-report.md").write_text(
        "<!-- ship-gate: code-review=pass -->\n", encoding="utf-8")
    d.joinpath("verify-report.md").write_text(
        "---\nship-gate:\n  verify: PASS\n---\n# 验证报告\n", encoding="utf-8")
    commit_all(repo, "cr+verify")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "RUN_VERIFY"


def test_live_verify_absent_fallback_inline(repo):
    # 无 ship-gate frontmatter 键 + 旧 inline verify=FAIL 锚 → absent 回退 inline 读出（过渡期零破坏）
    d = impl_done(repo)
    d.joinpath("code-review-report.md").write_text(
        "<!-- ship-gate: code-review=pass -->\n", encoding="utf-8")
    d.joinpath("verify-report.md").write_text(
        "<!-- ship-gate: verify=FAIL -->\n", encoding="utf-8")
    commit_all(repo, "cr+verify")
    code, js, _ = run_gate(repo)
    assert code == 5 and js["verdict"] == "VERIFY_FAIL"   # 回退 inline 读出 FAIL


def test_live_verify_bad_no_fallback(repo):
    # frontmatter verify: MAYBE(越域) → UNKNOWN(6)，MUST NOT 回退 inline。
    # 正文另塞 inline verify=PASS 锚做诱饵：若错误回退会读出 PASS 推进，断言证明未回退。
    d = impl_done(repo)
    d.joinpath("code-review-report.md").write_text(
        "<!-- ship-gate: code-review=pass -->\n", encoding="utf-8")
    d.joinpath("verify-report.md").write_text(
        "---\nship-gate:\n  verify: MAYBE\n---\n<!-- ship-gate: verify=PASS -->\n",
        encoding="utf-8")
    commit_all(repo, "cr+verify")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"
    # D12：reason 点名被拒字段名 + 失败类别
    assert "verify" in js["reason"] and "out-of-domain" in js["reason"]


def test_live_body_mention_immune(repo):
    # frontmatter 无键（首行非 ---）+ 正文散文提及 ship-gate: verify: PASS → absent 回退 inline，
    # inline 也无真锚 → 不命中（STEP_IN_PROGRESS，非误读 PASS 推进）。
    d = impl_done(repo)
    d.joinpath("code-review-report.md").write_text(
        "<!-- ship-gate: code-review=pass -->\n", encoding="utf-8")
    d.joinpath("verify-report.md").write_text(
        "# 验证报告\n正文提及 ship-gate: verify: PASS 但这不是 frontmatter\n",
        encoding="utf-8")
    commit_all(repo, "cr+verify")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "STEP_IN_PROGRESS"


def test_live_design_approved_frontmatter(repo):
    # spec-review-report frontmatter design_approved: true（无 inline 锚）→ 过设计门 → plan 缺 RUN_PLAN
    d = mkchange(repo)
    d.joinpath("spec-review-report.md").write_text(
        "---\nship-gate:\n  design_approved: true\n---\n# 设计审报告\n", encoding="utf-8")
    d.joinpath("proposal.md").write_text("# p\n〔TG-01：工具链〕\n", encoding="utf-8")
    commit_all(repo, "seed")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "RUN_PLAN"   # 过设计门（frontmatter）→ plan 缺


def test_live_dup_key_unknown(repo):
    # 重复 verify 键 → duplicate-key → UNKNOWN(6)（早检拦下，不取最后一个）
    d = impl_done(repo)
    d.joinpath("code-review-report.md").write_text(
        "<!-- ship-gate: code-review=pass -->\n", encoding="utf-8")
    d.joinpath("verify-report.md").write_text(
        "---\nship-gate:\n  verify: PASS\n  verify: FAIL\n---\n", encoding="utf-8")
    commit_all(repo, "cr+verify")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"
    assert "verify" in js["reason"] and "duplicate-key" in js["reason"]
