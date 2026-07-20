import subprocess, sys
from pathlib import Path

import pytest

from conftest import commit_all, mkchange
from test_gate_preflight import run_gate
from test_gate_impl_progress import approved_change, PLAN2, _sg
from test_gate_tail import impl_done

BASE = "openspec/changes/demo/"
TASKS_REL = BASE + "tasks.md"

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

# ══════════════════════════════════════════════════════════════════════════
# [fix-design-gate-freshness-proxy Task1] 设计门内容可见性 + 保守回落
#
# 本票**不引入任何豁免**：交付「判定有能力看见内容」这件能力本身，以及看不清时
# 一律判失鲜的保守方向。对外可观察行为与本票之前逐字一致（既有用例全绿即证）。
# ══════════════════════════════════════════════════════════════════════════

def _git(root, *args, check=True):
    return subprocess.run(["git", "-C", str(root), *args],
                          check=check, capture_output=True, text=True)

def _head(repo):
    return _git(repo, "rev-parse", "HEAD").stdout.strip()

def _write_tasks(repo, data, name="tasks.md"):
    """原始字节写入 change 目录下的文件（不经文本层，保真测试用）。"""
    p = repo / "openspec" / "changes" / "demo" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return p

def _reanchor(repo, d):
    """把 design-approved 锚推到 HEAD（重提交 spec-review-report.md，它不在监视集内）。

    端到端用例必需：`_seed_tasks` 里**新建** tasks.md 的那一提交本身落在锚之后的窗口内，
    而「新建」形态不合格 ⇒ 该帧照判失鲜，会先于待测的翻转帧触发，把用例的结论理由换掉。
    """
    (d / "spec-review-report.md").write_text(
        "---\nship-gate:\n  design_approved: true\n---\n# 设计审报告 v2\n", encoding="utf-8")
    commit_all(repo, "re-approve design")

def _seed_tasks(repo, data=b"### Task 1: A\n- [ ] s\n"):
    """建一个已有 tasks.md 的 change，返回 (change_dir, 该提交 sha)。"""
    d = approved_change(repo, plan=PLAN2)
    _write_tasks(repo, data)
    commit_all(repo, "seed tasks.md")
    return d, _head(repo)


# ── ① 「监视集内触及路径集」与「提交完整文件列表」是两个量 ──────────────

def test_watched_subs_is_not_the_full_file_list():
    frame_files = [
        "src/app.py",                       # 仓库别处源码（git add -A 必然打包）
        "README.md",
        BASE + "tasks.md",
        BASE + "verify-report.md",          # change 目录内、但不在 design 监视集
        "openspec/changes/other/design.md", # 别的 change
    ]
    assert _sg.design_watched_subs(frame_files, BASE) == {"tasks.md"}
    # 与完整文件列表是两个不同的量——后者含 5 项，前者只 1 项
    assert len(frame_files) == 5

def test_watched_subs_collects_all_watched_members():
    frame_files = [BASE + n for n in ("tasks.md", "design.md", "proposal.md",
                                      "specs/foo/spec.md")] + ["src/a.py"]
    assert _sg.design_watched_subs(frame_files, BASE) == {
        "tasks.md", "design.md", "proposal.md", "specs/foo/spec.md"}


# ── ② 能取到前后两版原始字节，且读取保真 ────────────────────────────────

def test_blob_pair_returns_raw_bytes_verbatim(repo):
    # 首尾空白 / 末尾换行 / CRLF / 非 UTF-8 字节：四者各自可造假等值，必须原样保真。
    # 前提校准：本机全局 core.autocrlf=input 会在 **commit 时**把 CRLF 清成 LF（blob 里
    # 根本不存在 CR）——那样 CRLF 维度失去区分力。目标态下消费仓两种 config 都存在，
    # 故这里显式钉 false，让 CRLF 真进 blob，才测得出「读取端是否保真」。
    _git(repo, "config", "core.autocrlf", "false")
    before = b"  \r\n### Task 1: A\r\n- [ ] s \xff\xfe\r\n   "
    after  = b"  \r\n### Task 1: A\r\n- [x] s \xff\xfe\r\n   "
    _, parent = _seed_tasks(repo, before)
    _write_tasks(repo, after)
    commit_all(repo, "flip")
    sha = _head(repo)
    ok, got_b, got_a = _sg.blob_pair(repo, parent, sha, TASKS_REL)
    assert ok is True
    assert got_b == before and got_a == after      # 逐字节等于写入的原始内容
    assert isinstance(got_b, bytes) and isinstance(got_a, bytes)

def test_blob_pair_preserves_crlf_and_trailing_newline_difference(repo):
    # 仅行尾 / 末尾换行不同 ⇒ 两版字节必须可区分（若走 .strip()/文本解码就会趋同）
    _git(repo, "config", "core.autocrlf", "false")   # 同上：让 CRLF 真进 blob
    _, parent = _seed_tasks(repo, b"- [ ] s\n")
    _write_tasks(repo, b"- [ ] s\r\n")
    commit_all(repo, "crlf")
    ok, b0, a0 = _sg.blob_pair(repo, parent, _head(repo), TASKS_REL)
    assert ok and b0 != a0


# ── ③ 返回状态被显式检查；任一侧失败 ⇒ 保守（不得依赖空值恰好相等）────────

def test_blob_pair_rc_failure_on_both_sides_is_not_equal_bytes(repo, monkeypatch):
    # 直击 1.1c：绕过形态闸门后，双侧 git show 都失败 ⇒ MUST 返回 ok=False，
    # MUST NOT 返回 (True, b"", b"")——那会被下游读成「两版等值」⇒ 放行真实设计改动。
    _, parent = _seed_tasks(repo)
    commit_all(repo, "noop")
    monkeypatch.setattr(_sg, "_plain_content_modification", lambda *a, **k: True)
    ok, b0, a0 = _sg.blob_pair(repo, parent, _head(repo),
                                     BASE + "does-not-exist.md")
    assert ok is False
    assert not (ok and b0 == a0)

def test_blob_pair_rc_failure_on_one_side_is_conservative(repo, monkeypatch):
    _, parent = _seed_tasks(repo)
    _write_tasks(repo, b"- [x] s\n")
    commit_all(repo, "flip")
    sha = _head(repo)
    monkeypatch.setattr(_sg, "_plain_content_modification", lambda *a, **k: True)
    real = _sg.run_git_bytes
    def one_side_fails(root, *args):
        if args and args[-1].startswith(parent):     # 前版侧失败
            return 128, b""
        return real(root, *args)
    monkeypatch.setattr(_sg, "run_git_bytes", one_side_fails)
    ok, _, _ = _sg.blob_pair(repo, parent, sha, TASKS_REL)
    assert ok is False


# ── ④ 形态不合格一律保守（前版不存在 / 后版不存在 / 非普通内容修改）────────

def test_blob_pair_added_in_this_commit_is_conservative(repo):
    # 前版不存在（该提交中新建 tasks.md）⇒ 判失鲜
    approved_change(repo, plan=PLAN2)
    parent = _head(repo)
    _write_tasks(repo, b"- [ ] s\n")
    commit_all(repo, "add tasks.md")
    ok, _, _ = _sg.blob_pair(repo, parent, _head(repo), TASKS_REL)
    assert ok is False

def test_blob_pair_deleted_in_this_commit_is_conservative(repo):
    # 后版不存在（该提交中删除）⇒ 判失鲜
    d, parent = _seed_tasks(repo)
    (d / "tasks.md").unlink()
    commit_all(repo, "delete tasks.md")
    ok, _, _ = _sg.blob_pair(repo, parent, _head(repo), TASKS_REL)
    assert ok is False

def test_blob_pair_renamed_away_is_conservative(repo):
    # git mv 迁走（后版取不到）⇒ 判失鲜
    _, parent = _seed_tasks(repo)
    _git(repo, "mv", TASKS_REL, BASE + "tasks-renamed.md")
    commit_all(repo, "rename tasks.md")
    ok, _, _ = _sg.blob_pair(repo, parent, _head(repo), TASKS_REL)
    assert ok is False

def test_blob_pair_chmod_only_is_conservative(repo):
    # 仅权限位变更：前后两版 blob 字节**完全相同**，纯内容判据会误判「无实质改动」
    d, parent = _seed_tasks(repo)
    (d / "tasks.md").chmod(0o755)
    commit_all(repo, "chmod +x tasks.md")
    sha = _head(repo)
    raw = _git(repo, "diff", "--raw", parent, sha, "--", TASKS_REL).stdout
    assert raw.strip(), "前提校准：chmod 未被 git 记录（core.fileMode 关？）本例失去区分力"
    ok, _, _ = _sg.blob_pair(repo, parent, sha, TASKS_REL)
    assert ok is False

def test_blob_pair_type_change_to_symlink_is_conservative(repo):
    # regular ↔ symlink 类型变更 ⇒ 判失鲜
    d, parent = _seed_tasks(repo, b"- [ ] s\n")
    (d / "target.md").write_bytes(b"- [ ] s\n")
    (d / "tasks.md").unlink()
    (d / "tasks.md").symlink_to("target.md")
    commit_all(repo, "tasks.md → symlink")
    sha = _head(repo)
    # [impl-review-fix F3] 前提校准：core.symlinks=false 时 git 把 symlink 记成普通文件
    # 内容变更（dstmode 仍 100644、status M）⇒ 本例退化成「普通内容修改」，照样绿但
    # 通过理由变了、类型变更这条分支静默失守。故显式断言 git 真把它记成了类型变更。
    raw = _git(repo, "diff", "--raw", parent, sha, "--", TASKS_REL).stdout
    fields = raw.split("\t", 1)[0].split()
    assert len(fields) >= 5 and (fields[1] == "120000" or fields[4].startswith("T")), \
        f"前提校准：symlink 未被记为类型变更（core.symlinks 关？）本例失去区分力：{raw!r}"
    ok, _, _ = _sg.blob_pair(repo, parent, sha, TASKS_REL)
    assert ok is False

def test_plain_content_modification_true_only_for_real_edit(repo):
    _, parent = _seed_tasks(repo)
    _write_tasks(repo, b"- [x] s\n")
    commit_all(repo, "edit")
    assert _sg._plain_content_modification(repo, parent, _head(repo), TASKS_REL) is True

def test_raw_line_plain_modification_true_for_content_edit():
    assert _sg._plain_modification_from_raw(
        ":100644 100644 aaaaaaa bbbbbbb M\topenspec/changes/demo/tasks.md") is True

def test_raw_line_rejects_non_modification_statuses():
    # 合成 raw 行直测 status 闸门——A/D/R/C/T 各自可在真实 git 下出现，
    # 但其中几种在「路径限定 + --no-renames」下会被 rc/mode 两道先兜住，
    # 光靠 git 驱动的用例杀不掉这一分支，故对纯函数直测（PV 规则 5 可证伪性）
    for status in ("A", "D", "T", "R100", "C90", "U", "X"):
        line = f":100644 100644 aaaaaaa bbbbbbb {status}\tp/tasks.md"
        assert _sg._plain_modification_from_raw(line) is False, status

def test_raw_line_rejects_mode_only_change():
    assert _sg._plain_modification_from_raw(
        ":100644 100755 aaaaaaa aaaaaaa M\tp/tasks.md") is False
    assert _sg._plain_modification_from_raw(
        ":100644 120000 aaaaaaa bbbbbbb M\tp/tasks.md") is False

def test_raw_line_rejects_malformed_shapes():
    for line in ("", "100644 100644 a b M\tp", "not a raw line",
                 ":100644 100644 a b\tp", ":100644\tp",
                 # 字段齐、模式位「相等」、状态 M，唯独不以 : 起始 ⇒ 不是 raw 行形，
                 # 少了行形闸门就会被当成合法普通修改（此例专杀该分支）
                 "X100644 100644 aaaaaaa bbbbbbb M\tp/tasks.md"):
        assert _sg._plain_modification_from_raw(line) is False, repr(line)

def test_plain_content_modification_false_when_path_untouched(repo):
    _, parent = _seed_tasks(repo)
    (repo / "src.py").write_text("x\n", encoding="utf-8")
    commit_all(repo, "unrelated")
    assert _sg._plain_content_modification(repo, parent, _head(repo), TASKS_REL) is False


# ── ⑤ merge：「前版」相对每个 parent 各自定义；BR-6 护栏逐字不动 ───────────

def test_commit_parents_enumerates_every_parent_of_a_merge(repo):
    _seed_tasks(repo)
    main_tip = _head(repo)
    _git(repo, "checkout", "-q", "-b", "side")
    _write_tasks(repo, b"- [ ] side\n")
    commit_all(repo, "side edit")
    side_tip = _head(repo)
    _git(repo, "checkout", "-q", "main")
    (repo / "m.txt").write_text("m\n", encoding="utf-8")
    commit_all(repo, "main edit")
    main_tip2 = _head(repo)
    _git(repo, "merge", "--no-ff", "-q", "-m", "merge side", "side")
    parents = _sg.commit_parents(repo, _head(repo))
    assert set(parents) == {main_tip2, side_tip}      # 每个 parent 都在，非只 first-parent
    assert main_tip not in parents

def test_commit_parents_root_commit_is_empty(repo):
    (repo / "a.txt").write_text("a\n", encoding="utf-8")
    commit_all(repo, "root")
    assert _sg.commit_parents(repo, _head(repo)) == []

def test_commit_parents_unresolvable_sha_is_none(repo):
    (repo / "a.txt").write_text("a\n", encoding="utf-8")
    commit_all(repo, "root")
    assert _sg.commit_parents(repo, "0" * 40) is None

def test_br6_guard_no_no_merges_or_first_parent_in_design_scope():
    # 〔BR-6 护栏逐字不动〕design 域遍历 MUST NOT 引入 --no-merges / --first-parent
    src = (Path(_sg.__file__)).read_text(encoding="utf-8")
    design_branch = src.split('if scope == "design":', 1)[1].split(
        '# scope == "code"', 1)[0]
    # 只看代码行——护栏注释本身就写着这两个 flag 名，连注释一起扫会永远假红
    code_lines = [ln for ln in design_branch.splitlines()
                  if not ln.lstrip().startswith("#")]
    body = "\n".join(code_lines)
    assert "--no-merges" not in body
    assert "--first-parent" not in body
    assert "%H" in body            # 反向：sha 确实被 format 携带（能力在场）


# ── ⑥ 帧级豁免：纯勾选框翻转成立，其余一律保守 ─────────────────────────

def test_design_frame_exempt_true_on_pure_checkbox_flip(repo):
    # 最贴近目标态的形态：纯勾选翻转、帧内监视路径恰为 {tasks.md}、同帧还带源码
    _, _ = _seed_tasks(repo, b"### Task 1: A\n- [ ] s\n")
    _write_tasks(repo, b"### Task 1: A\n- [x] s\n")
    commit_all(repo, "flip checkbox only")
    assert _sg.design_frame_exempt(
        repo, _head(repo), [TASKS_REL, "src.py"], BASE) is True

def _always_exempt(monkeypatch):
    """把 Task2 的等值判据替身为「恒可豁免」——只有这样，上游各道保守回落分支
    才各自可证伪（否则 Task1 的恒 False 会把它们全遮住，删掉也没人红）。"""
    monkeypatch.setattr(_sg, "_tasks_content_exempt", lambda b, a: True)

def test_exempt_conservative_when_other_watched_path_touched_even_if_content_ok(repo, monkeypatch):
    d, _ = _seed_tasks(repo)
    (d / "design.md").write_text("v2\n", encoding="utf-8")
    _write_tasks(repo, b"- [x] s\n")
    commit_all(repo, "tasks + design")
    _always_exempt(monkeypatch)
    assert _sg.design_frame_exempt(
        repo, _head(repo), [TASKS_REL, BASE + "design.md"], BASE) is False

def test_exempt_conservative_on_root_commit(repo, monkeypatch):
    _write_tasks(repo, b"- [ ] s\n")
    commit_all(repo, "root commit creating tasks.md")
    _always_exempt(monkeypatch)
    assert _sg.design_frame_exempt(repo, _head(repo), [TASKS_REL], BASE) is False

def test_exempt_conservative_on_unresolvable_sha(repo, monkeypatch):
    _seed_tasks(repo)
    _always_exempt(monkeypatch)
    assert _sg.design_frame_exempt(repo, "0" * 40, [TASKS_REL], BASE) is False

def test_exempt_conservative_when_form_disqualified(repo, monkeypatch):
    # 仅 chmod（两版 blob 字节完全相同、内容判据必说「等值」）⇒ 形态闸门 MUST 先拦下
    d, parent = _seed_tasks(repo)
    (d / "tasks.md").chmod(0o755)
    commit_all(repo, "chmod only")
    sha = _head(repo)
    # [impl-review-fix F2] 前提校准（同 test_blob_pair_chmod_only_is_conservative）：
    # core.fileMode=false 时 chmod 不入 git ⇒ 该提交对 tasks.md 根本无变更，用例会因
    # 「路径未触及」而绿、而非因形态闸门拦下——通过理由变了，形态分支静默失守。
    raw = _git(repo, "diff", "--raw", parent, sha, "--", TASKS_REL).stdout
    assert raw.strip(), "前提校准：chmod 未被 git 记录（core.fileMode 关？）本例失去区分力"
    _always_exempt(monkeypatch)
    assert _sg.design_frame_exempt(repo, sha, [TASKS_REL], BASE) is False

def test_exempt_conservative_when_added_in_this_commit(repo, monkeypatch):
    approved_change(repo, plan=PLAN2)
    _write_tasks(repo, b"- [x] s\n")
    commit_all(repo, "add tasks.md")
    _always_exempt(monkeypatch)
    assert _sg.design_frame_exempt(repo, _head(repo), [TASKS_REL], BASE) is False

def test_exempt_requires_every_parent_of_a_merge(repo, monkeypatch):
    # 🔴 判别性构造：merge 相对 **first parent** 合格（普通内容修改 v1→v2），相对
    # **second parent** 不合格（该侧根本没有 tasks.md ⇒ 新建 A）。只看 first parent
    # 的实现会在此放行；逐 parent 求值才拦得住。
    approved_change(repo, plan=PLAN2)          # C0：尚无 tasks.md
    _git(repo, "branch", "side")               # side 从 C0 分出
    _write_tasks(repo, b"- [ ] s\n")
    commit_all(repo, "main: tasks.md v1")      # M1（first parent）
    _git(repo, "checkout", "-q", "side")
    (repo / "side.txt").write_text("s\n", encoding="utf-8")
    commit_all(repo, "side: unrelated")        # S（second parent，无 tasks.md）
    _git(repo, "checkout", "-q", "main")
    _git(repo, "merge", "--no-ff", "--no-commit", "-q", "side", check=False)
    _write_tasks(repo, b"- [x] s\n")           # merge 提交自身改 tasks.md → vs M1 是 M
    commit_all(repo, "merge side")
    sha = _head(repo)
    parents = _sg.commit_parents(repo, sha)
    assert len(parents) == 2                   # 前提校准：确实是 merge 提交
    # 前提校准：first parent 侧确实合格 —— 否则本例退化，测不出「逐 parent」
    assert _sg._plain_content_modification(repo, parents[0], sha, TASKS_REL) is True
    assert _sg._plain_content_modification(repo, parents[1], sha, TASKS_REL) is False
    _always_exempt(monkeypatch)
    assert _sg.design_frame_exempt(repo, sha, [TASKS_REL], BASE) is False

def test_design_frame_exempt_false_when_other_watched_path_touched(repo):
    d, _ = _seed_tasks(repo)
    (d / "design.md").write_text("v2\n", encoding="utf-8")
    _write_tasks(repo, b"- [x] s\n")
    commit_all(repo, "tasks + design")
    assert _sg.design_frame_exempt(
        repo, _head(repo), [TASKS_REL, BASE + "design.md"], BASE) is False

def test_tasks_only_checkbox_flip_not_stale(repo):
    # 端到端正例：只翻勾选框、帧内监视集恰为 {tasks.md} ⇒ 不再 REFUSE_START
    d, _ = _seed_tasks(repo, b"### Task 1: A\n- [ ] s\n")
    _reanchor(repo, d)
    _write_tasks(repo, b"### Task 1: A\n- [x] s\n")
    commit_all(repo, "docs: 勾选回填")
    code, js, _h = run_gate(repo)
    # [fix1 M1] 断确切值，MUST NOT 用 `!= "REFUSE_START"`——UNKNOWN(6) 等异常出口
    # 也满足弱断言，会把"门崩了"读成"门放行了"。
    assert code == 0 and js["verdict"] == "CONTINUE_IMPL"

def test_tasks_flip_plus_source_code_not_stale(repo):
    # 🔴 主用例：`git add -A` 打包形态（勾选 tasks.md + 仓库别处源码）⇒ 仍豁免。
    # 若把「只触及 tasks.md」按整个 commit 的文件列表求值，豁免在真实世界永不触发，
    # 而其余全部用例照样通过——本条是该错误的唯一钉子。
    d, _ = _seed_tasks(repo, b"### Task 1: A\n- [ ] s\n")
    _reanchor(repo, d)
    _write_tasks(repo, b"### Task 1: A\n- [x] s\n")
    (repo / "src.py").write_text("# impl\n", encoding="utf-8")
    commit_all(repo, "docs: 勾选回填 + 实现")
    code, js, _h = run_gate(repo)
    assert code == 0 and js["verdict"] == "CONTINUE_IMPL"        # [fix1 M1] 断确切值

def test_merge_commit_pure_flip_not_stale(repo):
    # merge 场景**整体**不撞门。
    # [impl-review-fix F1] 原注释「本例没有验到 merge 帧逐 parent 求值（--name-only 对
    # merge 恒空 ⇒ subs 为空 ⇒ 直接跳过）」已随枚举协议换成 diff-tree -m 而失效：merge
    # 帧现在会被真正枚举出触及 tasks.md（相对 main-parent 有改动），并逐 parent 求值——
    # 相对 side-parent 为 unchanged（跳过）、相对 main-parent 为纯翻转（豁免）。
    # 本例因此从「拓扑不误判」升级为「普通 merge 的逐 parent 求值不产生假失鲜」的钉子。
    d, _ = _seed_tasks(repo, b"### Task 1: A\n- [ ] s\n")
    _reanchor(repo, d)
    _git(repo, "checkout", "-q", "-b", "side")
    _write_tasks(repo, b"### Task 1: A\n- [x] s\n")
    commit_all(repo, "side flip")
    _git(repo, "checkout", "-q", "main")
    (repo / "m.txt").write_text("m\n", encoding="utf-8")
    commit_all(repo, "main edit")
    _git(repo, "merge", "--no-ff", "-q", "-m", "merge side", "side")
    code, js, _h = run_gate(repo)
    assert code == 0 and js["verdict"] == "CONTINUE_IMPL"        # [fix1 M1] 断确切值

def test_frame_sha_parsed_from_subject_with_spaces_and_colons(repo):
    # 〔1.1b〕分隔符须无歧义：subject 含空格与冒号时 sha 仍可正确切出
    d, _ = _seed_tasks(repo)
    (d / "design.md").write_text("v2\n", encoding="utf-8")
    commit_all(repo, "docs(scope): 带空格 与: 冒号的 subject")
    expect = _head(repo)
    out = _sg.run_git(repo, "log", "-1", "--name-only", "--format=%x00%H%x1f%s")
    frame = [f for f in out.split("\x00") if f][0]
    sha_field, _, subject = frame.split("\n")[0].partition("\x1f")
    assert sha_field == expect
    assert subject == "docs(scope): 带空格 与: 冒号的 subject"


# ══════════════════════════════════════════════════════════════════════════
# [fix-design-gate-freshness-proxy Task2] 纯勾选框翻转不再撞门
#
# 判据 = 勾选框标记归一化后**逐行等值**（位置对齐，禁 LCS）。归一化只动
# task-list 行首那一个标记，且 fenced code block 内不参与。其余一切差异形态
# （措辞 / 空白 / 行尾 / 段落增删 / 行重排 / 字面量里的方括号）照判失鲜。
# ══════════════════════════════════════════════════════════════════════════

E = _sg._tasks_content_exempt


# ── ⑦a 正例：勾选框翻转（含反向、大写、缩进/空白原样保留）─────────────────

def test_content_exempt_forward_flip():
    assert E(b"### Task 1: A\n- [ ] s\n", b"### Task 1: A\n- [x] s\n") is True

def test_content_exempt_reverse_flip_is_symmetric():
    # 归一化对称：[x] 翻回 [ ] 同样豁免
    assert E(b"- [x] s\n", b"- [ ] s\n") is True

def test_content_exempt_uppercase_marker():
    assert E(b"- [ ] s\n", b"- [X] s\n") is True

def test_content_exempt_multi_line_partial_flip():
    before = b"### Task 1: A\n- [ ] a\n- [ ] b\n### Task 2: B\n- [ ] c\n"
    after  = b"### Task 1: A\n- [x] a\n- [ ] b\n### Task 2: B\n- [x] c\n"
    assert E(before, after) is True

def test_content_exempt_preserves_indent_and_spacing():
    # 归一化只替换标记本身：缩进、标记后空白、行内其余字符一律不触碰。
    # 两版缩进不同（其余全同）⇒ 必须失鲜——若归一化顺手 strip 了空白就会假绿。
    assert E(b"  - [ ] s\n", b"    - [x] s\n") is False
    # 反向：缩进一致时，带缩进的勾选行照样能豁免（不是靠「有缩进就拒」蒙对的）
    assert E(b"  - [ ] s\n", b"  - [x] s\n") is True


# ── ⑦b 负例：勾选框以外的一切差异 ───────────────────────────────────────

def test_content_stale_on_fenced_code_block_flip():
    # fence 内的 `- [ ]` 是代码/示例，不是任务状态 ⇒ 不参与归一化 ⇒ 失鲜
    before = b"# T\n\n```\n- [ ] sample\n```\n"
    after  = b"# T\n\n```\n- [x] sample\n```\n"
    assert E(before, after) is False

def test_content_stale_on_table_and_inline_code_literals():
    # 表格单元格 / 行内反引号里的标记：非行首 task marker ⇒ 不归一化 ⇒ 失鲜
    assert E(b"| a | [ ] |\n", b"| a | [x] |\n") is False
    assert E(b"\xe8\xaf\xb4\xe6\x98\x8e `[ ]` \xe6\xa0\xbc\xe5\xbc\x8f\n",
             b"\xe8\xaf\xb4\xe6\x98\x8e `[x]` \xe6\xa0\xbc\xe5\xbc\x8f\n") is False

def test_content_stale_on_prose_literal_marker():
    assert E(b"before [ ] after\n", b"before [x] after\n") is False

def test_content_stale_when_second_marker_on_same_line_flips_back():
    # 🔴 行首锚定的判别性构造：行首 task marker 正向翻、同行文档字面量反向翻。
    # 若归一化改成「全行替换所有标记」，两版会被抹成同一串 ⇒ 假绿放行。
    before = b"- [ ] \xe5\x86\x99 `[x]` \xe5\x88\xb0\xe6\x96\x87\xe6\xa1\xa3\n"
    after  = b"- [x] \xe5\x86\x99 `[ ]` \xe5\x88\xb0\xe6\x96\x87\xe6\xa1\xa3\n"
    assert E(before, after) is False

def test_content_stale_on_pure_line_reorder():
    # 🔴 零字符改动的纯行重排：LCS/difflib 下删除行与插入行逐字节相同 ⇒ 会被判等值。
    # 判据 MUST 按行号位置对齐比较。
    before = b"- [ ] a\n- [x] b\n"
    after  = b"- [x] b\n- [ ] a\n"
    assert sorted(before.split(b"\n")) == sorted(after.split(b"\n"))   # 前提：多重集相同
    assert E(before, after) is False

def test_content_stale_on_flip_plus_same_line_wording():
    assert E(b"- [ ] \xe5\x86\x99\xe6\x96\x87\xe6\xa1\xa3\n",
             b"- [x] \xe5\x86\x99\xe6\x96\x87\xe6\xa1\xa3\xef\xbc\x88\xe6\x94\xb9\xef\xbc\x89\n") is False

def test_content_stale_on_flip_plus_task_section_added():
    before = b"### Task 1: A\n- [ ] a\n"
    after  = b"### Task 1: A\n- [x] a\n### Task 2: B\n- [ ] b\n"
    assert E(before, after) is False

def test_content_stale_on_flip_plus_task_section_removed():
    before = b"### Task 1: A\n- [ ] a\n### Task 2: B\n- [ ] b\n"
    after  = b"### Task 1: A\n- [x] a\n"
    assert E(before, after) is False

def test_content_stale_on_whitespace_only_change():
    assert E(b"- [ ] s\n", b"- [ ]  s\n") is False
    assert E(b"### Task 1: A\n", b"###  Task 1: A\n") is False

def test_content_stale_on_crlf_and_trailing_newline_and_edge_whitespace():
    assert E(b"- [ ] s\n", b"- [ ] s\r\n") is False        # 行尾
    assert E(b"- [ ] s\n", b"- [ ] s") is False            # 末尾换行删除
    assert E(b"- [ ] s\n", b"- [ ] s\n\n") is False        # 末尾换行新增
    assert E(b"- [ ] s\n", b"  - [ ] s\n   ") is False     # 首尾空白

def test_content_stale_on_line_count_change_alone():
    assert E(b"- [ ] a\n- [ ] b\n", b"- [ ] a\n") is False

def test_content_exempt_conservative_on_unbalanced_fence():
    # 围栏未闭合 ⇒ 「哪些行在 fence 内」不可信 ⇒ 保守判失鲜（同 _line_scoped_hits 口径）
    assert E(b"```\n- [ ] s\n", b"```\n- [x] s\n") is False


# ── ⑦c 端到端：豁免只在监视集恰为 {tasks.md} 时成立 ─────────────────────

def test_e2e_flip_plus_design_edit_still_stale(repo):
    # 同一提交既纯勾选 tasks.md、又改 design.md ⇒ 照判失鲜（豁免资格三连之一）
    d, _ = _seed_tasks(repo, b"### Task 1: A\n- [ ] s\n")
    _reanchor(repo, d)
    _write_tasks(repo, b"### Task 1: A\n- [x] s\n")
    (d / "design.md").write_text("# design changed\n", encoding="utf-8")
    commit_all(repo, "docs: 勾选 + 改设计")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"

def test_e2e_tasks_wording_change_still_stale(repo):
    # 勾选框以外的 tasks.md 改动（措辞）⇒ 照判失鲜
    d, _ = _seed_tasks(repo, b"### Task 1: A\n- [ ] s\n")
    _reanchor(repo, d)
    _write_tasks(repo, b"### Task 1: A\n- [ ] s2\n")
    commit_all(repo, "docs: 改任务措辞")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"

def test_e2e_br7_impl_review_subject_exemption_intact(repo):
    # BR-7 精确式 subject 豁免逐字不受本票影响：改的是 design.md（内容豁免够不着）
    d = approved_change(repo, plan=PLAN2)
    (d / "design.md").write_text("v1\n", encoding="utf-8")
    commit_all(repo, "checkpoint(impl-review): 收尾修订")
    _, js, _h = run_gate(repo)
    assert js["verdict"] != "REFUSE_START"


# ══════════════════════════════════════════════════════════════════════════
# [fix1 Important-1] 勾选框归一化的 fence 口径：`~~~` / 四 backtick 围栏
#
# 旧口径只认 ```：`~~~` 块内 task-list 形状行的**实质改动**被当成块外普通勾选翻转
# ⇒ 豁免误开（fail-open，放行未批准的设计改动）。修法 = 四个 fence 追踪点收敛到
# 单一源 fence_delim/FenceTracker，口径按 CommonMark 有界词法写全。
# ══════════════════════════════════════════════════════════════════════════

def test_content_stale_on_tilde_fenced_code_block_flip():
    # 🔴 Important-1 复现钉：删掉 `~~~` 支持 ⇒ 本例转红（返回 True = 假阳放行）
    assert E(b"~~~\n- [ ] s\n~~~\n", b"~~~\n- [x] s\n~~~\n") is False

def test_content_stale_on_four_backtick_fenced_flip():
    assert E(b"````\n- [ ] s\n````\n", b"````\n- [x] s\n````\n") is False

def test_content_stale_on_tilde_fence_with_info_string():
    assert E(b"~~~python\n- [ ] s\n~~~\n", b"~~~python\n- [x] s\n~~~\n") is False

def test_content_exempt_conservative_on_unbalanced_tilde_fence():
    # `~~~` 未闭合 ⇒ 保守判失鲜（同 ``` 口径）
    assert E(b"~~~\n- [ ] s\n", b"~~~\n- [x] s\n") is False

def test_content_exempt_conservative_when_cross_type_fence_cannot_close():
    # 异种围栏关不掉：~~~ 开、``` 关不上 ⇒ EOF 仍在块内 ⇒ 保守
    assert _sg._normalize_checkbox_lines(b"~~~\n- [ ] s\n```\n") is None

def test_content_exempt_conservative_when_shorter_fence_cannot_close():
    # 闭合符须 ≥ 开启符长度：``` 关不掉 ```` 开的块
    assert _sg._normalize_checkbox_lines(b"````\n- [ ] s\n```\n") is None

def test_normalize_still_works_outside_tilde_fence():
    # 反向证：`~~~` 块外的真勾选行照常归一化（不是靠「见 ~ 就全拒」蒙对的）
    assert E(b"~~~\ncode\n~~~\n- [ ] s\n", b"~~~\ncode\n~~~\n- [x] s\n") is True


# ── [fix1 Important-2] CHECKBOX_RE / CHECKBOX_BYTES_RE 单一源机械守 ──────────

def test_checkbox_re_bytes_derived_from_single_source():
    # 把「口径同源」从注释变成门：手抄一份字节副本并改口径 ⇒ 本例转红
    assert _sg.CHECKBOX_BYTES_RE.pattern == _sg.CHECKBOX_RE.pattern.encode()
    assert _sg.CHECKBOX_RE.pattern == _sg.CHECKBOX_RE_PATTERN

def test_checkbox_str_vs_bytes_nbsp_divergence_is_conservative():
    # 注释订正的机械锚：`\s` 在 str 模式认 Unicode 空白、bytes 模式只认 ASCII。
    # NBSP 缩进行 ⇒ str 版认、bytes 版不认 ⇒ 该行不被归一化 ⇒ 判失鲜（保守方向）。
    nbsp = " - [ ] s"
    assert _sg.CHECKBOX_RE.match(nbsp) is not None
    assert _sg.CHECKBOX_BYTES_RE.match(nbsp.encode("utf-8")) is None
    assert _sg.CHECKBOX_RE.match("\t- [ ] s") is not None
    assert _sg.CHECKBOX_BYTES_RE.match(b"\t- [ ] s") is not None
    assert E(" - [ ] s\n".encode(), " - [x] s\n".encode()) is False


# ══════════════════════════════════════════════════════════════════════════
# [fix-design-gate-freshness-proxy Task3] 两条豁免通道的优先级唯一解（SW-1）
#
# 通道 A（subject 精确式，BR-7）：subject == "checkpoint(impl-review)" 或以
#   "checkpoint(impl-review):" 起首 ⇒ **在读取任何 blob 之前**短路豁免。
# 通道 B（内容判据，Task2）：其余任何 subject——包括 BR-7 要拒的变体形态、空
#   subject、普通 subject——都可凭「勾选框归一化后逐行等值」获得豁免。
#
# 🔴 BR-7 的语义 = 「变体**不因 subject** 获豁免」，**不是**「变体必然失鲜」。
#   变体 subject + 纯勾选内容走通道 B 豁免是正确的：豁免面取自内容本身，
#   不取自被监管方书写的 subject（∴ 伪造 subject 拿不到任何额外豁免面）。
#   既有 BR-7 回归用例（evil 尾串 / impl-review-fix 变体）改的都是 design.md
#   ——落在通道 B 的适用面之外（帧内监视路径集 ≠ {tasks.md}），故不受影响。
# ══════════════════════════════════════════════════════════════════════════

_ANCHOR_REL = BASE + "spec-review-report.md"

_PURE_FLIP = b"### Task 1: A\n- [x] s\n"          # 纯勾选翻转
_SEMANTIC = b"### Task 1: A retitled\n- [ ] s\n"  # 勾选框以外的语义改动（标题措辞）


def _stale_after(repo, subject, after, empty_subject=False):
    """建 change → 重锚 → 以给定 subject 提交 tasks.md 的给定新内容 → 返回是否失鲜。

    帧内落在 design 监视集的路径恰为 {tasks.md}（另带一份源码，贴 `git add -A`
    的真实形态），故通道 A 不命中时判定完全由通道 B 的内容判据决定。
    """
    d, _ = _seed_tasks(repo, b"### Task 1: A\n- [ ] s\n")
    _reanchor(repo, d)
    _write_tasks(repo, after)
    (repo / "src.py").write_text("# impl\n", encoding="utf-8")
    if empty_subject:
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "--allow-empty-message", "-m", "")
    else:
        commit_all(repo, subject)
    stale, _fresh = _sg.is_stale(repo, _ANCHOR_REL, "design", "demo")
    return stale


# ── ⑧a 真值表 8 格：{精确 / 变体 / 空 / 普通} subject × {纯勾选 / 语义改动} ──

def test_tt_exact_subject_pure_flip_exempt(repo):
    assert _stale_after(repo, "checkpoint(impl-review): 勾选回填", _PURE_FLIP) is False

def test_tt_exact_subject_semantic_exempt_by_subject(repo):
    # 通道 A 独有的格：内容是语义改动，仍豁免——BR-7 既有语义，本 change 不动它。
    assert _stale_after(repo, "checkpoint(impl-review)", _SEMANTIC) is False

def test_tt_variant_subject_pure_flip_exempt_via_content(repo):
    # 🔴 判别性最强的一格：变体 subject 拿不到通道 A，但内容是纯勾选 ⇒ 经通道 B 豁免。
    assert _stale_after(repo, "checkpoint(impl-review)evil", _PURE_FLIP) is False

def test_tt_variant_subject_semantic_stale(repo):
    # 变体 subject + 语义改动 ⇒ 两条通道都不给 ⇒ 失鲜（BR-7 的杀伤面完好）。
    assert _stale_after(repo, "checkpoint(impl-review)evil", _SEMANTIC) is True

def test_tt_empty_subject_pure_flip_exempt_via_content(repo):
    assert _stale_after(repo, None, _PURE_FLIP, empty_subject=True) is False

def test_tt_empty_subject_semantic_stale(repo):
    assert _stale_after(repo, None, _SEMANTIC, empty_subject=True) is True

def test_tt_plain_subject_pure_flip_exempt_via_content(repo):
    assert _stale_after(repo, "docs: 勾选回填", _PURE_FLIP) is False

def test_tt_plain_subject_semantic_stale(repo):
    assert _stale_after(repo, "docs: 手动改设计", _SEMANTIC) is True


# ── ⑧b 短路次序：精确 subject MUST 在读取任何 blob **之前**判定 ─────────────

def test_exact_subject_short_circuits_before_any_blob_read(repo, monkeypatch):
    """通道 A 短路发生在读取之前——把 blob_pair 替身为「一调用即爆」，精确 subject
    帧仍须判不失鲜。

    这不只是效率：短路保证精确 subject 帧的判定**不受任何读取失败 / 形态不合格的
    影响**。若次序颠倒（先读内容再看 subject），本例会在 blob_pair 处抛异常而红。
    """
    calls = []

    def exploding_blob_pair(*a, **k):
        calls.append(a)
        raise AssertionError("blob_pair 在精确 subject 短路之前被调用（次序错）")

    monkeypatch.setattr(_sg, "blob_pair", exploding_blob_pair)
    d, _ = _seed_tasks(repo, b"### Task 1: A\n- [ ] s\n")
    _reanchor(repo, d)
    _write_tasks(repo, _SEMANTIC)
    commit_all(repo, "checkpoint(impl-review): 收尾修订")
    assert _sg.is_stale(repo, _ANCHOR_REL, "design", "demo") == (False, "fresh")
    assert calls == []                      # 一次都没读


def test_non_exact_subject_does_reach_blob_read(repo, monkeypatch):
    """反向证：上例的绿不是靠「blob_pair 从来不被调用」蒙对的——非精确 subject 下
    它**必须**被调到（否则短路用例失去判别力，变成恒真断言）。"""
    calls = []
    real = _sg.blob_pair
    monkeypatch.setattr(_sg, "blob_pair",
                        lambda *a, **k: (calls.append(a), real(*a, **k))[1])
    d, _ = _seed_tasks(repo, b"### Task 1: A\n- [ ] s\n")
    _reanchor(repo, d)
    _write_tasks(repo, _PURE_FLIP)
    commit_all(repo, "docs: 勾选回填")
    assert _sg.is_stale(repo, _ANCHOR_REL, "design", "demo") == (False, "fresh")
    assert len(calls) == 1


# ── ⑧c 豁免面不由被监管方书写的声明单独决定 ──────────────────────────────

@pytest.mark.parametrize("subject", [
    "docs: 随手一提交",
    "checkpoint(impl-review)evil",           # 伪装成豁免形态（BR-7 要拒的尾串垃圾）
    "checkpoint(impl-review-fix): 改设计",   # 另一种伪装变体
    "feat!: 完全无关的 subject",
])
def test_content_channel_verdict_independent_of_subject(repo, subject):
    """同一份语义改动，subject 换成任意花样（含伪装成豁免形态的变体）⇒ 判定恒为失鲜。

    被监管方能书写的只有 subject；通道 B 的判据取自内容本身，故伪装拿不到任何
    额外豁免面。与 ⑧a 的 `*_pure_flip_exempt_via_content` 三格互为正反两面。"""
    assert _stale_after(repo, subject, _SEMANTIC) is True


def test_content_criterion_takes_only_content(repo):
    """机械锚：内容判据的入参只有前后两版内容——无 subject、无路径、无文件存在性。

    将来若有人往判据里塞 subject / 路径（把豁免面交回给被监管方书写的声明），本例转红。"""
    import inspect
    assert list(inspect.signature(_sg._tasks_content_exempt).parameters) == ["before", "after"]


# ══════════════════════════════════════════════════════════════════════════
# [fix-design-gate-freshness-proxy Task4] 撞门者被告知撞在哪、下一步做什么（SW-1）
#
# 失鲜 REFUSE_START 须携带**结构化**触发点（短 sha / subject / 触发路径 / 分类
# 原因），人读与机读两侧同源同步。**纯诊断**：不参与判定、不改退出码、不改任何
# 既有判定结论——本节所有断言都只看输出内容，verdict/exit code 由前面各节锁死。
#
# 🔴 默认处置只推荐「重跑设计门」一条。`checkpoint(impl-review)` MUST NOT 出现在
#   默认处置指引里：它是显式越权口，且**对撞门者根本无效**——豁免逐提交求值，已经
#   触发失鲜的那个提交不会因为**后补**一个 `checkpoint(impl-review)` 提交而被追溯
#   赦免。写进指引 = 教人去做一件不起作用的事。
# ══════════════════════════════════════════════════════════════════════════

def _stale_gate(repo, subject, mutate):
    """建 change → 重锚 → mutate(change_dir) 改动 → 以 subject 提交 → 跑 gate。

    返回 run_gate 的 (code, js, human)。同帧另带一份源码，贴 `git add -A` 的真实形态。
    """
    d, _ = _seed_tasks(repo, b"### Task 1: A\n- [ ] s\n")
    _reanchor(repo, d)
    mutate(d)
    (repo / "src.py").write_text("# impl\n", encoding="utf-8")
    commit_all(repo, subject)
    return run_gate(repo)


def _mutate_design(d):
    (d / "design.md").write_text("v2 手动改的设计\n", encoding="utf-8")


# ── ⑨a 四条分类原因各自可达，且 sha/subject/路径逐字对得上 ────────────────

def test_stale_trigger_category_mixed_paths(repo):
    subject = "docs: 手动改设计"
    code, js, human = _stale_gate(repo, subject, _mutate_design)
    assert code == 3 and js["verdict"] == "REFUSE_START"
    t = js["stale_trigger"]
    assert t["category"] == "mixed-paths"
    assert t["subject"] == subject
    assert t["sha"] == _head(repo)[:7]
    assert "design.md" in t["paths"] and "tasks.md" not in t["paths"]
    # 人读侧同源：短 sha / subject / 路径三者都在
    assert t["sha"] in human and subject in human and "design.md" in human


def test_stale_trigger_category_content_changed(repo):
    # 帧内监视路径恰为 {tasks.md}，但改的是勾选框以外的内容 ⇒ 内容判据不给豁免
    subject = "docs: 改 task 标题"
    code, js, _ = _stale_gate(repo, subject, lambda d: _write_tasks(repo, _SEMANTIC))
    assert code == 3 and js["verdict"] == "REFUSE_START"
    t = js["stale_trigger"]
    assert t["category"] == "content-changed"
    assert t["paths"] == ["tasks.md"] and t["subject"] == subject


def test_stale_trigger_category_shape_unfit(repo):
    # 删除 tasks.md：形态闸门（非普通内容修改）先于内容判据拦下
    subject = "chore: 删掉 tasks.md"
    code, js, _ = _stale_gate(repo, subject,
                              lambda d: (d / "tasks.md").unlink())
    assert code == 3 and js["verdict"] == "REFUSE_START"
    assert js["stale_trigger"]["category"] == "shape-unfit"


def test_stale_trigger_category_blob_unreadable(repo, monkeypatch):
    # 形态合格（普通内容修改）但前后版 blob 读取失败 ⇒ 与 shape-unfit 分开归类
    d, _ = _seed_tasks(repo, b"### Task 1: A\n- [ ] s\n")
    _reanchor(repo, d)
    _write_tasks(repo, b"### Task 1: A\n- [x] s\n")
    commit_all(repo, "docs: 勾选回填")
    monkeypatch.setattr(_sg, "run_git_bytes", lambda root, *a: (128, b""))
    res = _sg.is_stale(repo, _ANCHOR_REL, "design", "demo")
    assert res == (True, "stale")
    assert res.trigger["category"] == "blob-unreadable"
    assert res.trigger["paths"] == ["tasks.md"]


# ── ⑨b 默认处置指引：只推荐重跑设计门，不提 checkpoint(impl-review) ────────

def test_default_disposition_recommends_rerun_design_gate_only(repo):
    _, js, human = _stale_gate(repo, "docs: 手动改设计", _mutate_design)
    assert "sdflow-spec-review" in js["reason"]          # 唯一推荐动作
    # 🔴 硬要求：显式越权口 MUST NOT 出现在默认处置指引里（对撞门者无效，教人白做）
    assert "checkpoint(impl-review)" not in js["reason"]
    assert "checkpoint(impl-review)" not in human


# ── ⑨c 纯诊断：不改任何既有判定结论，且 code 域取值逐字不变 ────────────────

def test_code_domain_freshness_string_unchanged_and_no_trigger(repo):
    """`code` 域的新鲜度取值字符串逐字不变（下游读点依赖它），且不携触发点。"""
    tail_ok(repo)
    touch_code(repo)
    _, js, _ = run_gate(repo)
    assert js["verdict"] == "RERUN_STALE" and js["freshness"] == "stale"
    assert "stale_trigger" not in js
    res = _sg.is_stale(repo, BASE + "verify-report.md", "code", "demo")
    assert res == (True, "stale") and res.trigger is None


def test_is_stale_result_stays_two_tuple_compatible(repo):
    """结构化返回 MUST 保持 (stale, freshness) 的二元组形状——既有调用点与用例
    都按二元组解包 / 等值比较，触发点是**附加**诊断物，不改判定值的形状。"""
    d, _ = _seed_tasks(repo)
    _reanchor(repo, d)
    res = _sg.is_stale(repo, _ANCHOR_REL, "design", "demo")
    stale, freshness = res                              # 解包仍是二元
    assert (stale, freshness) == (False, "fresh") and res == (False, "fresh")
    assert res.stale is False and res.freshness == "fresh" and res.trigger is None


# ══════════════════════════════════════════════════════════════════════════
# [impl-review-fix F1/F2/F3] 帧枚举面 fail-open 三洞 + 枚举失败 + 归一化第三支
#
# 🔴 本节全部走 **is_stale / run_gate 端到端**（不直调内部函数、不打替身）——
#   三个洞的共同特征就是「内部函数各自正确，但生产路径根本走不到它们」，
#   直调内部函数的用例对它们**结构性免疫**（原 rename 用例只直调 blob_pair 即假绿）。
# ══════════════════════════════════════════════════════════════════════════

def _merge_amended(repo, mutate, msg="merge side"):
    """造一个 merge 提交，其树由 mutate 决定（两个 parent 各自都没有这份内容）。

    `git merge --no-ff` 后 `git commit --amend -a` 保留双 parent，是构造 evil-merge
    的最短确定性路径（不依赖冲突解决的交互）。
    """
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


# ── F1-a evil-merge：改动只存在于 merge 自身 resolve 出的树 ─────────────────

def test_evil_merge_design_edit_is_stale(repo):
    # 🔴 旧协议 `git log --name-only` 对 merge 提交**不输出任何文件** ⇒ subs 为空 ⇒
    #   `continue` 跳过整帧 ⇒ design 域整体判 fresh = 放行未批准的设计改动。
    d, _ = _seed_tasks(repo)
    (d / "design.md").write_text("v1\n", encoding="utf-8")
    commit_all(repo, "seed design")
    _reanchor(repo, d)
    _merge_amended(repo, lambda: (d / "design.md").write_text("evil v2\n", encoding="utf-8"))
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"
    assert js["stale_trigger"]["category"] == "mixed-paths"
    assert "design.md" in js["stale_trigger"]["paths"]


def test_evil_merge_tasks_semantic_edit_is_stale(repo):
    # 同一个洞的 tasks.md 分支：merge 自身把 task 标题改了（非勾选框）⇒ 必须失鲜。
    d, _ = _seed_tasks(repo, b"### Task 1: A\n- [ ] s\n")
    _reanchor(repo, d)
    _merge_amended(repo, lambda: _write_tasks(repo, _SEMANTIC))
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"
    assert js["stale_trigger"]["category"] == "content-changed"


def test_merge_frame_pure_flip_is_exempt_end_to_end(repo):
    # 反向证（判别性）：merge 自身只做**纯勾选框翻转**、对**每个 parent** 都成立
    # ⇒ 豁免真能在 merge 上生效，不是靠「见 merge 就一刀切拒绝」蒙对上一条。
    # 同时这是 Task1 逐 parent 校验在**生产路径**上可达的端到端证据。
    d, _ = _seed_tasks(repo, b"### Task 1: A\n- [ ] s\n")
    _reanchor(repo, d)
    _merge_amended(repo, lambda: _write_tasks(repo, b"### Task 1: A\n- [x] s\n"))
    code, js, _h = run_gate(repo)
    assert code == 0 and js["verdict"] == "CONTINUE_IMPL"


def test_merge_frame_is_actually_enumerated(repo):
    # 机械守枚举协议本身：merge 提交的触及路径**非空**（旧 --name-only 恒空）。
    d, _ = _seed_tasks(repo)
    _merge_amended(repo, lambda: (d / "design.md").write_text("evil\n", encoding="utf-8"))
    paths = _sg.frame_touched_paths(repo, _head(repo))
    assert paths is not None and BASE + "design.md" in paths
    # 对照：旧协议下同一提交的文件列表为空——这就是洞本身
    assert _sg.run_git(repo, "log", "-1", "--name-only", "--format=", _head(repo)) == ""


# ── F1-b rename：源路径 MUST 进监视集（本 change 的 delta spec 明写） ───────

def test_git_mv_tasks_is_stale_end_to_end(repo):
    # 🔴 旧协议默认开 rename 检测，`git mv tasks.md x.md` **只**输出目标路径 ⇒
    #   源 tasks.md 看不到 ⇒ 跳过整帧判 fresh。既有 rename 用例只直调 blob_pair，
    #   对这个前置洞结构性免疫（假绿）。本例走端到端补上。
    d, _ = _seed_tasks(repo)
    _reanchor(repo, d)
    _git(repo, "mv", "openspec/changes/demo/tasks.md",
         "openspec/changes/demo/tasks-renamed.md")
    commit_all(repo, "chore: 迁走 tasks.md")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"
    # 源路径进了触发路径集（分类为形态不合格：改名分解成 A+D，D 非普通内容修改）
    assert js["stale_trigger"]["paths"] == ["tasks.md"]
    assert js["stale_trigger"]["category"] == "shape-unfit"


def test_frame_paths_include_rename_source(repo):
    # 机械守：--no-renames ⇒ 源路径与目标路径**都**在枚举里
    d, _ = _seed_tasks(repo)
    _git(repo, "mv", "openspec/changes/demo/tasks.md",
         "openspec/changes/demo/tasks-renamed.md")
    commit_all(repo, "rename")
    paths = _sg.frame_touched_paths(repo, _head(repo))
    assert BASE + "tasks.md" in paths and BASE + "tasks-renamed.md" in paths


# ── F1-c 路径含 Tab：文本行协议会把它拆碎/加引号，NUL 协议不会 ──────────────

def test_spec_path_with_tab_is_stale(repo):
    # 换行文件名在部分平台/工具链上不便构造，此处只做 Tab（同一个协议面：
    # 旧 --name-only 按行切 + C-quote 包裹 ⇒ startswith(base) 失配 ⇒ 逃出监视集）。
    d, _ = _seed_tasks(repo)
    _reanchor(repo, d)
    specs = d / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    (specs / "we\tird.md").write_text("delta\n", encoding="utf-8")
    commit_all(repo, "docs: 加一份带 Tab 文件名的 delta spec")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"
    assert js["stale_trigger"]["paths"] == ["specs/we\tird.md"]


def test_frame_paths_preserve_tab_unquoted(repo):
    # 机械守 -z 协议：路径原样、无 C-quote、无按行拆碎
    d, _ = _seed_tasks(repo)
    (d / "specs").mkdir(parents=True, exist_ok=True)
    (d / "specs" / "we\tird.md").write_text("x\n", encoding="utf-8")
    commit_all(repo, "tab path")
    paths = _sg.frame_touched_paths(repo, _head(repo))
    assert BASE + "specs/we\tird.md" in paths
    assert not any(p.startswith('"') for p in paths)


# ── F2 枚举失败 MUST 判失鲜（旧路径：run_git 折叠成空串 ⇒ 零帧 ⇒ fresh） ────

def test_stale_when_commit_enumeration_fails(repo, monkeypatch):
    d, _ = _seed_tasks(repo)
    _reanchor(repo, d)
    real = _sg.run_git_rc

    def fake(root, *args):
        if args[:1] == ("log",) and any(a.endswith("..HEAD") for a in args):
            return 128, ""                  # 模拟 git log 失败
        return real(root, *args)

    monkeypatch.setattr(_sg, "run_git_rc", fake)
    res = _sg.is_stale(repo, _ANCHOR_REL, "design", "demo")
    assert res == (True, "stale")
    assert res.trigger["category"] == "frame-enum-failed"


def test_stale_when_frame_path_enumeration_fails(repo, monkeypatch):
    d, _ = _seed_tasks(repo)
    _reanchor(repo, d)
    (d / "design.md").write_text("v2\n", encoding="utf-8")
    commit_all(repo, "docs: 改设计")
    monkeypatch.setattr(_sg, "frame_touched_paths", lambda root, sha: None)
    res = _sg.is_stale(repo, _ANCHOR_REL, "design", "demo")
    assert res == (True, "stale")
    assert res.trigger["category"] == "frame-enum-failed"


def test_frame_touched_paths_returns_none_on_git_failure(repo):
    assert _sg.frame_touched_paths(repo, "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef") is None


def test_frame_enum_failed_is_registered_category():
    # 分类枚举与判定分支同源：新增分支必须同步登记（否则人读侧拿不到标签）
    assert "frame-enum-failed" in _sg.STALE_CATEGORIES


# ── F3 归一化：CommonMark 缩进代码块 + HTML 注释块（第三、四支） ─────────────

def test_content_stale_on_indented_code_block_flip():
    # 🔴 四空格缩进代码块内的翻转此前被归一化 ⇒ 误判豁免（fail-open）
    before = b"# T\n\n    - [ ] sample\n"
    after = b"# T\n\n    - [x] sample\n"
    assert E(before, after) is False


def test_content_stale_on_tab_indented_code_block_flip():
    # tab 按 4 列制表位展开 ⇒ 同样落在缩进代码块口径内
    assert E(b"# T\n\n\t- [ ] s\n", b"# T\n\n\t- [x] s\n") is False


def test_content_stale_on_html_comment_block_flip():
    # 多行 HTML 注释块内的翻转 ⇒ 不归一化 ⇒ 失鲜
    before = b"# T\n\n<!--\n- [ ] s\n-->\n"
    after = b"# T\n\n<!--\n- [x] s\n-->\n"
    assert E(before, after) is False


def test_normalize_still_works_outside_indent_and_comment():
    # 反向证（判别性）：不是靠「见缩进/见注释就全拒」蒙对的——
    # 浅缩进（<4 列）与注释块**外**的真勾选行照常归一化。
    assert E(b"  - [ ] s\n", b"  - [x] s\n") is True
    assert E(b"<!-- c -->\n- [ ] s\n", b"<!-- c -->\n- [x] s\n") is True
    assert E(b"<!--\nx\n-->\n- [ ] s\n", b"<!--\nx\n-->\n- [x] s\n") is True


def test_html_comment_tracker_reports_line_start_state():
    t = _sg.HtmlCommentTracker()
    assert t.feed("<!-- open") is False        # 本行行首在注释外
    assert t.feed("- [ ] s") is True           # 已进注释
    assert t.feed("--> tail") is True          # 闭合行的行首仍在注释内
    assert t.feed("- [ ] s") is False          # 之后回到注释外


def test_indent_columns_tab_stop():
    assert _sg.indent_columns("   x") == 3 and _sg.is_indented_code_line("   x") is False
    assert _sg.indent_columns("    x") == 4 and _sg.is_indented_code_line("    x") is True
    assert _sg.indent_columns("\tx") == 4 and _sg.is_indented_code_line(b"\tx", is_bytes=True) is True


def test_fence_wins_over_comment_and_indent():
    # 围栏内的 `<!--` 不开注释、围栏内缩进行不另判——三者优先级固定，不互相污染
    assert E(b"```\n<!--\n```\n- [ ] s\n", b"```\n<!--\n```\n- [x] s\n") is True


# ── [impl-review-fix F4] 嵌套示例围栏：gate 侧回归（姊妹用例在 sdflow-implement） ──

def test_nested_example_fence_hides_pseudo_task_and_checkboxes():
    # 外层 ````markdown 内嵌 ```text 示例：内层 ``` 长度 3 < 开启符 4 且带 info string，
    # 关不掉外层 ⇒ 整块内容（伪 `### Task 9:` + 两个伪复选框）一律不可见。
    fx = Path(__file__).resolve().parent / "fixtures" / "tickets_plan_nested_fence.md"
    ids, boxes = _sg._parse_plan(fx.read_text(encoding="utf-8"))[:2]
    assert set(ids) == {"1", "2"}                       # 无伪 Task 9
    assert boxes["1"] == [True] and boxes["2"] == [False]   # 伪复选框未混入
