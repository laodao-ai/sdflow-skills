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
    assert R.map_stage("feat(x): 随手") == "unknown"


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
    import lens_metric_aggregate as LMA
    r = {"layer": "spec-review", "lens": "", "runner": "claude", "site": "—"}
    assert LMA.group_key(r) == ("spec-review", "?", "claude", "—")
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
