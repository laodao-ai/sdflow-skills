import subprocess, sys
from pathlib import Path

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


# ── ⑥ 本票不变量：能力就位，但对外行为逐字未变（一律照判失鲜）─────────────

def test_design_frame_exempt_never_exempts_in_task1(repo):
    # 最贴近目标态的形态：纯勾选翻转、帧内监视路径恰为 {tasks.md}
    # —— Task1 仍 MUST 返回 False（判据未接入）
    _, _ = _seed_tasks(repo, b"### Task 1: A\n- [ ] s\n")
    _write_tasks(repo, b"### Task 1: A\n- [x] s\n")
    commit_all(repo, "flip checkbox only")
    assert _sg.design_frame_exempt(
        repo, _head(repo), [TASKS_REL, "src.py"], BASE) is False

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

def test_tasks_only_checkbox_flip_still_stale(repo):
    # 对外可观察行为不变：只翻勾选框、只触及 tasks.md ⇒ 仍 REFUSE_START
    d, _ = _seed_tasks(repo, b"### Task 1: A\n- [ ] s\n")
    _write_tasks(repo, b"### Task 1: A\n- [x] s\n")
    commit_all(repo, "docs: 勾选回填")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"

def test_tasks_flip_plus_source_code_still_stale(repo):
    # `git add -A` 打包形态（勾选 tasks.md + 仓库别处源码）⇒ Task1 仍照判失鲜
    _seed_tasks(repo, b"### Task 1: A\n- [ ] s\n")
    _write_tasks(repo, b"### Task 1: A\n- [x] s\n")
    (repo / "src.py").write_text("# impl\n", encoding="utf-8")
    commit_all(repo, "docs: 勾选回填 + 实现")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"

def test_merge_commit_touching_tasks_still_stale(repo):
    _seed_tasks(repo, b"### Task 1: A\n- [ ] s\n")
    _git(repo, "checkout", "-q", "-b", "side")
    _write_tasks(repo, b"### Task 1: A\n- [x] s\n")
    commit_all(repo, "side flip")
    _git(repo, "checkout", "-q", "main")
    (repo / "m.txt").write_text("m\n", encoding="utf-8")
    commit_all(repo, "main edit")
    _git(repo, "merge", "--no-ff", "-q", "-m", "merge side", "side")
    code, js, _h = run_gate(repo)
    assert code == 3 and js["verdict"] == "REFUSE_START"

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
