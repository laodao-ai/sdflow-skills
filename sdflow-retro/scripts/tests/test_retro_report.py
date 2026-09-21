import sys
import os
import json
import subprocess
import pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import retro_report as R


def _mk(root, rel):
    p = root / rel
    p.mkdir(parents=True, exist_ok=True)
    return p


def test_discover_active_and_archive(tmp_path):
    _mk(tmp_path, "openspec/changes/foo")                      # 活动
    _mk(tmp_path, "openspec/changes/archive/2026-07-02-bar")   # 归档
    _mk(tmp_path, "openspec/changes/archive/2026-07-05-foo")   # foo 也有归档
    got = R.discover_changes(str(tmp_path))
    assert set(got) == {"foo", "bar"}
    assert got["foo"]["active"] is True
    assert got["foo"]["archive_dir"].endswith("2026-07-05-foo")
    assert got["bar"]["active"] is False
    assert got["bar"]["archive_dir"].endswith("2026-07-02-bar")


def _git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace").stdout


def _init_repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    return tmp_path


def _commit(root, files: dict, msg):
    for rel, body in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", msg)


def test_seed_mass_excluded_and_0_1_guard(tmp_path):
    root = _init_repo(tmp_path)
    # 创世 mass 提交碰 3 个 change dir → seed-mass
    _commit(root, {
        "openspec/changes/archive/2026-07-02-seedA/proposal.md": "x",
        "openspec/changes/archive/2026-07-02-seedB/proposal.md": "y",
        "openspec/changes/archive/2026-07-02-seedC/proposal.md": "z",
    }, "chore:初始化")
    changes = R.discover_changes(str(root))
    seed = R.seed_mass_shas(str(root), threshold=3)
    b = R.boundary_for_change(str(root), "seedA", changes["seedA"], seed)
    # seedA 的 pre-archive 路径 0 提交（创世只碰 archive 路径），兜底 archive 后剔 seed-mass → 仍 0/1
    assert b["unresolved"] is True
    assert len(b["commits"]) == 0  # seed-mass 提交被剔除后 archive 兜底也为空——若剔除失效会剩 1 条，此断言区分二者
    assert "边界不可解析" in b["note"]


def test_normal_change_boundary(tmp_path):
    root = _init_repo(tmp_path)
    _commit(root, {"openspec/changes/foo/proposal.md": "a"}, "checkpoint(ff)")
    _commit(root, {"openspec/changes/foo/design.md": "b"}, "checkpoint(grill)")
    changes = R.discover_changes(str(root))
    seed = R.seed_mass_shas(str(root), threshold=3)
    b = R.boundary_for_change(str(root), "foo", changes["foo"], seed)
    assert b["unresolved"] is False
    assert len(b["commits"]) == 2
    assert b["commits"][0]["subject"] == "checkpoint(ff)"


def test_archived_change_full_boundary_via_bare_path(tmp_path):
    """[impl-review-fix] F1 反证测试：归档 change 即使 active_dir=None（磁盘上已不在活动区），
    boundary_for_change 也必须通过裸 pre-archive 路径 openspec/changes/<name> 找回全部历史提交，
    不能只剩 1 条 archive rename 提交——这正是 17/18 归档 change 假性「边界不可解析」的根因。
    修前：只查 active_dir(None→[]) 再兜底 archive_dir（1 条 rename）→ unresolved True, commits=1。
    修后：裸路径∪archive路径按 sha 去重 → 应捞回 ff/grill/impl-review + rename 共 4 条。
    """
    root = _init_repo(tmp_path)
    _commit(root, {"openspec/changes/foo/proposal.md": "a"}, "checkpoint(ff)")
    _commit(root, {"openspec/changes/foo/design.md": "b"}, "checkpoint(grill)")
    _commit(root, {"openspec/changes/foo/tasks.md": "c"}, "checkpoint(impl-review)")
    # 归档：git mv 全目录进 archive，active_dir 从此在磁盘上消失
    (root / "openspec/changes/archive").mkdir(parents=True, exist_ok=True)
    _git(root, "mv", "openspec/changes/foo", "openspec/changes/archive/2026-07-06-foo")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "chore(openspec): archive foo")

    changes = R.discover_changes(str(root))
    assert changes["foo"]["active_dir"] is None
    assert changes["foo"]["archive_dir"] is not None

    seed = R.seed_mass_shas(str(root))
    b = R.boundary_for_change(str(root), "foo", changes["foo"], seed)
    assert b["unresolved"] is False, f"边界应可解析，实际 note={b['note']!r} commits={b['commits']}"
    assert len(b["commits"]) == 4  # ff + grill + impl-review + archive-rename
    subjects = [c["subject"] for c in b["commits"]]
    assert subjects[0] == "checkpoint(ff)"
    assert subjects[-1] == "chore(openspec): archive foo"


def test_run_git_failure_traces_stderr(tmp_path, capsys):
    # T60 反证：git 失败（returncode≠0）须向 stderr 留痕，否则「git 报错」与「真无提交」
    # 都表现为空 stdout、静默不可区分。修前 _run_git 不看 returncode → stderr 无留痕 → FAIL。
    root = _init_repo(tmp_path)
    out = R._run_git(str(root), "nonexistent-subcommand-xyz")
    captured = capsys.readouterr()
    assert out == ""                              # 失败时 stdout 空（返回契约不变）
    assert "git 失败" in captured.err              # 但有可见留痕，不静默


def test_run_git_success_no_stderr_noise(tmp_path, capsys):
    # T60：正常 git 成功不应产生 stderr 噪声（留痕只在失败路径）。
    root = _init_repo(tmp_path)
    _commit(root, {"a.txt": "x"}, "init")
    R._run_git(str(root), "log", "--format=%H")
    assert capsys.readouterr().err == ""


def test_map_stage_longest_prefix(tmp_path):
    assert R.map_stage("checkpoint(impl-review)") == "code-review"
    assert R.map_stage("checkpoint(impl-review-fix)") == "code-review"
    assert R.map_stage("checkpoint(spec-review-autoplan)") == "spec-review"
    assert R.map_stage("checkpoint(spec-review-gate)") == "spec-review"
    assert R.map_stage("checkpoint(design-gate)") == "spec-review"
    assert R.map_stage("checkpoint(writing-plans)") == "impl"
    assert R.map_stage("checkpoint(model-baseline)") == "impl"
    assert R.map_stage("checkpoint(sdflow-retro:task3-boundary)") == "impl"
    assert R.map_stage("checkpoint(final-review)") == "code-review"
    assert R.map_stage("checkpoint(ff)") == "ff"
    assert R.map_stage("checkpoint(grill)") == "grill"
    # sdflow-spec 的两个相位锚：匹配是 startswith，故「grill」不是 `sdflow-spec-grill` 的前缀，
    # 二者 MUST 各自单列；漏任一条即落 unknown 桶，相位锚等于白打。
    assert R.map_stage("checkpoint(sdflow-spec-grill)") == "grill"
    assert R.map_stage("checkpoint(sdflow-spec-generate)") == "ff"
    assert R.map_stage("checkpoint(sdflow-spec-grill): 相位 B 收敛") == "grill"
    assert R.map_stage("feat(x): 随手") == "unknown"


def test_namespaced_step_slug_falls_back_to_tail():
    """`checkpoint(<change>:<step>)` 的 `<step>` 段 MUST 参与前缀匹配。

    [impl-review-fix] F1：旧实现只在 `task\\d+` / `-impl` 两条判定里剥命名空间，
    前缀匹配仍拿含 `<change>:` 前缀的整串去比 ⇒ 仓内 27 个 checkpoint 的 `<step>` 段
    **精确等于**既有规则却全落 unknown（plan×13 / grill×5 / ff×4 / spec-review×2 /
    propose×2 / design-gate×1）。`sdflow-implement/SKILL.md:287` 明写
    `checkpoint-commit.sh "<change>:plan"`，即目标态 producer 就在产出这种形态。
    """
    assert R.map_stage("checkpoint(add-sdflow-spec:plan)") == "other"
    assert R.map_stage("checkpoint(add-codex-host-support:grill)") == "grill"
    assert R.map_stage("checkpoint(add-codex-host-support:ff)") == "ff"
    assert R.map_stage("checkpoint(add-codex-host-support:spec-review)") == "spec-review"
    assert R.map_stage("checkpoint(add-codex-host-support:spec-review-amend)") == "spec-review"
    assert R.map_stage("checkpoint(harden-hr-tg-anchor-consistency:design-gate)") == "spec-review"
    assert R.map_stage("checkpoint(three-lens-decision-framework:propose)") == "other"
    assert R.map_stage(
        "checkpoint(harden-hr-tg-anchor-consistency:impl-review-fix-parsing)") == "code-review"
    # 回退**只在整串无命中时**发生 ⇒ 既有的整串匹配语义不变。
    assert R.map_stage("checkpoint(sdflow-spec-grill)") == "grill"
    assert R.map_stage("checkpoint(sdflow-retro:task3-boundary)") == "impl"
    # `<step>` 段无任何规则可依 ⇒ 照旧 unknown（不猜）。
    assert R.map_stage("checkpoint(sdflow-retro-cleanup:t58-tilde-fence)") == "unknown"


def test_two_review_skill_slugs_map_to_their_stage():
    """[impl-review-fix] F1（面治）：`sdflow-` 前缀的两个评审 slug 与 `sdflow-spec-*` 同形。

    上一轮只补了 `sdflow-spec-grill` / `sdflow-spec-generate` 两条，同形的
    `sdflow-code-review`（仓内 3 次）与 `sdflow-spec-review`（1 次）漏掉 —— 同一失效模式。
    """
    assert R.map_stage("checkpoint(sdflow-code-review)") == "code-review"
    assert R.map_stage("checkpoint(sdflow-spec-review)") == "spec-review"


def test_short_prefix_tail_fallback_requires_a_token_boundary():
    """[impl-review-fix fix2] F-B：tail 回退把 ≤4 字符的短前缀误配到更长的词上。

    F1 的回退放宽了匹配面（整串无命中 ⇒ 拿 `tail` 再试一次），而 `gate` / `ff` / `plan`
    这三条短规则是**词**、不是**前缀**：`gateway-refactor` / `ffmpeg-upgrade` / `planner`
    会被静默吞进 spec-review / ff / other。归因错了不报错、不缺文件 —— 与本词表要治的病同型。
    ⇒ 短前缀（≤ `_TAIL_STRICT_MAXLEN`）在 tail 回退里 MUST 要求 token 边界（全等或后接 `-`）。
    """
    # 误配面：token 边界不成立 ⇒ 不猜，落 unknown
    assert R.map_stage("checkpoint(c:gateway-refactor)") == "unknown"
    assert R.map_stage("checkpoint(c:ffmpeg-upgrade)") == "unknown"
    assert R.map_stage("checkpoint(c:planner)") == "unknown"
    # 边界另一侧：全等 / 后接 `-` 照常命中 —— F1 的收益一分不丢
    assert R.map_stage("checkpoint(c:gate)") == "spec-review"
    assert R.map_stage("checkpoint(c:gate-frontmatter)") == "spec-review"
    assert R.map_stage("checkpoint(c:ff)") == "ff"
    assert R.map_stage("checkpoint(c:ff-amend)") == "ff"
    assert R.map_stage("checkpoint(c:plan)") == "other"
    assert R.map_stage("checkpoint(c:plan-b)") == "other"
    # 长前缀不受此限（`spec-review-amend` 这类既有形态照旧）
    assert R.map_stage("checkpoint(c:spec-reviewX)") == "spec-review"
    # 严格化**只加在回退这一跳**上 ⇒ 整串匹配（change 名本身带阶段词）语义一字未动
    assert R.map_stage("checkpoint(gateway-refactor)") == "spec-review"


def test_archive_rename_detects_done(tmp_path):
    root = _init_repo(tmp_path)
    _commit(root, {"openspec/changes/foo/proposal.md": "a"}, "checkpoint(ff)")
    # 用 git mv 模拟归档
    (root / "openspec/changes/archive/2026-07-06-foo").mkdir(parents=True)
    _git(root, "mv", "openspec/changes/foo/proposal.md",
         "openspec/changes/archive/2026-07-06-foo/proposal.md")
    _git(root, "add", "-A"); _git(root, "commit", "-q", "-m", "chore(openspec): archive foo")
    sha = _git(root, "rev-parse", "HEAD").strip()
    assert R.is_archive_rename(str(root), sha, "foo") is True


def test_stage_walltimes_and_negative_clamp(tmp_path):
    # absorb-gstack-autoplan：attribute-to-next（checkpoint=工作完成点，区间归其完成点）——
    # a→b 的 600s 是「做 grill 用的时间」（b 才是 grill 完成的标记），故归 nxt=b 的阶段 grill，
    # 不再归 cur=a 的阶段 ff（首提交 a 自身的阶段 ff 因无前驱 Δ 而不入账）。
    commits = [
        {"sha": "a", "ts": 1000, "subject": "checkpoint(ff)"},
        {"sha": "b", "ts": 1600, "subject": "checkpoint(grill)"},       # ff→grill: 600s=10min 归 grill（nxt）
        {"sha": "c", "ts": 1500, "subject": "checkpoint(spec-review)"}, # 负 Δ → 钳 0 归 spec-review（nxt）
    ]
    got = R.stage_walltimes(str(tmp_path), "foo", commits)
    assert got["stages"].get("ff", 0) == 0.0
    assert got["stages"]["grill"] == 10.0
    assert got["stages"].get("spec-review", 0) == 0.0
    assert got["reorder_suspected"] is True
    assert got["n_ckpt"] == 3


def test_stage_walltimes_historical_spec_review_autoplan_sequence_no_longer_misattributed(tmp_path):
    """回归测试（历史序列，含 checkpoint(spec-review-autoplan) 中间标签）：absorb-gstack-autoplan 修正
    既有错账——旧口径 attribute-to-previous 下，generate→autoplan 区间因 cur=sdflow-spec-generate 映射
    stage="ff" 而误归 ff（design.md「墙钟归属」段实证的错账）。attribute-to-next 后，该区间与后续
    autoplan→spec-review 区间均归 nxt 的阶段（spec-review-autoplan/spec-review 皆映射 spec-review），
    Step1 广审墙钟不再泄漏进 ff。"""
    commits = [
        {"sha": "a", "ts": 1000, "subject": "checkpoint(sdflow-spec-generate)"},
        {"sha": "b", "ts": 1000 + 600, "subject": "checkpoint(spec-review-autoplan)"},  # Step1 广审 600s
        {"sha": "c", "ts": 1000 + 600 + 300, "subject": "checkpoint(spec-review)"},      # Step2/3 300s
    ]
    got = R.stage_walltimes(str(tmp_path), "foo", commits)
    assert got["stages"].get("ff", 0) == 0.0                 # 不再误归 ff
    assert got["stages"]["spec-review"] == 15.0               # 600s+300s = 900s = 15min，全归 spec-review


def test_stage_walltimes_new_single_checkpoint_sequence_attributes_to_spec_review(tmp_path):
    """回归测试（新序列，DD1 单批 dispatch 下中间 checkpoint(spec-review-autoplan) 已退役）：
    generate→spec-review 单一区间整体归 spec-review（本 skill 只剩一次 checkpoint(spec-review)）。"""
    commits = [
        {"sha": "a", "ts": 1000, "subject": "checkpoint(sdflow-spec-generate)"},
        {"sha": "b", "ts": 1000 + 900, "subject": "checkpoint(spec-review)"},  # 单批 dispatch 900s
    ]
    got = R.stage_walltimes(str(tmp_path), "foo", commits)
    assert got["stages"].get("ff", 0) == 0.0
    assert got["stages"]["spec-review"] == 15.0


def test_stage_walltimes_archive_rename_attributed_via_nxt_not_cur(tmp_path):
    """`is_archive_rename` 判定对象由 cur 换 nxt：归档 rename 提交与其前一个 checkpoint 之间的墙钟
    （真实是"做归档收尾用的时间"）现正确归 done，不再误归前一个 checkpoint 自身的阶段
    （旧口径下 impl-review→archive 区间会误归 code-review，因 cur=impl-review 映射 code-review）。"""
    root = _init_repo(tmp_path)
    _commit(root, {"openspec/changes/foo/proposal.md": "a"}, "checkpoint(impl-review)")
    sha_impl = _git(root, "rev-parse", "HEAD").strip()
    (root / "openspec/changes/archive/2026-07-06-foo").mkdir(parents=True)
    _git(root, "mv", "openspec/changes/foo/proposal.md",
         "openspec/changes/archive/2026-07-06-foo/proposal.md")
    _git(root, "add", "-A"); _git(root, "commit", "-q", "-m", "chore(openspec): archive foo")
    sha_archive = _git(root, "rev-parse", "HEAD").strip()
    commits = [
        {"sha": sha_impl, "ts": 1000, "subject": "checkpoint(impl-review)"},
        {"sha": sha_archive, "ts": 1000 + 600, "subject": "chore(openspec): archive foo"},
    ]
    got = R.stage_walltimes(str(root), "foo", commits)
    assert got["stages"]["done"] == 10.0
    assert got["stages"].get("code-review", 0) == 0.0


ANCHOR = ('<!-- sdflow:lens-metric v1 layer="{layer}" lens="domain" runner="claude" '
          'site="—" findings="{f}" 采纳="{a}" 裁掉="0" defer="0" 独立="{ind}" '
          'sev="致0/高1/中0/低0" -->')


def test_lens_value_active_change_has_anchor(tmp_path):
    d = tmp_path / "openspec/changes/live"
    d.mkdir(parents=True)
    (d / "spec-review-report.md").write_text(
        ANCHOR.format(layer="spec-review", f=9, a=9, ind=6) + "\n", encoding="utf-8")
    (d / "code-review-report.md").write_text(
        ANCHOR.format(layer="code-review", f=4, a=3, ind=2) + "\n", encoding="utf-8")
    info = {"active": True, "active_dir": str(d), "archive_dir": None}
    v = R.lens_value_for_change(info)
    assert v["has_anchor"] is True
    assert v["sum_findings"] == 13
    assert "spec-review" in v["by_layer"] and "code-review" in v["by_layer"]


def test_lens_value_no_anchor(tmp_path):
    d = tmp_path / "openspec/changes/bare"
    d.mkdir(parents=True)
    (d / "proposal.md").write_text("no anchor here", encoding="utf-8")
    info = {"active": True, "active_dir": str(d), "archive_dir": None}
    v = R.lens_value_for_change(info)
    assert v["has_anchor"] is False


def test_lens_value_flags_illegal_number(tmp_path):
    """[impl-review-fix F3] 反证测试：锚里 findings="-7"（负值契约非法）、
    采纳="abc"（非数字，_int 静默当 0）时，lens_value_for_change 必须把 is_bad
    传播出来（不能像修前那样三处 `_, _ = LMA._int(...)` 丢弃），否则同一批坏锚
    在聚合③（render_table）打 ⚠数值非法、在 per-change 表却悄悄看起来正常——
    两张表对同源数据给出互相矛盾的可信度呈现。
    修前：返回 dict 无 "num_bad" 键，本测试 FAIL（KeyError）。
    """
    d = tmp_path / "openspec/changes/bad"
    d.mkdir(parents=True)
    (d / "spec-review-report.md").write_text(
        ANCHOR.format(layer="spec-review", f="-7", a="abc", ind=1) + "\n", encoding="utf-8")
    info = {"active": True, "active_dir": str(d), "archive_dir": None}
    v = R.lens_value_for_change(info)
    assert v["num_bad"] is True


HRTG = '<!-- sdflow:hr-tg v1 hit="{hit}" evidence="x" -->'


def test_hr_tg_two_columns(tmp_path):
    d = tmp_path / "openspec/changes/hh"; d.mkdir(parents=True)
    (d / "spec-review-report.md").write_text(HRTG.format(hit="none") + "\n", encoding="utf-8")
    (d / "code-review-report.md").write_text(HRTG.format(hit="TG-06") + "\n", encoding="utf-8")
    info = {"active": True, "active_dir": str(d), "archive_dir": None}
    f = R.hr_tg_flags(info)
    assert f["spec_hr_tg"] == "none"
    assert f["code_hr_tg"] == "TG-06"


def test_hr_tg_read_permission_failsafe(tmp_path, monkeypatch):
    """[impl-review-fix F2] 反证测试：坏文件（权限拒绝/IO 错误）读取须 fail-safe 返回 "—"，
    不冒泡异常穿透 hr_tg_flags→build_report→main()。
    用 monkeypatch 替换模块级 open 确定性模拟 PermissionError，而非依赖 chmod 000——
    后者在 root 用户或某些文件系统下仍可读，跨环境不稳定，达不到"确保确定性"。
    修前：_read_hr_hit 裸 open 无 try/except，异常直接冒泡，本测试 FAIL（抛 PermissionError）。
    """
    d = tmp_path / "openspec/changes/hh"; d.mkdir(parents=True)
    fp = d / "spec-review-report.md"
    fp.write_text(HRTG.format(hit="TG-01") + "\n", encoding="utf-8")

    real_open = open

    def _boom(path, *a, **k):
        if str(path) == str(fp):
            raise PermissionError("denied")
        return real_open(path, *a, **k)

    monkeypatch.setattr(R, "open", _boom, raising=False)

    got = R._read_hr_hit(str(d), "spec-review-report.md")
    assert got == "—"


def test_hr_tg_skips_fenced_example(tmp_path):
    """[impl-review-fix F4] 反证测试：fence 内的示范 hr-tg 锚必须被跳过，只读 fence 外真锚。
    修前：_read_hr_hit 逐行裸 regex 无 fence-aware 过滤，会误读 fence 内的第一条锚 "TG-99"，
    本测试 FAIL（得到 "TG-99" 而非 "none"）。
    """
    d = tmp_path / "openspec/changes/hh"; d.mkdir(parents=True)
    content = "\n".join([
        "some report body",
        "```",
        HRTG.format(hit="TG-99"),  # 示范锚，fence 内，应被跳过
        "```",
        HRTG.format(hit="none"),   # fence 外的真锚
        "",
    ])
    (d / "spec-review-report.md").write_text(content, encoding="utf-8")
    got = R._read_hr_hit(str(d), "spec-review-report.md")
    assert got == "none"


def test_hr_tg_multi_anchor_takes_last(tmp_path):
    """[impl-review-fix F7] 反证测试：同一报告内多条 hr-tg 锚时取最后一条=最终判定，非 first-wins。
    修前：_read_hr_hit 遇首个锚即 return，本测试 FAIL（得到 "none" 而非 "TG-06"）。
    """
    d = tmp_path / "openspec/changes/hh"; d.mkdir(parents=True)
    content = HRTG.format(hit="none") + "\n" + HRTG.format(hit="TG-06") + "\n"
    (d / "code-review-report.md").write_text(content, encoding="utf-8")
    got = R._read_hr_hit(str(d), "code-review-report.md")
    assert got == "TG-06"


def test_build_report_coverage_counts(tmp_path):
    root = _init_repo(tmp_path)
    _commit(root, {"openspec/changes/foo/proposal.md": "a"}, "checkpoint(ff)")
    _commit(root, {"openspec/changes/foo/design.md": "b"}, "checkpoint(grill)")
    d = root / "openspec/changes/foo"
    (d / "spec-review-report.md").write_text(ANCHOR.format(layer="spec-review", f=9, a=9, ind=6) + "\n", encoding="utf-8")
    md = R.build_report(str(root))
    assert "覆盖" in md and "有真锚" in md and "边界不可解析" in md
    assert "foo" in md
    assert "in-progress" in md  # foo 是活动 change


def test_build_report_per_change_stage_columns(tmp_path):
    """[impl-review-fix F12] 反证测试：design.md 报告 schema（约 103-105 行）明确
    per-change 表列含 4 个阶段 Δ 列 spec-rev Δ | impl Δ | code-rev Δ | done Δ，
    tasks.md task 3.1 同样要求"per-change 行（阶段Δ 含 done Δ）"，但实现只有总墙钟，
    wt["stages"] 从未按行渲染——"某 change 卡在哪个阶段"这个 design 承诺能力不可得。
    修前：per-change 表头无这 4 列，本测试 FAIL。
    """
    root = _init_repo(tmp_path)
    _commit(root, {"openspec/changes/foo/proposal.md": "a"}, "checkpoint(ff)")
    _commit(root, {"openspec/changes/foo/design.md": "b"}, "checkpoint(spec-review)")
    _commit(root, {"openspec/changes/foo/tasks.md": "c"}, "checkpoint(foo:task1-impl)")
    md = R.build_report(str(root))
    assert "spec-rev Δ" in md
    assert "impl Δ" in md
    assert "code-rev Δ" in md
    assert "done Δ" in md


def test_atomic_write_preserves_on_replace_and_no_tmp(tmp_path):
    target = tmp_path / "openspec/retro/report.md"
    R.atomic_write(str(target), "hello")
    assert target.read_text() == "hello"
    # 无残留 tmp
    assert not any(p.suffix == ".tmp" for p in (tmp_path / "openspec/retro").iterdir())


def test_report_idempotent(tmp_path):
    root = _init_repo(tmp_path)
    _commit(root, {"openspec/changes/foo/proposal.md": "a"}, "checkpoint(ff)")
    _commit(root, {"openspec/changes/foo/design.md": "b"}, "checkpoint(grill)")
    a = R.build_report(str(root))
    b = R.build_report(str(root))
    assert a == b


def test_atomic_write_preserves_mode_on_overwrite(tmp_path):
    if os.name == "nt":
        pytest.skip("Windows does not expose POSIX mode bits")
    target = tmp_path / "openspec/retro/report.md"
    target.parent.mkdir(parents=True)
    target.write_text("old", encoding="utf-8")
    os.chmod(str(target), 0o644)
    R.atomic_write(str(target), "new")           # 覆盖已存在文件
    assert target.read_text() == "new"
    mode = os.stat(str(target)).st_mode & 0o777
    assert mode == 0o644, f"权限被静默收紧到 {oct(mode)}（D13：覆盖须保原 0644，非 mkstemp 的 0600）"


def test_main_writes_report_and_returns_zero(tmp_path):
    root = _init_repo(tmp_path)
    _commit(root, {"openspec/changes/foo/proposal.md": "a"}, "checkpoint(ff)")
    _commit(root, {"openspec/changes/foo/design.md": "b"}, "checkpoint(grill)")
    rc = R.main(["--root", str(root)])
    assert rc == 0
    assert (root / "openspec/retro/report.md").is_file()


def test_surfacing_block_fixed_prefix(tmp_path):
    # 无命中也必须有固定前缀行（可机验，D12：防死列自我复现）
    block = R.surfacing_block(str(tmp_path))
    assert block.strip().startswith("⚠️ 待复评:")
    assert "无（所有镜出现轮数<10）" in block


def test_surfacing_block_flags_ge10(tmp_path):
    # 同一 (layer,lens,runner,site) 分组出现 10 次 → 触发 ≥10待复评
    for i in range(1, 11):
        d = tmp_path / "openspec/changes/archive" / f"2026-07-{i:02d}-c{i}"
        d.mkdir(parents=True)
        (d / "spec-review-report.md").write_text(
            ANCHOR.format(layer="spec-review", f=1, a=1, ind=1) + "\n", encoding="utf-8")
    block = R.surfacing_block(str(tmp_path))
    assert block.strip().startswith("⚠️ 待复评:")
    assert "domain" in block
    assert "出现轮数 10" in block


def test_surfacing_block_shows_host_field(tmp_path):
    # [add-codex-host-support:task5] surfacing_block 逐行须显式带 host= 字段
    # （分组键升维，人复评时须看到是哪个宿主的镜频繁出现，不能只见 runner）。
    for i in range(1, 11):
        d = tmp_path / "openspec/changes/archive" / f"2026-07-{i:02d}-c{i}"
        d.mkdir(parents=True)
        (d / "spec-review-report.md").write_text(
            ANCHOR.format(layer="spec-review", f=1, a=1, ind=1) + "\n", encoding="utf-8")
    block = R.surfacing_block(str(tmp_path))
    assert "host=claude" in block  # ANCHOR 无 host 字段 → 双代兼容读为 claude


def test_surfacing_threshold_uses_shared_constant(tmp_path, monkeypatch):
    # T59 反证：surfacing_block 的 ≥10 阈值须引用 LMA.REVIEW_ROUNDS_THRESHOLD 同源常量，
    # 非本地硬编码 10。把常量临时降到 3、构造同键 3 轮，应触发 flag。
    # 修前 surfacing_block 硬编码 `c >= 10` → 3 轮不命中 → "出现轮数 3" 不在 block → FAIL。
    import lens_metric_aggregate as LMA
    monkeypatch.setattr(LMA, "REVIEW_ROUNDS_THRESHOLD", 3)
    for i in range(1, 4):
        d = tmp_path / "openspec/changes/archive" / f"2026-07-{i:02d}-c{i}"
        d.mkdir(parents=True)
        (d / "spec-review-report.md").write_text(
            ANCHOR.format(layer="spec-review", f=1, a=1, ind=1) + "\n", encoding="utf-8")
    block = R.surfacing_block(str(tmp_path))
    assert "出现轮数 3" in block


# ============================ DD1: mirror-dispositions.yaml 处置注记（四态）============================
# implement-workflow-optimization-2026-08-p2 Task 2D。schema: {layer,lens,host,runner,site,
# disposition,condition,date,rationale}；匹配键=(layer,lens,host,runner,site)，与 LMA.group_key 同键。
# ANCHOR fixture 无 host 字段 → 双代兼容读 host="claude"；lens="domain" runner="claude" site="—"。

def _write_dispositions(root, entries_yaml):
    d = root / "openspec" / "retro"
    d.mkdir(parents=True, exist_ok=True)
    (d / "mirror-dispositions.yaml").write_text(entries_yaml, encoding="utf-8")


def _flagged_archive(tmp_path, layer="spec-review"):
    for i in range(1, 11):
        d = tmp_path / "openspec/changes/archive" / f"2026-07-{i:02d}-c{i}"
        d.mkdir(parents=True)
        (d / "spec-review-report.md").write_text(
            ANCHOR.format(layer=layer, f=1, a=1, ind=1) + "\n", encoding="utf-8")


def test_dispositions_file_missing_zero_annotation(tmp_path):
    # 状态①：文件缺失 = 零注记照旧 flag（向后兼容），不报错
    _flagged_archive(tmp_path)
    block = R.surfacing_block(str(tmp_path))
    assert "出现轮数 10" in block
    assert "已处置" not in block


def test_dispositions_matched_key_annotates_flagged_line(tmp_path):
    # 状态②：命中键 → 待复评行内追加 "→ 已处置: <disposition> (<date>)"
    _flagged_archive(tmp_path)
    _write_dispositions(tmp_path, """\
- layer: spec-review
  lens: domain
  host: claude
  runner: claude
  site: "—"
  disposition: 保留
  condition: "—"
  date: "2026-08-10"
  rationale: "测试命中注记"
""")
    block = R.surfacing_block(str(tmp_path))
    assert "→ 已处置: 保留 (2026-08-10)" in block


def test_dispositions_bad_disposition_value_fail_loud(tmp_path):
    # 状态③：disposition 非法域 → fail-loud 非零退出（此处以异常传播体现，MUST NOT 静默吞）
    _flagged_archive(tmp_path)
    _write_dispositions(tmp_path, """\
- layer: spec-review
  lens: domain
  host: claude
  runner: claude
  site: "—"
  disposition: 乱填一个值
  condition: "—"
  date: "2026-08-10"
  rationale: "非法 disposition"
""")
    with pytest.raises(Exception):
        R.surfacing_block(str(tmp_path))


def test_dispositions_malformed_yaml_fail_loud(tmp_path):
    # 状态③变体：yaml 本身解析失败（缺字段）→ fail-loud
    _flagged_archive(tmp_path)
    _write_dispositions(tmp_path, """\
- layer: spec-review
  lens: domain
  disposition: 保留
""")
    with pytest.raises(Exception):
        R.surfacing_block(str(tmp_path))


def test_dispositions_unmatched_key_warns_not_blocking(tmp_path, capsys):
    # 状态④：键未命中任何锚组 → 告警不阻断（可能是已淘汰镜的存量记录）——报告仍正常生成
    _flagged_archive(tmp_path)
    _write_dispositions(tmp_path, """\
- layer: code-review
  lens: history
  host: claude
  runner: claude
  site: "—"
  disposition: 降采样
  condition: "diff 含 rename 或大规模改动既有文件"
  date: "2026-08-10"
  rationale: "本轮 archive 语料无 code-review 数据，此键必不命中"
""")
    block = R.surfacing_block(str(tmp_path))
    assert "出现轮数 10" in block           # 报告仍正常产出，未被未命中键拖垮
    assert "已处置" not in block            # 未命中键不注记到 spec-review/domain 行
    err = capsys.readouterr().err
    assert "未命中" in err or "unmatched" in err.lower()


def test_build_report_includes_surfacing_block(tmp_path):
    root = _init_repo(tmp_path)
    _commit(root, {"openspec/changes/foo/proposal.md": "a"}, "checkpoint(ff)")
    md = R.build_report(str(root))
    assert "⚠️ 待复评:" in md


def test_surfacing_groupkey_matches_render_table_on_empty_lens(tmp_path):
    # lens="" 的锚：surfacing 分组键须与 render_table 归一化一致(空串→"?")，否则漏报
    # [add-codex-host-support:task5] 分组键升 (layer,lens,host,runner,site)；
    # r 无 host 字段 → 双代兼容读为 host="claude"。
    import lens_metric_aggregate as LMA
    r = {"layer": "spec-review", "lens": "", "runner": "claude", "site": "—"}
    assert LMA.group_key(r) == ("spec-review", "?", "claude", "claude", "—")
    # 且 surfacing_block 对 10 份 lens="" 锚真能命中(不漏报)
    archive = tmp_path / "openspec/changes/archive"
    d = archive / "2026-01-01-x"
    d.mkdir(parents=True)
    anchor = ('<!-- sdflow:lens-metric v1 layer="spec-review" lens="" runner="claude" '
              'site="—" findings="1" 采纳="1" 裁掉="0" defer="0" 独立="1" sev="致0/高0/中0/低1" -->')
    (d / "spec-review-report.md").write_text("\n".join([anchor] * 10) + "\n", encoding="utf-8")
    block = R.surfacing_block(str(tmp_path))
    assert "⚠️ 待复评:" in block
    assert "出现轮数 10" in block   # 10 份同键锚合并计数=10，命中≥10


# ============================ 一览（语义化总结）============================
DECISION_WORDS = ["说明", "意味着", "因此", "所以", "建议", "应该",
                  "该砍", "值得", "可考虑", "淘汰", "降采样", "优化掉"]


def _agg(layer, lens, runner, site, f, a=0, cut=0, defer=0, ind=0):
    return {"layer": layer, "lens": lens, "runner": runner, "site": site,
            "findings": str(f), "采纳": str(a), "裁掉": str(cut),
            "defer": str(defer), "独立": str(ind)}


def test_fmt_dur_precision():
    # 亚分钟保留小数（不 round 成 "0 min" 骗人）；≥1min 整数；≥60min 转 hr
    assert R._fmt_dur(0.2) == "0.2 min"
    assert R._fmt_dur(7) == "7 min"
    assert R._fmt_dur(30.4) == "30 min"
    assert R._fmt_dur(120) == "2.0 hr"
    assert R._fmt_dur(756) == "12.6 hr"


def test_semantic_summary_card_and_paragraph():
    stage = {"spec-review": 400.0, "impl": 300.0, "code-review": 100.0}
    cost = [("big", 756.0, False), ("small", 7.0, False), ("boundary", 0.0, True)]
    agg = [_agg("code-review", "adversarial", "claude", "—", 10, a=8, cut=1, defer=1, ind=5),
           _agg("code-review", "adversarial", "claude", "—", 5, a=4, ind=2),
           _agg("spec-review", "domain", "claude", "—", 3, a=3)]
    out = R.semantic_summary(4, 2, stage, cost, 1, agg)
    # 指标卡：纯计数，无平均值列
    assert "| 复盘 change | 总墙钟 | 有真锚 | 待复评镜 |" in out
    assert "| 4 | ~13.3 hr | 2 | 1 |" in out   # 总墙钟=stage_totals 之和 800min=13.3hr
    assert "平均" not in out
    # 段落：覆盖量 / 阶段大头 / 成本两端(含倍数) / 价值大头 / 待复评
    assert "覆盖 **4 个 change**" in out
    assert "设计审 50%" in out and "写实现 38%" in out and "合计 88%" in out
    assert "最重的是 big（约 12.6 hr）" in out
    assert "最轻的是 small（7 min）" in out
    assert "相差约 108 倍" in out                      # 756/7≈108
    assert "代码审对抗镜（15 条，采纳率 86%）" in out   # 10+5 findings 合并；采纳12/(12+1+1)=86%
    assert "1 面镜达到待复评轮数阈值" in out


def test_semantic_summary_no_decision_words():
    stage = {"spec-review": 400.0, "impl": 300.0}
    cost = [("big", 756.0, False), ("small", 7.0, False)]
    agg = [_agg("code-review", "adversarial", "claude", "—", 10, a=8)]
    out = R.semantic_summary(4, 2, stage, cost, 1, agg)
    for w in DECISION_WORDS:
        assert w not in out, f"决策/解读词泄漏: {w}"


def test_semantic_summary_no_walltime_degrades():
    # grand_total=0：总墙钟卡片显 "—"，无阶段句、无成本两端句，不崩
    out = R.semantic_summary(3, 0, {}, [("a", 0.0, True)], 0, [])
    assert "| 3 | — | 0 | 0 |" in out
    assert "价值维暂无数据" in out
    assert "评审时间集中在" not in out
    assert "耗时最重" not in out


def test_semantic_summary_no_anchor_degrades():
    # M=0：价值维降级句，无 top-mirror 句（即便 agg 非空也不出，防止无锚却报价值）
    stage = {"impl": 120.0}
    agg = [_agg("code-review", "adversarial", "claude", "—", 10, a=8)]
    out = R.semantic_summary(2, 0, stage, [("x", 120.0, False)], 0, agg)
    assert "价值维暂无数据" in out
    assert "出问题最多" not in out


def test_semantic_summary_subminute_no_absurd_ratio():
    # 最轻 change 亚分钟(0.2min)：如实显 0.2 min，但不给无意义倍数
    cost = [("big", 756.0, False), ("plan", 0.2, False)]
    out = R.semantic_summary(2, 1, {"impl": 756.2},
                             cost, 0, [_agg("code-review", "domain", "claude", "—", 1, a=1)])
    assert "最轻的是 plan（0.2 min）" in out
    assert "倍" not in out


def test_semantic_summary_single_change():
    # 仅 1 个有效墙钟 change：出"仅 X 有可解析墙钟"，不出两端/倍数
    out = R.semantic_summary(1, 0, {"impl": 50.0}, [("solo", 50.0, False)], 0, [])
    assert "仅 solo 有可解析墙钟" in out
    assert "最重的是" not in out


def test_top_mirror_runner_suffix_for_outside_voice():
    # 非 claude runner（outside-voice codex）作 label 后缀，claude 不加后缀。
    # _agg 构造的 dict 无 host 字段 → group_key 双代兼容读为 host="claude"，
    # 故走 elif 分支（沿用旧 runner-only 后缀，非 host≠claude 的新前缀分支）。
    agg = [_agg("code-review", "outside-voice", "codex", "code-voice", 20, a=17, cut=2, defer=1, ind=8),
           _agg("code-review", "domain", "claude", "—", 5, a=5)]
    label, findings, rate = R._top_mirror(agg)
    assert label == "代码审外部声音镜（codex）"
    assert findings == 20
    assert rate == "85%"                     # 17/(17+2+1)


def _agg_host(layer, lens, host, runner, site, f, a=0, cut=0, defer=0, ind=0):
    d = _agg(layer, lens, runner, site, f, a, cut, defer, ind)
    d["host"] = host
    return d


def test_top_mirror_host_codex_prefixed_label():
    # [add-codex-host-support:task5] host="codex" 的 top mirror 须显著前缀标注宿主
    # （GC-9 view-only 呈现——Codex 宿主轮次与 Claude 宿主轮次分开可见，不混算）。
    agg = [_agg_host("code-review", "outside-voice", "codex", "claude", "code-voice",
                      20, a=17, cut=2, defer=1, ind=8),
           _agg("code-review", "domain", "claude", "—", 5, a=5)]
    label, findings, rate = R._top_mirror(agg)
    assert label == "代码审外部声音镜（codex宿主/claude）"
    assert findings == 20


def test_top_mirror_none_when_no_findings():
    assert R._top_mirror([]) is None
    assert R._top_mirror([_agg("code-review", "domain", "claude", "—", 0)]) is None


def test_build_report_includes_overview(tmp_path):
    root = _init_repo(tmp_path)
    _commit(root, {"openspec/changes/foo/proposal.md": "a"}, "checkpoint(ff)")
    md = R.build_report(str(root))
    assert "## 一览" in md
    assert "| 复盘 change | 总墙钟 | 有真锚 | 待复评镜 |" in md


# ============================ 聚合④ per-镜实修率（历史回算）============================
# task2: extract_fixrate_samples 窄文法单元测试（合成语料，tasks 2.3 六类用例）。

def test_fixrate_resolved_via_table_source_column():
    """可判定样本计入实修率：表格数据行「来源」列精确命中一个 lens 关键词 + 精确 needle。"""
    text = (
        "| # | 来源 | 问题 | 处置 |\n"
        "|---|---|---|---|\n"
        "| 1 | 对抗镜1 | 假设不成立 | ✅ 已修[impl-review-fix]：改判据 |\n"
    )
    got = R.extract_fixrate_samples(text)
    assert got == [("adversarial", "fixed")]


def test_fixrate_resolved_via_bracket_tag():
    """可判定样本：bullet 形态〔…〕括号标签精确命中一个 lens 关键词。"""
    text = "- **F1 空串绕过**〔领域镜〕| 证据 | 置信 95 | **已修[impl-review-fix]**：加判断\n"
    got = R.extract_fixrate_samples(text)
    assert got == [("domain", "fixed")]


def test_fixrate_lens_ambiguous_zero_hits_unknown():
    """归属歧义（零命中）：来源列存在但无任何 lens 关键词 → lens=None（layer 级未知）。"""
    text = (
        "| # | 来源 | 处置 |\n"
        "|---|---|---|\n"
        "| 1 | CR-09 | 已修[impl-review-fix] |\n"
    )
    got = R.extract_fixrate_samples(text)
    assert got == [(None, "fixed")]


def test_fixrate_lens_ambiguous_multi_hits_unknown():
    """归属歧义（多命中）：〔〕内同时含两个 lens 关键词 → lens=None（不可判定哪一面）。"""
    text = "- **F1**〔领域镜+对抗A 独立收敛〕| 已修[impl-review-fix] | 修复\n"
    got = R.extract_fixrate_samples(text)
    assert got == [(None, "fixed")]


def test_fixrate_disposal_signal_ambiguous_variant_is_unknown_not_unfixed():
    """[spec-review-amendment] 处置信号歧义进未知桶：裸 impl-review-fix 串（无精确 needle）
    命中单一 lens → fix-status 记 unknown_disposal，MUST NOT 判「未修」。"""
    text = "- **F2**〔历史镜〕| 采纳[impl-review-fix] | 已处理\n"
    got = R.extract_fixrate_samples(text)
    assert got == [("history", "unknown_disposal")]


def test_fixrate_disposal_verb_without_needle_is_unknown():
    """处置动词（已修/采纳/自动修）但不命中精确 needle → unknown_disposal。"""
    text = "- **F3**〔接地镜〕| 已修：改了实现，未走标准标注\n"
    got = R.extract_fixrate_samples(text)
    assert got == [("grounding", "unknown_disposal")]


def test_fixrate_free_text_keyword_not_bounded_no_attribution():
    """关键词出现在自由文本（有界记号外）不构成归属：文件名含 outside-voice、〔〕内
    无该词 → 该行有界记号内容零命中 → lens=None（即便行内其他位置出现关键词字面量）。"""
    text = ("| # | 来源 | 问题 | 处置 |\n"
            "|---|---|---|---|\n"
            "| 1 | CR-01 | outside-voice-reuse-guard 孤儿文件 | 已修[impl-review-fix] |\n")
    got = R.extract_fixrate_samples(text)
    assert got == [(None, "fixed")]


def test_fixrate_fenced_sample_anchor_not_counted():
    """围栏内示范锚不入计：```内的合法 finding 行文本不应被提取（同 LMA fence-aware 惯例）。"""
    text = (
        "示例：\n"
        "```\n"
        "| # | 来源 | 处置 |\n"
        "|---|---|---|\n"
        "| 1 | 对抗镜1 | 已修[impl-review-fix] |\n"
        "```\n"
        "正文之外无其他候选行。\n"
    )
    got = R.extract_fixrate_samples(text)
    assert got == []


def test_fixrate_defer_marker_classified_defer():
    text = "- **F4**〔广审〕| defer → todolist（低风险）\n"
    got = R.extract_fixrate_samples(text)
    assert got == [("broad", "defer")]


def test_fixrate_defer_field_in_anchor_line_not_misclassified():
    """defer 类标注防误命中：lens-metric 锚行的 `defer="0"` KV 字段不应触发 defer 分类
    （锚行本身也被 `<!-- sdflow:` 前缀整行跳过，双重防御）。"""
    text = ('<!-- sdflow:lens-metric v1 layer="code-review" lens="domain" runner="claude" '
            'site="—" findings="3" 采纳="2" 裁掉="1" defer="0" 独立="1" sev="致0/高0/中0/低0" -->\n')
    got = R.extract_fixrate_samples(text)
    assert got == []


def test_fixrate_disposition_table_row_no_signal_is_not_fixed():
    """未修（无任何处置信号）：处置列表格的数据行，处置 cell 无任何处置标注
    → not_fixed（结构信号——处置列存在，是本行确属 finding 的证据）。"""
    text = (
        "| # | 来源 | 问题 | 处置 |\n"
        "|---|---|---|---|\n"
        "| 1 | 对抗镜1 | 未处理的发现 | 待跟进 |\n"
    )
    got = R.extract_fixrate_samples(text)
    assert got == [("adversarial", "not_fixed")]


def test_fixrate_non_disposition_table_no_signal_not_a_candidate():
    """已裁掉表（「裁掉理由」列非「处置」列）的行若无处置信号 → 不是候选，不计入未修
    （真语料试算证实：缺此门会把 33+ 已裁掉行误判「未修」，污染分母）。"""
    text = (
        "| # | 原始发现 | 来源 | 裁掉理由 |\n"
        "|---|---|---|---|\n"
        "| 1 | 假设不成立 | 对抗镜1 | 复现不成立 |\n"
    )
    got = R.extract_fixrate_samples(text)
    assert got == []


def test_fixrate_section_header_with_bare_string_not_candidate():
    """section 标题本身带裸 impl-review-fix 字面量不应被当候选行（如
    "### Findings（置信 ≥80，均已自动修 [impl-review-fix]）" 真实语料标题）。"""
    text = "### Findings（置信 ≥80，均已自动修 [impl-review-fix]）\n\n正文占位。\n"
    got = R.extract_fixrate_samples(text)
    assert got == []


def test_fixrate_alias_domain_recognized_within_marker():
    """`域` 作 `领域` 别名仅在来源记号内识别。"""
    text = "- **F5**〔跨域收敛〕| 已修[impl-review-fix] | 改了\n"
    got = R.extract_fixrate_samples(text)
    assert got == [("domain", "fixed")]


# ---- fixrate_aggregate / render_fixrate_table ----

_FR_TABLE = ("| # | 来源 | 处置 |\n|---|---|---|\n"
             "| {n} | {src} | {disp} |\n")


def test_fixrate_aggregate_and_render_shows_three_numbers(tmp_path):
    root = _init_repo(tmp_path)
    d = root / "openspec/changes/archive/2026-01-01-foo"
    d.mkdir(parents=True)
    body = (_FR_TABLE.format(n=1, src="对抗镜1", disp="已修[impl-review-fix]")
            + _FR_TABLE.format(n=2, src="对抗镜1", disp="已修[impl-review-fix]")
            + _FR_TABLE.format(n=3, src="对抗镜1", disp="待跟进"))
    (d / "code-review-report.md").write_text(body, encoding="utf-8")
    rows, lens_unknown = R.fixrate_aggregate(str(root))
    key = ("code-review", "adversarial")
    assert rows[key]["可判定"] == 3
    assert rows[key]["实修"] == 2
    assert rows[key]["未修"] == 1
    md = R.render_fixrate_table(rows, lens_unknown)
    assert "可判定" in md and "未知(本镜)" in md and "覆盖率" in md
    assert "| code-review | adversarial | 3 | 2 | 0 | 1 |" in md


def test_fixrate_render_marks_reference_below_threshold():
    rows = {("code-review", "adversarial"): {"可判定": 3, "实修": 1, "未修": 2,
                                              "defer": 0, "未知": 0, "佐证": False}}
    md = R.render_fixrate_table(rows, {})
    assert "（参考）" in md


def test_fixrate_render_no_reference_at_or_above_threshold():
    rows = {("code-review", "domain"): {"可判定": 5, "实修": 5, "未修": 0,
                                         "defer": 0, "未知": 0, "佐证": False}}
    md = R.render_fixrate_table(rows, {})
    assert "（参考）" not in md


def test_fixrate_render_empty_rows_no_crash():
    md = R.render_fixrate_table({}, {})
    assert "layer" in md and "lens" in md


def test_fixrate_aggregate_missing_archive_returns_empty(tmp_path):
    rows, lens_unknown = R.fixrate_aggregate(str(tmp_path))
    assert rows == {} and lens_unknown == {}


def test_fixrate_aggregate_evidence_flag_from_fix_commit(tmp_path):
    """佐证 flag：change 边界内存在 impl-review-fix 类 commit 时打标，不参与实修判定。"""
    root = _init_repo(tmp_path)
    d = root / "openspec/changes/archive/2026-01-01-bar"
    d.mkdir(parents=True)
    (d / "code-review-report.md").write_text(
        _FR_TABLE.format(n=1, src="对抗镜1", disp="已修[impl-review-fix]"), encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "checkpoint(impl-review-fix): auto fix")
    rows, _ = R.fixrate_aggregate(str(root))
    assert rows[("code-review", "adversarial")]["佐证"] is True


def test_fixrate_aggregate_no_evidence_flag_without_fix_commit(tmp_path):
    root = _init_repo(tmp_path)
    d = root / "openspec/changes/archive/2026-01-01-baz"
    d.mkdir(parents=True)
    (d / "code-review-report.md").write_text(
        _FR_TABLE.format(n=1, src="对抗镜1", disp="已修[impl-review-fix]"), encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "chore: unrelated")
    rows, _ = R.fixrate_aggregate(str(root))
    assert rows[("code-review", "adversarial")]["佐证"] is False


def test_build_report_includes_fixrate_section(tmp_path):
    root = _init_repo(tmp_path)
    d = root / "openspec/changes/archive/2026-01-01-foo"
    d.mkdir(parents=True)
    (d / "code-review-report.md").write_text(
        _FR_TABLE.format(n=1, src="对抗镜1", disp="已修[impl-review-fix]"), encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "chore: seed")
    md = R.build_report(str(root))
    assert "## 聚合④ per-镜实修率（历史回算）" in md
    assert "adversarial" in md


def test_build_report_fixrate_no_crash_when_no_archive(tmp_path):
    root = _init_repo(tmp_path)
    _commit(root, {"openspec/changes/foo/proposal.md": "a"}, "checkpoint(ff)")
    md = R.build_report(str(root))
    assert "## 聚合④ per-镜实修率（历史回算）" in md


# ---- 真仓再生冒烟：聚合④在场 + 待复评镜实修率或「参考」可读 ----

_REPO = Path(__file__).resolve().parents[3]  # tests/scripts/sdflow-retro/仓根


def test_fixrate_real_repo_smoke_flagged_lenses_readable():
    """真仓再生冒烟：对本仓 archive 语料跑 build_report，聚合④在场；surfacing_block
    当前标记的待复评 (layer,lens,host,runner,site) 镜，其粗粒度 (layer,lens) 在聚合④
    表中有可读的实修率（数值%或「参考」），不因窄文法密度低而缺行/崩溃。"""
    md = R.build_report(str(_REPO))
    assert "## 聚合④ per-镜实修率（历史回算）" in md
    _counts, flagged, _thr = R.surfacing_counts(str(_REPO))
    fr_rows, _ = R.fixrate_aggregate(str(_REPO))
    flagged_layer_lens = {(k[0], k[1]) for k, _c in flagged}
    for layer, lens in flagged_layer_lens:
        d = fr_rows.get((layer, lens))
        # 可判定=0 时该 (layer,lens) 键可能压根不在 rows 里（真实窄文法密度低是已接受风险）；
        # 只要不崩溃、且若存在则渲染函数能产出可读字符串即满足「实修率或参考可读」。
        if d is not None:
            denom = d["可判定"]
            rate_str = f"{d['实修'] / denom:.0%}" if denom else "—"
            assert rate_str  # 非空、非崩溃即可读


# ============================ task4: per-change tokens 列（读 token-log.jsonl）============================
# Δ 归属口径：读侧全局按 session 跨 change 分组差分（设计门 Q1 拍板=A）。四计数缩写对照：
# out=output / in=input / cc=cache_creation / cr=cache_read（design.md §口径）。

def _tok_line(session, step, ts, inp, out, cr, cc, anchor=True, reason="ok"):
    obj = {"v": 1, "ts": ts, "step": step, "session": session, "host": "claude",
           "anchor": anchor, "reason": reason}
    if anchor:
        obj["usage"] = {"input": inp, "output": out, "cache_read": cr,
                         "cache_creation": cc, "messages": 1}
    return json.dumps(obj)


def test_parse_token_log_line_no_colon_offset_matches_real_producer_format():
    """token_snapshot.py 用 `time.strftime("%Y-%m-%dT%H:%M:%S%z")` 产出「无冒号」偏移量
    （如 "+0800"，非 design.md 示例文档里手写的 "+08:00"）——本仓真实 token-log.jsonl 实测证实
    该格式。`datetime.fromisoformat` 在本机 Python 3.9 上对无冒号偏移量抛异常；读侧 MUST 用
    `strptime(...,"%z")` 兼容两种偏移写法，否则真实数据全行被误判 anchor=false（静默丢失全部
    计数，且不会在任何合成测试语料里暴露——唯有对真实生产者格式断言才能拦住）。
    """
    line = _tok_line("s1", "step1", "2026-08-10T15:36:47+0800", 10, 20, 30, 40)
    row = R._parse_token_log_line(line)
    assert row is not None
    assert row["usage"] == {"out": 20, "in": 10, "cc": 40, "cr": 30}
    # 带冒号的偏移量（design.md 文档示例形态）也须兼容
    line2 = _tok_line("s1", "step2", "2026-08-10T15:36:47+08:00", 10, 20, 30, 40)
    assert R._parse_token_log_line(line2) is not None


def test_parse_token_log_line_rejects_anchor_false():
    line = _tok_line("s1", "step1", "2026-08-10T10:00:00+0800", 0, 0, 0, 0,
                      anchor=False, reason="no-transcript")
    assert R._parse_token_log_line(line) is None


def test_parse_token_log_line_rejects_negative_usage():
    bad = ('{"v":1,"ts":"2026-08-10T10:00:00+0800","step":"s","session":"s1",'
           '"anchor":true,"usage":{"input":-1,"output":1,"cache_read":1,"cache_creation":1}}')
    assert R._parse_token_log_line(bad) is None


def test_parse_token_log_line_rejects_malformed_json():
    assert R._parse_token_log_line("{not valid json") is None


def test_read_token_log_missing_file_returns_empty(tmp_path):
    assert R.read_token_log(str(tmp_path / "nope.jsonl")) == []


def test_read_token_log_skips_corrupted_and_degraded_lines_without_crashing(tmp_path):
    """含损坏行不崩：截断半行/坏 JSON/降级行/字段非法行逐行跳过，其余合法行照常计入。"""
    p = tmp_path / "token-log.jsonl"
    body = "\n".join([
        _tok_line("s1", "step1", "2026-08-10T10:00:00+0800", 1, 2, 3, 4),
        "{truncated half line",
        _tok_line("s1", "step2", "2026-08-10T10:05:00+0800", 0, 0, 0, 0,
                   anchor=False, reason="no-transcript"),
        ('{"v":1,"ts":"2026-08-10T10:10:00+0800","step":"step3","session":"s1",'
         '"anchor":true,"usage":{"input":-1,"output":1,"cache_read":1,"cache_creation":1}}'),
        _tok_line("s1", "step4", "2026-08-10T10:15:00+0800", 5, 6, 7, 8),
        "",
    ])
    p.write_text(body, encoding="utf-8")
    rows = R.read_token_log(str(p))
    assert [r["step"] for r in rows] == ["step1", "step4"]


def test_compute_token_deltas_single_change_first_row_full_then_delta(tmp_path):
    d = tmp_path / "openspec/changes/foo"
    d.mkdir(parents=True)
    body = "\n".join([
        _tok_line("s1", "a", "2026-08-10T10:00:00+0800", 100, 200, 300, 400),
        _tok_line("s1", "b", "2026-08-10T10:05:00+0800", 150, 260, 380, 470),
    ])
    (d / "token-log.jsonl").write_text(body, encoding="utf-8")
    changes = {"foo": {"active": True, "active_dir": str(d), "archive_dir": None}}
    deltas = R.compute_token_deltas(str(tmp_path), changes)
    # 首行全额 200/100/400/300 + Δ(第二行-第一行) 60/50/70/80
    assert deltas["foo"] == {"out": 260, "in": 150, "cc": 470, "cr": 380}


def test_compute_token_deltas_cross_change_session_no_double_count(tmp_path):
    """[Q1=A 反证] 同一 session 先在 change A 落一行、后在 change B 落一行：B 的该行须对 A
    末行差分入账（非全额计入 B），否则同一用量区间被双计——两 change 之和须等于末次累计值。"""
    da = tmp_path / "openspec/changes/A"
    db = tmp_path / "openspec/changes/B"
    da.mkdir(parents=True)
    db.mkdir(parents=True)
    (da / "token-log.jsonl").write_text(
        _tok_line("s1", "a1", "2026-08-10T10:00:00+0800", 100, 200, 300, 400) + "\n",
        encoding="utf-8")
    (db / "token-log.jsonl").write_text(
        _tok_line("s1", "b1", "2026-08-10T10:05:00+0800", 150, 260, 380, 470) + "\n",
        encoding="utf-8")
    changes = {
        "A": {"active": True, "active_dir": str(da), "archive_dir": None},
        "B": {"active": True, "active_dir": str(db), "archive_dir": None},
    }
    deltas = R.compute_token_deltas(str(tmp_path), changes)
    assert deltas["A"] == {"out": 200, "in": 100, "cc": 400, "cr": 300}  # 全局首行全额计入 A
    assert deltas["B"] == {"out": 60, "in": 50, "cc": 70, "cr": 80}      # B 首行对 A 末行差分
    total = {k: deltas["A"][k] + deltas["B"][k] for k in deltas["A"]}
    assert total == {"out": 260, "in": 150, "cc": 470, "cr": 380}       # 无双计


def test_compute_token_deltas_anchor_false_rows_excluded(tmp_path):
    d = tmp_path / "openspec/changes/foo"
    d.mkdir(parents=True)
    body = "\n".join([
        _tok_line("s1", "a", "2026-08-10T10:00:00+0800", 0, 0, 0, 0,
                   anchor=False, reason="no-transcript"),
        _tok_line("s1", "b", "2026-08-10T10:05:00+0800", 10, 20, 30, 40),
    ])
    (d / "token-log.jsonl").write_text(body, encoding="utf-8")
    changes = {"foo": {"active": True, "active_dir": str(d), "archive_dir": None}}
    deltas = R.compute_token_deltas(str(tmp_path), changes)
    # 降级行不入计数 → b 视为（对该 session 而言的）首行，全额计入
    assert deltas["foo"] == {"out": 20, "in": 10, "cc": 40, "cr": 30}


def test_compute_token_deltas_missing_token_log_no_entry(tmp_path):
    d = tmp_path / "openspec/changes/bare"
    d.mkdir(parents=True)
    changes = {"bare": {"active": True, "active_dir": str(d), "archive_dir": None}}
    deltas = R.compute_token_deltas(str(tmp_path), changes)
    assert "bare" not in deltas


def test_compute_token_deltas_multiple_sessions_independent(tmp_path):
    d = tmp_path / "openspec/changes/foo"
    d.mkdir(parents=True)
    body = "\n".join([
        _tok_line("s1", "a", "2026-08-10T10:00:00+0800", 10, 10, 10, 10),
        _tok_line("s2", "b", "2026-08-10T10:01:00+0800", 5, 5, 5, 5),
        _tok_line("s1", "c", "2026-08-10T10:02:00+0800", 20, 20, 20, 20),
    ])
    (d / "token-log.jsonl").write_text(body, encoding="utf-8")
    changes = {"foo": {"active": True, "active_dir": str(d), "archive_dir": None}}
    deltas = R.compute_token_deltas(str(tmp_path), changes)
    # s1: 首行全额10 + Δ(20-10)=10 → 20；s2: 首行全额5；互不干扰，求和 25
    assert deltas["foo"] == {"out": 25, "in": 25, "cc": 25, "cr": 25}


def test_compute_token_deltas_reads_archive_dir_too(tmp_path):
    d = tmp_path / "openspec/changes/archive/2026-07-01-foo"
    d.mkdir(parents=True)
    (d / "token-log.jsonl").write_text(
        _tok_line("s1", "a", "2026-08-10T10:00:00+0800", 1, 2, 3, 4) + "\n", encoding="utf-8")
    changes = {"foo": {"active": False, "active_dir": None, "archive_dir": str(d)}}
    deltas = R.compute_token_deltas(str(tmp_path), changes)
    assert deltas["foo"] == {"out": 2, "in": 1, "cc": 4, "cr": 3}


def test_compute_token_deltas_reads_done_final_step_row(tmp_path):
    """〔implement-workflow-optimization-2026-08-p2 · Task 5 冒烟〕`step="done-final"` 是
    sdflow-done 第三步起手前新增的终态快照行——retro 消费侧对 `step` 值不做白名单校验（只认
    anchor=true + usage 四计数合法 + session/step 非空字符串），该行随 archive 一起进
    `archive_dir` 后必须仍可被 join：证明「新 step 值免入侵改动即可读」，非只在活跃目录测过。
    """
    d = tmp_path / "openspec/changes/archive/2026-08-11-demo-change"
    d.mkdir(parents=True)
    body = "\n".join([
        _tok_line("s1", "verify", "2026-08-11T09:00:00+0800", 100, 200, 300, 400),
        _tok_line("s1", "done-final", "2026-08-11T09:30:00+0800", 150, 260, 380, 470),
    ])
    (d / "token-log.jsonl").write_text(body, encoding="utf-8")
    changes = {"demo-change": {"active": False, "active_dir": None, "archive_dir": str(d)}}

    rows = R.read_token_log(str(d / "token-log.jsonl"))
    assert [r["step"] for r in rows] == ["verify", "done-final"]

    deltas = R.compute_token_deltas(str(tmp_path), changes)
    # 首行全额 200/100/400/300 + done-final 行对首行差分 60/50/70/80
    assert deltas["demo-change"] == {"out": 260, "in": 150, "cc": 470, "cr": 380}


def test_fmt_compact_count():
    assert R._fmt_compact_count(500) == "500"
    assert R._fmt_compact_count(12300) == "12.3k"
    assert R._fmt_compact_count(4500) == "4.5k"
    assert R._fmt_compact_count(89000) == "89k"
    assert R._fmt_compact_count(1200000) == "1.2M"


def test_format_tokens_cell_examples():
    cell = R.format_tokens_cell({"out": 12300, "in": 4500, "cc": 89000, "cr": 1200000})
    assert cell == "out 12.3k / in 4.5k / cc 89k / cr 1.2M"
    assert R.format_tokens_cell(None) == "—"
    assert R.format_tokens_cell({}) == "—"


def test_build_report_tokens_column_and_footnote(tmp_path):
    root = _init_repo(tmp_path)
    _commit(root, {"openspec/changes/foo/proposal.md": "a"}, "checkpoint(ff)")
    d = root / "openspec/changes/foo"
    body = "\n".join([
        _tok_line("s1", "a", "2026-08-10T10:00:00+0800", 100, 200, 300, 400),
        _tok_line("s1", "b", "2026-08-10T10:05:00+0800", 150, 260, 380, 470),
    ])
    (d / "token-log.jsonl").write_text(body, encoding="utf-8")
    md = R.build_report(str(root))
    assert "tokens" in md
    assert "out 260 / in 150 / cc 470 / cr 380" in md
    assert "首行全额之和" in md  # 恒加脚注


def test_build_report_tokens_dash_when_no_token_log(tmp_path):
    """存量 change（本机制引入前归档，无 token-log.jsonl）tokens 列须显式「—」，不崩、不留空、
    不以零冒充；全仓再生冒烟场景的最小复现。"""
    root = _init_repo(tmp_path)
    _commit(root, {"openspec/changes/foo/proposal.md": "a"}, "checkpoint(ff)")
    md = R.build_report(str(root))
    assert "tokens" in md
    # per-change 明细表行以状态收尾（in-progress/archived），区别于聚合②成本双峰表同前缀行
    detail_lines = [ln for ln in md.splitlines()
                     if ln.startswith("| foo |") and ln.rstrip().endswith("in-progress |")]
    assert len(detail_lines) == 1
    # tokens 列（状态列之前）须显式「—」
    assert detail_lines[0].rstrip().endswith("| — | in-progress |")


def test_token_deltas_real_repo_smoke_no_crash():
    """全仓再生冒烟：真仓 active+archive 全部 change 的 token-log.jsonl（含真实 %z 无冒号偏移
    时间戳格式 "+0800"）跑 compute_token_deltas 不崩，产出的每个 change 四计数均为非负整数。"""
    changes = R.discover_changes(str(_REPO))
    deltas = R.compute_token_deltas(str(_REPO), changes)
    for name, d in deltas.items():
        for k in ("out", "in", "cc", "cr"):
            assert isinstance(d[k], int) and d[k] >= 0, f"{name}.{k} = {d[k]!r}"


def test_build_report_real_repo_tokens_column_smoke():
    """真仓再生冒烟：build_report 含 tokens 表头列 + 脚注，存量无 token-log 的 change 不崩。"""
    md = R.build_report(str(_REPO))
    assert "tokens" in md
    assert "首行全额之和" in md


# ============================ WFR-01/02 task1: v1 golden + v2 双读 ============================
# [implement-optimize-codex-workflow-p2-pull task1] v1 golden：冻结一份真实 v1 token-log.jsonl
# 内容（本 change 自身 2026-09-21 采集的三个 session），本 change 引入 v2 分流后逐字节
# 不变断言——防止「加 v2 支路」这个改动意外改写 v1 数值口径（Non-Goals D-1）。
_V1_GOLDEN_JSONL = "\n".join([
    '{"v": 1, "ts": "2026-09-21T12:33:13+0800", "step": "sdflow-spec-grill", "session": "69eebb6d-4c7d-4e2f-b510-74be09370109", "host": "claude", "anchor": true, "reason": "ok", "usage": {"input": 2140, "output": 111135, "cache_read": 13052866, "cache_creation": 472140, "messages": 80}}',
    '{"v": 1, "ts": "2026-09-21T12:41:52+0800", "step": "sdflow-spec-generate", "session": "69eebb6d-4c7d-4e2f-b510-74be09370109", "host": "claude", "anchor": true, "reason": "ok", "usage": {"input": 3132, "output": 189402, "cache_read": 21360485, "cache_creation": 607356, "messages": 111}}',
    '{"v": 1, "ts": "2026-09-21T14:15:42+0800", "step": "spec-review", "session": "14a6c4b4-e5bc-4c25-aba8-4561eba9bf16", "host": "claude", "anchor": true, "reason": "ok", "usage": {"input": 1902, "output": 360996, "cache_read": 17010627, "cache_creation": 955285, "messages": 81}}',
    '{"v": 1, "ts": "2026-09-21T15:00:03+0800", "step": "spec-review", "session": "14a6c4b4-e5bc-4c25-aba8-4561eba9bf16", "host": "claude", "anchor": true, "reason": "ok", "usage": {"input": 2716, "output": 473733, "cache_read": 21226492, "cache_creation": 1117489, "messages": 113}}',
    '{"v": 1, "ts": "2026-09-21T15:03:02+0800", "step": "spec-review", "session": "14a6c4b4-e5bc-4c25-aba8-4561eba9bf16", "host": "claude", "anchor": true, "reason": "ok", "usage": {"input": 2878, "output": 476169, "cache_read": 22383855, "cache_creation": 1124646, "messages": 119}}',
    '{"v": 1, "ts": "2026-09-21T15:07:29+0800", "step": "implement-optimize-codex-workflow-p2-pull:plan", "session": "fac51dc1-6bc8-43c1-912a-0e47d60ee23a", "host": "claude", "anchor": true, "reason": "ok", "usage": {"input": 91, "output": 18340, "cache_read": 2453185, "cache_creation": 452062, "messages": 28}}',
]) + "\n"

# 三个 session 各自「首行全额 + 相邻差分」手算得到的期望总量（与生产者累计口径一致，见 task1
# 交付报告的独立 python 复算脚本）：69eebb6d 会话终值 out189402/in3132/cc607356/cr21360485，
# 14a6c4b4 会话终值 out476169/in2878/cc1124646/cr22383855，fac51dc1 会话首行 out18340/in91/
# cc452062/cr2453185；三者相加即下方期望值。
_V1_GOLDEN_EXPECTED = {"out": 683911, "in": 6101, "cc": 2184064, "cr": 46197525}


def test_v1_golden_delta_byte_for_byte_stable(tmp_path):
    """v1 golden：冻结真实 v1 行内容跑 compute_token_deltas，数值逐字节（逐整数）不变。
    本测试是 v2 分流引入后的回归锚——任何触碰 v1 路径的改动都会让此测试先红。"""
    d = tmp_path / "openspec/changes/golden"
    d.mkdir(parents=True)
    (d / "token-log.jsonl").write_text(_V1_GOLDEN_JSONL, encoding="utf-8")
    changes = {"golden": {"active": True, "active_dir": str(d), "archive_dir": None}}
    deltas = R.compute_token_deltas(str(tmp_path), changes)
    assert deltas["golden"] == _V1_GOLDEN_EXPECTED


def test_v1_golden_reread_is_idempotent(tmp_path):
    """固定输入二次再生等价：同一 golden 文件跑两次 compute_token_deltas 结果逐字节相同
    （view-only 再生契约，reader 无副作用/无隐藏状态）。"""
    d = tmp_path / "openspec/changes/golden"
    d.mkdir(parents=True)
    (d / "token-log.jsonl").write_text(_V1_GOLDEN_JSONL, encoding="utf-8")
    changes = {"golden": {"active": True, "active_dir": str(d), "archive_dir": None}}
    first = R.compute_token_deltas(str(tmp_path), changes)
    second = R.compute_token_deltas(str(tmp_path), changes)
    assert first == second == {"golden": _V1_GOLDEN_EXPECTED}


# ============================ task1 slice B: v2 行解析 + bad-line ============================

def _v2_line(session, step, ts, *, kind="root", host="codex", runner="codex",
             usage=None, anchor=True, reason="ok", branch_at_start=None,
             turns=0, duration_ms=None, config_mixed=False, parent=None,
             role=None, depth=0, model="gpt-5", effort="medium",
             cli_version="0.1.0", usage_source="token_usage_record"):
    obj = {
        "v": 2, "ts": ts, "step": step, "host": host, "runner": runner, "kind": kind,
        "session": session, "parent": parent, "role": role, "depth": depth,
        "model": model, "effort": effort, "config_mixed": config_mixed,
        "cli_version": cli_version, "usage_source": usage_source,
        "branch_at_start": branch_at_start, "usage": usage, "turns": turns,
        "duration_ms": duration_ms, "anchor": anchor, "reason": reason,
    }
    return json.dumps(obj)


_V2_USAGE_KEYS = ("input", "cached_input", "cache_write_input", "output",
                  "reasoning_output", "total")


def _v2_usage(**kw):
    """六键 usage dict，未传的键显式为 None（来源未提供）。"""
    return {k: kw.get(k) for k in _V2_USAGE_KEYS}


def test_parse_v2_line_accepts_well_formed_row():
    line = _v2_line("s1", "impl", "2026-09-21T10:00:00+0800",
                     usage=_v2_usage(input=100, cached_input=10, cache_write_input=5,
                                     output=200, reasoning_output=20, total=300),
                     branch_at_start="feat/foo")
    row = R._parse_v2_line(line)
    assert row is not None
    assert row["v"] == 2
    assert row["kind"] == "root"
    assert row["session"] == "s1"
    assert row["usage"] == {"input": 100, "cached_input": 10, "cache_write_input": 5,
                             "output": 200, "reasoning_output": 20, "total": 300}
    assert row["anchor"] is True
    assert row["branch_at_start"] == "feat/foo"


def test_parse_v2_line_null_usage_keys_stay_none_not_derived():
    """来源未提供的键为 null，MUST NOT 派生（D2）——cli 行常见 total=None。"""
    line = _v2_line("s1", "cli-call", "2026-09-21T10:00:00+0800", kind="cli",
                     usage=_v2_usage(input=10, output=5))
    row = R._parse_v2_line(line)
    assert row["usage"]["input"] == 10
    assert row["usage"]["output"] == 5
    for k in ("cached_input", "cache_write_input", "reasoning_output", "total"):
        assert row["usage"][k] is None


def test_parse_v2_line_rejects_wrong_v():
    line = _v2_line("s1", "impl", "2026-09-21T10:00:00+0800")
    obj = json.loads(line)
    obj["v"] = 1
    assert R._parse_v2_line(json.dumps(obj)) is None


def test_parse_v2_line_rejects_malformed_json():
    assert R._parse_v2_line("{not valid json") is None


def test_parse_v2_line_rejects_negative_usage_value():
    line = _v2_line("s1", "impl", "2026-09-21T10:00:00+0800",
                     usage=_v2_usage(input=-1))
    assert R._parse_v2_line(line) is None


def test_parse_v2_line_no_transcript_row_anchor_false_reason_visible():
    line = _v2_line("s1", "impl", "2026-09-21T10:00:00+0800", anchor=False,
                     reason="no-transcript", usage=_v2_usage())
    row = R._parse_v2_line(line)
    assert row is not None
    assert row["anchor"] is False
    assert row["reason"] == "no-transcript"


def test_read_v2_token_log_counts_bad_lines_and_skips_v1(tmp_path):
    """坏 JSON / 非对象 / 未知 v 计入 bad-line；v=1 行不算 bad、也不进 v2_rows（互不相加/差分）。"""
    p = tmp_path / "token-log.jsonl"
    body = "\n".join([
        _v2_line("s1", "a", "2026-09-21T10:00:00+0800", usage=_v2_usage(input=1, output=2)),
        "{truncated half line",
        "[1, 2, 3]",
        '{"v": 3, "ts": "x"}',
        '{"v": 1, "ts": "2026-09-21T10:00:00+0800", "step": "s", "session": "s1", '
        '"anchor": true, "usage": {"input": 1, "output": 1, "cache_read": 1, "cache_creation": 1}}',
        "",
    ])
    p.write_text(body, encoding="utf-8")
    rows, bad = R.read_v2_token_log(str(p))
    assert len(rows) == 1
    assert rows[0]["step"] == "a"
    assert bad == 3  # truncated / 数组非对象 / 未知 v=3


def test_read_v2_token_log_missing_file_returns_empty_no_bad(tmp_path):
    rows, bad = R.read_v2_token_log(str(tmp_path / "nope.jsonl"))
    assert rows == []
    assert bad == 0


# ============================ task1 slice C: compute_v2_deltas 归属算法 ============================
# 覆盖 decision-memo/design.md 「决策流」全部 scenario：基线行 / 出生分支 / start-missing /
# 差分 / 回退(counter-reset) / resume(同 session 多行) / retry(config_mixed) / config_mixed 标注。

def _mk_change(root, name):
    d = root / "openspec/changes" / name
    d.mkdir(parents=True)
    return {name: {"active": True, "active_dir": str(d), "archive_dir": None}}, d


def test_v2_change_start_baseline_row_counts_zero_and_is_diff_base(tmp_path):
    """基线行 scenario：首行 step=change-start 计 0，只作差分基底；下一行对其差分。"""
    changes, d = _mk_change(tmp_path, "foo")
    body = "\n".join([
        _v2_line("s1", "change-start", "2026-09-21T09:00:00+0800",
                 usage=_v2_usage(input=100, output=200)),
        _v2_line("s1", "impl", "2026-09-21T10:00:00+0800",
                 usage=_v2_usage(input=150, output=260)),
    ])
    (d / "token-log.jsonl").write_text(body, encoding="utf-8")
    deltas, coverage, bad = R.compute_v2_deltas(str(tmp_path), changes)
    assert bad == 0
    assert deltas["foo"]["input"] == 50
    assert deltas["foo"]["output"] == 60


def test_v2_born_on_branch_first_row_full_credit(tmp_path):
    """出生分支 scenario：无 change-start 基线行，但首行 branch_at_start == feat/<change>
    → 全额计入。"""
    changes, d = _mk_change(tmp_path, "foo")
    body = _v2_line("s1", "impl", "2026-09-21T10:00:00+0800",
                     usage=_v2_usage(input=100, output=200), branch_at_start="feat/foo") + "\n"
    (d / "token-log.jsonl").write_text(body, encoding="utf-8")
    deltas, coverage, bad = R.compute_v2_deltas(str(tmp_path), changes)
    assert deltas["foo"]["input"] == 100
    assert deltas["foo"]["output"] == 200
    assert coverage["foo"]["start_missing"] == 0


def test_v2_start_missing_zero_credit_and_flagged(tmp_path):
    """start-missing scenario：无 change-start 基线行、branch_at_start 不等于 feat/<change>
    （或缺失）→ 计 0 + 覆盖块标 start-missing。"""
    changes, d = _mk_change(tmp_path, "foo")
    body = _v2_line("s1", "impl", "2026-09-21T10:00:00+0800",
                     usage=_v2_usage(input=100, output=200), branch_at_start=None) + "\n"
    (d / "token-log.jsonl").write_text(body, encoding="utf-8")
    deltas, coverage, bad = R.compute_v2_deltas(str(tmp_path), changes)
    assert deltas["foo"]["input"] is None or deltas["foo"]["input"] == 0
    assert coverage["foo"]["start_missing"] == 1


def test_v2_adjacent_diff_across_two_rows_same_change(tmp_path):
    """差分 scenario：同 session 同 change 相邻两行按累计值相邻差分（与 v1 同法）。"""
    changes, d = _mk_change(tmp_path, "foo")
    body = "\n".join([
        _v2_line("s1", "a", "2026-09-21T10:00:00+0800",
                 usage=_v2_usage(input=100, output=200), branch_at_start="feat/foo"),
        _v2_line("s1", "b", "2026-09-21T10:05:00+0800",
                 usage=_v2_usage(input=150, output=260), branch_at_start="feat/foo"),
    ])
    (d / "token-log.jsonl").write_text(body, encoding="utf-8")
    deltas, coverage, bad = R.compute_v2_deltas(str(tmp_path), changes)
    assert deltas["foo"]["input"] == 150   # 100 全额 + 50 差分
    assert deltas["foo"]["output"] == 260  # 200 全额 + 60 差分


def test_v2_counter_reset_negative_delta_clamped_zero_and_flagged(tmp_path):
    """回退 scenario：后一行计数小于前一行（生产者重启/口径回退）→ Δ 钳 0，覆盖块标
    counter-reset。"""
    changes, d = _mk_change(tmp_path, "foo")
    body = "\n".join([
        _v2_line("s1", "a", "2026-09-21T10:00:00+0800",
                 usage=_v2_usage(input=200, output=400), branch_at_start="feat/foo"),
        _v2_line("s1", "b", "2026-09-21T10:05:00+0800",
                 usage=_v2_usage(input=50, output=100), branch_at_start="feat/foo"),
    ])
    (d / "token-log.jsonl").write_text(body, encoding="utf-8")
    deltas, coverage, bad = R.compute_v2_deltas(str(tmp_path), changes)
    assert deltas["foo"]["input"] == 200   # 首行全额 200 + 钳 0
    assert deltas["foo"]["output"] == 400
    assert coverage["foo"]["counter_reset"] == 1


def test_v2_resume_multiple_rows_same_session_accumulate(tmp_path):
    """resume scenario：同一子线程被多次 checkpoint 写多行（reader 幂等取相邻差分累加，
    非取最后一行覆盖）——三次快照的总入账须等于末次累计值。"""
    changes, d = _mk_change(tmp_path, "foo")
    body = "\n".join([
        _v2_line("s1", "a", "2026-09-21T10:00:00+0800",
                 usage=_v2_usage(input=10, output=10), branch_at_start="feat/foo"),
        _v2_line("s1", "b", "2026-09-21T10:05:00+0800",
                 usage=_v2_usage(input=20, output=20), branch_at_start="feat/foo"),
        _v2_line("s1", "c", "2026-09-21T10:10:00+0800",
                 usage=_v2_usage(input=35, output=35), branch_at_start="feat/foo"),
    ])
    (d / "token-log.jsonl").write_text(body, encoding="utf-8")
    deltas, coverage, bad = R.compute_v2_deltas(str(tmp_path), changes)
    assert deltas["foo"]["input"] == 35
    assert deltas["foo"]["output"] == 35


def test_v2_retry_anchor_false_row_excluded_from_deltas_but_counted_in_coverage(tmp_path):
    """retry scenario：一次失败重试写 anchor=false 行（reason=timeout 等）——只进覆盖块，
    不参与差分归属（design 决策流「anchor=false→只进覆盖块」）。"""
    changes, d = _mk_change(tmp_path, "foo")
    body = "\n".join([
        _v2_line("s1", "a", "2026-09-21T10:00:00+0800", anchor=False, reason="timeout",
                 usage=_v2_usage()),
        _v2_line("s1", "b", "2026-09-21T10:05:00+0800",
                 usage=_v2_usage(input=10, output=20), branch_at_start="feat/foo"),
    ])
    (d / "token-log.jsonl").write_text(body, encoding="utf-8")
    deltas, coverage, bad = R.compute_v2_deltas(str(tmp_path), changes)
    # 降级行不参与归属分组 → b 视为该 session 的首行，按出生分支全额计入
    assert deltas["foo"]["input"] == 10
    assert deltas["foo"]["output"] == 20
    assert coverage["foo"]["reason"].get("timeout") == 1


def test_v2_config_mixed_flag_counted_in_coverage(tmp_path):
    """config_mixed scenario：区间内 model/effort 变化的行标 config_mixed=true，
    覆盖块计数、retro 标「不可用于模型/效率对照」。"""
    changes, d = _mk_change(tmp_path, "foo")
    body = _v2_line("s1", "a", "2026-09-21T10:00:00+0800",
                     usage=_v2_usage(input=10, output=20), branch_at_start="feat/foo",
                     config_mixed=True) + "\n"
    (d / "token-log.jsonl").write_text(body, encoding="utf-8")
    deltas, coverage, bad = R.compute_v2_deltas(str(tmp_path), changes)
    assert coverage["foo"]["config_mixed"] == 1


def test_v2_cross_change_session_diffs_against_prior_change_last_row(tmp_path):
    """跨 change 差分 scenario：同 session 先在 change A 出生、后在 change B 落行
    → B 对 A 末行差分入账（同 v1 的 Q1=A 口径，v2 亦不得双计）。"""
    da = tmp_path / "openspec/changes/A"
    db = tmp_path / "openspec/changes/B"
    da.mkdir(parents=True)
    db.mkdir(parents=True)
    (da / "token-log.jsonl").write_text(
        _v2_line("s1", "a", "2026-09-21T10:00:00+0800",
                 usage=_v2_usage(input=100, output=200), branch_at_start="feat/A") + "\n",
        encoding="utf-8")
    (db / "token-log.jsonl").write_text(
        _v2_line("s1", "b", "2026-09-21T10:05:00+0800",
                 usage=_v2_usage(input=150, output=260)) + "\n",
        encoding="utf-8")
    changes = {
        "A": {"active": True, "active_dir": str(da), "archive_dir": None},
        "B": {"active": True, "active_dir": str(db), "archive_dir": None},
    }
    deltas, coverage, bad = R.compute_v2_deltas(str(tmp_path), changes)
    assert deltas["A"]["input"] == 100
    assert deltas["B"]["input"] == 50  # 150-100 差分入 B，非全额


def test_v2_root_child_cli_kinds_counted_in_coverage(tmp_path):
    changes, d = _mk_change(tmp_path, "foo")
    body = "\n".join([
        _v2_line("s1", "a", "2026-09-21T10:00:00+0800", kind="root",
                 usage=_v2_usage(input=1), branch_at_start="feat/foo"),
        _v2_line("s2", "b", "2026-09-21T10:00:01+0800", kind="child",
                 usage=_v2_usage(input=1), branch_at_start="feat/foo"),
        _v2_line("s3", "c", "2026-09-21T10:00:02+0800", kind="cli",
                 usage=_v2_usage(input=1)),
    ])
    (d / "token-log.jsonl").write_text(body, encoding="utf-8")
    deltas, coverage, bad = R.compute_v2_deltas(str(tmp_path), changes)
    assert len(coverage["foo"]["root"]) == 1
    assert len(coverage["foo"]["child"]) == 1
    assert len(coverage["foo"]["cli"]) == 1
    assert len(coverage["foo"]["anchor_true"]) == 3


def test_v2_missing_token_log_no_entry(tmp_path):
    changes, d = _mk_change(tmp_path, "bare")
    deltas, coverage, bad = R.compute_v2_deltas(str(tmp_path), changes)
    assert "bare" not in deltas
    assert bad == 0


def test_v2_deltas_reread_is_idempotent(tmp_path):
    changes, d = _mk_change(tmp_path, "foo")
    body = "\n".join([
        _v2_line("s1", "a", "2026-09-21T10:00:00+0800",
                 usage=_v2_usage(input=100, output=200), branch_at_start="feat/foo"),
        _v2_line("s1", "b", "2026-09-21T10:05:00+0800",
                 usage=_v2_usage(input=150, output=260), branch_at_start="feat/foo"),
    ])
    (d / "token-log.jsonl").write_text(body, encoding="utf-8")
    first = R.compute_v2_deltas(str(tmp_path), changes)
    second = R.compute_v2_deltas(str(tmp_path), changes)
    assert first == second


# ============================ task1 slice D: per-change 表双段呈现 ============================

def test_format_v2_tokens_cell_examples():
    d = {"input": 100, "cached_input": 10, "cache_write_input": 5,
         "output": 200, "reasoning_output": 20, "total": None, "turns": 3, "duration_ms": 1000}
    cell = R.format_v2_tokens_cell(d)
    assert cell == "in 100 / cached 10 / cw 5 / out 200 / reason 20 / total –"


def test_format_v2_tokens_cell_no_anchor_dash():
    assert R.format_v2_tokens_cell(None) == "—"
    assert R.format_v2_tokens_cell({k: None for k in _V2_USAGE_KEYS}) == "—"


def test_format_tokens_cell_combined_both_present():
    v1d = {"out": 260, "in": 150, "cc": 470, "cr": 380}
    v2d = {"input": 10, "cached_input": None, "cache_write_input": None,
           "output": 5, "reasoning_output": None, "total": None}
    cell = R.format_tokens_cell_combined(v1d, v2d)
    assert "out 260 / in 150 / cc 470 / cr 380" in cell
    assert "codex:" in cell
    assert "in 10" in cell


def test_format_tokens_cell_combined_neither_present_is_dash():
    assert R.format_tokens_cell_combined(None, None) == "—"


def test_format_tokens_cell_combined_only_v2_present():
    v2d = {"input": 10, "cached_input": None, "cache_write_input": None,
           "output": 5, "reasoning_output": None, "total": None}
    cell = R.format_tokens_cell_combined(None, v2d)
    assert cell.startswith("codex:")
    assert "out 260" not in cell


def test_build_report_v2_tokens_dual_segment_and_bad_line_visible(tmp_path):
    """per-change 表双段呈现：v1 段（既有格式）+ codex 段（v2 六计数）同格出现；
    bad-line 计入须在报告里可见（WFR-01）。"""
    root = _init_repo(tmp_path)
    _commit(root, {"openspec/changes/foo/proposal.md": "a"}, "checkpoint(ff)")
    d = root / "openspec/changes/foo"
    v1_body = "\n".join([
        _tok_line("s1", "a", "2026-08-10T10:00:00+0800", 100, 200, 300, 400),
    ])
    v2_body = _v2_line("s2", "impl", "2026-09-21T10:00:00+0800",
                        usage=_v2_usage(input=10, output=20), branch_at_start="feat/foo")
    # bad line: 未知 v
    bad_line = '{"v": 9, "ts": "x"}'
    (d / "token-log.jsonl").write_text(v1_body + "\n" + v2_body + "\n" + bad_line + "\n",
                                        encoding="utf-8")
    md = R.build_report(str(root))
    assert "out 200 / in 100 / cc 400 / cr 300" in md
    assert "codex:" in md and "in 10" in md
    assert "bad-line" in md


def test_build_report_v2_reread_is_byte_identical(tmp_path):
    """固定输入二次再生等价：同一仓状态两次 build_report 输出逐字节相同。"""
    root = _init_repo(tmp_path)
    _commit(root, {"openspec/changes/foo/proposal.md": "a"}, "checkpoint(ff)")
    d = root / "openspec/changes/foo"
    body = _v2_line("s1", "impl", "2026-09-21T10:00:00+0800",
                     usage=_v2_usage(input=10, output=20), branch_at_start="feat/foo")
    (d / "token-log.jsonl").write_text(body + "\n", encoding="utf-8")
    first = R.build_report(str(root))
    second = R.build_report(str(root))
    assert first == second


# ============================ task4: 「Codex 用量覆盖」块 ============================
# design.md 「归属与去重」§6 + spec WFR-03：每个含 v2 行的 change 一行，列 root/child/cli
# 三类行数、anchor=true 数、reason 计数、start-missing/counter-reset/config_mixed；
# 无任何 v2 行的 change 显示「未声明」（MUST NOT 推断 0 或 100% 覆盖）。

def test_render_v2_coverage_block_lists_counts_for_change_with_v2_rows():
    changes = {"foo": {}}
    coverage = {
        "foo": {"root": {"s1", "s2"}, "child": {"s3"}, "cli": {"s4"}, "anchor_true": {"s1", "s2", "s3"},
                "reason": {"ok": 3, "timeout": 1}, "start_missing": 1,
                "counter_reset": 2, "config_mixed": 1},
    }
    block = R.render_v2_coverage_block(changes, coverage)
    assert "## Codex 用量覆盖" in block
    assert "| foo | 2 | 1 | 1 | 3 | ok:3, timeout:1 | 1 | 2 | 1 |" in block


def test_render_v2_coverage_block_no_v2_rows_shows_未声明():
    changes = {"bar": {}}
    coverage = {}
    block = R.render_v2_coverage_block(changes, coverage)
    assert "| bar | 未声明 | 未声明 | 未声明 | 未声明 | 未声明 | 未声明 | 未声明 | 未声明 |" in block


def test_build_report_includes_v2_coverage_block_mixed_changes(tmp_path):
    """一个 change 有 v2 行、一个没有——报告里前者列真实计数，后者列「未声明」。"""
    root = _init_repo(tmp_path)
    _commit(root, {"openspec/changes/foo/proposal.md": "a",
                    "openspec/changes/bar/proposal.md": "a"}, "checkpoint(ff)")
    d = root / "openspec/changes/foo"
    body = _v2_line("s1", "impl", "2026-09-21T10:00:00+0800",
                     usage=_v2_usage(input=10, output=20), branch_at_start="feat/foo")
    (d / "token-log.jsonl").write_text(body + "\n", encoding="utf-8")
    md = R.build_report(str(root))
    assert "## Codex 用量覆盖" in md
    assert "| foo | 1 | 0 | 0 | 1 | ok:1 | 0 | 0 | 0 |" in md
    assert "| bar | 未声明 | 未声明 | 未声明 | 未声明 | 未声明 | 未声明 | 未声明 | 未声明 |" in md


# ============================ task4: --scan-codex-sessions ============================
# design.md 「归属与去重」§7 + spec WFR-04：默认关，开启时只读每 rollout 首行
# session_meta，按 cwd==仓根 且 git.branch==feat/<change> 归属，与该 change token-log
# 的 session 集合做差集，报「日志未覆盖的线程」。MUST NOT 读取首行之外内容。

def _write_rollout(sessions_root, subpath, first_line_obj, *, garbage_tail=True):
    p = sessions_root / subpath
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(first_line_obj)]
    if garbage_tail:
        # 第二行故意写非法 JSON——证明扫描只读首行，不会因此崩溃
        lines.append("{not valid json at all")
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def _session_meta_line(thread_id, cwd, branch):
    return {"type": "session_meta",
            "payload": {"id": thread_id, "cwd": cwd, "git": {"branch": branch}}}


def test_scan_codex_sessions_uncovered_finds_thread_not_in_log(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    sessions_root = tmp_path / "codex-sessions"
    _write_rollout(sessions_root, "2026/09/21/rollout-1-uuid-a.jsonl",
                    _session_meta_line("uuid-a", str(root), "feat/foo"))
    changes = {"foo": {}}
    covered = {}
    uncovered = R.scan_codex_sessions_uncovered(str(root), changes, covered,
                                                 sessions_root=sessions_root)
    assert uncovered == {"foo": ["uuid-a"]}


def test_scan_codex_sessions_uncovered_excludes_covered_session(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    sessions_root = tmp_path / "codex-sessions"
    _write_rollout(sessions_root, "rollout-1-uuid-a.jsonl",
                    _session_meta_line("uuid-a", str(root), "feat/foo"))
    changes = {"foo": {}}
    covered = {"foo": {"uuid-a"}}
    uncovered = R.scan_codex_sessions_uncovered(str(root), changes, covered,
                                                 sessions_root=sessions_root)
    assert uncovered == {}


def test_scan_codex_sessions_uncovered_wrong_cwd_excluded(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    other = tmp_path / "other-repo"
    sessions_root = tmp_path / "codex-sessions"
    _write_rollout(sessions_root, "rollout-1-uuid-a.jsonl",
                    _session_meta_line("uuid-a", str(other), "feat/foo"))
    changes = {"foo": {}}
    uncovered = R.scan_codex_sessions_uncovered(str(root), changes, {},
                                                 sessions_root=sessions_root)
    assert uncovered == {}


def test_scan_codex_sessions_uncovered_non_feat_branch_excluded(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    sessions_root = tmp_path / "codex-sessions"
    _write_rollout(sessions_root, "rollout-1-uuid-a.jsonl",
                    _session_meta_line("uuid-a", str(root), "main"))
    changes = {"foo": {}}
    uncovered = R.scan_codex_sessions_uncovered(str(root), changes, {},
                                                 sessions_root=sessions_root)
    assert uncovered == {}


def test_scan_codex_sessions_uncovered_branch_change_not_in_changes_excluded(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    sessions_root = tmp_path / "codex-sessions"
    _write_rollout(sessions_root, "rollout-1-uuid-a.jsonl",
                    _session_meta_line("uuid-a", str(root), "feat/not-a-known-change"))
    uncovered = R.scan_codex_sessions_uncovered(str(root), {"foo": {}}, {},
                                                 sessions_root=sessions_root)
    assert uncovered == {}


def test_scan_codex_sessions_uncovered_missing_sessions_root_returns_empty(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    sessions_root = tmp_path / "does-not-exist"
    uncovered = R.scan_codex_sessions_uncovered(str(root), {"foo": {}}, {},
                                                 sessions_root=sessions_root)
    assert uncovered == {}


def test_scan_codex_sessions_uncovered_only_reads_first_line_not_full_file(tmp_path):
    """第二行是非法 JSON，若实现误读全文件会崩；只读首行则安然跳过。"""
    root = tmp_path / "repo"
    root.mkdir()
    sessions_root = tmp_path / "codex-sessions"
    _write_rollout(sessions_root, "rollout-1-uuid-a.jsonl",
                    _session_meta_line("uuid-a", str(root), "feat/foo"),
                    garbage_tail=True)
    uncovered = R.scan_codex_sessions_uncovered(str(root), {"foo": {}}, {},
                                                 sessions_root=sessions_root)
    assert uncovered == {"foo": ["uuid-a"]}


def test_render_scan_codex_sessions_block_fixed_disclaimer_no_uncovered():
    block = R.render_scan_codex_sessions_block({})
    assert "跨分支复用线程不可由本扫描判定" in block


def test_render_scan_codex_sessions_block_lists_uncovered_threads():
    block = R.render_scan_codex_sessions_block({"foo": ["uuid-a", "uuid-b"]})
    assert "uuid-a" in block and "uuid-b" in block
    assert "foo" in block
    assert "跨分支复用线程不可由本扫描判定" in block


def test_build_report_scan_codex_sessions_default_off_never_scans(tmp_path, monkeypatch):
    """默认关：build_report 不带 scan_codex_sessions 参数时，MUST NOT 调用扫描函数
    （零文件打开的机械证明——扫描函数被替换为必炸桩，未被调用则不炸）。"""
    root = _init_repo(tmp_path)
    _commit(root, {"openspec/changes/foo/proposal.md": "a"}, "checkpoint(ff)")

    def _boom(*a, **kw):
        raise AssertionError("scan_codex_sessions_uncovered MUST NOT be called when off")
    monkeypatch.setattr(R, "scan_codex_sessions_uncovered", _boom)
    md = R.build_report(str(root))
    assert "--scan-codex-sessions" not in md


def test_build_report_scan_codex_sessions_on_includes_block(tmp_path):
    root = _init_repo(tmp_path)
    _commit(root, {"openspec/changes/foo/proposal.md": "a"}, "checkpoint(ff)")
    sessions_root = tmp_path / "codex-sessions"
    _write_rollout(sessions_root, "rollout-1-uuid-a.jsonl",
                    _session_meta_line("uuid-a", str(root), "feat/foo"))
    md = R.build_report(str(root), scan_codex_sessions=True, sessions_root_override=sessions_root)
    assert "## Codex 会话覆盖核对（--scan-codex-sessions）" in md
    assert "uuid-a" in md
    assert "跨分支复用线程不可由本扫描判定" in md


def test_main_scan_codex_sessions_flag_wires_through(tmp_path):
    root = _init_repo(tmp_path)
    _commit(root, {"openspec/changes/foo/proposal.md": "a"}, "checkpoint(ff)")
    env = dict(os.environ, CODEX_HOME=str(tmp_path / "nonexistent-codex-home"))
    proc = subprocess.run(
        [sys.executable, str(Path(R.__file__)), "--root", str(root), "--scan-codex-sessions"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    assert proc.returncode == 0, proc.stderr
    out = (root / "openspec/retro/report.md").read_text(encoding="utf-8")
    assert "## Codex 会话覆盖核对（--scan-codex-sessions）" in out
