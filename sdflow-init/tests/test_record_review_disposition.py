"""record-review-disposition.py 的行为契约（improve-review-page-lifecycle · RVP-24，tasks 2.1）。

只经公共接口测：子进程跑 CLI，看退出码、stderr 与 review-notes.md 的字节；
「写出的块能被生成器读回」用生成器自己的 read_saved_blocks 验证。每个用例在 tmp_path 里建仓。
"""
import importlib.util
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
HACK = REPO / "sdflow-init" / "assets" / "hack"
SCRIPT = HACK / "record-review-disposition.py"
RENDERER = HACK / "render-review-page.py"

NOTES = "openspec/changes/x/review/review-notes.md"
PAGE = "design-gate.html"
PAGE_PATH = "openspec/changes/x/review/" + PAGE
HEX_A = "0123456789abcdef"
HEX_B = "fedcba9876543210"
HEX_C = "00112233445566ff"
FIXED_AT = "2023-11-14T22:13:20+00:00"


def run(stdin_text, cwd, args=("--stdin",)):
    r = subprocess.run(
        [sys.executable, "-I", str(SCRIPT), *args],
        input=stdin_text.encode("utf-8"), cwd=str(cwd), capture_output=True, timeout=60,
        env={**os.environ, "SOURCE_DATE_EPOCH": "1700000000", "TZ": "UTC"},
    )
    return subprocess.CompletedProcess(r.args, r.returncode,
                                       r.stdout.decode("utf-8", errors="replace"),
                                       r.stderr.decode("utf-8", errors="replace"))


def payload(items, page=PAGE):
    return json.dumps({"page": page, "dispositions": items}, ensure_ascii=False)


def request(items, path=NOTES, page=PAGE):
    return path + "\n" + payload(items, page) + "\n"


def item(ident=HEX_A, action="采纳", detail="已改 design", **kw):
    d = {"id": ident, "action": action, "detail": detail}
    d.update(kw)
    return d


def note_block(ids, page_path=PAGE_PATH):
    notes = [{"n": i + 1, "id": ident, "doc": "design", "path": "openspec/changes/x/design.md",
              "heading": "H", "quote": "原文%d" % i, "before": "", "after": "", "comment": "意见%d" % i}
             for i, ident in enumerate(ids)]
    line = json.dumps({"v": 2, "page": page_path, "notes": notes}, ensure_ascii=False)
    return "```json\n%s\n```\n" % line


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    (root / "openspec" / "changes" / "x" / "review").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    return root


def write_notes(repo, text):
    p = repo / NOTES
    p.write_bytes(text.encode("utf-8"))
    return p


def assert_rejected(r, notes_file, before, *parts):
    assert r.returncode == 1, (r.stdout, r.stderr)
    assert r.stdout == ""
    assert "✗ problem=" in r.stderr and " cause=" in r.stderr and " fix=" in r.stderr
    for part in parts:
        assert part in r.stderr, (part, r.stderr)
    assert notes_file.read_bytes() == before, "拒绝时不得改动 review-notes.md"
    assert [p.name for p in notes_file.parent.iterdir() if p.name.startswith(".")] == []


def load_renderer():
    spec = importlib.util.spec_from_file_location("render_review_page_for_record_test", RENDERER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── 成功 ────────────────────────────────────────────────────────────────────

def test_records_two_dispositions_as_one_block(repo):
    notes = write_notes(repo, "说明\n" + note_block([HEX_A, HEX_B]))
    before = notes.read_bytes()
    r = run(request([item(HEX_A, "采纳", "已改"), item(HEX_B, "不采纳", "与目标冲突")]), repo)
    assert r.returncode == 0, r.stderr
    assert "已记录 2 条处置：%s" % NOTES in r.stdout
    after = notes.read_bytes()
    assert after.startswith(before)
    appended = after[len(before):].decode("utf-8").splitlines()
    assert appended[0] == "```json" and appended[2] == "```" and len(appended) == 3
    block = json.loads(appended[1])
    assert block == {"v": 1, "kind": "disposition", "page": PAGE, "at": FIXED_AT,
                     "dispositions": [{"id": HEX_A, "action": "采纳", "detail": "已改"},
                                      {"id": HEX_B, "action": "不采纳", "detail": "与目标冲突"}]}


def test_transfer_disposition_carries_issue_number(repo):
    notes = write_notes(repo, note_block([HEX_A]))
    r = run(request([item(action="转 issue", detail="拆到下个 change", issue="T404")]), repo)
    assert r.returncode == 0, r.stderr
    block = json.loads(notes.read_text(encoding="utf-8").splitlines()[-2])
    assert block["dispositions"] == [{"id": HEX_A, "action": "转 issue", "detail": "拆到下个 change",
                                      "issue": "T404"}]


def test_detail_with_backticks_and_newlines_stays_inside_one_json_line(repo):
    notes = write_notes(repo, note_block([HEX_A]))
    tricky = "含 ``` 与换行\n第二行 `x`"
    r = run(request([item(detail=tricky)]), repo)
    assert r.returncode == 0, r.stderr
    _, dispositions = load_renderer().read_saved_blocks(notes, PAGE)
    assert dispositions[HEX_A]["detail"] == tricky


def test_original_file_mode_is_preserved(repo):
    if os.name == "nt":
        pytest.skip("Windows 没有 POSIX 权限位")
    notes = write_notes(repo, note_block([HEX_A]))
    notes.chmod(0o664)
    assert run(request([item()]), repo).returncode == 0
    assert stat.S_IMODE(notes.stat().st_mode) == 0o664


def test_written_block_is_read_back_by_renderer(repo):
    notes = write_notes(repo, note_block([HEX_A, HEX_B]))
    r = run(request([item(HEX_A, "部分采纳", "改了一半")]), repo)
    assert r.returncode == 0, r.stderr
    saved, dispositions = load_renderer().read_saved_blocks(notes, PAGE)
    assert [n["id"] for n in saved] == [HEX_A, HEX_B]
    assert dispositions == {HEX_A: {"action": "部分采纳", "detail": "改了一半", "issue": "", "at": FIXED_AT}}


def test_second_record_for_same_id_is_accepted_and_later_one_wins(repo):
    notes = write_notes(repo, note_block([HEX_A]))
    assert run(request([item(action="不采纳", detail="先记")]), repo).returncode == 0
    assert run(request([item(action="采纳", detail="后记")]), repo).returncode == 0
    _, dispositions = load_renderer().read_saved_blocks(notes, PAGE)
    assert (dispositions[HEX_A]["action"], dispositions[HEX_A]["detail"]) == ("采纳", "后记")


def test_runs_from_a_subdirectory(repo):
    write_notes(repo, note_block([HEX_A]))
    assert run(request([item()]), repo / "openspec").returncode == 0


# ── 原文件末尾无换行 ─────────────────────────────────────────────────────────

def test_missing_trailing_newline_gets_one_before_the_block(repo):
    notes = write_notes(repo, note_block([HEX_A]) + "末行没有换行")
    r = run(request([item()]), repo)
    assert r.returncode == 0, r.stderr
    lines = notes.read_text(encoding="utf-8").split("\n")
    assert "末行没有换行" in lines  # 原末行独占一行，没有被块的开围栏接在后面
    assert lines[lines.index("末行没有换行") + 1] == "```json"
    _, dispositions = load_renderer().read_saved_blocks(notes, PAGE)
    assert list(dispositions) == [HEX_A]


def test_empty_notes_file_is_rejected_for_lack_of_ids_not_crashed(repo):
    notes = write_notes(repo, "")
    r = run(request([item()]), repo)
    assert_rejected(r, notes, b"", HEX_A, "没有带 ID 的已落盘意见")


# ── 拒写 ────────────────────────────────────────────────────────────────────

def test_unknown_id_rejected_and_legal_ids_listed(repo):
    notes = write_notes(repo, note_block([HEX_A, HEX_B]))
    before = notes.read_bytes()
    r = run(request([item(HEX_A), item(HEX_C)]), repo)
    assert_rejected(r, notes, before, HEX_C, "不属于该页", HEX_A, HEX_B)


def test_note_of_another_page_is_not_a_legal_id(repo):
    notes = write_notes(repo, note_block([HEX_A], "openspec/changes/x/review/shipped.html"))
    before = notes.read_bytes()
    assert_rejected(run(request([item()]), repo), notes, before, HEX_A, "不属于该页")


def test_transfer_without_issue_number_rejected(repo):
    notes = write_notes(repo, note_block([HEX_A]))
    before = notes.read_bytes()
    r = run(request([item(action="转 issue")]), repo)
    assert_rejected(r, notes, before, "转 issue", "没有 issue 编号")


@pytest.mark.parametrize("action", ["采纳", "部分采纳", "不采纳"])
def test_non_transfer_with_issue_number_rejected(repo, action):
    notes = write_notes(repo, note_block([HEX_A]))
    before = notes.read_bytes()
    r = run(request([item(action=action, issue="T404")]), repo)
    assert_rejected(r, notes, before, "不得带 issue 编号")


def test_duplicate_id_in_one_batch_rejected(repo):
    notes = write_notes(repo, note_block([HEX_A]))
    before = notes.read_bytes()
    r = run(request([item(), item(action="不采纳")]), repo)
    assert_rejected(r, notes, before, "重复")


@pytest.mark.parametrize("bad", [
    item(action="搁置"),
    item(detail=""),
    {"id": HEX_A, "action": "采纳"},
    item(extra="x"),
    "不是对象",
])
def test_ill_formed_item_rejected(repo, bad):
    notes = write_notes(repo, note_block([HEX_A]))
    before = notes.read_bytes()
    assert_rejected(run(request([bad]), repo), notes, before)


def test_one_bad_item_blocks_the_whole_batch(repo):
    notes = write_notes(repo, note_block([HEX_A, HEX_B]))
    before = notes.read_bytes()
    r = run(request([item(HEX_A), item(HEX_B, action="转 issue")]), repo)
    assert_rejected(r, notes, before)


@pytest.mark.parametrize("path, cause", [
    ("openspec/changes/x/review/other.md", "不以 /review/review-notes.md 结尾"),
    ("../outside/review/review-notes.md", ".. 段"),
    ("/abs/openspec/x/review/review-notes.md", "绝对路径"),
    ("docs/review/review-notes.md", "不以 openspec/ 开头"),
])
def test_illegal_path_rejected_without_writing(repo, path, cause):
    notes = write_notes(repo, note_block([HEX_A]))
    before = notes.read_bytes()
    r = run(request([item()], path=path), repo)
    assert r.returncode == 1 and r.stdout == ""
    assert cause in r.stderr
    assert notes.read_bytes() == before
    assert not any(p.name.startswith("review-notes") and p != notes for p in notes.parent.iterdir())


def test_symlinked_notes_file_rejected(repo):
    if os.name == "nt":
        pytest.skip("Windows 建符号链接需要特权")
    real = repo / "openspec" / "changes" / "x" / "real.md"
    real.write_bytes(note_block([HEX_A]).encode("utf-8"))
    before = real.read_bytes()
    (repo / NOTES).symlink_to(real)
    r = run(request([item()]), repo)
    assert r.returncode == 1 and "符号链接" in r.stderr
    assert real.read_bytes() == before


def test_non_utf8_notes_file_reports_unreadable_not_unknown_id(repo):
    notes = repo / NOTES
    notes.write_bytes(note_block([HEX_A]).encode("utf-8") + b"\xff\xfe bad\n")   # [impl-review-fix] C2
    before = notes.read_bytes()
    r = run(request([item()]), repo)
    assert r.returncode == 1 and r.stdout == ""
    assert "无法读取" in r.stderr and "不属于该页" not in r.stderr
    assert notes.read_bytes() == before


def test_missing_notes_file_rejected_and_not_created(repo):
    r = run(request([item()]), repo)
    assert r.returncode == 1 and r.stdout == ""
    assert "review-notes.md 不存在" in r.stderr
    assert not (repo / NOTES).exists()
    assert [p.name for p in (repo / NOTES).parent.iterdir()] == []


def test_missing_parent_directory_rejected(repo):
    r = run(request([item()], path="openspec/changes/nope/review/review-notes.md"), repo)
    assert r.returncode == 1 and "父目录不存在" in r.stderr


@pytest.mark.parametrize("stdin_text", [
    "",
    NOTES + "\n",
    NOTES + "\n{not json\n",
    NOTES + "\n[]\n",
    NOTES + "\n" + json.dumps({"dispositions": [item()]}) + "\n",
    NOTES + "\n" + json.dumps({"page": PAGE, "dispositions": []}) + "\n",
])
def test_malformed_stdin_rejected_without_writing(repo, stdin_text):
    notes = write_notes(repo, note_block([HEX_A]))
    before = notes.read_bytes()
    assert_rejected(run(stdin_text, repo), notes, before, "处置输入格式不对")


# ── 用法错误 ─────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("args", [(), ("--stdin", "extra"), (NOTES,), ("--help",)])
def test_usage_errors_exit_64(repo, args):
    notes = write_notes(repo, note_block([HEX_A]))
    before = notes.read_bytes()
    r = run(request([item()]), repo, args=args)
    assert r.returncode == 64
    assert "✗ problem=用法错误" in r.stderr
    assert notes.read_bytes() == before


# ── 写入失败 ─────────────────────────────────────────────────────────────────

@pytest.mark.skipif(os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
                    reason="目录只读权限在 Windows 与 root 下不生效")
def test_unwritable_directory_fails_without_partial_block_or_temp(repo):
    notes = write_notes(repo, note_block([HEX_A]))
    before = notes.read_bytes()
    notes.parent.chmod(stat.S_IRUSR | stat.S_IXUSR)
    try:
        r = run(request([item()]), repo)
    finally:
        notes.parent.chmod(stat.S_IRWXU)
    assert r.returncode == 1 and "写入失败" in r.stderr
    assert notes.read_bytes() == before
    assert [p.name for p in notes.parent.iterdir()] == ["review-notes.md"]


def test_script_has_reconfigure_prelude():
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'for _s in (sys.stdout, sys.stderr):\n    try: _s.reconfigure(encoding="utf-8", errors="replace")\n' \
           '    except Exception: pass\n' in text
