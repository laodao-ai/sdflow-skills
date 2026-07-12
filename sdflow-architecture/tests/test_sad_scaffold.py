import subprocess, sys, pathlib, shutil
from conftest import make_sad  # noqa: E402  (模块级导入：repo-wide pytest 下多 tests/ 目录同名
                                # conftest.py 在 sys.modules 只留一个绑定；模块级导入随本文件
                                # collection 期早绑定，避开函数级运行期延迟导入撞名的坑)
SCRIPT = pathlib.Path(__file__).parent.parent / "scripts" / "sad_scaffold.py"

def run(args, cwd):
    return subprocess.run([sys.executable, str(SCRIPT)] + args,
                          capture_output=True, text=True, cwd=cwd)

def make_repo(tmp_path, with_openspec=True):
    if with_openspec:
        (tmp_path / "openspec" / "changes").mkdir(parents=True)
        (tmp_path / "openspec" / "specs").mkdir(parents=True)
    return tmp_path

def test_preflight_no_openspec_fail_closed(tmp_path):
    r = run(["init", "--root", str(make_repo(tmp_path, with_openspec=False))], tmp_path)
    assert r.returncode == 3 and "sdflow-init" in r.stderr   # 指引含完整入口，不自造布局
    assert not (tmp_path / "openspec").exists()

def test_preflight_level2_first_create(tmp_path):
    repo = make_repo(tmp_path)
    r = run(["init", "--root", str(repo)], tmp_path)
    assert r.returncode == 0 and "首次创建" in (r.stdout + r.stderr)
    assert (repo / "openspec" / "adr").is_dir()
    assert "## Language" in (repo / "openspec" / "CONTEXT.md").read_text(encoding="utf-8")
    sad = (repo / "openspec" / "architecture" / "sad.md").read_text(encoding="utf-8")
    assert "sad_status: draft" in sad
    log = (repo / "openspec" / "architecture" / "sad-log.md").read_text(encoding="utf-8")
    assert "init" in log

def test_singleton_no_silent_overwrite(tmp_path):
    repo = make_repo(tmp_path)
    run(["init", "--root", str(repo)], tmp_path)
    marked = repo / "openspec" / "architecture" / "sad.md"
    marked.write_text(marked.read_text(encoding="utf-8") + "\n定制内容\n", encoding="utf-8")
    r = run(["init", "--root", str(repo)], tmp_path)
    assert r.returncode == 4 and "continue" in r.stderr and "replan" in r.stderr
    assert "定制内容" in marked.read_text(encoding="utf-8")      # 未被覆盖
    r2 = run(["init", "--root", str(repo), "--on-exists", "continue"], tmp_path)
    assert r2.returncode == 0 and "定制内容" in marked.read_text(encoding="utf-8")
    r3 = run(["init", "--root", str(repo), "--on-exists", "replan", "--reason", "方向推翻"], tmp_path)
    assert r3.returncode == 0 and "定制内容" not in marked.read_text(encoding="utf-8")
    assert "replan" in (repo / "openspec" / "architecture" / "sad-log.md").read_text(encoding="utf-8")

def test_log_append_only_bytes(tmp_path):
    repo = make_repo(tmp_path)
    run(["init", "--root", str(repo)], tmp_path)
    logp = repo / "openspec" / "architecture" / "sad-log.md"
    before = logp.read_bytes()
    r = run(["log", "--root", str(repo), "--line", "step=2 reached"], tmp_path)
    assert r.returncode == 0
    after = logp.read_bytes()
    assert after[:len(before)] == before and b"step=2 reached" in after

def test_atomic_no_temp_residue(tmp_path):
    repo = make_repo(tmp_path)
    run(["init", "--root", str(repo)], tmp_path)
    assert not list((repo / "openspec" / "architecture").glob("*.tmp*"))

def test_log_before_init_exit2(tmp_path):
    # openspec/ 布局存在（changes+specs），但从未跑过 init → 无 sad-log.md
    repo = make_repo(tmp_path)
    r = run(["log", "--root", str(repo), "--line", "x"], tmp_path)
    assert r.returncode == 2
    assert "sad-log.md 不存在" in r.stderr

def test_template_missing_fail_closed_no_partial_layout(tmp_path):
    # 模拟"安装不完整"：把脚本复制到独立目录，references/ 存在但缺 sad-template.md
    fake_install = tmp_path / "fake_install"
    fake_scripts = fake_install / "scripts"
    fake_scripts.mkdir(parents=True)
    (fake_install / "references").mkdir(parents=True)
    shutil.copy(SCRIPT, fake_scripts / "sad_scaffold.py")
    shutil.copy(SCRIPT.parent / "sad_schema.py", fake_scripts / "sad_schema.py")

    consumer = tmp_path / "consumer"
    make_repo(consumer)   # 新鲜消费仓：openspec/changes + openspec/specs 已建，无 adr/CONTEXT.md

    r = subprocess.run(
        [sys.executable, str(fake_scripts / "sad_scaffold.py"), "init", "--root", str(consumer)],
        capture_output=True, text=True, cwd=tmp_path,
    )
    assert r.returncode == 2
    assert "sad-template.md" in r.stderr
    # fail-closed：模版缺失须在任何 preflight 副作用之前拒绝，不留半套布局
    assert not (consumer / "openspec" / "adr").exists()
    assert not (consumer / "openspec" / "CONTEXT.md").exists()


def seed(repo, **kw):
    p = repo / "openspec" / "architecture" / "sad.md"
    p.write_text(make_sad(**kw), encoding="utf-8")
    return p

ANSWERED = {"positioning": "answered", "external_systems": "answered", "hard_constraints": "answered"}

def test_missing_fact_locks_draft(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, facts={**ANSWERED, "external_systems": "missing"})
    slice_f = tmp_path / "s.md"; slice_f.write_text("- 穿越点[采集端]：§5\n", encoding="utf-8")
    r = run(["transition", "--root", str(repo), "--to", "skeleton-ready",
             "--slice-file", str(slice_f)], tmp_path)
    assert r.returncode == 5 and "external_systems" in r.stderr   # 指明缺失问项

def test_unresolved_assumption_locks_draft(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, facts=ANSWERED, assumptions=[(1, "接受"), (2, "未处置")])
    slice_f = tmp_path / "s.md"; slice_f.write_text("- 穿越点[采集端]：§5\n", encoding="utf-8")
    r = run(["transition", "--root", str(repo), "--to", "skeleton-ready",
             "--slice-file", str(slice_f)], tmp_path)
    assert r.returncode == 5 and "假设-2" in r.stderr

def test_happy_path_to_skeleton_ready_inserts_slice(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, facts=ANSWERED, assumptions=[(1, "接受")], cache=0)
    slice_f = tmp_path / "s.md"
    slice_f.write_text("- 穿越点[采集端]：§5.1 contract 条目\n- 骨架 DoD：…\n- 建议 change 名：skeleton-x\n", encoding="utf-8")
    r = run(["transition", "--root", str(repo), "--to", "skeleton-ready",
             "--slice-file", str(slice_f)], tmp_path)
    assert r.returncode == 0
    text = (repo / "openspec" / "architecture" / "sad.md").read_text(encoding="utf-8")
    assert "sad_status: skeleton-ready" in text and "## 骨架切片建议" in text
    assert "skeleton-ready" in (repo / "openspec" / "architecture" / "sad-log.md").read_text(encoding="utf-8")

def test_pierce_set_mismatch_refused(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, facts=ANSWERED, subsystems=("采集端", "上报端"))
    slice_f = tmp_path / "s.md"; slice_f.write_text("- 穿越点[采集端]：§5\n", encoding="utf-8")
    r = run(["transition", "--root", str(repo), "--to", "skeleton-ready",
             "--slice-file", str(slice_f)], tmp_path)
    assert r.returncode == 5 and "上报端" in r.stderr

def test_out_of_table_transition_refused(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, facts=ANSWERED)                       # draft
    r = run(["transition", "--root", str(repo), "--to", "validated", "--dod-confirmed"], tmp_path)
    assert r.returncode == 5 and "迁移表" in r.stderr # draft→validated 表外

def test_validated_removes_slice_and_fallback_logs_reason(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, status="skeleton-ready", facts=ANSWERED, slice_section=True)
    r = run(["transition", "--root", str(repo), "--to", "validated", "--dod-confirmed"], tmp_path)
    assert r.returncode == 0
    text = (repo / "openspec" / "architecture" / "sad.md").read_text(encoding="utf-8")
    assert "## 骨架切片建议" not in text and "sad_status: validated" in text
    r2 = run(["transition", "--root", str(repo), "--to", "draft", "--reason", "contract 大面积否决"], tmp_path)
    assert r2.returncode == 0
    assert "contract 大面积否决" in (repo / "openspec" / "architecture" / "sad-log.md").read_text(encoding="utf-8")

def test_set_fact_and_set_assumption_update_cache(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, assumptions=[(1, "未处置")], cache=1)
    r = run(["set-fact", "--root", str(repo), "--fact", "positioning=answered"], tmp_path)
    assert r.returncode == 0
    r = run(["set-assumption", "--root", str(repo), "--assumption", "1=接受"], tmp_path)
    assert r.returncode == 0
    text = (repo / "openspec" / "architecture" / "sad.md").read_text(encoding="utf-8")
    assert "positioning: answered" in text and "assumptions_open: 0" in text and "| 接受 |" in text
    r = run(["set-assumption", "--root", str(repo), "--assumption", "9=接受"], tmp_path)
    assert r.returncode == 2                          # 行不存在 fail-closed

def test_slice_file_missing_exit2(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, facts=ANSWERED)
    slice_f = tmp_path / "nonexistent.md"
    r = run(["transition", "--root", str(repo), "--to", "skeleton-ready",
             "--slice-file", str(slice_f)], tmp_path)
    assert r.returncode == 2 and "slice 文件不存在" in r.stderr

def test_write_commands_before_init_exit2(tmp_path):
    # openspec/ 布局存在但未 init，故无 sad.md
    repo = make_repo(tmp_path)
    r1 = run(["set-fact", "--root", str(repo), "--fact", "positioning=answered"], tmp_path)
    assert r1.returncode == 2 and "sad.md 不存在" in r1.stderr
    r2 = run(["set-assumption", "--root", str(repo), "--assumption", "1=接受"], tmp_path)
    assert r2.returncode == 2 and "sad.md 不存在" in r2.stderr
    r3 = run(["transition", "--root", str(repo), "--to", "skeleton-ready"], tmp_path)
    assert r3.returncode == 2 and "sad.md 不存在" in r3.stderr


# ---- Task 5: scaffold 分家机械化（adr-new + context-add） -------------------------------

def test_adr_new_max_plus_one(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    (repo / "openspec" / "adr" / "0007-x.md").write_text("x", encoding="utf-8")
    r = run(["adr-new", "--root", str(repo), "--title", "分解判据", "--slug", "decomposition"], tmp_path)
    assert r.returncode == 0
    assert (repo / "openspec" / "adr" / "0008-decomposition.md").exists()

def test_adr_new_unrecognized_pattern_fail_closed(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    (repo / "openspec" / "adr" / "notes.md").write_text("x", encoding="utf-8")
    r = run(["adr-new", "--root", str(repo), "--title", "T", "--slug", "t"], tmp_path)
    assert r.returncode == 2 and "notes.md" in r.stderr          # 留人工，--number 可越
    r2 = run(["adr-new", "--root", str(repo), "--title", "T", "--slug", "t", "--number", "12"], tmp_path)
    assert r2.returncode == 0 and (repo / "openspec" / "adr" / "0012-t.md").exists()

def test_context_add_append_and_conflict(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    r = run(["context-add", "--root", str(repo), "--term", "SAD", "--definition", "系统架构设计文档"], tmp_path)
    assert r.returncode == 0
    ctx = (repo / "openspec" / "CONTEXT.md").read_text(encoding="utf-8")
    assert "**SAD**" in ctx
    r2 = run(["context-add", "--root", str(repo), "--term", "SAD", "--definition", "另一定义"], tmp_path)
    assert r2.returncode == 2 and "已存在" in r2.stderr
    assert "另一定义" not in (repo / "openspec" / "CONTEXT.md").read_text(encoding="utf-8")

def test_adr_new_bad_slug_exit2(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    r = run(["adr-new", "--root", str(repo), "--title", "T", "--slug", "Bad_Slug!"], tmp_path)
    assert r.returncode == 2
    assert not list((repo / "openspec" / "adr").glob("*Bad*"))

def test_adr_new_target_exists_exit2(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    existing = repo / "openspec" / "adr" / "0007-decomposition.md"
    existing.write_text("既有内容", encoding="utf-8")
    r = run(["adr-new", "--root", str(repo), "--title", "T", "--slug", "decomposition",
             "--number", "7"], tmp_path)
    assert r.returncode == 2 and "0007-decomposition.md" in r.stderr
    assert existing.read_text(encoding="utf-8") == "既有内容"   # 未被覆盖

def test_adr_new_empty_dir_starts_at_0001(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    assert not list((repo / "openspec" / "adr").glob("*.md"))
    r = run(["adr-new", "--root", str(repo), "--title", "T", "--slug", "t"], tmp_path)
    assert r.returncode == 0
    assert (repo / "openspec" / "adr" / "0001-t.md").exists()

def test_adr_new_ignores_readme(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    (repo / "openspec" / "adr" / "README.md").write_text("非编号命名，须被忽略", encoding="utf-8")
    r = run(["adr-new", "--root", str(repo), "--title", "T", "--slug", "t"], tmp_path)
    assert r.returncode == 0
    assert (repo / "openspec" / "adr" / "0001-t.md").exists()

def test_adr_new_skeleton_content(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    r = run(["adr-new", "--root", str(repo), "--title", "决策标题", "--slug", "decision-x"], tmp_path)
    assert r.returncode == 0
    created = repo / "openspec" / "adr" / "0001-decision-x.md"
    assert str(created) in r.stdout
    text = created.read_text(encoding="utf-8")
    assert text.startswith("# ADR 0001: 决策标题\n\n- Status: Proposed\n- Date: ")
    assert "## Context\n\n## Decision\n\n## Consequences\n" in text

def test_context_add_creates_language_section_if_missing(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    ctx_path = repo / "openspec" / "CONTEXT.md"
    ctx_path.write_text("# Context\n\n## Other\n\nsomething\n", encoding="utf-8")
    r = run(["context-add", "--root", str(repo), "--term", "X", "--definition", "定义X"], tmp_path)
    assert r.returncode == 0
    text = ctx_path.read_text(encoding="utf-8")
    assert "## Language" in text and "**X**" in text and "定义X" in text

def test_adr_new_no_openspec_exit3(tmp_path):
    repo = make_repo(tmp_path, with_openspec=False)
    r = run(["adr-new", "--root", str(repo), "--title", "T", "--slug", "t"], tmp_path)
    assert r.returncode == 3 and "sdflow-init" in r.stderr
    assert not (repo / "openspec").exists()

def test_context_add_no_openspec_exit3(tmp_path):
    repo = make_repo(tmp_path, with_openspec=False)
    r = run(["context-add", "--root", str(repo), "--term", "X", "--definition", "D"], tmp_path)
    assert r.returncode == 3 and "sdflow-init" in r.stderr
    assert not (repo / "openspec").exists()

def test_adr_new_missing_sad_log_notice_not_blocking(tmp_path):
    # openspec/ 布局存在（changes+specs）但从未跑过 sad_scaffold init → 无 sad-log.md；
    # adr-new 合法运行于此态，MUST NOT 因日志缺失被拒——显式提示 + 继续 + exit 0。
    repo = make_repo(tmp_path)
    r = run(["adr-new", "--root", str(repo), "--title", "T", "--slug", "t"], tmp_path)
    assert r.returncode == 0
    assert (repo / "openspec" / "adr" / "0001-t.md").exists()
    assert not (repo / "openspec" / "architecture" / "sad-log.md").exists()
    assert "sad-log" in (r.stdout + r.stderr)

def test_context_add_missing_sad_log_notice_not_blocking(tmp_path):
    repo = make_repo(tmp_path)
    r = run(["context-add", "--root", str(repo), "--term", "X", "--definition", "D"], tmp_path)
    assert r.returncode == 0
    assert not (repo / "openspec" / "architecture" / "sad-log.md").exists()
    assert "sad-log" in (r.stdout + r.stderr)

def test_adr_new_and_context_add_append_log_when_present(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    run(["adr-new", "--root", str(repo), "--title", "T", "--slug", "t"], tmp_path)
    run(["context-add", "--root", str(repo), "--term", "Y", "--definition", "D"], tmp_path)
    log = (repo / "openspec" / "architecture" / "sad-log.md").read_text(encoding="utf-8")
    assert "adr-new 0001-t" in log
    assert "context-add Y" in log
