import subprocess, sys, pathlib, shutil, os, unicodedata
import pytest
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
    shutil.copy(SCRIPT.parent / "sad_lint.py", fake_scripts / "sad_lint.py")  # B1 迁移前复检依赖

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

def _log_walkthrough(repo, tmp_path):
    """B13 前置：写入冷走查 + 升档判定留痕两行（skeleton-ready 迁移的存在性锚）。"""
    run(["log", "--root", str(repo), "--line", "冷走查完成，无阻断项"], tmp_path)
    run(["log", "--root", str(repo), "--line", "升档判定：满足 skeleton-ready 条件"], tmp_path)

def test_happy_path_to_skeleton_ready_inserts_slice(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, facts=ANSWERED, assumptions=[(1, "接受")], cache=0)
    _log_walkthrough(repo, tmp_path)   # B13 前置留痕
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
    # B1：升 validated 要求 contract 已达 validated（否则前置复检拒），故 seed contract=validated
    seed(repo, status="skeleton-ready", facts=ANSWERED, slice_section=True, contract="validated")
    r = run(["transition", "--root", str(repo), "--to", "validated", "--dod-confirmed"], tmp_path)
    assert r.returncode == 0
    sad_p = repo / "openspec" / "architecture" / "sad.md"
    text = sad_p.read_text(encoding="utf-8")
    assert "## 骨架切片建议" not in text and "sad_status: validated" in text
    # 回落 draft 前须先把 contract 标签降回 draft（否则 B1 目标态复检拒——见 test_..._retained_validated_refused）
    sad_p.write_text(text.replace("contract[validated]", "contract[draft]"), encoding="utf-8")
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

def test_load_sad_non_utf8_fail_closed(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    sad_path = repo / "openspec" / "architecture" / "sad.md"
    sad_path.write_bytes(b"---\nsad_schema: 1\nsad_status: draft\n---\nbad \x92 byte\n")
    r = run(["set-fact", "--root", str(repo), "--fact", "positioning=answered"], tmp_path)
    assert r.returncode == 2
    assert "FAIL" in r.stderr


def test_adr_new_and_context_add_append_log_when_present(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    run(["adr-new", "--root", str(repo), "--title", "T", "--slug", "t"], tmp_path)
    run(["context-add", "--root", str(repo), "--term", "Y", "--definition", "D"], tmp_path)
    log = (repo / "openspec" / "architecture" / "sad-log.md").read_text(encoding="utf-8")
    assert "adr-new 0001-t" in log
    assert "context-add Y" in log


def test_adr_new_number_collision_exit2(tmp_path):
    """Fix 1: 重复编号应被占用检查拒绝。"""
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    # 先创建 0007-x.md
    (repo / "openspec" / "adr" / "0007-x.md").write_text("existing", encoding="utf-8")
    # 再用 --number 7 尝试创建 0007-y.md → 应返回码 2，stderr 含 0007，文件未创建
    r = run(["adr-new", "--root", str(repo), "--number", "7", "--slug", "y", "--title", "T"], tmp_path)
    assert r.returncode == 2
    assert "0007" in r.stderr and "已被占用" in r.stderr
    assert not (repo / "openspec" / "adr" / "0007-y.md").exists()


def test_context_add_single_blank_between_entries(tmp_path):
    """Fix 2: 两次连续 context-add 应只产生单空行分隔（无三连空行）。"""
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    # 第一次 context-add
    r1 = run(["context-add", "--root", str(repo), "--term", "A", "--definition", "定义A"], tmp_path)
    assert r1.returncode == 0
    # 第二次 context-add
    r2 = run(["context-add", "--root", str(repo), "--term", "B", "--definition", "定义B"], tmp_path)
    assert r2.returncode == 0
    # 检查文件内容：不应有三连空行
    ctx = (repo / "openspec" / "CONTEXT.md").read_text(encoding="utf-8")
    assert "\n\n\n" not in ctx, "检测到三连空行，说明 entry_block 空行未归一"
    # 确保两个术语都在
    assert "**A**" in ctx and "**B**" in ctx


def test_context_add_fenced_term_not_conflict(tmp_path):
    """Fix 2 回归: context-add 应 fence-aware，不与 fenced 块内的术语冲突。"""
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    ctx_path = repo / "openspec" / "CONTEXT.md"
    # 构造一个含 ## Language 和 fenced 块（块内有 **SAD**）的 CONTEXT.md
    ctx_path.write_text(
        "# Context\n\n## Language\n\n```example\n**SAD**: 这是 fenced 块内的内容，不算术语定义\n```\n",
        encoding="utf-8"
    )
    # 再用 context-add --term SAD 尝试添加 → 应返回 0（fence-aware，不认为 SAD 已存在）
    r = run(["context-add", "--root", str(repo), "--term", "SAD", "--definition", "系统架构设计"], tmp_path)
    assert r.returncode == 0, f"fence-aware 失效；stderr: {r.stderr}"
    # 确保 SAD 被新增（作为术语定义，而非冲突）
    text = ctx_path.read_text(encoding="utf-8")
    assert "**SAD**:" in text  # 术语定义形式


# ==== Code-review fix wave B（scaffold 状态机/环境/并发面）[impl-review-fix] ====================

SAD_MD = lambda repo: repo / "openspec" / "architecture" / "sad.md"
SAD_LOG = lambda repo: repo / "openspec" / "architecture" / "sad-log.md"
LINT = SCRIPT.parent / "sad_lint.py"


# ---- B1: 迁移前目标态全量不变式复检（不落盘先验） ----------------------------------------

def test_b1_validated_rejects_contract_draft(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, status="skeleton-ready", facts=ANSWERED, slice_section=True, contract="draft")
    r = run(["transition", "--root", str(repo), "--to", "validated", "--dod-confirmed"], tmp_path)
    assert r.returncode == 5 and "lint 违规" in r.stderr and "contract" in r.stderr
    # 不落盘：status 仍 skeleton-ready
    assert "sad_status: skeleton-ready" in SAD_MD(repo).read_text(encoding="utf-8")

def test_b1_validated_passes_with_contract_validated_then_lint_clean(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, status="skeleton-ready", facts=ANSWERED, slice_section=True, contract="validated")
    r = run(["transition", "--root", str(repo), "--to", "validated", "--dod-confirmed"], tmp_path)
    assert r.returncode == 0
    lr = subprocess.run([sys.executable, str(LINT), "--root", str(repo)],
                        capture_output=True, text=True, cwd=tmp_path)
    assert lr.returncode == 0, f"事后 lint 未过: {lr.stdout}{lr.stderr}"

def test_b1_validated_to_draft_retained_validated_refused(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, status="validated", facts=ANSWERED, contract="validated")
    r = run(["transition", "--root", str(repo), "--to", "draft", "--reason", "推翻"], tmp_path)
    assert r.returncode == 5 and "contract" in r.stderr
    assert "planned/draft" in r.stderr           # 回落专属文案
    assert "sad_status: validated" in SAD_MD(repo).read_text(encoding="utf-8")   # 未落盘


# ---- B2: set-fact 高阶态写 missing 拒绝 -------------------------------------------------

def test_b2_set_fact_missing_on_high_order_refused(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, status="validated", facts=ANSWERED, contract="validated")
    r = run(["set-fact", "--root", str(repo), "--fact", "positioning=missing"], tmp_path)
    assert r.returncode == 5 and "回落" in r.stderr
    assert "positioning: answered" in SAD_MD(repo).read_text(encoding="utf-8")   # 未回写

def test_b2_set_fact_missing_on_draft_ok(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, status="draft", facts=ANSWERED)
    r = run(["set-fact", "--root", str(repo), "--fact", "positioning=missing"], tmp_path)
    assert r.returncode == 0
    assert "positioning: missing" in SAD_MD(repo).read_text(encoding="utf-8")


# ---- B3: sad-log 破口两处 --------------------------------------------------------------

def test_b3_reinit_after_sad_deleted_preserves_log(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    before = SAD_LOG(repo).read_bytes()
    SAD_MD(repo).unlink()
    r = run(["init", "--root", str(repo)], tmp_path)
    assert r.returncode == 0
    after = SAD_LOG(repo).read_bytes()
    assert after[:len(before)] == before          # 旧日志字节完整保留（append-only）
    assert after.count(b"init") >= 2              # 两次 init 各留一痕

def test_b3_readonly_log_file_set_fact_exit2_sad_unchanged(tmp_path):
    if os.geteuid() == 0:
        pytest.skip("root 绕过权限位，跳过只读日志测试")
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, facts=ANSWERED)
    before = SAD_MD(repo).read_bytes()
    SAD_LOG(repo).chmod(0o444)   # 日志不可写、目录/SAD 可写 → 探针须先行拦截
    try:
        r = run(["set-fact", "--root", str(repo), "--fact", "positioning=answered"], tmp_path)
        assert r.returncode == 2
        assert SAD_MD(repo).read_bytes() == before   # 探针先行 → SAD 未动（无未审计迁移）
    finally:
        SAD_LOG(repo).chmod(0o644)


# ---- B4: set-assumption 走共享 fence-aware 附录口径 -------------------------------------

def test_b4_set_assumption_fence_aware_targets_real_row(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    # 真附录行（假设-1 未处置）；正文靠前处塞 fence 内伪行（假设-1 待校准）——旧实现会先改伪行假成功
    text = make_sad(facts=ANSWERED, assumptions=[(1, "未处置")], cache=1)
    fake_fence = "```\n| 假设-1 | §X | 伪行 | 伪 | 待校准 |\n```\n"
    text = text.replace("# SAD\n", "# SAD\n\n" + fake_fence, 1)
    SAD_MD(repo).write_text(text, encoding="utf-8")
    r = run(["set-assumption", "--root", str(repo), "--assumption", "1=接受"], tmp_path)
    assert r.returncode == 0
    out = SAD_MD(repo).read_text(encoding="utf-8")
    assert "| 假设-1 | §X | 伪行 | 伪 | 待校准 |" in out          # fence 伪行原样未动
    assert "| 假设-1 | §2 | 某推测 | 类比 | 接受 |" in out        # 真附录行被改
    # 目标行不存在 → exit 2（既有守卫，B4 复扫路径同样兜住）
    r2 = run(["set-assumption", "--root", str(repo), "--assumption", "9=接受"], tmp_path)
    assert r2.returncode == 2


# ---- B5: 读守卫补齐 --------------------------------------------------------------------

def test_b5_non_utf8_slice_file_exit2(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, facts=ANSWERED)
    slice_f = tmp_path / "s.md"; slice_f.write_bytes(b"- \x92\xff bad bytes\n")
    r = run(["transition", "--root", str(repo), "--to", "skeleton-ready",
             "--slice-file", str(slice_f)], tmp_path)
    assert r.returncode == 2 and "slice-file" in r.stderr

def test_b5_non_utf8_context_exit2(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    (repo / "openspec" / "CONTEXT.md").write_bytes(b"# Context\n\xff\xfe bad\n")
    r = run(["context-add", "--root", str(repo), "--term", "X", "--definition", "D"], tmp_path)
    assert r.returncode == 2 and "CONTEXT.md" in r.stderr


# ---- B6: OSError 边界 + preflight 类型检查 ---------------------------------------------

def test_b6_preflight_architecture_is_file_exit3(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "openspec" / "architecture").write_text("我是文件不是目录", encoding="utf-8")
    r = run(["init", "--root", str(repo)], tmp_path)
    assert r.returncode == 3 and "architecture" in r.stderr

def test_b6_readonly_architecture_dir_set_fact_exit2(tmp_path):
    if os.geteuid() == 0:
        pytest.skip("root 绕过权限位，跳过只读目录测试")
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, facts=ANSWERED)
    arch = repo / "openspec" / "architecture"
    before = SAD_MD(repo).read_bytes()
    arch.chmod(0o555)
    try:
        r = run(["set-fact", "--root", str(repo), "--fact", "positioning=answered"], tmp_path)
        assert r.returncode == 2
        assert SAD_MD(repo).read_bytes() == before   # atomic_write OSError 兜住，SAD 未动
    finally:
        arch.chmod(0o755)


# ---- B7: frontmatter 复刻消除 + 静默 no-op 堵死 ----------------------------------------

def test_b7_missing_assumptions_open_key_set_fact_exit2(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    p = SAD_MD(repo)
    text = "\n".join(l for l in p.read_text(encoding="utf-8").splitlines()
                     if not l.startswith("assumptions_open:")) + "\n"
    p.write_text(text, encoding="utf-8")
    r = run(["set-fact", "--root", str(repo), "--fact", "positioning=answered"], tmp_path)
    assert r.returncode == 2 and "assumptions_open" in r.stderr   # 非静默假成功


# ---- B8: 写命令互斥锁面 ----------------------------------------------------------------

def test_b8_preset_lock_blocks_set_fact(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, facts=ANSWERED)
    (repo / "openspec" / ".sad-scaffold.lock").write_text("held", encoding="utf-8")  # 新 mtime
    r = run(["set-fact", "--root", str(repo), "--fact", "positioning=answered"], tmp_path)
    assert r.returncode == 2 and "进行中" in r.stderr

def test_b8_concurrent_adr_new_unique_numbers(tmp_path):
    # 6 路并发 adr-new：锁串行化 → 编号互不相同 且 全部 exit 0（CI 不稳可标注但保留）
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    procs = [subprocess.Popen(
                [sys.executable, str(SCRIPT), "adr-new", "--root", str(repo),
                 "--title", f"T{i}", "--slug", f"s{i}"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=tmp_path)
             for i in range(6)]
    # 先全部并发启动，再逐个 communicate 收割：drain + close PIPE，避免 ResourceWarning
    rcs = []
    for p in procs:
        p.communicate()
        rcs.append(p.returncode)
    assert all(rc == 0 for rc in rcs), f"部分进程失败: {rcs}"
    names = sorted(p.name for p in (repo / "openspec" / "adr").glob("*.md"))
    nums = [n[:4] for n in names]
    assert len(nums) == len(set(nums)) == 6, f"编号非唯一或数量不符: {names}"


# ---- B9: log 换行注入拒绝 --------------------------------------------------------------

def test_b9_log_newline_injection_rejected(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    r = run(["log", "--root", str(repo), "--line", "正常行\n- 伪造审计行"], tmp_path)
    assert r.returncode == 2 and "换行" in r.stderr
    assert "伪造审计行" not in SAD_LOG(repo).read_text(encoding="utf-8")


# ---- B10: NFC 对称 --------------------------------------------------------------------

def test_b10_pierce_nfd_nfc_normalization_passes(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    name_nfc = unicodedata.normalize("NFC", "café端")   # é 单码点
    name_nfd = unicodedata.normalize("NFD", "café端")   # e + 组合尖音符
    assert name_nfc != name_nfd                          # 前提：两形态字节不同
    seed(repo, facts=ANSWERED, subsystems=(name_nfc,))
    _log_walkthrough(repo, tmp_path)
    slice_f = tmp_path / "s.md"; slice_f.write_text(f"- 穿越点[{name_nfd}]：§5\n", encoding="utf-8")
    r = run(["transition", "--root", str(repo), "--to", "skeleton-ready",
             "--slice-file", str(slice_f)], tmp_path)
    assert r.returncode == 0, f"NFC/NFD 归一失败: {r.stderr}"


# ---- B11: --reason 未消费告警 ---------------------------------------------------------

def test_b11_reason_unused_warns(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, facts=ANSWERED, assumptions=[(1, "接受")], cache=0)
    _log_walkthrough(repo, tmp_path)
    slice_f = tmp_path / "s.md"; slice_f.write_text("- 穿越点[采集端]：§5\n", encoding="utf-8")
    r = run(["transition", "--root", str(repo), "--to", "skeleton-ready",
             "--slice-file", str(slice_f), "--reason", "多余理由"], tmp_path)
    assert r.returncode == 0 and "未使用" in r.stdout


# ---- B12: slice 节唯一性守卫 ----------------------------------------------------------

def test_b12_transition_skeleton_rejects_preexisting_slice(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, facts=ANSWERED, assumptions=[(1, "接受")], cache=0, slice_section=True)  # 遗留切片节
    _log_walkthrough(repo, tmp_path)
    slice_f = tmp_path / "s.md"; slice_f.write_text("- 穿越点[采集端]：§5\n", encoding="utf-8")
    r = run(["transition", "--root", str(repo), "--to", "skeleton-ready",
             "--slice-file", str(slice_f)], tmp_path)
    assert r.returncode == 5 and "骨架切片建议" in r.stderr

def test_b12_transition_validated_rejects_duplicate_slice(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    p = seed(repo, status="skeleton-ready", facts=ANSWERED, slice_section=True, contract="validated")
    # 追加第二个骨架切片建议节（模拟遗留重复）
    p.write_text(p.read_text(encoding="utf-8") + "\n## 骨架切片建议\n\n- 穿越点[采集端]：§5\n",
                 encoding="utf-8")
    r = run(["transition", "--root", str(repo), "--to", "validated", "--dod-confirmed"], tmp_path)
    assert r.returncode == 5 and "骨架切片建议" in r.stderr


# ---- B13: 走查留痕存在性前置 ----------------------------------------------------------

def test_b13_transition_skeleton_requires_walkthrough_log(tmp_path):
    repo = make_repo(tmp_path); run(["init", "--root", str(repo)], tmp_path)
    seed(repo, facts=ANSWERED, assumptions=[(1, "接受")], cache=0)
    slice_f = tmp_path / "s.md"; slice_f.write_text("- 穿越点[采集端]：§5\n", encoding="utf-8")
    # 无走查/升档判定留痕 → 拒
    r = run(["transition", "--root", str(repo), "--to", "skeleton-ready",
             "--slice-file", str(slice_f)], tmp_path)
    assert r.returncode == 5 and "走查" in r.stderr
    # 补两行 log 后 → 过
    _log_walkthrough(repo, tmp_path)
    r2 = run(["transition", "--root", str(repo), "--to", "skeleton-ready",
              "--slice-file", str(slice_f)], tmp_path)
    assert r2.returncode == 0
