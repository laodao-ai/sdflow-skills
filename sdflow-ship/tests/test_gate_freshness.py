from conftest import commit_all, mkchange
from test_gate_preflight import run_gate
from test_gate_impl_progress import approved_change, PLAN2
from test_gate_tail import impl_done

def tail_ok(repo):
    # [mlh-p5 Task5] live 迁 frontmatter（原 inline 双锚，产出的 gate verdict 不变）
    d = impl_done(repo)
    (d / "code-review-report.md").write_text(
        "---\nship-gate:\n  code_review: pass\n---\n# 代码审报告\n", encoding="utf-8")
    (d / "verify-report.md").write_text(
        "---\nship-gate:\n  verify: PASS\n---\n# 验证报告\n", encoding="utf-8")
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
    assert js["freshness"] == "stale"  # [impl-review-fix] 裁决项7：freshness 键锚定

def test_stale_fail_reruns_not_exit5(repo):
    d = impl_done(repo)
    # [mlh-p5 Task5] live 迁 frontmatter
    (d / "code-review-report.md").write_text(
        "---\nship-gate:\n  code_review: pass\n---\n# 代码审报告\n", encoding="utf-8")
    (d / "verify-report.md").write_text(
        "---\nship-gate:\n  verify: FAIL\n---\n# 验证报告\n", encoding="utf-8")
    commit_all(repo, "reports")
    touch_code(repo)             # FAIL 之后修了代码 → 重验不卡死
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "RERUN_STALE" and js["next"] == "sdflow-done"

def test_stale_unclosed_verify_appends_hint(repo):
    # [impl-review-fix OV-2] verify 读点 stale 分支（next=sdflow-done）在 verify-report 首行 ---
    # 无闭合(absent) 时追加纯结构提示：避免把无有效结论的报告误称「结论陈旧」且吞掉未闭合诊断。
    # 该分支仅在「code-review 新鲜 ∧ verify 陈旧」窄边界可达——否则 code-review stale 分支
    # (next=sdflow-code-review) 先触发。故 fixture 须把 code-review-report 提交在外部改动之后
    # （cr 新鲜），verify-report 提交在其前（verify 因后续外部提交而陈旧）。verdict/退出码/next 不变。
    d = impl_done(repo)
    (d / "verify-report.md").write_text(
        "---\nship-gate:\n  verify: PASS\n无闭合横线，正文继续\n", encoding="utf-8")   # 首块无闭合 → absent
    commit_all(repo, "verify report (unclosed)")
    touch_code(repo)             # 外部提交 → 使 verify-report 陈旧
    (d / "code-review-report.md").write_text(
        "---\nship-gate:\n  code_review: pass\n---\n# 代码审报告\n", encoding="utf-8")
    commit_all(repo, "code-review report after external change → cr 新鲜")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "RERUN_STALE" and js["next"] == "sdflow-done"
    assert "未见闭合" in js["reason"]   # 结构提示未被 stale 分支吞掉

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
    # [impl-review-fix] 裁决项7：原用 tail_ok() 先提交过 verify-report.md 再工作区覆盖，
    # git log 仍能找到该路径的历史 sha，实测得到 freshness="fresh" 而非 "uncommitted"
    # （report_last_sha 只看提交历史，不看工作区）——与本用例名/注释意图（报告从未
    # 提交过）不符。改为让 verify-report.md 全程不进任何 commit，才是真正的
    # "never committed" 路径（sha 为空 → freshness=uncommitted）。
    d = impl_done(repo)
    # [mlh-p5 Task5] live 迁 frontmatter（未提交语义靠"从未进 commit"承载，与锚承载格式无关）
    (d / "code-review-report.md").write_text(
        "---\nship-gate:\n  code_review: pass\n---\n# 代码审报告\n", encoding="utf-8")
    (d / "hand-off.md").write_text("x", encoding="utf-8")
    arch = repo / "openspec" / "changes" / "archive" / "2026-07-04-demo"
    arch.mkdir(parents=True); (arch / "p.md").write_text("a", encoding="utf-8")
    commit_all(repo, "tail without verify report")
    # verify-report.md 只写盘，从未进入任何提交
    (d / "verify-report.md").write_text(
        "---\nship-gate:\n  verify: PASS\n---\n新一轮手写\n", encoding="utf-8")
    code, js, _ = run_gate(repo)
    # 〔H1〕active 存在 → RUN_VERIFY（非 SHIPPED）；本用例主张仍是 freshness=uncommitted
    # （report_last_sha 空 → 人机同权），验其经 final RUN_VERIFY 携带 freshness 无误
    assert code == 0 and js["verdict"] == "RUN_VERIFY"
    assert js["freshness"] == "uncommitted"

def test_openspec_only_commits_keep_fresh(repo):
    d = tail_ok(repo)
    (d / "hand-off.md").write_text("x", encoding="utf-8")
    commit_all(repo, "handoff only touches openspec")   # 正常尾流不误伤
    _, js, _ = run_gate(repo)
    assert js["verdict"] in ("RUN_VERIFY", "SHIPPED")   # 不得 RERUN_STALE

def test_impl_review_exempt_bare_and_colon(repo):
    # 〔B2〕checkpoint(impl-review) 裸 + 带冒号描述，触及 design.md/tasks.md → 豁免不失鲜
    d = approved_change(repo, plan=PLAN2)
    (d / "design.md").write_text("v1\n", encoding="utf-8")
    commit_all(repo, "checkpoint(impl-review)")               # 裸
    (d / "tasks.md").write_text("t\n", encoding="utf-8")
    commit_all(repo, "checkpoint(impl-review): 勾选回填")      # 冒号
    _, js, _ = run_gate(repo)
    assert js["verdict"] != "REFUSE_START"   # 豁免,续跑(CONTINUE_IMPL)

def test_impl_review_evil_suffix_stale(repo):
    # 〔BR-7〕checkpoint(impl-review)evil 右括号后尾串垃圾 → 精确式不豁免 → 失鲜
    d = approved_change(repo, plan=PLAN2)
    (d / "design.md").write_text("v1\n", encoding="utf-8")
    commit_all(repo, "checkpoint(impl-review)evil")
    code, js, _ = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"

def test_impl_review_fix_variant_stale(repo):
    # 〔grill/BR-7〕checkpoint(impl-review-fix) 变体 → 不豁免 → 失鲜
    d = approved_change(repo, plan=PLAN2)
    (d / "design.md").write_text("v1\n", encoding="utf-8")
    commit_all(repo, "checkpoint(impl-review-fix): 改设计")
    code, js, _ = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"

def test_empty_subject_touch_design_stale(repo):
    # 〔BR-6 分帧边界〕空 subject 帧触及 design.md → 不豁免 → 失鲜
    import subprocess
    d = approved_change(repo, plan=PLAN2)
    (d / "design.md").write_text("v1\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "--allow-empty-message", "-m", ""],
                   check=True, capture_output=True)
    code, js, _ = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"

def test_interleaved_impl_review_and_normal_stale(repo):
    # 〔BR-6 分帧正确性〕同窗口 impl-review(改 tasks.md) + 普通 subject(改 design.md) 交错
    # → 分帧须把 design.md 正确归到普通帧 → 失鲜（分帧 bug 的杀伤方向=假豁免，专测）
    d = approved_change(repo, plan=PLAN2)
    (d / "tasks.md").write_text("t\n", encoding="utf-8")
    commit_all(repo, "checkpoint(impl-review): 勾选回填 tasks")   # 豁免帧
    (d / "design.md").write_text("语义改\n", encoding="utf-8")
    commit_all(repo, "docs: 手动改设计")                          # 普通帧 → design.md 失鲜
    code, js, _ = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"

def test_chinese_named_spec_edit_still_stale(repo):
    # 〔Adv-A / impl-review-fix〕core.quotePath: 拍板后改中文名 spec 路径 → 必须仍判失鲜
    # （git 默认 C-quote 非 ASCII 路径会让裸 startswith 失配 → 静默放行=假✅）
    d = approved_change(repo, plan=PLAN2)
    specs = d / "specs"
    specs.mkdir(exist_ok=True)
    (specs / "功能规格.md").write_text("拍板后偷改设计语义\n", encoding="utf-8")
    commit_all(repo, "docs: 改中文名 spec")
    code, js, _ = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"   # 不因中文名放行

def test_cr_stale_verify_fresh_fail_carries_cr_note(repo):
    # F1 fix 轮：cr 陈旧 + verify 自身新鲜且 FAIL → VERIFY_FAIL 携带 cr 陈旧提示
    d = impl_done(repo)
    # [mlh-p5 Task5] live 迁 frontmatter
    (d / "code-review-report.md").write_text(
        "---\nship-gate:\n  code_review: pass\n---\n# 代码审报告\n", encoding="utf-8")
    commit_all(repo, "cr alone")
    touch_code(repo)             # 触及 src.py → cr 变陈旧
    (d / "verify-report.md").write_text(
        "---\nship-gate:\n  verify: FAIL\n---\n# 验证报告\n", encoding="utf-8")
    commit_all(repo, "verify alone")   # verify 本身新鲜（其后无提交）
    code, js, _ = run_gate(repo)
    assert code == 5 and js["verdict"] == "VERIFY_FAIL"
    assert js.get("cr_freshness") == "stale"
    assert "code-review 结论亦已陈旧" in js["reason"]
