import subprocess, sys, ast, importlib.util, os
from pathlib import Path
import pytest

TOOLS = Path(__file__).resolve().parent.parent
SCRIPT = TOOLS / "outside_voice_guard.py"


def _mod():
    spec = importlib.util.spec_from_file_location("outside_voice_guard", SCRIPT)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


# --- 夹具构造：造一个 change 目录（源文件 + 一份 gstack-review.md），mtime 显式钉死 ---

def _mode_anchor(mode="native"):
    return f'<!-- sdflow:step1-broad-review v1 mode="{mode}" -->'


def _ov_anchor(findings=1, runner="codex"):
    return (f'<!-- sdflow:outside-voice v1 site="design-voice" guard="none" '
            f'runner="{runner}" reason_code="ok" findings="{findings}" truncated="false" -->')


def _make_change(tmp_path, mode="native", codex=True, findings=1,
                 src_mtime=1_000_000, product_mtime=2_000_000, extra_body=""):
    """返回 (review_path, change_dir)。product_mtime > src_mtime = fresh；反之 stale。"""
    cd = tmp_path / "changes" / "mychange"
    (cd / "specs" / "cap").mkdir(parents=True)
    for name in ("proposal.md", "design.md", "tasks.md"):
        f = cd / name; f.write_text(f"# {name}\n", encoding="utf-8")
        os.utime(f, (src_mtime, src_mtime))
    sp = cd / "specs" / "cap" / "spec.md"; sp.write_text("## ADDED\n", encoding="utf-8")
    os.utime(sp, (src_mtime, src_mtime))
    body = _mode_anchor(mode) + "\n# review\n" + extra_body
    if codex:
        body += "\n" + _ov_anchor(findings)
    rp = cd / "gstack-review.md"; rp.write_text(body + "\n", encoding="utf-8")
    os.utime(rp, (product_mtime, product_mtime))
    return rp, cd


# --- 六 reason_code 各一正例（直调核心归约函数）---

def test_none_reusable(tmp_path):
    m = _mod(); rp, cd = _make_change(tmp_path)
    assert m.classify(rp, cd) == "none"


def test_simulated_source(tmp_path):
    m = _mod(); rp, cd = _make_change(tmp_path, mode="simulated")
    assert m.classify(rp, cd) == "simulated-source"


def test_stale(tmp_path):
    m = _mod(); rp, cd = _make_change(tmp_path, product_mtime=500_000)   # 早于源 1M
    assert m.classify(rp, cd) == "stale"


def test_section_not_found(tmp_path):
    m = _mod(); rp, cd = _make_change(tmp_path, codex=False)
    assert m.classify(rp, cd) == "section-not-found"


def test_zero_findings(tmp_path):
    m = _mod(); rp, cd = _make_change(tmp_path, findings=0)
    assert m.classify(rp, cd) == "zero-findings"


def test_file_missing(tmp_path):
    m = _mod(); rp, cd = _make_change(tmp_path); rp.unlink()
    assert m.classify(rp, cd) == "file-missing"


def test_reason_codes_are_six_enum():
    m = _mod()
    assert set(m.REASON_CODES) == {
        "none", "file-missing", "section-not-found", "zero-findings", "stale", "simulated-source"}
    assert len(m.REASON_CODES) == 6


# --- 坏输入 fail-closed（EmitError；非静默产码掩盖损坏）---

def test_anchor_missing_fail_closed(tmp_path):
    m = _mod(); rp, cd = _make_change(tmp_path)
    rp.write_text("# no anchor here\n" + _ov_anchor(1) + "\n", encoding="utf-8")
    os.utime(rp, (2_000_000, 2_000_000))
    with pytest.raises(m.EmitError):
        m.classify(rp, cd)


def test_mode_non_enum_fail_closed(tmp_path):
    m = _mod(); rp, cd = _make_change(tmp_path, mode="adapted")   # 非 native|simulated
    with pytest.raises(m.EmitError):
        m.classify(rp, cd)


def test_change_dir_missing_fail_closed(tmp_path):
    m = _mod(); rp, cd = _make_change(tmp_path)
    with pytest.raises(m.EmitError):
        m.classify(rp, tmp_path / "nonexistent")


def test_change_dir_no_sources_fail_closed(tmp_path):
    m = _mod(); rp, cd = _make_change(tmp_path)
    empty = tmp_path / "empty"; empty.mkdir()
    with pytest.raises(m.EmitError):
        m.classify(rp, empty)


# --- 三前置按序（来源 > 新鲜度 > 结构）---

def test_simulated_precedes_stale(tmp_path):
    m = _mod(); rp, cd = _make_change(tmp_path, mode="simulated", product_mtime=500_000)
    assert m.classify(rp, cd) == "simulated-source"   # 来源判先于新鲜度


def test_stale_precedes_structure(tmp_path):
    m = _mod(); rp, cd = _make_change(tmp_path, codex=False, product_mtime=500_000)
    assert m.classify(rp, cd) == "stale"              # 新鲜度先于结构


# --- 新鲜度：排除评审产物自身 / specs 计入源 ---

def test_review_artifacts_excluded_from_freshness(tmp_path):
    m = _mod(); rp, cd = _make_change(tmp_path)        # product 2M > src 1M
    srr = cd / "spec-review-report.md"; srr.write_text("# report\n", encoding="utf-8")
    os.utime(srr, (9_000_000, 9_000_000))             # 评审产物远新于 product
    ovdir = cd / ".outside-voice"; ovdir.mkdir()
    ctx = ovdir / "design-voice-context.md"; ctx.write_text("ctx\n", encoding="utf-8")
    os.utime(ctx, (9_000_000, 9_000_000))
    assert m.classify(rp, cd) == "none"               # 评审产物不算源 → 不 stale


def test_specs_file_counts_as_source_stale(tmp_path):
    m = _mod(); rp, cd = _make_change(tmp_path)        # product 2M, src 1M
    sp = cd / "specs" / "cap" / "spec.md"
    os.utime(sp, (5_000_000, 5_000_000))              # specs 文件新于 product → stale
    assert m.classify(rp, cd) == "stale"


# --- codex 段 best-effort 解析 ---

def test_codex_hash_label_fallback(tmp_path):
    m = _mod(); rp, cd = _make_change(
        tmp_path, codex=False, extra_body="- codex#1 finding a\n- codex#2 finding b\n")
    assert m.classify(rp, cd) == "none"               # 2 个 codex#N 标签 → findings>0


def test_malformed_codex_findings_section_not_found(tmp_path):
    m = _mod(); rp, cd = _make_change(tmp_path, codex=False)
    bad = _mode_anchor("native") + '\n<!-- sdflow:outside-voice v1 runner="codex" findings="oops" -->\n'
    rp.write_text(bad, encoding="utf-8"); os.utime(rp, (2_000_000, 2_000_000))
    assert m.classify(rp, cd) == "section-not-found"  # 畸形 findings → best-effort fail-closed


def test_claude_fallback_runner_not_codex(tmp_path):
    m = _mod(); rp, cd = _make_change(tmp_path, codex=False)
    body = _mode_anchor("native") + "\n" + _ov_anchor(3, runner="claude-fallback") + "\n"
    rp.write_text(body, encoding="utf-8"); os.utime(rp, (2_000_000, 2_000_000))
    assert m.classify(rp, cd) == "section-not-found"  # 非 codex runner 不计入 codex 段


# --- fence 感知：fence 内的示例锚不参与匹配（与姊妹校验器 anchor_lint 同口径）---

def test_fenced_codex_anchor_not_counted_findings(tmp_path):
    """fence 内的 runner=codex 示例锚（文档演示）不得计入 findings——真实无 codex 锚 → section-not-found，非 none（假绿）。"""
    m = _mod()
    fenced = "```\n" + _ov_anchor(2, runner="codex") + "\n```\n"
    rp, cd = _make_change(tmp_path, codex=False, extra_body=fenced)   # 无真实 codex 锚，仅 fence 内示例
    assert m.classify(rp, cd) == "section-not-found"


def test_fenced_step1_anchor_not_taken_as_mode(tmp_path):
    """fence 内的 simulated step1 示例锚不得被 parse_mode 取——fence 外真实 native 锚为准 → 不判 simulated-source。"""
    m = _mod(); rp, cd = _make_change(tmp_path)
    body = ("```\n" + _mode_anchor("simulated") + "\n```\n"
            + _mode_anchor("native") + "\n# review\n" + _ov_anchor(1) + "\n")
    rp.write_text(body, encoding="utf-8"); os.utime(rp, (2_000_000, 2_000_000))
    assert m.classify(rp, cd) == "none"               # fence 内 simulated 被跳过 → 取 fence 外 native


# --- 纯 stdlib / 无 subprocess / 无 git fork（静态断言，comment/docstring 安全）---

def test_no_subprocess_no_os_import_ast():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                imported.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module.split(".")[0])
    assert "subprocess" not in imported    # 无 subprocess → 无 fork/exec 子进程（含 git）
    assert "os" not in imported            # 连 os 都不引 → 无 os.system/fork/exec/popen 通路


def test_no_exec_tokens_in_source():
    src = SCRIPT.read_text(encoding="utf-8")
    for tok in ("os.system", "os.popen", "os.fork", "os.exec", "Popen", "check_output", "check_call"):
        assert tok not in src


# --- CLI 契约（子进程；exit 码 + stdout reason / stderr FAIL 分流）---

def _run(review_path, change_dir):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--review-path", str(review_path),
         "--change-dir", str(change_dir)], capture_output=True, text=True)


def test_cli_none_exit0(tmp_path):
    rp, cd = _make_change(tmp_path)
    r = _run(rp, cd)
    assert r.returncode == 0 and r.stdout.strip() == "none"


def test_cli_simulated_exit_nonzero_stdout(tmp_path):
    rp, cd = _make_change(tmp_path, mode="simulated")
    r = _run(rp, cd)
    assert r.returncode != 0 and r.stdout.strip() == "simulated-source" and r.stderr.strip() == ""


def test_cli_stale_exit_nonzero(tmp_path):
    rp, cd = _make_change(tmp_path, product_mtime=500_000)
    r = _run(rp, cd)
    assert r.returncode != 0 and r.stdout.strip() == "stale"


def test_cli_bad_input_fail_closed_stderr_no_stdout(tmp_path):
    rp, cd = _make_change(tmp_path, mode="adapted")
    r = _run(rp, cd)
    assert (r.returncode != 0 and r.stdout.strip() == ""
            and "[outside_voice_guard] FAIL" in r.stderr and "Traceback" not in r.stderr)


def test_cli_file_missing(tmp_path):
    rp, cd = _make_change(tmp_path); rp.unlink()
    r = _run(rp, cd)
    assert r.returncode != 0 and r.stdout.strip() == "file-missing"
