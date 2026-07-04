import subprocess
from conftest import commit_all, mkchange
from test_gate_preflight import run_gate


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True,
                   capture_output=True, text=True)


def mk_archive(repo, name, verify_pass=True):
    """工作树建归档目录（不提交，调用方决定是否 commit）。"""
    arch = repo / "openspec" / "changes" / "archive" / name
    arch.mkdir(parents=True, exist_ok=True)
    (arch / "proposal.md").write_text("归档\n", encoding="utf-8")
    if verify_pass:
        (arch / "verify-report.md").write_text(
            "<!-- ship-gate: verify=PASS -->\n", encoding="utf-8")
    return arch


def test_archived_in_base_with_verify_shipped(repo):
    # ① 归档在 base 树 + archived verify=PASS 锚 → SHIPPED
    mk_archive(repo, "2026-07-04-demo")
    commit_all(repo, "archive demo")            # 进 main(=base)
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "SHIPPED"


def test_archived_only_in_head_run_verify(repo):
    # ② 归档仅在 HEAD 树（未并 base）→ RUN_VERIFY(next=sdflow-done)
    _git(repo, "commit", "-q", "--allow-empty", "-m", "base seed")   # main 基点
    _git(repo, "checkout", "-q", "-b", "feat/x")
    mk_archive(repo, "2026-07-04-demo")
    commit_all(repo, "archive on feature")      # 仅 feat/x，未并 main
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "RUN_VERIFY" and js["next"] == "sdflow-done"


def test_no_active_no_archive_refuse_not_exist(repo):
    # ③ active 与 archive 均无 → REFUSE「change 不存在」
    commit_all(repo, "seed")
    code, js, _ = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START" and "不存在" in js["reason"]


def test_active_present_old_archive_active_wins(repo):
    # ④ active 存在 + 精确同名旧归档 → active 优先（走 pre-flight，短路不触发）
    d = mkchange(repo)
    (d / "spec-review-report.md").write_text("# 报告\n无锚\n", encoding="utf-8")
    mk_archive(repo, "2026-07-04-demo")
    commit_all(repo, "active + old archive")
    code, js, _ = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START" and "设计门" in js["reason"]


def test_suffix_collision_not_matched(repo):
    # ⑤ 后缀撞名旧档（查 demo，archive 只有 …-cross-demo）→ 不误命中 → REFUSE 不存在
    mk_archive(repo, "2026-07-04-cross-demo")
    commit_all(repo, "archive cross-demo")
    code, js, _ = run_gate(repo)                # change=demo
    assert code == 3 and js["verdict"] == "REFUSE_START" and "不存在" in js["reason"]


def test_cross_branch_shipped_by_base(repo):
    # ⑥ 归档已并 base + verify 锚，HEAD 在无关未并分支 → 仍 SHIPPED（change 域，非 branch_state）
    mk_archive(repo, "2026-07-04-demo")
    commit_all(repo, "archive on main")
    _git(repo, "checkout", "-q", "-b", "feat/other")
    _git(repo, "commit", "-q", "--allow-empty", "-m", "unrelated unmerged")
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "SHIPPED"


def test_shell_archive_no_verify_not_shipped(repo):
    # ⑦〔H1〕归档在 base 但无 verify=PASS 锚（空壳）→ 不 SHIPPED（fail-safe UNKNOWN）
    mk_archive(repo, "2026-07-04-demo", verify_pass=False)
    commit_all(repo, "shell archive no verify")
    code, js, _ = run_gate(repo)
    assert js["verdict"] != "SHIPPED"
    assert code == 6 and js["verdict"] == "UNKNOWN"


def test_untracked_junk_archive_not_run_verify(repo):
    # ⑧〔H2〕磁盘未 git 跟踪的 archive 垃圾目录 → 纯 git 域不误命中 → REFUSE（非假 RUN_VERIFY）
    commit_all(repo, "seed")
    mk_archive(repo, "2026-07-04-demo")         # 只写盘，不 commit
    code, js, _ = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START" and "不存在" in js["reason"]


def test_detached_head_archived_shipped(repo):
    # ⑨〔H4〕detached HEAD + 归档已并 base → SHIPPED（detached 对 D3 无关）
    mk_archive(repo, "2026-07-04-demo")
    commit_all(repo, "archive demo")
    sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    _git(repo, "checkout", "-q", sha)           # detached
    code, js, _ = run_gate(repo)
    assert code == 0 and js["verdict"] == "SHIPPED"


def test_archived_verify_conflict_unknown(repo):
    # 〔CV-1/HRTG-c2〕归档 verify-report 并存 PASS+FAIL 冲突锚 → UNKNOWN（同 active pick_exclusive）
    arch = mk_archive(repo, "2026-07-04-demo", verify_pass=False)
    (arch / "verify-report.md").write_text(
        "<!-- ship-gate: verify=PASS -->\n<!-- ship-gate: verify=FAIL -->\n",
        encoding="utf-8")
    commit_all(repo, "archive with conflict anchors")
    code, js, _ = run_gate(repo)
    assert code == 6 and js["verdict"] == "UNKNOWN" and "冲突" in js["reason"]


def test_gbk_archived_verify_no_crash(repo):
    # 〔Corr-1/F1〕归档 verify-report 非 UTF-8(GBK) → 不崩(errors=replace)，给合法 verdict
    arch = repo / "openspec" / "changes" / "archive" / "2026-07-04-demo"
    arch.mkdir(parents=True)
    (arch / "proposal.md").write_text("归档\n", encoding="utf-8")
    body = b"<!-- ship-gate: verify=PASS -->\n" + "验证通过".encode("gbk") + b"\n"
    (arch / "verify-report.md").write_bytes(body)
    commit_all(repo, "archive gbk verify")
    code, js, _ = run_gate(repo)
    assert code in (0, 3, 4, 5, 6)          # 合法退出码集,未因解码崩溃(exit 1)
    assert js["verdict"] == "SHIPPED"       # ASCII 锚行不受 GBK 正文影响


def test_change_with_glob_metachar_safe(repo):
    # ⑩〔H5〕--change 含 glob 元字符 → re.escape 不当模式；archive 有 …-axb，查 a?b 不误命中
    mk_archive(repo, "2026-07-04-axb")
    commit_all(repo, "archive axb")
    code, js, _ = run_gate(repo, change="a?b")
    assert code == 3 and js["verdict"] == "REFUSE_START" and "不存在" in js["reason"]
