"""check-notes-path.py 的行为契约（harden-review-page-followups · RVP-06，tasks 5.0）。

只经公共接口测：子进程跑 CLI，看退出码与 stdout/stderr。每个用例在 tmp_path 里 git init 建仓。
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "sdflow-init" / "assets" / "hack" / "check-notes-path.py"

GOOD = "openspec/changes/x/review/review-notes.md"
FIX = "fix=给出正确路径，或回复「不落盘，直接处理」"


def run(args, cwd, stdin=None):
    # stdin 按字节送：text 模式在 Windows 上会把写入的 "\n" 换成 "\r\n"，
    # 用例想送的 "...\r\n" 实际变成 "...\r\r\n"，测的就不是 CRLF 了。
    r = subprocess.run(
        [sys.executable, "-I", str(SCRIPT), *args],
        input=None if stdin is None else stdin.encode("utf-8"),
        cwd=str(cwd), capture_output=True, timeout=60,
    )
    return subprocess.CompletedProcess(
        r.args, r.returncode,
        r.stdout.decode("utf-8", errors="replace"),
        r.stderr.decode("utf-8", errors="replace"),
    )


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    (root / "openspec" / "changes" / "x" / "review").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    return root


def assert_rejected(r, cause_part):
    assert r.returncode == 1, (r.stdout, r.stderr)
    assert r.stdout == ""
    line = r.stderr.strip()
    assert "\n" not in line
    assert line.startswith("✗ problem=粘回路径不能写入 cause=")
    assert cause_part in line
    assert line.endswith(FIX)


def test_valid_path_passes_and_prints_absolute_target(repo):
    r = run([GOOD], repo)
    assert r.returncode == 0, r.stderr
    assert Path(r.stdout.strip()) == (repo / GOOD).resolve()
    assert r.stdout.count("\n") == 1


def test_valid_path_passes_from_subdirectory(repo):
    r = run([GOOD], repo / "openspec" / "changes")
    assert r.returncode == 0, r.stderr
    assert Path(r.stdout.strip()) == (repo / GOOD).resolve()


def test_archive_path_passes(repo):
    d = repo / "openspec/changes/archive/2026-10-20-x/review"
    d.mkdir(parents=True)
    r = run(["openspec/changes/archive/2026-10-20-x/review/review-notes.md"], repo)
    assert r.returncode == 0, r.stderr


def test_existing_regular_target_passes(repo):
    (repo / GOOD).write_text("old\n", encoding="utf-8")
    assert run([GOOD], repo).returncode == 0


def test_script_never_writes(repo):
    run([GOOD], repo)
    assert not (repo / GOOD).exists()


def test_dotdot_segment_rejected(repo):
    r = run(["openspec/changes/x/review/../../../../etc/review/review-notes.md"], repo)
    assert_rejected(r, "..")


def test_not_under_openspec_rejected(repo):
    (repo / "docs" / "review").mkdir(parents=True)
    assert_rejected(run(["docs/review/review-notes.md"], repo), "openspec/")


def test_other_repo_absolute_path_rejected(repo):
    assert_rejected(run(["/tmp/other-repo/openspec/changes/x/review/review-notes.md"], repo), "绝对路径")


def test_wrong_suffix_rejected(repo):
    assert_rejected(run(["openspec/changes/x/review/notes.md"], repo), "/review/review-notes.md")


def test_backslash_rejected(repo):
    assert_rejected(run([r"openspec\changes\x\review\review-notes.md"], repo), "反斜杠")


@pytest.mark.parametrize("p", [
    "openspec/changes//x/review/review-notes.md",
    "openspec/changes/./x/review/review-notes.md",
])
def test_empty_or_dot_segment_rejected(repo, p):
    assert_rejected(run([p], repo), "空段或 . 段")


def test_review_dir_symlink_to_outside_rejected(repo, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    shutil_target = repo / "openspec/changes/y"
    shutil_target.mkdir()
    os.symlink(outside, shutil_target / "review")
    r = run(["openspec/changes/y/review/review-notes.md"], repo)
    assert_rejected(r, "真实路径")
    assert not (outside / "review-notes.md").exists()


def test_missing_parent_dir_rejected_and_not_created(repo):
    r = run(["openspec/changes/nope/review/review-notes.md"], repo)
    assert_rejected(r, "父目录不存在")
    assert not (repo / "openspec/changes/nope").exists()


def test_target_symlink_rejected(repo, tmp_path):
    victim = tmp_path / "victim.md"
    victim.write_text("v", encoding="utf-8")
    os.symlink(victim, repo / GOOD)
    assert_rejected(run([GOOD], repo), "符号链接")


def test_outside_git_repo_rejected(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    assert_rejected(run([GOOD], plain), "git 仓")


def test_no_args_is_usage_error(repo):
    r = run([], repo)
    assert r.returncode == 64
    assert r.stdout == ""


def test_two_args_is_usage_error(repo):
    assert run([GOOD, GOOD], repo).returncode == 64


# ── [impl-review-fix] --stdin 模式与目录目标 ──────────────────────────────

def test_stdin_valid_path_passes(repo):
    r = run(["--stdin"], repo, stdin=GOOD + "\n")
    assert r.returncode == 0, r.stderr
    assert Path(r.stdout.strip()) == (repo / GOOD).resolve()


def test_stdin_crlf_and_no_trailing_newline(repo):
    assert run(["--stdin"], repo, stdin=GOOD + "\r\n").returncode == 0
    assert run(["--stdin"], repo, stdin=GOOD).returncode == 0


def test_stdin_only_first_line_is_used(repo):
    r = run(["--stdin"], repo, stdin=GOOD + "\n$(touch pwned)\n")
    assert r.returncode == 0, r.stderr
    assert not (repo / "pwned").exists()


@pytest.mark.parametrize("p", [
    "openspec/changes/it's/review/review-notes.md",
    "openspec/changes/$(touch pwned)/review/review-notes.md",
    "openspec/changes/`touch pwned`/review/review-notes.md",
])
def test_stdin_shell_metacharacters_are_data(repo, p):
    r = run(["--stdin"], repo, stdin=p + "\n")
    assert_rejected(r, "父目录不存在")
    assert not (repo / "pwned").exists()


def test_stdin_empty_rejected(repo):
    assert run(["--stdin"], repo, stdin="").returncode == 1
    assert run(["--stdin"], repo, stdin="\n").returncode == 1


def test_stdin_with_positional_is_usage_error(repo):
    r = run(["--stdin", GOOD], repo, stdin=GOOD)
    assert r.returncode == 64
    assert r.stdout == ""


def test_target_directory_rejected(repo):
    (repo / GOOD).mkdir()
    assert_rejected(run([GOOD], repo), "目录")
