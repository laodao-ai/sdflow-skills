import sys
import os
import subprocess
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
                          capture_output=True, text=True, errors="replace").stdout


def _init_repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    return tmp_path


def _commit(root, files: dict, msg):
    for rel, body in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body)
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
    commits = [
        {"sha": "a", "ts": 1000, "subject": "checkpoint(ff)"},
        {"sha": "b", "ts": 1600, "subject": "checkpoint(grill)"},       # ff→grill: 600s=10min 归 ff
        {"sha": "c", "ts": 1500, "subject": "checkpoint(spec-review)"}, # 负 Δ → 钳 0 归 grill
    ]
    got = R.stage_walltimes(str(tmp_path), "foo", commits)
    assert got["stages"]["ff"] == 10.0
    assert got["stages"].get("grill", 0) == 0.0
    assert got["reorder_suspected"] is True
    assert got["n_ckpt"] == 3


ANCHOR = ('<!-- sdflow:lens-metric v1 layer="{layer}" lens="domain" runner="claude" '
          'site="—" findings="{f}" 采纳="{a}" 裁掉="0" defer="0" 独立="{ind}" '
          'sev="致0/高1/中0/低0" -->')


def test_lens_value_active_change_has_anchor(tmp_path):
    d = tmp_path / "openspec/changes/live"
    d.mkdir(parents=True)
    (d / "spec-review-report.md").write_text(
        ANCHOR.format(layer="spec-review", f=9, a=9, ind=6) + "\n")
    (d / "code-review-report.md").write_text(
        ANCHOR.format(layer="code-review", f=4, a=3, ind=2) + "\n")
    info = {"active": True, "active_dir": str(d), "archive_dir": None}
    v = R.lens_value_for_change(info)
    assert v["has_anchor"] is True
    assert v["sum_findings"] == 13
    assert "spec-review" in v["by_layer"] and "code-review" in v["by_layer"]


def test_lens_value_no_anchor(tmp_path):
    d = tmp_path / "openspec/changes/bare"
    d.mkdir(parents=True)
    (d / "proposal.md").write_text("no anchor here")
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
        ANCHOR.format(layer="spec-review", f="-7", a="abc", ind=1) + "\n")
    info = {"active": True, "active_dir": str(d), "archive_dir": None}
    v = R.lens_value_for_change(info)
    assert v["num_bad"] is True


HRTG = '<!-- sdflow:hr-tg v1 hit="{hit}" evidence="x" -->'


def test_hr_tg_two_columns(tmp_path):
    d = tmp_path / "openspec/changes/hh"; d.mkdir(parents=True)
    (d / "spec-review-report.md").write_text(HRTG.format(hit="none") + "\n")
    (d / "code-review-report.md").write_text(HRTG.format(hit="TG-06") + "\n")
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
    fp.write_text(HRTG.format(hit="TG-01") + "\n")

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
    (d / "spec-review-report.md").write_text(content)
    got = R._read_hr_hit(str(d), "spec-review-report.md")
    assert got == "none"


def test_hr_tg_multi_anchor_takes_last(tmp_path):
    """[impl-review-fix F7] 反证测试：同一报告内多条 hr-tg 锚时取最后一条=最终判定，非 first-wins。
    修前：_read_hr_hit 遇首个锚即 return，本测试 FAIL（得到 "none" 而非 "TG-06"）。
    """
    d = tmp_path / "openspec/changes/hh"; d.mkdir(parents=True)
    content = HRTG.format(hit="none") + "\n" + HRTG.format(hit="TG-06") + "\n"
    (d / "code-review-report.md").write_text(content)
    got = R._read_hr_hit(str(d), "code-review-report.md")
    assert got == "TG-06"


def test_build_report_coverage_counts(tmp_path):
    root = _init_repo(tmp_path)
    _commit(root, {"openspec/changes/foo/proposal.md": "a"}, "checkpoint(ff)")
    _commit(root, {"openspec/changes/foo/design.md": "b"}, "checkpoint(grill)")
    d = root / "openspec/changes/foo"
    (d / "spec-review-report.md").write_text(ANCHOR.format(layer="spec-review", f=9, a=9, ind=6) + "\n")
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
    target = tmp_path / "openspec/retro/report.md"
    target.parent.mkdir(parents=True)
    target.write_text("old")
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
            ANCHOR.format(layer="spec-review", f=1, a=1, ind=1) + "\n")
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
            ANCHOR.format(layer="spec-review", f=1, a=1, ind=1) + "\n")
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
            ANCHOR.format(layer="spec-review", f=1, a=1, ind=1) + "\n")
    block = R.surfacing_block(str(tmp_path))
    assert "出现轮数 3" in block


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
    (d / "spec-review-report.md").write_text("\n".join([anchor] * 10) + "\n")
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
