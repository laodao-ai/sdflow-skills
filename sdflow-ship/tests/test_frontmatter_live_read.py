# [mlh-p5 Task6] live 读点 **只读 frontmatter**（inline 回退已退役）：frontmatter 有效→state；
# 坏→UNKNOWN(6) 不回退；absent（无 frontmatter / 无 ship-gate 键）→ 既有无锚语义（不回退 inline，
# 正文残留 inline 锚被完全忽略）。归档读半场仍 dual-read inline（永久，见 test_gate_anchor_scope）。
# 沿用 test_gate_*.py 的 fixture 构造法：写 openspec/changes/{c}/ 报告 + 跑 decide，断言退出码/verdict。
from conftest import commit_all, mkchange, head_sha, write_report
from test_gate_preflight import run_gate
from test_gate_tail import impl_done


def test_live_verify_frontmatter_pass(repo):
    # verify-report frontmatter verify: PASS → 走 frontmatter 读出 PASS → 正常推进（RUN_VERIFY 收尾）
    d = impl_done(repo)
    d.joinpath("code-review-report.md").write_text(
        f"---\nship-gate:\n  code_review: pass\n  reviewed_sha: {head_sha(repo)}\n---\n# 代码审报告\n", encoding="utf-8")
    d.joinpath("verify-report.md").write_text(
        f"---\nship-gate:\n  verify: PASS\n  reviewed_sha: {head_sha(repo)}\n---\n# 验证报告\n", encoding="utf-8")
    commit_all(repo, "cr+verify")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "RUN_VERIFY"


def test_live_verify_inline_retired_absent(repo):
    # [mlh-p5 Task6 D1] 退役 live inline 回退：verify-report **仅**旧 inline verify=FAIL 锚
    # （无 frontmatter）→ absent → live 只读 frontmatter → 正文 inline FAIL 被完全忽略 →
    # 不再回退读出 FAIL（Task2 曾判 VERIFY_FAIL），而是走无锚语义 STEP_IN_PROGRESS。
    # 这是 D1 退役的直接对照：同一 fixture 在 Task2 判 VERIFY_FAIL(5)，Task6 判 STEP_IN_PROGRESS(0)。
    d = impl_done(repo)
    d.joinpath("code-review-report.md").write_text(
        f"---\nship-gate:\n  code_review: pass\n  reviewed_sha: {head_sha(repo)}\n---\n# 代码审报告\n", encoding="utf-8")
    d.joinpath("verify-report.md").write_text(
        "<!-- ship-gate: verify=FAIL -->\n", encoding="utf-8")
    commit_all(repo, "cr+verify")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "STEP_IN_PROGRESS"   # inline FAIL 不再回退读出
    assert js["next"] == "sdflow-done"


def test_live_code_review_inline_retired_absent(repo):
    # [mlh-p5 Task6 D1] code-review 读点退役 inline：code-review-report **仅**旧 inline
    # code-review=pass 锚（无 frontmatter）→ absent → 不再回退读出 pass → STEP_IN_PROGRESS
    # （该步进行中），MUST NOT 因正文独占行 inline pass 锚假放行推进到 verify。
    d = impl_done(repo)
    d.joinpath("code-review-report.md").write_text(
        "<!-- ship-gate: code-review=pass -->\n", encoding="utf-8")
    commit_all(repo, "cr")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "STEP_IN_PROGRESS"
    assert js["next"] == "sdflow-code-review"


def test_live_verify_bad_no_fallback(repo):
    # frontmatter verify: MAYBE(越域) → UNKNOWN(6)（verify 早检拦下）。
    # [mlh-p5 Task6] 正文另塞独占行 inline verify=PASS 锚做诱饵：退役后无回退且早检已 fail-closed
    # UNKNOWN，断言证明坏 frontmatter 不被 inline 兜底、正文 inline 锚不被读。
    d = impl_done(repo)
    d.joinpath("code-review-report.md").write_text(
        f"---\nship-gate:\n  code_review: pass\n  reviewed_sha: {head_sha(repo)}\n---\n# 代码审报告\n", encoding="utf-8")
    d.joinpath("verify-report.md").write_text(
        "---\nship-gate:\n  verify: MAYBE\n---\n<!-- ship-gate: verify=PASS -->\n",
        encoding="utf-8")
    commit_all(repo, "cr+verify")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"
    # D12：reason 点名被拒字段名 + 失败类别
    assert "verify" in js["reason"] and "out-of-domain" in js["reason"]


def test_live_verify_body_mention_immune(repo):
    # [mlh-p5 Task6] frontmatter 无键（首行非 ---）+ 正文散文提及 ship-gate: verify: PASS →
    # absent → live 只读 frontmatter，正文提及不命中 → STEP_IN_PROGRESS（非误读 PASS 推进）。
    d = impl_done(repo)
    d.joinpath("code-review-report.md").write_text(
        f"---\nship-gate:\n  code_review: pass\n  reviewed_sha: {head_sha(repo)}\n---\n# 代码审报告\n", encoding="utf-8")
    d.joinpath("verify-report.md").write_text(
        "# 验证报告\n正文提及 ship-gate: verify: PASS 但这不是 frontmatter\n",
        encoding="utf-8")
    commit_all(repo, "cr+verify")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "STEP_IN_PROGRESS"
    assert js["next"] == "sdflow-done"


def test_live_body_mention_immune_design_approved(repo):
    # [mlh-p5 Task5/Task6 B4/B5 根治验证] spec-review-report 正文含旧 inline 锚字面
    # `<!-- ship-gate: design-approved -->` 但仅作【描述性提及】（反引号内、非独占裸行），
    # frontmatter 无 design_approved 键（absent）→ live 只读 frontmatter → REFUSE_START
    # （未过设计门），MUST NOT 因正文提及假过门。
    d = mkchange(repo)
    d.joinpath("spec-review-report.md").write_text(
        "# 设计审报告\n讨论：模板锚形如 `<!-- ship-gate: design-approved -->`（尚未拍板）。\n",
        encoding="utf-8")
    d.joinpath("proposal.md").write_text("# p\n〔TG-01：工具链〕\n", encoding="utf-8")
    commit_all(repo, "seed")
    code, js, _ = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"


def test_live_design_standalone_inline_retired_refuse(repo):
    # [mlh-p5 Task6 D1 最强正文免疫证明 — 退役后根治] spec-review-report **无 frontmatter**
    # （absent）+ 正文含**独占一行**（旧 live inline 读半场会命中）的 inline
    # `<!-- ship-gate: design-approved -->`。
    # Task2 时 absent → 回退旧 live inline 读半场 → 读出独占行真锚 → design_ok=True → 假过门放行；
    # Task6 退役后 absent → live 只读 frontmatter → 独占行 inline 锚被完全忽略 → REFUSE_START。
    # 这是 D1 退役对独占裸行 inline 锚（唯一能骗过旧 live inline 读半场的形态）的根治证据
    # （该读半场专属函数已随 T75 删除）。
    d = mkchange(repo)
    d.joinpath("spec-review-report.md").write_text(
        "# 设计审报告\n\n## 拍板\n<!-- ship-gate: design-approved -->\n", encoding="utf-8")
    d.joinpath("proposal.md").write_text("# p\n〔TG-01：工具链〕\n", encoding="utf-8")
    commit_all(repo, "seed")
    code, js, _ = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"


def test_live_design_frontmatter_present_no_key_inline_ignored(repo):
    # [mlh-p5 Task6 Q4 不漏假过] spec-review-report **有 frontmatter 首块**（含 ship-gate 键但
    # **非 design_approved**）+ 正文含独占一行 inline design-approved → design 门仍 REFUSE_START。
    # frontmatter 首块存在（sr_state 非 None）→ live 只读 frontmatter 状态，design_approved 缺 →
    # design_ok=False；正文独占行 inline 锚被完全忽略（Q4「frontmatter 存在则不回退 inline」）。
    d = mkchange(repo)
    d.joinpath("spec-review-report.md").write_text(
        "---\nship-gate:\n  verify: PASS\n---\n# 设计审报告\n\n"
        "## 拍板\n<!-- ship-gate: design-approved -->\n", encoding="utf-8")
    d.joinpath("proposal.md").write_text("# p\n〔TG-01：工具链〕\n", encoding="utf-8")
    commit_all(repo, "seed")
    code, js, _ = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"


def test_live_body_mention_immune_code_review(repo):
    # [mlh-p5 Task5/Task6 B4/B5 根治验证] code-review-report 正文含旧 inline 锚字面
    # `<!-- ship-gate: code-review=pass -->` 但仅作【描述性提及】（反引号内、非独占裸行），
    # frontmatter 无 code_review 键 → live 只读 frontmatter → STEP_IN_PROGRESS
    # （该步进行中，MUST NOT 因正文提及假放行）。
    d = impl_done(repo)
    d.joinpath("code-review-report.md").write_text(
        "# 代码审报告\n对账清单：结论锚字面为 `<!-- ship-gate: code-review=pass -->`（审查中，未落）。\n",
        encoding="utf-8")
    commit_all(repo, "cr")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "STEP_IN_PROGRESS" and js["next"] == "sdflow-code-review"


def test_live_design_approved_frontmatter(repo):
    # spec-review-report frontmatter design_approved: true（无 inline 锚）→ 过设计门 → plan 缺 RUN_PLAN
    d = mkchange(repo)
    d.joinpath("proposal.md").write_text("# p\n〔TG-01：工具链〕\n", encoding="utf-8")
    commit_all(repo, "seed")          # [harden-gate-git-layer Task1] 先有盘面才锚得住
    write_report(d, "spec-review-report.md", head_sha(repo),
                 body="# 设计审报告\n", design_approved="true")
    commit_all(repo, "spec-review report")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "RUN_PLAN"   # 过设计门（frontmatter）→ plan 缺


def test_live_toplevel_scalar_bad_unknown(repo):
    # [impl-review-fix FIX-2] 顶层 ship-gate 带内联标量值（ship-gate: true）→ bad-type →
    # live 侧 fail-closed UNKNOWN(6)（非 absent 假放行）。设计门读点即拦下。
    d = mkchange(repo)
    d.joinpath("spec-review-report.md").write_text(
        "---\nship-gate: true\n---\n# 设计审报告\n", encoding="utf-8")
    d.joinpath("proposal.md").write_text("# p\n〔TG-01：工具链〕\n", encoding="utf-8")
    commit_all(repo, "seed")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"
    assert "ship-gate" in js["reason"] and "bad-type" in js["reason"]


def test_live_dup_key_unknown(repo):
    # 重复 verify 键 → duplicate-key → UNKNOWN(6)（verify 早检拦下，不取最后一个）
    d = impl_done(repo)
    d.joinpath("code-review-report.md").write_text(
        f"---\nship-gate:\n  code_review: pass\n  reviewed_sha: {head_sha(repo)}\n---\n# 代码审报告\n", encoding="utf-8")
    d.joinpath("verify-report.md").write_text(
        "---\nship-gate:\n  verify: PASS\n  verify: FAIL\n---\n", encoding="utf-8")
    commit_all(repo, "cr+verify")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN"
    assert "verify" in js["reason"] and "duplicate-key" in js["reason"]


UNCLOSED = "---\nship-gate:\n  design_approved: true\n无闭合横线，正文继续\n"


def test_live_unclosed_design_refuse_with_hint(repo):
    # [T74 1.5/3.1b] 首行 --- 无闭合的 spec-review-report → design 读点 absent → REFUSE_START(3)，
    # 且 emit reason 含结构提示子串（提醒补闭合行）。
    d = mkchange(repo)
    d.joinpath("proposal.md").write_text("# p\n〔TG-01：工具链〕\n", encoding="utf-8")  # 非嵌入式避 RUN_SOP
    d.joinpath("spec-review-report.md").write_text(UNCLOSED, encoding="utf-8")
    commit_all(repo, "seed")
    code, js, _ = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"
    assert "未见闭合" in js["reason"]


def test_live_unclosed_code_review_step_in_progress_with_hint(repo):
    # [T74 3.1b] 同形态报告作 code-review-report → STEP_IN_PROGRESS(0)/next=sdflow-code-review，
    # 不 UNKNOWN(6)，reason 含结构提示。
    d = impl_done(repo)
    d.joinpath("code-review-report.md").write_text(UNCLOSED, encoding="utf-8")
    commit_all(repo, "cr-unclosed")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "STEP_IN_PROGRESS"
    assert js["next"] == "sdflow-code-review"
    assert "未见闭合" in js["reason"]


def test_live_unclosed_verify_step_in_progress_with_hint(repo):
    # [T74 3.1b] 同形态报告作 verify-report → STEP_IN_PROGRESS(0)/next=sdflow-done，
    # **不 UNKNOWN(6)**（坐实无闭合首块不再硬崩），reason 含结构提示。
    d = impl_done(repo)
    d.joinpath("code-review-report.md").write_text(
        f"---\nship-gate:\n  code_review: pass\n  reviewed_sha: {head_sha(repo)}\n---\n# 代码审报告\n", encoding="utf-8")
    d.joinpath("verify-report.md").write_text(UNCLOSED, encoding="utf-8")
    commit_all(repo, "verify-unclosed")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "STEP_IN_PROGRESS"
    assert js["next"] == "sdflow-done"
    assert "未见闭合" in js["reason"]
