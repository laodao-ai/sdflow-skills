import base64
import hashlib
import os
import re
import subprocess, sys
from pathlib import Path

import pytest

from conftest import commit_all, mkchange, head_sha, write_report, fingerprint
from test_gate_preflight import run_gate
from test_gate_impl_progress import approved_change, PLAN2, PLAN2_TICKETS, _sg
from test_gate_tail import impl_done

BASE = "openspec/changes/demo/"
TASKS_REL = BASE + "tasks.md"


def _cr_verify_frontmatter(repo, ref, **fields):
    """`code-review-report.md` / `verify-report.md` 两个 code 域消费方共用的锚构造：
    在 `ref` 上算 code 域指纹，构造 frontmatter 文本（结论字段 + 锚）。"""
    sha, manifest = fingerprint(repo, ref, "code")
    lines = ["---", "ship-gate:"]
    for k, v in fields.items():
        lines.append(f"  {k}: {v}")
    lines.append(f"  reviewed_sha: {sha}")
    lines.append(f'  reviewed_manifest: "{manifest}"')
    lines.append("---")
    return "\n".join(lines) + "\n"


def tail_ok(repo):
    # [mlh-p5 Task5] live 迁 frontmatter（原 inline 双锚，产出的 gate verdict 不变）
    d = impl_done(repo)
    (d / "code-review-report.md").write_text(
        _cr_verify_frontmatter(repo, head_sha(repo), code_review="pass") + "# 代码审报告\n",
        encoding="utf-8")
    (d / "verify-report.md").write_text(
        _cr_verify_frontmatter(repo, head_sha(repo), verify="PASS") + "# 验证报告\n",
        encoding="utf-8")
    commit_all(repo, "reports")
    return d

def touch_code(repo, name="src.py"):
    (repo / name).write_text("# code\n", encoding="utf-8")
    commit_all(repo, "code change")

def test_stale_pass_reruns_not_ship(repo):
    d = tail_ok(repo)
    # code-review-report.md 落盘的 reviewed_sha 锚是「报告写盘时的 HEAD」（tail_ok 内部先写文件
    # 再提交），非「tail_ok 返回后的当前 HEAD」（那已是 "reports" 提交本身）——故不用 head_sha(repo)，
    # 直接从已提交文件内容里读回真正写进去的锚值，避免用错时序的假通过。
    anchor_sha = re.search(r"reviewed_sha: (\S+)",
                           (d / "code-review-report.md").read_text(encoding="utf-8")).group(1)
    touch_code(repo)             # 报告后有 openspec/ 外提交
    _, js, _ = run_gate(repo)
    assert js["verdict"] == "RERUN_STALE" and js["next"] == "sdflow-code-review"
    assert js["freshness"] == "stale"  # [impl-review-fix] 裁决项7：freshness 键锚定
    # [impl-review-fix F2] ADR-4：三处 stale 的 emit 都须带 reviewed_sha；此前 code 域漏带。
    assert js["reviewed_sha"] == anchor_sha, \
        "code 域 RERUN_STALE 须带该报告自己的 reviewed_sha 锚（ADR-4），不是当前 HEAD"

def test_stale_fail_reruns_not_exit5(repo):
    d = impl_done(repo)
    anchor_sha, anchor_manifest = fingerprint(repo, head_sha(repo), "code")
    # [mlh-p5 Task5] live 迁 frontmatter
    (d / "code-review-report.md").write_text(
        f"---\nship-gate:\n  code_review: pass\n  reviewed_sha: {anchor_sha}\n"
        f'  reviewed_manifest: "{anchor_manifest}"\n---\n# 代码审报告\n', encoding="utf-8")
    (d / "verify-report.md").write_text(
        f"---\nship-gate:\n  verify: FAIL\n  reviewed_sha: {anchor_sha}\n"
        f'  reviewed_manifest: "{anchor_manifest}"\n---\n# 验证报告\n', encoding="utf-8")
    commit_all(repo, "reports")
    touch_code(repo)             # FAIL 之后修了代码 → 重验不卡死
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "RERUN_STALE" and js["next"] == "sdflow-done"
    # [impl-review-fix F2] ADR-4：verify 域 RERUN_STALE 同须带 reviewed_sha。
    assert js["reviewed_sha"] == anchor_sha, \
        "verify 域 RERUN_STALE 须带该报告自己的 reviewed_sha 锚（ADR-4），不是当前 HEAD"

def test_unclosed_verify_frontmatter_keeps_structural_hint(repo):
    # [impl-review-fix OV-2 → harden-gate-git-layer Task1 重新设计] 原用例名
    # test_stale_unclosed_verify_appends_hint，断言 verdict=RERUN_STALE 且 reason 含结构提示。
    # **承载的安全承诺不变**：verify-report 首行 --- 无闭合（parse 判 absent、无有效结论）时，
    # 「未见闭合」这条结构诊断 MUST NOT 被其它分支吞掉。
    d = impl_done(repo)
    (d / "verify-report.md").write_text(
        "---\nship-gate:\n  verify: PASS\n无闭合横线，正文继续\n", encoding="utf-8")   # 首块无闭合 → absent
    commit_all(repo, "verify report (unclosed)")
    touch_code(repo)             # 外部提交 → 使 verify-report 陈旧
    (d / "code-review-report.md").write_text(
        _cr_verify_frontmatter(repo, head_sha(repo), code_review="pass") + "# 代码审报告\n",
        encoding="utf-8")
    commit_all(repo, "code-review report after external change → cr 新鲜")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "STEP_IN_PROGRESS" and js["next"] == "sdflow-done"
    assert "未见闭合" in js["reason"]   # 结构提示未被任何先行分支吞掉（本用例的承重点）
    assert "陈旧" not in js["reason"]   # 无有效结论的报告不该被称「结论陈旧」（OV-2 本意）

def test_design_anchor_survives_impl_commits(repo):
    # Q1=B 断言①：实现提交不令 design-approved 失鲜
    approved_change(repo, plan=PLAN2_TICKETS)
    touch_code(repo)
    _, js, _ = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL"   # 而非 REFUSE_START（链自锁反例）

def test_design_anchor_stale_on_design_edit(repo):
    # Q1=B 断言②：四件套被改 → design-approved 失鲜
    d = approved_change(repo, plan=PLAN2_TICKETS)
    (d / "design.md").write_text("# 拍板后又改了设计\n", encoding="utf-8")
    commit_all(repo, "edit design after approval")
    code, js, _ = run_gate(repo)
    assert code == 3 and "重审" in js["reason"]

def test_uncommitted_report_still_evaluated_by_its_own_anchor(repo):
    # [harden-gate-git-layer Task1 · ADR-1] 原用例名 test_uncommitted_report_is_fresh，
    # 断言 freshness == "uncommitted"。该语义随**反推锚**一并退役：旧实现只能从
    # `git log -1 -- <report>` 反推锚，报告没进过提交 ⇒ 推不出锚 ⇒ 只好特判 uncommitted。
    # 新实现的锚是报告自己录下的内容指纹，**与报告有没有进过提交无关**——未提交的
    # 报告照样带得出有效锚，照常参与失鲜求值（Q3=A「人机同权、手写产物合法」由此保住：
    # 手写报告不被拒，只是同样要落锚）。故本用例改为验「未提交的报告仍经其自录锚正常求值」。
    d = impl_done(repo)
    # [mlh-p5 Task5] live 迁 frontmatter（未提交语义靠"从未进 commit"承载，与锚承载格式无关）
    (d / "code-review-report.md").write_text(
        _cr_verify_frontmatter(repo, head_sha(repo), code_review="pass") + "# 代码审报告\n",
        encoding="utf-8")
    (d / "hand-off.md").write_text("x", encoding="utf-8")
    arch = repo / "openspec" / "changes" / "archive" / "2026-07-04-demo"
    arch.mkdir(parents=True); (arch / "p.md").write_text("a", encoding="utf-8")
    commit_all(repo, "tail without verify report")
    # verify-report.md 只写盘，从未进入任何提交
    (d / "verify-report.md").write_text(
        _cr_verify_frontmatter(repo, head_sha(repo), verify="PASS") + "新一轮手写\n",
        encoding="utf-8")
    code, js, _ = run_gate(repo)
    # 〔H1〕active 存在 → RUN_VERIFY（非 SHIPPED）。未提交的 verify-report 携带指向当前
    # HEAD 的有效锚 ⇒ 正常求值、判 fresh（而非旧的特判 "uncommitted"），且**不**因
    # 「没进过提交」被判缺锚 UNKNOWN——人机同权保住。
    assert code == 0 and js["verdict"] == "RUN_VERIFY"
    assert js["freshness"] == "fresh"

def test_openspec_only_commits_keep_fresh(repo):
    d = tail_ok(repo)
    (d / "hand-off.md").write_text("x", encoding="utf-8")
    commit_all(repo, "handoff only touches openspec")   # 正常尾流不误伤
    _, js, _ = run_gate(repo)
    assert js["verdict"] in ("RUN_VERIFY", "SHIPPED")   # 不得 RERUN_STALE

def test_cr_stale_verify_fresh_fail_carries_cr_note(repo):
    # F1 fix 轮：cr 陈旧 + verify 自身新鲜且 FAIL → VERIFY_FAIL 携带 cr 陈旧提示
    d = impl_done(repo)
    # [mlh-p5 Task5] live 迁 frontmatter
    (d / "code-review-report.md").write_text(
        _cr_verify_frontmatter(repo, head_sha(repo), code_review="pass") + "# 代码审报告\n",
        encoding="utf-8")
    commit_all(repo, "cr alone")
    touch_code(repo)             # 触及 src.py → cr 变陈旧
    (d / "verify-report.md").write_text(
        _cr_verify_frontmatter(repo, head_sha(repo), verify="FAIL") + "# 验证报告\n",
        encoding="utf-8")
    commit_all(repo, "verify alone")   # verify 本身新鲜（其后无提交）
    code, js, _ = run_gate(repo)
    assert code == 5 and js["verdict"] == "VERIFY_FAIL"
    assert js.get("cr_freshness") == "stale"
    assert "code-review 结论亦已陈旧" in js["reason"]

def _git(root, *args, check=True):
    return subprocess.run(["git", "-C", str(root), *args],
                          check=check, capture_output=True, text=True, encoding="utf-8", errors="replace")

def _head(repo):
    return _git(repo, "rev-parse", "HEAD").stdout.strip()

def _reanchor(repo, d):
    """把 design-approved 锚推到 HEAD（重提交 spec-review-report.md）。"""
    sha, manifest = fingerprint(repo, head_sha(repo), "design")
    (d / "spec-review-report.md").write_text(
        f"---\nship-gate:\n  design_approved: true\n  reviewed_sha: {sha}\n"
        f'  reviewed_manifest: "{manifest}"\n---\n# 设计审报告 v2\n', encoding="utf-8")
    commit_all(repo, "re-approve design")


# ══════════════════════════════════════════════════════════════════════════
# 〔sweep-pool-debt D2〕tasks.md 移出监视集：不再有任何内容豁免层——
# 无论纯勾选翻转还是任意措辞改动，tasks.md 的变化一律不影响 design 域新鲜度。
# ══════════════════════════════════════════════════════════════════════════

def test_tasks_md_any_change_never_affects_design_freshness(repo):
    """〔D2 目标态〕tasks.md **不在**监视集内——无论勾选框翻转、措辞改动、新建、删除、
    重命名，design 域新鲜度均不受影响（这与旧实现"仅勾选框翻转豁免"的窄口径不同：
    D2 之后 tasks.md 整个不在监视集，故连"措辞改动"这类旧口径下会照判失鲜的差异
    现在也是 fresh）。"""
    d = approved_change(repo, plan=PLAN2_TICKETS)
    (d / "tasks.md").write_text("### Task 1: A 改了措辞\n- [x] s\n", encoding="utf-8")
    commit_all(repo, "docs: 随意改 tasks.md")
    stale, freshness = _sg.is_stale(repo, BASE + "spec-review-report.md", "design", "demo")
    assert (stale, freshness) == (False, "fresh")
    code, js, _h = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL"


def test_impl_source_edits_and_plan_checkbox_flip_keep_design_fresh(repo):
    """🔴 本 change 的**头号自噬风险**钉：判定收紧后若把监视集画大（如整个 change 目录、
    或整棵树），实现期的正常动作会立刻把设计门自锁死。

    实现期两个正常动作各来一次：① 改源码 ② 勾 `tickets.md` 的复选框
    （它是**实现计划**，不在 design 监视集内——监视集只有 proposal/design 与 specs/）。
    """
    d = approved_change(repo, plan=PLAN2_TICKETS)
    (repo / "src.py").write_text("# impl\n", encoding="utf-8")
    (d / "tickets.md").write_text(
        PLAN2_TICKETS.replace("- [ ] s\n### Task 2", "- [x] s\n### Task 2", 1), encoding="utf-8")
    commit_all(repo, "checkpoint(task1-a): 实现 + 勾计划")
    assert _sg.is_stale(repo, BASE + "spec-review-report.md", "design", "demo") == (False, "fresh")
    code, js, _h = run_gate(repo)
    assert code == 0 and js["verdict"] == "CONTINUE_IMPL"


def test_impl_reports_and_tail_artifacts_keep_design_fresh(repo):
    """change 目录里的非四件套产物（impl-report / hand-off / 评审报告）不在监视集内。"""
    d = approved_change(repo, plan=PLAN2_TICKETS)
    (d / "impl-reports").mkdir(exist_ok=True)
    (d / "impl-reports" / "task1-x.md").write_text("# 实现报告\n", encoding="utf-8")
    (d / "hand-off.md").write_text("x\n", encoding="utf-8")
    commit_all(repo, "checkpoint(task1-a): 落实现报告")
    assert _sg.is_stale(repo, BASE + "spec-review-report.md", "design", "demo") == (False, "fresh")


# ── 5.4 把已批准产物换回锚之前的旧内容 ⇒ 失鲜 ─────────────────────────────

def test_revert_to_pre_anchor_content_is_stale(repo):
    """🔴 判别性最强的一格：HEAD 侧内容**曾经存在过**（就在锚之前），
    任何「这份内容在历史上出现过就算见过」的判据都会在此假绿。
    内容比较锚的是**被批准的那一份**，∴ 换回旧版同样是失鲜。
    """
    d = approved_change(repo, plan=PLAN2_TICKETS)
    (d / "design.md").write_text("v1 旧设计\n", encoding="utf-8")
    commit_all(repo, "design v1")
    (d / "design.md").write_text("v2 被批准的设计\n", encoding="utf-8")
    commit_all(repo, "design v2")
    _reanchor(repo, d)                                   # 锚 = v2
    (d / "design.md").write_text("v1 旧设计\n", encoding="utf-8")
    commit_all(repo, "merge: resolve 回 v1")
    assert _sg.is_stale(repo, BASE + "spec-review-report.md", "design", "demo") == (True, "stale")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"


# ── 5.5 无关的报告排版提交不移动锚 ────────────────────────────────────────

def test_report_reformat_commit_does_not_move_anchor(repo):
    """排版提交顺带碰一下报告文件 ⇒ 锚 MUST NOT 前移，锚前的未审改动 MUST NOT 被埋掉。"""
    d = approved_change(repo, plan=PLAN2_TICKETS)
    (d / "design.md").write_text("拍板后偷改的设计\n", encoding="utf-8")
    commit_all(repo, "docs: 偷改设计")
    report = d / "spec-review-report.md"
    report.write_text(report.read_text(encoding="utf-8") + "\n<!-- CI 排版 -->\n",
                      encoding="utf-8")
    commit_all(repo, "chore: 报告排版（不动任何结论字段）")
    assert _sg.is_stale(repo, BASE + "spec-review-report.md", "design", "demo") == (True, "stale")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"


# ── 5.10 specs/ 子树：新增 / 删除 / rename（内容不变）三类各判失鲜 ──────────

def test_specs_added_file_is_stale(repo):
    d = approved_change(repo, plan=PLAN2_TICKETS)
    _reanchor(repo, d)
    specs = d / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    (specs / "new.md").write_text("# 新增 delta\n", encoding="utf-8")
    commit_all(repo, "docs: 新增 delta spec")
    assert _sg.is_stale(repo, BASE + "spec-review-report.md", "design", "demo") == (True, "stale")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"


def test_specs_deleted_file_is_stale(repo):
    d = approved_change(repo, plan=PLAN2_TICKETS)
    specs = d / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    (specs / "gone.md").write_text("# delta\n", encoding="utf-8")
    commit_all(repo, "docs: delta spec")
    _reanchor(repo, d)
    (specs / "gone.md").unlink()
    commit_all(repo, "chore: 删掉 delta spec")
    assert _sg.is_stale(repo, BASE + "spec-review-report.md", "design", "demo") == (True, "stale")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"


def test_specs_renamed_with_identical_content_is_stale(repo):
    """🔴 内容逐字节不变的纯改名：任何「逐文件比字节」的判据都会在此假绿
    （两侧各自枚举都能找到一份同样的字节）。映射比较看的是 **path → oid** 的对应，
    ∴ 路径动了就是不等。
    """
    d = approved_change(repo, plan=PLAN2)
    specs = d / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    (specs / "old.md").write_text("# delta\n", encoding="utf-8")
    commit_all(repo, "docs: delta spec")
    _reanchor(repo, d)
    _git(repo, "mv", BASE + "specs/old.md", BASE + "specs/new.md")
    commit_all(repo, "chore: 改名 delta spec（内容一字未动）")
    assert _sg.is_stale(repo, BASE + "spec-review-report.md", "design", "demo") == (True, "stale")


def test_specs_subtree_edit_is_stale(repo):
    d = approved_change(repo, plan=PLAN2)
    specs = d / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    (specs / "s.md").write_text("# v1\n", encoding="utf-8")
    commit_all(repo, "docs: delta spec")
    _reanchor(repo, d)
    (specs / "s.md").write_text("# v2 偷改\n", encoding="utf-8")
    commit_all(repo, "docs: 改 delta spec")
    assert _sg.is_stale(repo, BASE + "spec-review-report.md", "design", "demo") == (True, "stale")


# ── 读失败 ≠ 内容为空；HEAD 侧枚举失败 fail-closed ────────────────────────

def test_ls_tree_read_failure_is_indeterminate_not_fresh(repo, monkeypatch):
    """`ls-tree` 的 rc≠0 = 真读失败 ⇒ `GateIndeterminate`（→ UNKNOWN(6)），
    **MUST NOT** 当成空映射——两侧都失败会比出「空 == 空」⇒ 判 fresh ⇒ 放行一切改动。"""
    d = approved_change(repo, plan=PLAN2_TICKETS)
    (d / "design.md").write_text("偷改\n", encoding="utf-8")
    commit_all(repo, "docs: 偷改")
    real = _sg.run_git_bytes
    monkeypatch.setattr(_sg, "run_git_bytes", lambda root, *args:
                        (128, b"") if args[:1] == ("ls-tree",) else real(root, *args))
    with pytest.raises(_sg.GateIndeterminate) as ei:
        _sg.is_stale(repo, BASE + "spec-review-report.md", "design", "demo")
    assert ei.value.category == _sg.CAUSE_READ_FAILED


def test_ls_tree_unparsable_output_is_indeterminate(repo, monkeypatch):
    """协议外形态（无 `\\t` / 字段数不对）⇒ 看不清 ⇒ 不可判。
    MUST NOT 静默跳过该记录——跳过等于把一个真实条目从映射里抹掉（fail-open）。"""
    approved_change(repo, plan=PLAN2_TICKETS)
    monkeypatch.setattr(_sg, "run_git_bytes",
                        lambda root, *a: (0, b"garbage-without-tab\0"))
    with pytest.raises(_sg.GateIndeterminate) as ei:
        _sg.is_stale(repo, BASE + "spec-review-report.md", "design", "demo")
    assert ei.value.category == _sg.CAUSE_READ_FAILED


def test_no_blob_content_read_ever_for_design_freshness(repo, monkeypatch):
    """〔sweep-pool-debt D2/D3〕机械守：等值判定只走 manifest digest 比较，design 域
    **不再有任何** `cat-file blob` 调用（旧的 tasks.md 勾选框豁免层才需要读取单文件字节，
    该层已随 D2 整体退役）。"""
    d = approved_change(repo, plan=PLAN2_TICKETS)
    (d / "design.md").write_text("偷改\n", encoding="utf-8")
    commit_all(repo, "docs: 偷改")
    calls = []
    real = _sg.run_git_bytes

    def spy(root, *args):
        if args[:2] == ("cat-file", "blob"):
            calls.append(args)
        return real(root, *args)

    monkeypatch.setattr(_sg, "run_git_bytes", spy)
    assert _sg.is_stale(repo, BASE + "spec-review-report.md", "design", "demo") == (True, "stale")
    assert calls == []


@pytest.mark.skipif(os.name == "nt", reason="NTFS does not expose POSIX executable-bit changes")
def test_mode_only_change_on_design_is_stale(repo):
    """仅权限位变更：前后两版 blob 字节**完全相同**，但 manifest 记录 (mode, type, oid)，
    mode 变了 manifest 就变 ⇒ 必须失鲜（不会被"内容相同"掩盖状态位变更）。"""
    _git(repo, "config", "core.fileMode", "true")
    d = approved_change(repo, plan=PLAN2_TICKETS)
    _reanchor(repo, d)
    (d / "design.md").chmod(0o755)
    commit_all(repo, "chmod +x design.md")
    raw = _git(repo, "diff", "--raw", "HEAD~1", "HEAD", "--", BASE + "design.md").stdout
    assert raw.strip(), "前提校准：chmod 未被 git 记录（core.fileMode 关？）本例失去区分力"
    assert _sg.is_stale(repo, BASE + "spec-review-report.md", "design", "demo") == (True, "stale")


# ── 5.15b evil-merge：改动只存在于 merge 自身 resolve 出的树 ──────────────

def _merge_amended(repo, mutate, msg="merge side"):
    """造一个 merge 提交，其树由 mutate 决定（两个 parent 各自都没有这份内容）。"""
    _git(repo, "checkout", "-q", "-b", "side")
    (repo / "s.txt").write_text("s\n", encoding="utf-8")
    commit_all(repo, "side edit")
    _git(repo, "checkout", "-q", "main")
    (repo / "m.txt").write_text("m\n", encoding="utf-8")
    commit_all(repo, "main edit")
    _git(repo, "merge", "--no-ff", "-q", "-m", msg, "side")
    mutate()
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "--amend", "--no-edit")
    parents = _git(repo, "rev-list", "--parents", "-n", "1", "HEAD").stdout.split()
    assert len(parents) == 3, "构造失败：应为双 parent 的 merge 提交"


def test_evil_merge_design_edit_is_stale(repo):
    """改动**只存在于 merge 自身 resolve 出的树**（两个 parent 都没有这份内容）。
    内容比较对拓扑完全不敏感（只看锚与 HEAD 两个端点的树），必抓。"""
    d = approved_change(repo, plan=PLAN2_TICKETS)
    (d / "design.md").write_text("v1\n", encoding="utf-8")
    commit_all(repo, "seed design")
    _reanchor(repo, d)
    _merge_amended(repo, lambda: (d / "design.md").write_text("evil v2\n", encoding="utf-8"))
    assert _sg.is_stale(repo, BASE + "spec-review-report.md", "design", "demo") == (True, "stale")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"


@pytest.mark.skipif(os.name == "nt", reason="Win32 filenames cannot contain tab characters")
def test_spec_path_with_tab_is_stale(repo):
    """[5.15b] 含 Tab 的路径：`-z`（关掉 C-quote）+ 按**首个 `\\t`** 切分 +
    path 保持原始字节，该承诺依然生效。"""
    d = approved_change(repo, plan=PLAN2_TICKETS)
    _reanchor(repo, d)
    specs = d / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    (specs / "we\tird.md").write_text("delta\n", encoding="utf-8")
    commit_all(repo, "docs: 加一份带 Tab 文件名的 delta spec")
    assert _sg.is_stale(repo, BASE + "spec-review-report.md", "design", "demo") == (True, "stale")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"


@pytest.mark.skipif(os.name == "nt", reason="Win32 filenames cannot contain tab characters")
def test_ls_tree_keeps_tab_path_raw_and_unquoted(repo):
    """机械守 `-z` 协议本身：路径原样进映射键——无 C-quote 包裹、不按 Tab 拆碎。
    删掉 `-z` ⇒ git 会把这条路径 C-quote 成 `"...we\\tird.md"` ⇒ 本例转红。"""
    d = approved_change(repo, plan=PLAN2_TICKETS)
    (d / "specs").mkdir(parents=True, exist_ok=True)
    (d / "specs" / "we\tird.md").write_text("x\n", encoding="utf-8")
    commit_all(repo, "tab path")
    entries = _sg.ls_tree_map(repo, "HEAD", _sg.design_pathspecs(BASE))
    key = (BASE + "specs/we\tird.md").encode("utf-8")
    assert key in entries
    assert not any(k.startswith(b'"') for k in entries)


def test_chinese_named_spec_edit_still_stale(repo):
    """非 ASCII 路径（C-quote ⇒ 裸 startswith 失配 ⇒ 静默放行 = 假✅）。
    本项目中文文件名密集，realistic。"""
    d = approved_change(repo, plan=PLAN2_TICKETS)
    _reanchor(repo, d)
    specs = d / "specs"
    specs.mkdir(exist_ok=True)
    (specs / "功能规格.md").write_text("拍板后偷改设计语义\n", encoding="utf-8")
    commit_all(repo, "docs: 改中文名 spec")
    assert _sg.is_stale(repo, BASE + "spec-review-report.md", "design", "demo") == (True, "stale")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"


# ══ 〔sweep-pool-debt D3/D4〕manifest 字节保真 round-trip ═══════════════════
# spec「控制字符与非 UTF-8 路径下 manifest 稳定」Scenario：写锚与验锚两侧对同一盘面
# MUST 得到字节相同的 manifest 与相同 digest；不同路径 MUST NOT 折叠为同一记录。

@pytest.mark.skipif(os.name == "nt", reason="Win32 路径无法含 Tab/非法字符")
def test_manifest_round_trip_stable_for_tab_and_non_ascii_paths(repo):
    d = approved_change(repo, plan=PLAN2_TICKETS)
    specs = d / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    (specs / "we\tird.md").write_text("x\r\nCRLF content\r\n", encoding="utf-8")
    (specs / "中文名.md").write_text("y\n", encoding="utf-8")
    commit_all(repo, "docs: 特殊路径 + CRLF 内容")
    sha1, manifest1 = fingerprint(repo, head_sha(repo), "design")
    sha2, manifest2 = fingerprint(repo, head_sha(repo), "design")
    assert sha1 == sha2 and manifest1 == manifest2   # round-trip 无损、确定性可重算
    decoded = base64.b64decode(manifest1)
    assert hashlib.sha256(decoded).hexdigest() == sha1   # 互证


def test_manifest_distinguishes_different_paths_not_folded(repo):
    """不同路径 MUST NOT 折叠为同一 manifest 记录：改动一个新路径必须改变 digest。"""
    d = approved_change(repo, plan=PLAN2_TICKETS)
    sha_before, _ = fingerprint(repo, head_sha(repo), "design")
    specs = d / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    (specs / "a.md").write_text("x\n", encoding="utf-8")
    commit_all(repo, "docs: 加 a.md")
    sha_after, _ = fingerprint(repo, head_sha(repo), "design")
    assert sha_before != sha_after


# ── 保留复用件：全部已声明退役的构件真的不在了 ─────────────────────────────

def test_retired_checkbox_exemption_cluster_leaves_no_dangling_reference():
    """〔sweep-pool-debt D2〕`tasks.md` 移出监视集后，纯勾选框翻转豁免层的**私有**构件
    （`_normalize_checkbox_lines` / `_tasks_content_exempt` / `indent_columns` /
    `is_indented_code_line` / `CHECKBOX_BYTES_RE` / `read_blob_bytes`）整体退役——物理删除，
    仓内无悬空引用与孤儿代码。**`HtmlCommentTracker` 不在此列**——它是与 `FenceTracker` 同族
    的通用词法状态机、跨子系统共享单一源（`hack/tests/test_decision_memo_gate.py` 复用它判定
    decision-memo.md 的 ATX 标题是否落在 HTML 注释块内，与本文件的失鲜判定无关），删除它会
    击穿另一个子系统的引用（已实测：全仓 pytest 曾因此在 collection 阶段报
    `AttributeError: module has no attribute 'HtmlCommentTracker'`）。"""
    # 判据 = `hasattr`：退役件不再是模块可见符号，任何仍调用它们的代码路径都会在
    # import 时（`class`/顶层 `def`）或首次调用时（`NameError`/`AttributeError`）当场爆炸，
    # 已被本仓其余大量 is_stale/gate 测试间接覆盖。MUST NOT 用源码文本子串扫描——退役记录
    # 本身（本文件与 ship_gate.py 头注释里叙述"某某已随 D2 退役"的说明性文字）会合法提及
    # 这些历史符号名，子串扫描分不清"叙述退役"与"仍在调用"（基准 5：不手搓文本解析去回答
    # 一个 `hasattr` 已经能精确回答的问题）。
    retired = ["_normalize_checkbox_lines", "_tasks_content_exempt",
               "indent_columns", "is_indented_code_line", "CHECKBOX_BYTES_RE",
               "read_blob_bytes"]
    for name in retired:
        assert not hasattr(_sg, name), f"退役件仍在模块里：{name}"
    assert hasattr(_sg, "HtmlCommentTracker"), \
        "HtmlCommentTracker 是跨子系统共享单一源，不应被本次退役连带删除"


def test_design_watched_names_exclude_tasks_md():
    """〔D2〕监视集只含 proposal.md / design.md（+ specs/ 子树），tasks.md 不在其中。"""
    assert set(_sg.DESIGN_WATCHED_NAMES) == {"proposal.md", "design.md"}
    assert _sg.design_pathspecs(BASE) == [
        BASE + "proposal.md", BASE + "design.md", BASE + "specs/"]


def test_stale_verdict_carries_no_trigger_payload(repo):
    """[ADR-4] 失鲜输出不再携带 `stale_trigger`（触发点诊断已换成 manifest 差集点名，
    见 guard_design_freshness）。"""
    d = approved_change(repo, plan=PLAN2_TICKETS)
    (d / "design.md").write_text("偷改\n", encoding="utf-8")
    commit_all(repo, "docs: 偷改设计")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"
    assert "stale_trigger" not in js


# ══════════════════════════════════════════════════════════════════════════
# [fix1] 双轴审第 1 轮返修的三条守卫（F1 退出码契约 / F3 基座隔离）
# ══════════════════════════════════════════════════════════════════════════

EXIT_CONTRACT = {0, 3, 4, 5, 6}
_NON_UTF8_CHANGE = b"br\xffken".decode("utf-8", "surrogateescape")  # lone surrogate `\udcff`


@pytest.mark.skipif(os.name == "nt", reason="Windows argv is Unicode and cannot carry raw non-UTF-8 bytes")
def test_non_utf8_change_exit_code_stays_in_contract_set(repo):
    """端到端：非 UTF-8 的 `--change` 经 `main()` 求值，退出码 MUST 落在契约集内。

    ⚠ 诚实边界：本机文件系统拒绝该名字的目录 ⇒ 本例走的是 `decide()` 的归档短路半场。
    钉的是：argv 里的非 UTF-8 字节在**任何**一步都不得逸出成退出码 1。
    """
    mkchange(repo)
    commit_all(repo, "seed")
    code, js, _h = run_gate(repo, change=_NON_UTF8_CHANGE)
    assert code in EXIT_CONTRACT, f"退出码 {code} 落在契约集 {EXIT_CONTRACT} 之外"
    assert js.get("verdict")            # 有结构化输出，不是裸崩


@pytest.mark.parametrize("key,want", [("core.autocrlf", "false"), ("core.fileMode", "true")])
def test_repo_fixture_pins_byte_and_mode_semantics(repo, key, want):
    """[F3] `repo` fixture MUST 钉死这两项——用例的判别力直接建在它们上：
    manifest round-trip 依赖字节原样回环；chmod-only 用例依赖 fileMode 真进 git。"""
    got = subprocess.run(["git", "-C", str(repo), "config", "--get", key],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()
    assert got == want, f"{key}={got!r}，基座未钉死（期望 {want!r}）"


# ══ [harden-gate-git-layer Task4 · ADR-3 · tasks 2.5/2.6/2.7] 求值窗口 ══

def _anchor_of(d):
    """从 spec-review-report.md 的 frontmatter 读出锚（= gate 会拿来比的那个 digest）。"""
    for line in (d / "spec-review-report.md").read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("reviewed_sha:"):
            return line.split(":", 1)[1].strip()
    raise AssertionError("报告里没有 reviewed_sha 锚")

def _revise_design(d, repo, text="# 拍板后改了设计\n"):
    (d / "design.md").write_text(text, encoding="utf-8")
    commit_all(repo, "revise design artifacts")

def _assert_windowed_refusal(repo, d):
    """窗口内失鲜的共同断言：REFUSE_START(3) + 锚值可见 + 差异触发点点名〔ADR-4 / 2.7〕。"""
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START", js
    sha = _anchor_of(d)
    assert js["reviewed_sha"] == sha, "锚值 MUST 出现在 emit 的 extra 里（撞门者不必去翻 frontmatter）"
    assert "design.md" in js["reason"], js["reason"]   # 差异触发点点名（DT-2 诊断走 manifest）
    assert "触发点" in js["reason"]

# ── 5.3b RUN_PLAN 分支 ───────────────────────────────────────────────

def test_window_run_plan_evaluates_design_freshness(repo):
    d = approved_change(repo)                     # 无 plan ⇒ 判定停在 RUN_PLAN
    assert run_gate(repo)[1]["verdict"] == "RUN_PLAN"
    _revise_design(d, repo)
    _assert_windowed_refusal(repo, d)

# ── 5.3c CONTINUE_IMPL 分支 ──────────────────────────────────────────

def test_window_continue_impl_evaluates_design_freshness(repo):
    d = approved_change(repo, plan=PLAN2_TICKETS)  # plan 在、任务未完 ⇒ CONTINUE_IMPL
    assert run_gate(repo)[1]["verdict"] == "CONTINUE_IMPL"
    _revise_design(d, repo)
    _assert_windowed_refusal(repo, d)

# ── 5.3d 窗口之外：代码审期 / 收尾期修订四件套 MUST NOT 判 design 失鲜 ──

def test_window_closed_during_code_review(repo):
    """代码审期修订四件套 ⇒ 不判 design 失鲜。"""
    d = impl_done(repo)                            # plan 全勾、无 cr 报告 ⇒ 窗口右边界之外
    assert run_gate(repo)[1]["verdict"] == "RUN_CODE_REVIEW"
    _revise_design(d, repo)
    code, js, _h = run_gate(repo)
    assert js["verdict"] != "REFUSE_START", f"窗口外仍判 design 失鲜：{js}"
    assert code == 0 and js["verdict"] == "RUN_CODE_REVIEW", js

def test_window_closed_during_wrapup(repo):
    """收尾期（cr + verify 均已出结论）修订四件套 ⇒ 不判 design 失鲜。"""
    d = tail_ok(repo)
    assert run_gate(repo)[1]["verdict"] == "RUN_VERIFY"
    _revise_design(d, repo)
    code, js, _h = run_gate(repo)
    assert js["verdict"] != "REFUSE_START", f"窗口外仍判 design 失鲜：{js}"
    # 四件套是 openspec/ 内路径 ⇒ code 域顶层条目不变 ⇒ 也不该触 RERUN_STALE
    assert code == 0 and js["verdict"] == "RUN_VERIFY", js


# ══ [harden-gate-git-layer Task5 · ADR-2 · tasks 2.3 · 测试 5.11a/5.11b/5.12] code 域 ══

_CR_REL = BASE + "code-review-report.md"
_VF_REL = BASE + "verify-report.md"


def _code_stale(repo, rel):
    """经公共入口求 code 域失鲜（rel = 两个消费方之一的报告相对路径）。"""
    return _sg.is_stale(repo, rel, "code", "demo")


def _anchor_code_reports(repo, d, ref, verify="PASS"):
    """写 code-review-report + verify-report，锚为 `ref` 上的 code 域指纹（被代码审/验证
    批准的盘面），并提交。verify 取 PASS（e2e 走 code-review-report 消费方）或 FAIL（走
    verify-report 消费方）。"""
    sha, manifest = fingerprint(repo, ref, "code")
    (d / "code-review-report.md").write_text(
        f"---\nship-gate:\n  code_review: pass\n  reviewed_sha: {sha}\n"
        f'  reviewed_manifest: "{manifest}"\n---\n# 代码审报告\n', encoding="utf-8")
    (d / "verify-report.md").write_text(
        f"---\nship-gate:\n  verify: {verify}\n  reviewed_sha: {sha}\n"
        f'  reviewed_manifest: "{manifest}"\n---\n# 验证报告\n', encoding="utf-8")
    commit_all(repo, "code/verify 报告锚基线")


def _evil_merge_toplevel(repo, mutate, msg="evil merge resolve 出顶层源码"):
    """两个 parent 都**只碰 openspec/**（不引入顶层源码），merge 提交自身 resolve 出顶层改动。"""
    _git(repo, "checkout", "-q", "-b", "side")
    (repo / "openspec" / "changes" / "demo" / "note-side.md").write_text("s\n", encoding="utf-8")
    commit_all(repo, "side: 仅 openspec 记账")
    _git(repo, "checkout", "-q", "main")
    (repo / "openspec" / "changes" / "demo" / "note-main.md").write_text("m\n", encoding="utf-8")
    commit_all(repo, "main: 仅 openspec 记账")
    _git(repo, "merge", "--no-ff", "-q", "-m", msg, "side")
    mutate()
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "--amend", "--no-edit")
    parents = _git(repo, "rev-list", "--parents", "-n", "1", "HEAD").stdout.split()
    assert len(parents) == 3, "构造失败：应为双 parent 的 merge 提交"


def test_code_domain_merge_introduces_source_change_is_stale(repo):
    """[5.11a] merge 提交自身 resolve 出顶层源码 `resolved.py`（两 parent 都没有它）⇒
    该源码从未过代码审 ⇒ code 域必须判失鲜。经 `code-review-report` 消费方端到端求值。"""
    d = impl_done(repo)
    baseline = head_sha(repo)                 # 代码审通过的基线（尚无顶层源码）
    _anchor_code_reports(repo, d, baseline, verify="PASS")
    _evil_merge_toplevel(
        repo, lambda: (repo / "resolved.py").write_text("# merge 里冒出来的源码\n", encoding="utf-8"))
    assert _code_stale(repo, _CR_REL) == (True, "stale")
    code, js, _h = run_gate(repo)
    assert code == 0 and js["verdict"] == "RERUN_STALE" and js["next"] == "sdflow-code-review", js
    assert js["freshness"] == "stale"


def test_code_domain_git_mv_source_into_openspec_is_stale(repo):
    """[5.11b] `git mv` 把顶层源码 `src.py` 搬进 `openspec/`（记账目录）⇒ 顶层条目 `src.py`
    消失、映射不等 ⇒ 失鲜。经 `verify-report` 消费方端到端求值（verify=FAIL）。"""
    d = impl_done(repo)
    (repo / "src.py").write_text("# 已过代码审的顶层源码\n", encoding="utf-8")
    commit_all(repo, "seed 顶层源码进基线")
    baseline = head_sha(repo)
    _anchor_code_reports(repo, d, baseline, verify="FAIL")
    _git(repo, "mv", "src.py", BASE + "stashed-src.py")     # 源码搬进记账目录
    commit_all(repo, "chore: 把源码 git mv 进 openspec")
    assert _code_stale(repo, _VF_REL) == (True, "stale")
    code, js, _h = run_gate(repo)
    assert code == 0 and js["verdict"] == "RERUN_STALE" and js["next"] == "sdflow-done", js
    assert js["freshness"] == "stale"


def test_code_domain_openspec_accounting_writes_stay_fresh(repo):
    """[5.12] 排除 `openspec` 条目后，记账目录内部的一切正常写入都不动其余顶层条目 ⇒ fresh。"""
    d = impl_done(repo)
    (repo / "src.py").write_text("# 顶层源码（证明排除后仍有非空顶层可比）\n", encoding="utf-8")
    commit_all(repo, "seed 顶层源码")
    baseline = head_sha(repo)
    _anchor_code_reports(repo, d, baseline, verify="PASS")   # 记账写①：落 cr/verify 报告
    (d / "hand-off.md").write_text("交接\n", encoding="utf-8")
    arch = repo / "openspec" / "changes" / "archive" / "2026-07-21-demo"
    arch.mkdir(parents=True)
    (arch / "proposal.md").write_text("归档副本\n", encoding="utf-8")
    commit_all(repo, "openspec 记账：hand-off + 归档目录")
    assert _code_stale(repo, _CR_REL) == (False, "fresh")
    assert _code_stale(repo, _VF_REL) == (False, "fresh")


def test_code_domain_excludes_openspec_by_entry_name_not_pathspec(repo):
    """[tasks 2.3 机械守] 排除口径 = Python 侧按顶层条目名 `!= b"openspec"`，**非**负向
    pathspec。"""
    d = impl_done(repo)
    (repo / "src.py").write_text("# v1\n", encoding="utf-8")
    commit_all(repo, "seed 顶层源码")
    baseline = head_sha(repo)
    _anchor_code_reports(repo, d, baseline, verify="PASS")
    anchor_top = _sg.ls_tree_map(repo, baseline, recursive=False)
    head_top = _sg.ls_tree_map(repo, "HEAD", recursive=False)
    assert anchor_top[b"openspec"] != head_top[b"openspec"], "前提校准：openspec 顶层 tree 确实变了"
    assert anchor_top[b"src.py"] == head_top[b"src.py"], "前提校准：src.py 未动"
    assert _code_stale(repo, _CR_REL) == (False, "fresh")


# ══ [harden-gate-git-layer Task6 · ADR-7(a) · 测试 5.13] code-review 自动修复非空 ══

def test_code_review_autofix_two_stage_commit_does_not_self_stale(repo):
    """[5.13 · ADR-7(a) 正例] 自动修复非空时，两段提交时序令 code 域相对自己的锚 fresh。"""
    d = impl_done(repo)
    (repo / "src.py").write_text("# 被代码审的源码 v1\n", encoding="utf-8")
    commit_all(repo, "seed 顶层源码进代码审基线")
    (repo / "src.py").write_text("# 自动修复后 [impl-review-fix]\n", encoding="utf-8")
    commit_all(repo, "checkpoint(impl-review): 多镜代码审自动修复")
    fix_sha = head_sha(repo)                  # ② 锚指修复提交
    _anchor_code_reports(repo, d, fix_sha, verify="PASS")
    assert _code_stale(repo, _CR_REL) == (False, "fresh")
    assert _code_stale(repo, _VF_REL) == (False, "fresh")
    code, js, _h = run_gate(repo)
    assert code == 0 and js["verdict"] != "RERUN_STALE", js


def test_code_review_single_stage_commit_would_self_lock(repo):
    """[5.13 变异对照 · ADR-7(a)] 时序退回单段（修复与报告塞进同一次提交）⇒ 锚只能取修复
    **前**的 HEAD ⇒ 修复落盘后源码顶层条目已变 ⇒ code 域相对自己的锚立刻失鲜（自锁）。"""
    d = impl_done(repo)
    (repo / "src.py").write_text("# 被代码审的源码 v1\n", encoding="utf-8")
    commit_all(repo, "seed 顶层源码进代码审基线")
    pre_fix = head_sha(repo)                   # 锚指修复**前**（单段时序的错误锚）
    (repo / "src.py").write_text("# 自动修复后 [impl-review-fix]\n", encoding="utf-8")
    _anchor_code_reports(repo, d, pre_fix, verify="PASS")
    assert _code_stale(repo, _CR_REL) == (True, "stale")
    code, js, _h = run_gate(repo)
    assert code == 0 and js["verdict"] == "RERUN_STALE" and js["next"] == "sdflow-code-review", js
    assert js["freshness"] == "stale"


# ══ 〔sweep-pool-debt D3/D4〕rebase/amend 历史重写免疫（brief MUST，内容锚只认树内容） ══

def test_amend_rewriting_history_without_content_change_stays_fresh(repo):
    """内容不变、只重写提交历史（`git commit --amend` 改 message，或等效的 rebase 落地为
    新 commit sha）→ design 域 MUST 判 fresh/CURRENT——digest 只认监视集树内容，不认
    commit sha 本身。区别于 `_merge_amended`/`test_touching_the_report_does_not_move_the_anchor`
    覆盖的场景（那两个改的是内容或"报告被触碰"，不是"历史被重写、内容原样"）。"""
    d = approved_change(repo, plan=PLAN2_TICKETS)
    _reanchor(repo, d)                                   # 锚 = 当前 HEAD 的 design 域指纹
    pre_amend_sha = head_sha(repo)
    _git(repo, "commit", "-q", "--amend", "-m", "reword only, no content change")
    post_amend_sha = head_sha(repo)
    assert post_amend_sha != pre_amend_sha, "前提校准：amend 未改变 commit sha，本例失去区分力"
    stale, freshness = _sg.is_stale(repo, BASE + "spec-review-report.md", "design", "demo")
    assert (stale, freshness) == (False, "fresh")
    code, js, _h = run_gate(repo)
    assert js["verdict"] == "CONTINUE_IMPL"
